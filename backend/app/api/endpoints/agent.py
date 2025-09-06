#!/usr/bin/env python
"""
Agent-based API endpoints for intelligent document processing
"""

from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
from app.services.agent import run_agent_command, get_agent_status, reset_agent_state

router = APIRouter()

class AgentRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None

class AgentResponse(BaseModel):
    response: str
    status: str
    command: Optional[str] = None
    error: Optional[str] = None

@router.post("/command", response_model=AgentResponse)
async def execute_agent_command(request: AgentRequest):
    """
    Execute a command through the AI agent system
    """
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        result = run_agent_command(request.command)
        return AgentResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@router.get("/status")
async def get_agent_system_status():
    """
    Get the current status of the agent system
    """
    try:
        status = get_agent_status()
        return {
            "status": "success",
            "agent_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")

@router.post("/reset")
async def reset_agent_system():
    """
    Reset the agent system state for a new session
    """
    try:
        result = reset_agent_state()
        return {
            "status": "success",
            "message": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset agent: {str(e)}")

@router.post("/chat")
async def agent_chat(request: AgentRequest):
    """
    Interactive chat interface using the agent system
    """
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Add context if provided
        enhanced_command = request.command
        if request.context:
            context_info = f"Context: {request.context}"
            enhanced_command = f"{request.command}\n\n{context_info}"
        
        result = run_agent_command(enhanced_command)
        
        return {
            "response": result["response"],
            "status": result["status"],
            "agent_status": get_agent_status()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent chat failed: {str(e)}")
