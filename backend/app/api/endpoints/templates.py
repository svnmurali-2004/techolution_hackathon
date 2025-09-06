#!/usr/bin/env python
"""
Template generation and management API endpoints
"""

from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.services.template import list_templates, create_template, update_template, delete_template, suggest_template
from app.services.generator import get_available_sources

router = APIRouter()

class TemplateRequest(BaseModel):
    template: List[str]

class TemplateResponse(BaseModel):
    id: str
    template: List[str]

class TemplateSuggestionRequest(BaseModel):
    query: str
    source_id: Optional[str] = None

@router.get("/", response_model=List[Dict])
async def get_templates():
    """
    Get all available templates
    """
    return list_templates()

@router.post("/", response_model=Dict)
async def create_new_template(request: TemplateRequest):
    """
    Create a new template
    """
    return create_template({"template": request.template})

@router.put("/{template_id}", response_model=Dict)
async def update_existing_template(template_id: str, request: TemplateRequest):
    """
    Update an existing template
    """
    return update_template(template_id, {"template": request.template})

@router.delete("/{template_id}", response_model=Dict)
async def delete_existing_template(template_id: str):
    """
    Delete a template
    """
    return delete_template(template_id)

@router.post("/suggest", response_model=Dict)
async def suggest_template_sections(request: TemplateSuggestionRequest):
    """
    Suggest template sections based on a query and optionally a specific source
    """
    try:
        # Get available sources for content-aware suggestions
        available_sources = get_available_sources()
        
        # If source_id is provided, filter to just that source
        source_context = None
        if request.source_id:
            for source in available_sources.get("sources", []):
                if source.get("source_id") == request.source_id:
                    source_context = source
                    break
        
        # Generate template suggestions
        result = suggest_template(
            query=request.query,
            source_context=source_context,
            available_sources=available_sources
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Template suggestion failed: {str(e)}")
