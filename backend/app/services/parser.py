import fitz  # pymupdf
import pandas as pd
from pptx import Presentation
import pytesseract
from typing import Any
import os
import tempfile
from chromadb import Client

vector_db = Client()

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
    # Store in vector DB
    import uuid
    collection = vector_db.get_or_create_collection("documents")
    # Batch add documents to avoid timeouts
    batch_size = 10
    docs = [str(item)[:1000] for item in data]  # Truncate to 1000 chars to avoid large payloads
    metas = [{"filename": file.filename} for _ in data]
    ids = [str(uuid.uuid4()) for _ in data]
    for i in range(0, len(docs), batch_size):
        collection.add(
            documents=docs[i:i+batch_size],
            metadatas=metas[i:i+batch_size],
            ids=ids[i:i+batch_size]
        )
    return {"status": "parsed", "filename": file.filename, "data": data}
