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

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Backend is running"}

@router.post("/transcribe-audio")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Transcribe audio from voice input using Deepgram
    """
    try:
        # Save the uploaded audio file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            content = await audio.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Use the same transcription function as video processing
        from app.services.parser import extract_video_audio
        result = extract_video_audio(tmp_path)
        
        # Clean up temp file
        os.remove(tmp_path)
        
        if result and len(result) > 0 and 'text' in result[0]:
            return {
                "status": "success",
                "transcript": result[0]['text'],
                "word_count": result[0].get('word_count', 0),
                "duration": result[0].get('duration', 0)
            }
        else:
            return {
                "status": "error",
                "message": "No speech detected in audio"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Transcription failed: {str(e)}"
        }

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_id: Optional[str] = Form(None)
):
    """
    Upload and ingest a single document
    """
    try:
        # Generate a source ID if not provided
        if not source_id:
            source_id = f"doc_{str(uuid.uuid4())[:8]}"
        
        # Check file extension
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        
        # Process based on file type using the unified parser
        if file_ext in ['pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv', 'wav', 'mp3', 'm4a', 'flac']:
            from app.services.parser import parse_file
            # Use the updated parser that handles all file types
            parsed_data = await parse_file(file)
            
            # Log the extraction process
            print(f"Parsed file: {file.filename}")
            print(f"Extracted data: {parsed_data.get('message', 'No message')}")
            
            # The parser now handles ingestion internally, so we just need to verify
            if parsed_data.get('status') != 'parsed':
                raise HTTPException(status_code=400, detail=f"Failed to parse file: {parsed_data.get('error', 'Unknown error')}")
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

@router.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None)
):
    """
    Upload and ingest multiple documents of different types simultaneously
    """
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files provided")
        
        # Limit the number of files to prevent overload
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 files allowed per upload")
        
        # Generate session ID if not provided
        if not session_id:
            session_id = f"session_{str(uuid.uuid4())[:8]}"
        
        upload_results = []
        successful_uploads = 0
        failed_uploads = 0
        total_size = 0
        
        # Supported file types and their categories
        supported_types = {
            'documents': ['pdf', 'doc', 'docx', 'txt', 'rtf'],
            'presentations': ['ppt', 'pptx'],
            'spreadsheets': ['xls', 'xlsx', 'csv'],
            'images': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'],
            'videos': ['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv'],
            'audio': ['mp3', 'wav', 'm4a', 'flac', 'aac', 'ogg'],
            'archives': ['zip', 'rar', '7z', 'tar', 'gz']
        }
        
        # Process each file
        for file in files:
            try:
                # Validate file size (max 100MB per file)
                file_content = await file.read()
                file_size = len(file_content)
                total_size += file_size
                
                if file_size > 100 * 1024 * 1024:  # 100MB limit
                    upload_results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": "File too large (max 100MB per file)",
                        "size": file_size
                    })
                    failed_uploads += 1
                    continue
                
                # Reset file pointer for processing
                await file.seek(0)
                
                # Check file extension
                file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
                
                # Determine file category
                file_category = "unknown"
                for category, extensions in supported_types.items():
                    if file_ext in extensions:
                        file_category = category
                        break
                
                # Generate unique source ID for this file
                source_id = f"uploaded_{file.filename}_{str(uuid.uuid4())[:8]}"
                
                # Process based on file type
                if file_ext in ['pdf', 'pptx', 'ppt', 'xlsx', 'xls', 'txt', 'png', 'jpg', 'jpeg', 'mp4', 'avi', 'mov', 'mkv', 'wav', 'mp3', 'm4a', 'flac']:
                    from app.services.parser import parse_file
                    parsed_data = await parse_file(file)
                    
                    if parsed_data.get('status') == 'parsed':
                        upload_results.append({
                            "filename": file.filename,
                            "source_id": source_id,
                            "status": "success",
                            "category": file_category,
                            "size": file_size,
                            "message": f"Successfully processed {file_category} file"
                        })
                        successful_uploads += 1
                    else:
                        upload_results.append({
                            "filename": file.filename,
                            "status": "failed",
                            "error": parsed_data.get('error', 'Unknown parsing error'),
                            "size": file_size
                        })
                        failed_uploads += 1
                else:
                    # Handle unsupported file types
                    upload_results.append({
                        "filename": file.filename,
                        "status": "failed",
                        "error": f"Unsupported file type: {file_ext}",
                        "size": file_size
                    })
                    failed_uploads += 1
                    
            except Exception as file_error:
                print(f"Error processing file {file.filename}: {file_error}")
                upload_results.append({
                    "filename": file.filename,
                    "status": "failed",
                    "error": str(file_error),
                    "size": 0
                })
                failed_uploads += 1
        
        # Check total size limit (max 500MB total)
        if total_size > 500 * 1024 * 1024:  # 500MB total limit
            raise HTTPException(status_code=400, detail="Total file size exceeds 500MB limit")
        
        # Get final document count
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        # Prepare summary
        summary = {
            "session_id": session_id,
            "total_files": len(files),
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "total_size": total_size,
            "document_count": doc_count,
            "files": upload_results
        }
        
        return {
            "status": "completed",
            "message": f"Multi-file upload completed. {successful_uploads} files processed successfully, {failed_uploads} failed.",
            "summary": summary
        }
        
    except Exception as e:
        print(f"Error in multi-file upload: {e}")
        raise HTTPException(status_code=500, detail=f"Multi-file upload failed: {str(e)}")

@router.get("/status")
async def get_collection_status():
    """
    Get the status of the document collection with sources information
    """
    try:
        from app.services.generator import collection
        status = diagnose_collection()
        
        # Get unique source IDs from the collection
        try:
            # Get all documents to extract unique source IDs
            all_docs = collection.get()
            source_ids = set()
            if all_docs and 'metadatas' in all_docs:
                for metadata in all_docs['metadatas']:
                    if metadata and 'source_id' in metadata:
                        source_ids.add(metadata['source_id'])
            
            # Create sources array
            sources = []
            for source_id in source_ids:
                # Count documents for this source
                source_docs = collection.get(where={"source_id": source_id})
                count = len(source_docs['ids']) if source_docs and 'ids' in source_docs else 0
                sources.append({
                    "source_id": source_id,
                    "count": count
                })
            
            # Add sources to status
            status["sources"] = sources
            
        except Exception as e:
            print(f"Error getting sources: {e}")
            status["sources"] = []
        
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

@router.get("/samples")
async def get_document_samples():
    """
    Get sample content from uploaded documents for template analysis
    """
    try:
        from app.services.generator import get_document_samples_for_analysis
        samples = get_document_samples_for_analysis()
        return samples
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document samples: {str(e)}")

@router.post("/session/start")
async def start_new_session():
    """
    Start a new chat session - clears chat interface but keeps documents for report generation
    """
    try:
        # Just return a new session ID without clearing the collection
        # The collection should remain intact for report generation
        return {
            "status": "success", 
            "message": "New chat session started - documents preserved for report generation",
            "session_id": str(uuid.uuid4()),
            "details": "Chat interface cleared, documents remain available"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start new session: {str(e)}")

@router.post("/session/reset-all")
async def reset_all_documents():
    """
    Reset everything - clears both chat interface AND all documents (complete reset)
    """
    try:
        from app.services.generator import reset_collection
        result = reset_collection()
        return {
            "status": "success", 
            "message": "Complete reset - all documents and chat cleared",
            "session_id": str(uuid.uuid4()),
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset all documents: {str(e)}")

@router.post("/collection/recreate")
async def recreate_collection():
    """
    Recreate the ChromaDB collection if it's corrupted or inaccessible
    """
    try:
        from app.services.generator import recreate_collection
        result = recreate_collection()
        return {
            "status": "success",
            "message": "Collection recreated successfully",
            "details": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recreate collection: {str(e)}")

@router.post("/collection/recover")
async def recover_collection():
    """
    Recover a corrupted ChromaDB collection
    """
    try:
        from app.services.generator import recover_collection
        result = recover_collection()
        return {
            "status": "success",
            "message": "Collection recovered successfully",
            "details": "Collection has been recreated and is ready for use"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recover collection: {str(e)}")

@router.get("/session/current")
async def get_current_session_documents():
    """
    Get only the documents from the current session (all documents since last reset)
    """
    try:
        from app.services.generator import collection, diagnose_collection
        status = diagnose_collection()
        
        # Get all documents from current session
        all_docs = collection.get()
        current_documents = []
        
        if all_docs and 'metadatas' in all_docs and 'documents' in all_docs:
            for i, metadata in enumerate(all_docs['metadatas']):
                if metadata and 'source_id' in metadata:
                    current_documents.append({
                        "source_id": metadata['source_id'],
                        "content": all_docs['documents'][i] if i < len(all_docs['documents']) else "",
                        "page": metadata.get('page', 1)
                    })
        
        return {
            "session_documents": current_documents,
            "total_count": len(current_documents),
            "status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current session documents: {str(e)}")

@router.post("/analyze")
async def analyze_documents():
    """
    Analyze uploaded documents and provide a summary
    """
    try:
        from app.services.generator import collection, diagnose_collection, get_document_samples_for_analysis
        import os
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Get document status and samples
        status = diagnose_collection()
        samples_data = get_document_samples_for_analysis()
        
        if status.get("document_count", 0) == 0:
            return {
                "analysis": "No documents found. Please upload documents first.",
                "document_count": 0
            }
        
        # Set up Gemini LLM
        os.environ["GOOGLE_API_KEY"] = "AIzaSyAkQBm7Flsbd6YlAgNzvvVIs3hbtMRDjsg"
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        
        # Create analysis prompt
        document_count = status.get("document_count", 0)
        samples = samples_data.get("samples", [])
        
        prompt = f"""
        You are an expert document analyst. I have uploaded {document_count} document(s) and need you to analyze them.
        
        Here are sample contents from the documents:
        """
        
        for i, sample in enumerate(samples[:3], 1):
            content = sample.get('content_preview', str(sample))
            prompt += f"\nDocument {i} Sample:\n{content}\n"
        
        prompt += f"""
        
        Please provide a comprehensive analysis including:
        1. **Document Overview** - What types of documents these appear to be
        2. **Key Topics** - Main subjects and themes covered
        3. **Content Quality** - Assessment of the information quality
        4. **Report Recommendations** - What type of report would best suit this content
        5. **Template Suggestions** - Which report template would work best
        
        Be specific and reference the actual content you can see.
        """
        
        # Generate analysis
        response = llm.invoke(prompt)
        analysis = response.content if hasattr(response, "content") else str(response)
        
        return {
            "analysis": analysis,
            "document_count": document_count,
            "samples_analyzed": len(samples),
            "status": "success"
        }
        
    except Exception as e:
        print(f"Error in document analysis: {e}")
        return {
            "analysis": f"Error analyzing documents: {str(e)}",
            "document_count": 0,
            "error": str(e)
        }
