from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional, Any
import os
from app.services import template

router = APIRouter()

@router.get("/list", response_model=List[Dict])
async def list_templates():
    """List all available templates"""
    return template.list_templates()

@router.post("/create", response_model=Dict)
async def create_template(template_data: Dict = Body(...)):
    """Create a new template"""
    if "template" not in template_data:
        raise HTTPException(status_code=400, detail="Template sections are required")
    
    return template.create_template(template_data)

@router.put("/{template_id}", response_model=Dict)
async def update_template(template_id: str, template_data: Dict = Body(...)):
    """Update an existing template"""
    if "template" not in template_data:
        raise HTTPException(status_code=400, detail="Template sections are required")
    
    result = template.update_template(template_id, template_data)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result

@router.delete("/{template_id}", response_model=Dict)
async def delete_template(template_id: str):
    """Delete a template"""
    return template.delete_template(template_id)

@router.post("/suggest", response_model=Dict)
async def suggest_template(
    query: str = Body(..., embed=True),
    source_id: Optional[str] = Body(None, embed=True),
    context: Optional[Dict[str, Any]] = Body(None, embed=True),
    chat_history: Optional[List[Dict[str, Any]]] = Body(None, embed=True)
):
    """
    Suggest a template structure based on a query and optional source context
    
    Parameters:
    - query: The user's query or topic for the report
    - source_id: Optional ID of a specific source to focus on
    - context: Optional additional context like available sources
    - chat_history: Optional list of previous chat messages for a more conversational experience
    """
    source_context = None
    available_sources = context
    
    # If a specific source is requested, we'll need to retrieve sample content
    # In a real implementation, this would fetch from the database
    if source_id:
        # Mock implementation - in production, fetch actual content sample
        source_context = {
            "source_id": source_id,
            "sample": "Sample content would be retrieved here from the actual document storage"
        }
    
    result = template.suggest_template(query, source_context, available_sources, chat_history)
    return result

