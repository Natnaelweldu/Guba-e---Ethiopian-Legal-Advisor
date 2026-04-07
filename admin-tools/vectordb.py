import json
import re
import os
from huggingface_hub import InferenceClient
from pinecone import Pinecone
from dotenv import load_dotenv
from rich import print as rprint

# --- Configuration ---
load_dotenv()
INPUT_JSONL = "/home/natty_w/Nate_Theodore/MLops/projects/Guba-e---Ethiopian-Legal-Advisor/back-end/OUTPUT_JSONL/processed_data.jsonl"
MODEL_ID = "BAAI/bge-m3"
BATCH_SIZE = 16  # Keeping at 16 to respect Hugging Face free-tier payload limits

# Initialize Clients
hf_client = InferenceClient(api_key=os.getenv("HUGGING_FACE_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Use the exact index name you created in the dashboard
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "gubae-legal-index"))

def create_unique_id(filename, page_num, chunk_index):
    clean_name = filename.replace(".pdf", "")
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', clean_name)
    return f"{clean_name}_P{page_num}_C{chunk_index}"

def process_cloud_batch(batch):
    if not batch:
        return

    # Extract just the text to send to Hugging Face
    texts = [item["content"] for item in batch]
    ids = [item["id"] for item in batch]

    rprint(f"[bold blue]Processing {len(texts)} chunks via HF -> Pinecone...[/bold blue]")

    try:
        # 1. Get Embeddings from Hugging Face Cloud
        embeddings = hf_client.feature_extraction(texts, model=MODEL_ID)
        
        # 2. Format for Pinecone
        # Pinecone requires a list of dicts: {"id": str, "values": list, "metadata": dict}
        pinecone_vectors = []
        for i in range(len(batch)):
            pinecone_vectors.append({
                "id": ids[i],
                "values": embeddings[i],
                "metadata": {
                    "text": texts[i],  # CRITICAL: Text must live inside metadata now
                    "source": batch[i]["metadata"]["source"],
                    "page_num": batch[i]["metadata"]["page_num"]
                }
            })
        
        # 3. Upsert to Pinecone Cloud
        index.upsert(vectors=pinecone_vectors)
        
    except Exception as e:
        rprint(f"[red]Cloud Error: {e}[/red]")

def run_ingestion():
    if not os.path.exists(INPUT_JSONL):
        rprint(f"[red]Error: {INPUT_JSONL} not found.[/red]")
        return

    current_batch = []
    
    with open(INPUT_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            
            chunk_data = {
                "id": create_unique_id(data["source"], data["page_num"], data["chunk_id"]),
                "content": data["content"],
                "metadata": {
                    "source": data["source"],
                    "page_num": data["page_num"]
                }
            }
            current_batch.append(chunk_data)

            if len(current_batch) == BATCH_SIZE:
                process_cloud_batch(current_batch)
                current_batch = []

        # Final cleanup for remaining chunks
        if current_batch:
            process_cloud_batch(current_batch)

    rprint("[bold green]Guba'e Database is now permanently synced with Pinecone Cloud![/bold green]")

if __name__ == "__main__":
    run_ingestion()