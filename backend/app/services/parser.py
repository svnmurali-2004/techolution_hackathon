import fitz  # pymupdf
import pandas as pd
from pptx import Presentation
import pytesseract
from typing import Any
import os
import tempfile
from chromadb import PersistentClient

# Use the same ChromaDB setup as the generator
CHROMA_PATH = "./chromadb_reports"
vector_db = PersistentClient(path=CHROMA_PATH)

def extract_pdf(file_path):
    doc = fitz.open(file_path)
    texts = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        texts.append({"page": page_num, "text": text})
    return texts

def extract_pptx(file_path):
    prs = Presentation(file_path)
    slides = []
    for idx, slide in enumerate(prs.slides, 1):
        text = " ".join([shape.text for shape in slide.shapes if hasattr(shape, "text")])
        slides.append({"slide": idx, "text": text})
    return slides

def extract_xlsx(file_path):
    df = pd.read_excel(file_path)
    rows = df.to_dict(orient="records")
    return [{"row": idx+1, "data": row} for idx, row in enumerate(rows)]

def extract_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [{"text": f.read()}]

def extract_image(file_path):
    text = pytesseract.image_to_string(file_path)
    return [{"text": text}]

async def parse_file(file) -> dict:
    ext = os.path.splitext(file.filename)[1].lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    if ext == ".pdf":
        data = extract_pdf(tmp_path)
    elif ext in [".ppt", ".pptx"]:
        data = extract_pptx(tmp_path)
    elif ext in [".xls", ".xlsx"]:
        data = extract_xlsx(tmp_path)
    elif ext in [".txt"]:
        data = extract_txt(tmp_path)
    elif ext in [".png", ".jpg", ".jpeg"]:
        data = extract_image(tmp_path)
    else:
        data = [{"error": "Unsupported file type"}]
    os.remove(tmp_path)
    # Store in vector DB using the same collection as generator
    import uuid
    collection = vector_db.get_or_create_collection("reports")
    
    # Process and store the extracted data properly
    ingested_chunks = []
    for item in data:
        if 'text' in item and item['text'].strip():
            # Use the generator's ingest_documents function for consistency
            from app.services.generator import ingest_documents
            source_id = f"uploaded_{file.filename}_{str(uuid.uuid4())[:8]}"
            chunk_ids, _ = ingest_documents([item['text']], source_id=source_id)
            ingested_chunks.extend(chunk_ids)
    
    return {
        "status": "parsed", 
        "filename": file.filename, 
        "data": data,
        "ingested_chunks": len(ingested_chunks),
        "message": f"Successfully ingested {len(ingested_chunks)} chunks from {file.filename}"
    }
