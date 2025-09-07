from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from typing import Optional, List, Dict

from app.services import parser, template, generator, export
from pydantic import BaseModel
from app.api import templates

class GenerateRequest(BaseModel):
    template_id: Optional[str] = None
    query: str
    sections: Optional[List[str]] = None
    source_filter: Optional[str] = None
    top_k: Optional[int] = 5

router = APIRouter()

# Include the templates router
router.include_router(
    templates.router,
    prefix="/templates",
    tags=["templates"]
)

# Include the documents router
from app.api.endpoints import documents
router.include_router(
    documents.router,
    prefix="/documents",
    tags=["documents"]
)

# Include the reports router
from app.api.endpoints import reports
router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"]
)

# Include the agentic AI router
from app.api.endpoints import agentic
router.include_router(
    agentic.router,
    prefix="/agentic",
    tags=["agentic-ai"]
)

@router.post('/upload')
async def upload_file(file: UploadFile = File(...), source_id: Optional[str] = Form(None)):
    """Upload a single file and get source_id for future reference"""
    # Use the documents endpoint for proper document handling
    from app.api.endpoints.documents import upload_document
    return await upload_document(file, source_id)

@router.post('/upload-multiple')
async def upload_multiple_files(files: List[UploadFile] = File(...), session_id: Optional[str] = Form(None)):
    """Upload multiple files of different types simultaneously"""
    # Use the documents endpoint for proper multi-file handling
    from app.api.endpoints.documents import upload_multiple_documents
    return await upload_multiple_documents(files, session_id)

@router.get('/sources')
async def get_available_sources():
    """Get list of available document sources for filtering"""
    return generator.get_available_sources()

# Add direct routes for backward compatibility with existing frontend
@router.get('/templates')
async def get_templates_compat():
    """Backward compatibility route for listing templates"""
    return template.list_templates()

@router.post('/templates')
async def create_template_compat(template_json: dict):
    """Backward compatibility route for creating templates"""
    return template.create_template(template_json)

@router.post('/templates/suggest')
async def suggest_template_compat(request: dict):
    """Backward compatibility route for suggesting templates"""
    return template.suggest_template(
        query=request.get("query", ""),
        source_context=request.get("source_context"),
        available_sources=request.get("available_sources"),
        chat_history=request.get("chat_history")
    )

@router.post('/templates/chat')
async def chat_template_compat(request: dict):
    """Backward compatibility route for template chat interface"""
    # Forward to the new templates router chat endpoint
    from app.api.templates import chat_template
    return chat_template(
        message=request.get("message", ""),
        template_id=request.get("template_id"),
        chat_history=request.get("chat_history")
    )

# Templates routes have also been moved to app/api/templates.py and are included above

@router.post('/generate')
async def generate_report(req: GenerateRequest):
    """Generate a report using either provided sections or a template_id"""
    # If sections are provided directly, use them
    if req.sections:
        sections = req.sections
    # Otherwise if template_id is provided, fetch sections from template
    elif req.template_id:
        templates_list = template.list_templates()
        template_obj = next((t for t in templates_list if t.get("id") == req.template_id), None)
        if template_obj:
            sections = template_obj.get("template", ["Executive Summary", "Key Findings", "Recommendations"])
        else:
            # Default sections if template not found
            sections = ["Executive Summary", "Key Findings", "Recommendations"]
    else:
        # Default sections if neither sections nor template_id provided
        sections = ["Executive Summary", "Key Findings", "Recommendations"]
    
    # Generate report with source filtering to ensure we use only uploaded content
    return generator.generate_report_from_query(
        sections=sections, 
        query=req.query, 
        top_k=req.top_k,
        source_filter=req.source_filter
    )

@router.get('/preview/{report_id}')
def preview_report(report_id: str):
	return generator.preview(report_id)

@router.get('/export/{report_id}')
async def export_report_route(report_id: str, format: str):
    """
    Export a report to the specified format (GET endpoint)
    """
    try:
        result = export.export_report(report_id, format)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return the file as a binary response
        file_data = result.get("file", b"")
        if not file_data:
            raise HTTPException(status_code=404, detail="No file data found")
        
        # Determine content type based on format
        content_type = "application/pdf" if format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename = f"report_{report_id}.{format}"
        
        return Response(
            content=file_data,
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
