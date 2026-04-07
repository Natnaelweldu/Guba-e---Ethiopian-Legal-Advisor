import fitz  # PyMuPDF
import cv2
import pytesseract
import numpy as np
import json
import os
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Configuration
INPUT_DIR = "/home/natty_w/Nate_Theodore/MLops/projects/Guba-e---Ethiopian-Legal-Advisor/back-end/raw_pdfs"
OUTPUT_JSONL = "/home/natty_w/Nate_Theodore/MLops/projects/Guba-e---Ethiopian-Legal-Advisor/back-end/OUTPUT_JSONL/processed_data.jsonl"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

def is_file_already_processed(filename):
    # Check if this filename exists in your 'processed' folder
    processed_path = os.path.join("data/processed", filename)
    return os.path.exists(processed_path)

def get_all_processed_files():
    processed_dir = "data/processed"
    
    # Check if the directory even exists to avoid errors
    if not os.path.exists(processed_dir):
        print(f"Directory {processed_dir} not found. Returning empty list.")
        return []

    processed_files = os.listdir(processed_dir)
    
    # Return the list
    return processed_files

def clean_and_ocr(pix):
    """Converts PDF page to image, crops the right side (English), and runs OCR."""
    # Convert PyMuPDF pixmap to OpenCV format
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
    if pix.n == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Crop the right 48% of the page (Bypassing the left Amharic column)
    height, width = gray.shape
    crop_x = int(width * 0.52) 
    cropped_img = gray[:, crop_x:width]
    
    # Adaptive thresholding to clean gray backgrounds/noise
    thresh = cv2.adaptiveThreshold(
        cropped_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    
    # Run Tesseract OCR strictly in English
    text = pytesseract.image_to_string(thresh, lang='eng')
    return text.strip()

def process_document(pdf_path):
    """Processes a single PDF, handling the Digital/Scan/Bilingual routing."""
    doc_name = os.path.basename(pdf_path)
    doc = fitz.open(pdf_path)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    all_chunks = []
    chunk_counter = 0

    print(f"Processing: {doc_name} ({len(doc)} pages)")

    for page_num in range(len(doc)):
        page = doc[page_num]
        digital_text = page.get_text().strip()
        
        # The Gatekeeper: Check for bilingual Gazette markers
        is_bilingual_layout = "ነጋሪት" in digital_text or "Negarit" in digital_text or "ፌደራል" in digital_text

        if len(digital_text) > 50 and not is_bilingual_layout:
            # Clean digital English page
            raw_text = digital_text
        else:
            # Bilingual digital page OR scanned page -> Force OCR and Crop
            pix = page.get_pixmap(dpi=300)
            raw_text = clean_and_ocr(pix)

        if not raw_text:
            continue

        # Split text into chunks
        page_chunks = text_splitter.split_text(raw_text)
        
        for chunk in page_chunks:
            all_chunks.append({
                "source": doc_name,
                "page_num": page_num + 1,
                "chunk_id": chunk_counter,
                "processed_at": datetime.now().isoformat(),
                "content": chunk,
                "length": len(chunk)
            })
            chunk_counter += 1

    # Backfill the total chunks in the file
    for chunk in all_chunks:
        chunk["total_chunks_in_file"] = chunk_counter

    return all_chunks

def main():
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created directory {INPUT_DIR}. Please drop your PDFs there.")
        return

    # Clear old output file
    if os.path.exists(OUTPUT_JSONL):
        os.remove(OUTPUT_JSONL)

    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDFs found in {INPUT_DIR}.")
        return

    with open(OUTPUT_JSONL, 'a', encoding='utf-8') as f:
        for pdf_file in pdf_files:
            pdf_path = os.path.join(INPUT_DIR, pdf_file)
            try:
                document_chunks = process_document(pdf_path)
                for chunk in document_chunks:
                    f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
            except Exception as e:
                print(f"Failed to process {pdf_file}: {e}")

    print(f"\nIngestion complete. Data saved to {OUTPUT_JSONL}")

if __name__ == "__main__":
    main()