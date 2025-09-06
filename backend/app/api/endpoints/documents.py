#!/usr/bin/env python
"""
Document management API endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel
import uuid
from app.services.generator import ingest_documents, diagnose_collection

router = APIRouter()

class DocumentResponse(BaseModel):
    id: str
    source_id: str
    status: str

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_id: Optional[str] = Form(None)
):
    """
    Upload and ingest a document
    """
    try:
        # Generate a source ID if not provided
        if not source_id:
            source_id = f"doc_{str(uuid.uuid4())[:8]}"
        
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        # Process based on file type
        if file_ext == 'pdf':
            from app.services.parser import parse_file
            # Use the existing parser for PDF files
            parsed_data = await parse_file(file)
            # Extract text from parsed data
            text_contents = [item.get('text', '') for item in parsed_data if 'text' in item]
            
            # Log the extraction process
            print(f"Extracted {len(text_contents)} text segments from PDF")
            print(f"First segment preview: {text_contents[0][:100]}..." if text_contents else "No text extracted")
            
            # Ingest each text segment with a consistent parent source_id
            # This will allow filtering by this parent source ID
            for i, text in enumerate(text_contents):
                if text.strip():  # Skip empty text
                    page_source_id = f"{source_id}_page{i+1}"
                    ingest_documents([text], source_id=source_id)
        else:
            # Handle plain text files as before
            content = await file.read()
            try:
                text_content = content.decode("utf-8")
                ingest_documents([text_content], source_id=source_id)
            except UnicodeDecodeError:
                # If can't decode as text, treat as binary and report error
                raise HTTPException(status_code=400, detail=f"File type not supported: {file_ext}")
        
        # Verify documents were ingested
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        return {
            "id": str(uuid.uuid4()),
            "source_id": source_id,
            "status": "ingested",
            "document_count": doc_count,
            "usage_hint": "To generate a report using only this document, use this source_id in the report generation request"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

@router.get("/status")
async def get_collection_status():
    """
    Get the status of the document collection
    """
    try:
        status = diagnose_collection()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collection status: {str(e)}")
        
@router.get("/source/{source_id}")
async def get_documents_by_source(source_id: str):
    """
    Get all documents associated with a specific source_id
    """
    try:
        from app.services.generator import get_documents_by_source
        documents = get_documents_by_source(source_id)
        return {"source_id": source_id, "documents": documents}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")

@router.delete("/reset")
async def reset_collection():
    """
    Reset (delete all documents) from the collection.
    Use with caution as this will delete all ingested documents.
    """
    try:
        from app.services.generator import reset_collection
        result = reset_collection()
        return {"status": "success", "message": "Collection has been reset", "details": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset collection: {str(e)}")
