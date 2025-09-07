#!/usr/bin/env python
"""
Agentic AI API endpoints for autonomous document processing,
data analysis, template generation, and report generation.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.services.agentic_ai import run_agentic_command, get_agentic_status, reset_agentic_state

router = APIRouter()

# -----------------------------
# Request / Response Models
# -----------------------------
class AgenticRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "auto"  # "analysis", "template", "report", or "auto"

class AgenticResponse(BaseModel):
    response: str
    status: str
    command: Optional[str] = None
    error: Optional[str] = None
    agentic: bool = True
    memory_used: Optional[bool] = None

# -----------------------------
# Helpers
# -----------------------------
def build_enhanced_command(request: AgenticRequest) -> str:
    """
    Build a command string enriched with domain awareness
    for data analysis, template generation, and report generation.
    """
    domain_instruction = (
        f"Mode: {request.mode}. The AI must consider tasks including "
        f"Data Analysis, Template Generation, and Report Generation."
    )

    enhanced_command = f"{request.command}\n\n{domain_instruction}"

    if request.context:
        enhanced_command += f"\nContext: {request.context}"

    return enhanced_command

# -----------------------------
# Endpoints
# -----------------------------
@router.post("/command", response_model=AgenticResponse)
async def execute_agentic_command(request: AgenticRequest):
    """
    Execute a command through the agentic AI system.
    The AI will autonomously decide which tools to use:
    - Data Analysis
    - Template Generation
    - Report Generation
    """
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")

        enhanced_command = build_enhanced_command(request)
        result = run_agentic_command(enhanced_command)

        return AgenticResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agentic AI execution failed: {str(e)}")

@router.get("/status")
async def get_agentic_system_status():
    """
    Get the current status of the agentic AI system.
    """
    try:
        status = get_agentic_status()
        return {
            "status": "success",
            "agentic_ai_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agentic AI status: {str(e)}")

@router.post("/reset")
async def reset_agentic_system():
    """
    Reset the agentic AI system state for a new session.
    """
    try:
        result = reset_agentic_state()
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset agentic AI: {str(e)}")

@router.post("/chat")
async def agentic_chat(request: AgenticRequest):
    """
    Interactive chat interface using the agentic AI system.
    The AI will autonomously reason about:
    - Data Analysis
    - Template Generation
    - Report Generation
    """
    try:
        print(f"🤖 Agentic Chat Request: {request.command}")
        print(f"🤖 Context: {request.context}")

        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        enhanced_command = build_enhanced_command(request)
        result = run_agentic_command(enhanced_command)

        return {
            "response": result["response"],
            "status": result["status"],
            "agentic": True,
            "memory_used": result.get("memory_used", False),
            "agentic_status": get_agentic_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agentic AI chat failed: {str(e)}")

@router.post("/autonomous")
async def autonomous_processing(request: AgenticRequest):
    """
    Trigger fully autonomous processing.
    The AI will analyze the situation and take actions across:
    - Data Analysis
    - Template Generation
    - Report Generation
    """
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")

        enhanced_command = build_enhanced_command(request)
        result = run_agentic_command(f"Autonomously process this request:\n\n{enhanced_command}")

        return {
            "response": result["response"],
            "status": result["status"],
            "autonomous": True,
            "actions_taken": "AI autonomously decided on actions based on the request",
            "agentic_status": get_agentic_status()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous processing failed: {str(e)}")
