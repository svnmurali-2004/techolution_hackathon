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
        os.environ["GOOGLE_API_KEY"] = "AIzaSyB_Nqb1kP6NJ0PsfYONs4VxQWsjywc30Rs"
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
            "document summary", "summary", "what's in", "show me", "display", "template",
            "analyse", "analyze", "analyse my", "analyze my"
        ])
        
        print(f"Document analysis request detected: {wants_document_analysis}")
        print(f"Message: {message.lower()}")
        
        # Craft enhanced prompt for conversational template refinement
        prompt = f"""
        You are an expert AI assistant specializing in creating professional report templates with document analysis capabilities.
        
        Previous conversation:
        {formatted_history}
        
        {template_context}
        
        {document_context}
        
        Respond conversationally to help the user create or refine their report template.
        
        IMPORTANT CONTEXT HANDLING:
        - If the user has selected a template, acknowledge it and show them the template details
        - If they ask to "show the selected template", display the template information clearly
        - If they have uploaded documents, analyze what type of content they likely contain and suggest appropriate template structures
        - If they're asking for changes to the template, suggest specific additions, removals, or rearrangements
        - If they're asking for a completely new template, engage them to understand their needs and consider their uploaded documents
        
        REPORT GENERATION REQUESTS:
        - If the user wants to generate a report from their uploaded documents, acknowledge this and explain that you'll help them create a comprehensive report
        - Suggest using one of the available templates or creating a custom template based on their document content
        - If they say "use your own template" or similar, recommend the most appropriate template from the available options
        - Always provide clear next steps for report generation
        
        DOCUMENT ANALYSIS REQUESTS:
        - If the user asks about uploaded documents, check documents, or wants a summary, provide detailed analysis of their uploaded content
        - Use the document context and samples to give specific information about what's in their documents
        - If they ask "have you checked" or "uploaded docs", confirm you can see their documents and provide a summary
        - If they ask for a "template" or "summary", show them the document content and suggest appropriate templates
        
        CRITICAL: Always use the document context when available. If documents are uploaded, reference their content specifically.
        Never give generic responses when document context is available.
        
        Always maintain a helpful, consultative tone like a professional report writing expert who can see and analyze their documents.
        """
        
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
                template_suggestions = "\n\n**Available Templates for Your Report:**\n"
                for template in available_templates[:3]:  # Show top 3 templates
                    template_suggestions += f"• **{template.get('name', 'Unnamed')}** - {template.get('description', 'No description')}\n"
                
                template_suggestions += f"\n**Next Steps:**\n1. Select a template above that best fits your needs\n2. Or ask me to create a custom template based on your document content\n3. Once you choose, I'll generate your report using the uploaded documents"
                
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
            
            analysis += f"\n**What I can do with your documents:**\n"
            analysis += f"• Generate a comprehensive report using any template\n"
            analysis += f"• Create a custom template based on your content\n"
            analysis += f"• Answer specific questions about your documents\n"
            analysis += f"• Extract key insights and summaries\n\n"
            analysis += f"**Ready to proceed!** Just tell me what type of report you'd like to create."
            
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
            fallback = f"I can see you have {doc_count} document(s) uploaded! 📄\n\nI'm here to help you create professional reports from your documents. You can:\n\n• Ask me to **analyze your documents**\n• Request a **document summary**\n• **Generate a report** using a template\n• Ask **specific questions** about your content\n\nWhat would you like me to help you with?"
        else:
            fallback = "I'm here to help you create professional reports! You can:\n\n• **Upload documents** to analyze\n• **Design custom templates**\n• **Generate reports** from your content\n• **Refine existing templates**\n\nWhat would you like to do first?"
        
        chat_history.append({"role": "assistant", "content": fallback})
        
        return {
            "response": fallback,
            "chat_history": chat_history,
            "error": str(e)
        }