@router.post("/chat", response_model=Dict)
def chat_template(
    message: str = Body(..., embed=True),
    template_id: Optional[str] = Body(None, embed=True),
    chat_history: Optional[List[Dict[str, Any]]] = Body(None, embed=True),
    context: Optional[Dict[str, Any]] = Body(None, embed=True),
    selected_template: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """
    Interactive chat interface for template creation and refinement
    
    Parameters:
    - message: The user's message in the chat
    - template_id: Optional ID of an existing template being refined
    - chat_history: List of previous chat messages for context
    - context: Optional document context including available sources
    """
    # Initialize chat history if not provided
    if not chat_history:
        chat_history = []
    
    # Add user message to history
    chat_history.append({"role": "user", "content": message})
    
    # Debug logging
    print(f"Chat request - Message: {message}")
    print(f"Chat request - Context available: {context is not None}")
    if context:
        print(f"Chat request - Sources: {context.get('sources', [])}")
        print(f"Chat request - Samples: {len(context.get('samples', []))}")
    
    # Get existing template if template_id provided
    existing_template = None
    if template_id:
        templates_list = template.list_templates()
        existing_template = next((t for t in templates_list if t.get("id") == template_id), None)
    
    try:
        # Set up Gemini LLM
        os.environ["GOOGLE_API_KEY"] = "AIzaSyAkQBm7Flsbd6YlAgNzvvVIs3hbtMRDjsg"
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        
        print(f"LLM initialized successfully")
        
        # Build prompt with context of existing template if available
        template_context = ""
        if selected_template:
            sections = selected_template.get("template", [])
            sections_str = ", ".join(sections)
            template_context = f"""
            SELECTED TEMPLATE:
            The user has selected the template: "{selected_template.get('name', 'Unnamed Template')}"
            Description: {selected_template.get('description', 'No description available')}
            Category: {selected_template.get('category', 'General')}
            Sections: {sections_str}
            
            The user is working with this pre-built template and can modify it or use it as-is for report generation.
            """
        elif existing_template:
            sections = existing_template.get("template", [])
            sections_str = ", ".join(sections)
            template_context = f"""
            The user is currently working on a template with the following sections:
            {sections_str}
            
            They may want to refine this template further.
            """
        
        # Format chat history for context
        formatted_history = "\n".join([
            f"{'User' if msg.get('role', '') == 'user' else 'Assistant'}: {msg.get('content', '')}"
            for msg in chat_history[-5:]  # Use last 5 messages only
        ])
        
        # Add document context if available
        document_context = ""
        if context and "sources" in context and context["sources"]:
            document_context = f"""
        DOCUMENT CONTEXT:
        The user has uploaded {len(context["sources"])} document(s) to the system:
        {[f"- {s.get('source_id', 'Unknown')} ({s.get('count', 0)} documents)" for s in context["sources"]]}
        """
            
            # Add sample content analysis if available
            if "samples" in context and context["samples"]:
                document_context += f"""
        
        CONTENT ANALYSIS:
        I've analyzed sample content from their documents:
        """
                for sample in context["samples"][:3]:  # Show first 3 samples
                    document_context += f"""
        - Sample {sample.get('id', 'N/A')} (Source: {sample.get('source_id', 'Unknown')}):
          "{sample.get('content_preview', 'No preview available')}"
        """
                
                document_context += f"""
        
        Based on this content analysis, suggest the most appropriate template structure for their report.
        """
        
        # Check if user wants to generate a report from documents or analyze documents
        wants_report_generation = any(keyword in message.lower() for keyword in [
            "generate report", "create report", "make report", "build report", 
            "report from document", "report from uploaded", "use template", "generate from"
        ])
        
        wants_document_analysis = any(keyword in message.lower() for keyword in [
            "uploaded docs", "uploaded documents", "check documents", "analyze documents",
            "what's in", "show me", "display", "analyse", "analyze", "analyse my", "analyze my"
        ]) and not any(keyword in message.lower() for keyword in [
            "generate", "create", "make", "build", "report", "template"
        ])
        
        print(f"Document analysis request detected: {wants_document_analysis}")
        print(f"Message: {message.lower()}")
        
        # Craft engaging prompt for conversational template refinement
        prompt = f"""You are an enthusiastic, curious AI assistant who loves helping create amazing reports. Be engaging, ask thoughtful questions, and show genuine interest in their project.

Previous conversation: {formatted_history}
{template_context}
{document_context}

User message: {message}

Respond with curiosity and enthusiasm. Ask engaging questions, suggest interesting possibilities, and show excitement about their project. Be helpful but also curious about their goals and vision. Keep responses conversational but not too long."""
        
        # Generate response
        print(f"Calling LLM with prompt length: {len(prompt)}")
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        print(f"LLM response received: {content[:100]}...")
        
        # If user wants to generate a report and has documents, add actionable next steps
        if wants_report_generation and context and "sources" in context and context["sources"]:
            # Get available templates to suggest
            from app.services.template import list_templates
            available_templates = list_templates()
            
            if available_templates:
                template_suggestions = "\n\nAvailable templates:\n"
                for template in available_templates[:3]:  # Show top 3 templates
                    template_suggestions += f"• {template.get('name', 'Unnamed')}\n"
                
                template_suggestions += f"\nChoose a template or ask for a custom one!"
                
                content += template_suggestions
        
        # If user wants document analysis and has documents, provide detailed analysis
        print(f"Checking document analysis: wants_document_analysis={wants_document_analysis}, context={context is not None}")
        if context:
            print(f"Context sources: {context.get('sources', [])}")
        
        if wants_document_analysis and context and "sources" in context and context["sources"]:
            # Add detailed document analysis
            doc_count = len(context["sources"])
            analysis = f"\n\n**Document Analysis Summary:**\n"
            analysis += f"✅ I can see you have uploaded **{doc_count} document(s)** to analyze.\n\n"
            
            # Add source information
            for i, source in enumerate(context["sources"][:3], 1):
                analysis += f"**Document {i}:** {source.get('source_id', 'Unknown')} ({source.get('count', 0)} chunks)\n"
            
            # Add sample content if available
            if "samples" in context and context["samples"]:
                analysis += f"\n**Content Preview:**\n"
                for i, sample in enumerate(context["samples"][:2], 1):
                    content_preview = sample.get('content_preview', str(sample))[:150]
                    analysis += f"• **Sample {i}:** {content_preview}...\n"
            
            analysis += f"\nWhat I can do:\n"
            analysis += f"• Generate reports\n"
            analysis += f"• Create custom templates\n"
            analysis += f"• Answer questions\n"
            analysis += f"• Extract insights\n\n"
            analysis += f"Ready! What type of report do you want?"
            
            content += analysis
        
        # Add assistant response to history
        chat_history.append({"role": "assistant", "content": content})
        
        # Return response and updated history
        return {
            "response": content,
            "chat_history": chat_history
        }
    except Exception as e:
        print(f"Error in chat template: {e}")
        
        # Enhanced fallback response based on context
        if context and "sources" in context and context["sources"]:
            doc_count = len(context["sources"])
            fallback = f"Wow! I can see {doc_count} document(s) uploaded - this is exciting! 📄✨\n\nI'm really curious about what you're working on. I can help you:\n• Dive deep into document analysis\n• Create stunning reports\n• Design custom templates\n• Answer your burning questions\n\nWhat's your vision here? I'm excited to help you bring it to life! 🚀"
        else:
            fallback = "Hey there! I'm your enthusiastic report creation partner! 🎉\n\nI'm curious - what kind of amazing project are you working on? I can help you:\n• Upload and analyze documents\n• Generate professional reports\n• Create custom templates\n\nWhat's your goal? I'm excited to help you achieve it! ✨"
        
        chat_history.append({"role": "assistant", "content": fallback})
        
        return {
            "response": fallback,
            "chat_history": chat_history,
            "error": str(e)
        }
