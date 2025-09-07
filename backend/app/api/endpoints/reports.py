#!/usr/bin/env python
"""
Report generation API endpoints
"""

from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import Response
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from app.services.generator import generate_report_from_query, preview
from app.services.export import export_report

router = APIRouter()

class ReportRequest(BaseModel):
    sections: List[str]
    query: str
    top_k: Optional[int] = 5
    source_filter: Optional[str] = None  # To filter by specific source ID

class ReportResponse(BaseModel):
    report_id: str
    status: str

class PreviewResponse(BaseModel):
    report_id: str
    content: Dict[str, Any]
    citations: Dict[str, Any]

class ExportRequest(BaseModel):
    report_id: str
    format: str = "pdf"  # pdf, docx, html

@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: ReportRequest):
    """
    Generate a report based on query and sections
    """
    try:
        result = generate_report_from_query(
            request.sections,
            query=request.query,
            top_k=request.top_k,
            source_filter=request.source_filter
        )
        
        # Check if there was an error in the result
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "report_id": result["report_id"],
            "status": "generated"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

@router.get("/preview/{report_id}")
async def get_report_preview(report_id: str):
    """
    Get a preview of a generated report
    """
    try:
        result = preview(report_id)
        # Just return the full result as is - it already contains the preview key
        # that the frontend is expecting
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Report with ID {report_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview generation failed: {str(e)}")

@router.post("/export", response_model=Dict[str, str])
async def export_report_endpoint(request: ExportRequest):
    """
    Export a report to the specified format
    """
    try:
        result = export_report(request.report_id, request.format)
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        return {
            "report_id": request.report_id,
            "format": request.format,
            "file": result.get("file", ""),
            "status": "success"
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Report with ID {request.report_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/export/{report_id}")
async def export_report_get(report_id: str, format: str = "pdf"):
    """
    Export a report to the specified format (GET endpoint)
    """
    try:
        result = export_report(report_id, format)
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
