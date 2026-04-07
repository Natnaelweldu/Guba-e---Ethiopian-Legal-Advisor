from huggingface_hub import InferenceClient
from groq import Groq
from pinecone import Pinecone
import os 
from dotenv import load_dotenv
from rich import print as rprint

# --- Setup ---
load_dotenv()

# Initialize Clients
hf_client = InferenceClient(api_key=os.getenv("HUGGING_FACE_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

# Connect to your specific Pinecone Index
index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "gubae-legal-index"))

MODEL_ID = "BAAI/bge-m3"

def get_all_processed_files():
    processed_dir = "/home/natty_w/Nate_Theodore/MLops/projects/Guba-e---Ethiopian-Legal-Advisor/back-end/data/processed"
    
    # Check if the directory even exists to avoid errors
    if not os.path.exists(processed_dir):
        print(f"Directory {processed_dir} not found. Returning empty list.")
        return []

    processed_files = os.listdir(processed_dir)
    
    # Return the list
    return processed_files


def get_relevant_context(user_query, top_k=3):
    """Step 1: The Retriever - Finds the law in the cloud database."""
    
    # 1. Vectorize the question
    query_vector = hf_client.feature_extraction(user_query, model=MODEL_ID)
    
    # Convert from NumPy array to standard Python list
    if hasattr(query_vector, "tolist"):
        query_vector = query_vector.tolist()
    
    # Safety check: Pinecone expects a flat list of 1024 floats.
    # If Hugging Face returns a nested list [[0.1, 0.2...]], we flatten it.
    if isinstance(query_vector[0], list):
        query_vector = query_vector[0]
    
    # 2. Search Pinecone Cloud
    results = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )
    
    # 3. Extract the text and sources from the Pinecone 'matches'
    context_chunks = []
    sources = []
    
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        
        # Grab the actual text we stashed in the metadata
        context_chunks.append(meta.get("text", ""))
        
        # Keep track of the citation
        sources.append({
            "source": meta.get("source", "Unknown"),
            "page_num": meta.get("page_num", "?")
        })
        
    context_text = "\n---\n".join(context_chunks)
    
    return context_text, sources

def generate_legal_answer(user_query, context):
    """Step 2: The Generator - Uses Groq to explain the law."""
    system_prompt = f"""
    You are 'Guba'e', a ruthless and precise Ethiopian Legal AI Assistant.
    Your goal is to provide accurate answers based ONLY on the provided legal context.
    
    STRICT RULES:
    1. If the answer is not in the context, say: "I'm sorry, I cannot find this in the official proclamations."
    2. Always cite the Source and Page number provided in the context.
    3. Keep your tone professional, direct, and efficient.
    
    LEGAL CONTEXT:
    {context}
    """

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.1, # Low temperature = No rambling, high accuracy
    )
    
    return response.choices[0].message.content

def ask_gubae(question):
    """The Main Entry Point for the User."""
    rprint(f"[bold yellow]Searching the cloud archives for:[/bold yellow] {question}...")
    
    # 1. Get the facts from Pinecone
    context, sources = get_relevant_context(question)
    
    # 2. Get the explanation from Groq
    answer = generate_legal_answer(question, context)
    
    rprint("\n[bold green]GUBA'E RESPONSE:[/bold green]")
    print(answer)
    
    # Print the exact sources found
    print("\n[dim]Sources Found in Database:[/dim]")
    for s in sources:
        print(f"- {s['source']} (Page {s['page_num']})")
        
    return answer, sources

# --- Run it! ---
# if __name__ == "__main__":
#     user_q = input("Ask Guba'e about Ethiopian Law: ")
#     ask_gubae(user_q)