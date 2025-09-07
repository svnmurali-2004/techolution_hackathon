import json
from typing import List, Dict, Any, Optional
import uuid
import os
from langchain_google_genai import ChatGoogleGenerativeAI

def load_templates_from_file():
    """Load templates from file if it exists."""
    templates_file = "templates.json"
    if os.path.exists(templates_file):
        try:
            with open(templates_file, 'r', encoding='utf-8') as f:
                loaded_templates = json.load(f)
                print(f"📁 Loaded {len(loaded_templates)} templates from {templates_file}")
                return loaded_templates
        except Exception as e:
            print(f"⚠️ Warning: Could not load templates from file: {e}")
    return None

# Initialize templates - try to load from file first, otherwise use defaults
default_templates = [
    {
        "id": "default", 
        "name": "Default Template",
        "description": "Basic report template with essential sections",
        "template": ["Executive Summary", "Introduction", "Key Insights", "Recommendations"],
        "category": "General",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "business_report", 
        "name": "Business Report Template",
        "description": "Standard business report with executive summary and recommendations",
        "template": ["Executive Summary", "Introduction", "Key Findings", "Recommendations", "Conclusion"],
        "category": "Business",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "market_analysis", 
        "name": "Market Analysis Template",
        "description": "Comprehensive market analysis with competitive insights",
        "template": ["Executive Summary", "Market Overview", "Competitive Analysis", "Trends", "Recommendations"],
        "category": "Market Research",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "financial_report", 
        "name": "Financial Report Template",
        "description": "Financial analysis and performance review template",
        "template": ["Executive Summary", "Financial Overview", "Performance Analysis", "Risk Assessment", "Financial Projections", "Recommendations"],
        "category": "Finance",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "research_report", 
        "name": "Research Report Template",
        "description": "Academic and research-focused report structure",
        "template": ["Abstract", "Introduction", "Methodology", "Findings", "Analysis", "Conclusion", "References"],
        "category": "Research",
        "created_at": "2024-01-01T00:00:00Z"
    },
    {
        "id": "project_status", 
        "name": "Project Status Template",
        "description": "Project update and status reporting template",
        "template": ["Project Overview", "Current Status", "Milestones Achieved", "Challenges", "Next Steps", "Resource Requirements"],
        "category": "Project Management",
        "created_at": "2024-01-01T00:00:00Z"
    }
]

# Load templates from file or use defaults
loaded_templates = load_templates_from_file()
templates = loaded_templates if loaded_templates is not None else default_templates

def list_templates() -> List[Dict]:
    return templates

def create_template(template_json: Dict) -> Dict:
    template_id = str(uuid.uuid4())
    template_json["id"] = template_id
    
    # Add default values if not provided
    if "name" not in template_json:
        template_json["name"] = f"Custom Template {len(templates) + 1}"
    if "description" not in template_json:
        template_json["description"] = "User-created custom template"
    if "category" not in template_json:
        template_json["category"] = "Custom"
    if "created_at" not in template_json:
        from datetime import datetime
        template_json["created_at"] = datetime.now().isoformat() + "Z"
    
    templates.append(template_json)
    return {"status": "created", "template": template_json}

def update_template(template_id: str, new_template: Dict) -> Dict:
    for t in templates:
        if t["id"] == template_id:
            t["template"] = new_template["template"]
            return {"status": "updated", "template": t}
    return {"error": "Template not found"}

def delete_template(template_id: str) -> Dict:
    global templates
    templates = [t for t in templates if t["id"] != template_id]
    return {"status": "deleted", "id": template_id}

def suggest_template(query: str, source_context: Optional[Dict] = None, available_sources: Optional[Dict] = None, chat_history: Optional[List] = None) -> Dict:
    """
    Suggest a template structure based on a query and available source content using a conversational approach
    
    Args:
        query: The user's query or topic for the report
        source_context: Optional context about a specific source to focus on
        available_sources: Information about all available document sources
        chat_history: Optional list of previous chat messages for context
        
    Returns:
        Dict with suggested template sections, explanation and chat response
    """
    try:
        # Set up Gemini LLM
        os.environ["GOOGLE_API_KEY"] = "AIzaSyDGA_bxmpmbC7NkEaY97GQoZDUtS1N1nLA"
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
        
        # Build context based on available information
        content_context = ""
        if source_context:
            # If we have specific source information, include sample text
            source_name = source_context.get("source_id", "")
            sample_text = source_context.get("sample", "")[:500]  # First 500 chars as sample
            content_context = f"""
            The report will specifically focus on content from the document: '{source_name}'.
            Here's a sample of the content:
            ---
            {sample_text}
            ---
            """
        elif available_sources and "sources" in available_sources:
            # If we have multiple sources, list them
            sources_list = "\n".join([
                f"- {s.get('source_id', 'Unknown')} ({s.get('count', 0)} documents)" 
                for s in available_sources.get("sources", [])
            ])
            content_context = f"""
            The report will use content from the following sources:
            {sources_list}
            """
        
        # Format chat history if available
        chat_context = ""
        if chat_history and len(chat_history) > 0:
            formatted_history = "\n".join([
                f"{'User' if msg.get('role', '') == 'user' else 'Assistant'}: {msg.get('content', '')}"
                for msg in chat_history[-5:] # Use last 5 messages only
            ])
            chat_context = f"""
            Previous conversation:
            {formatted_history}
            
            Continue the conversation naturally, considering this history.
            """
        
        # Enhanced prompt with document analysis capabilities
        document_analysis = ""
        if available_sources and "sources" in available_sources and available_sources["sources"]:
            document_analysis = f"""
        DOCUMENT ANALYSIS:
        I can see you have {len(available_sources["sources"])} document(s) uploaded to the system. Based on the available sources, I can analyze the content and suggest the most appropriate template structure.
        
        Available sources: {[s.get('source_id', 'Unknown') for s in available_sources.get("sources", [])]}
        """
            
            # Add sample content analysis if available
            if "samples" in available_sources and available_sources["samples"]:
                document_analysis += f"""
        
        CONTENT SAMPLES:
        I've analyzed sample content from your documents:
        """
                for sample in available_sources["samples"][:3]:  # Show first 3 samples
                    document_analysis += f"""
        - Sample {sample.get('id', 'N/A')} (Source: {sample.get('source_id', 'Unknown')}):
          "{sample.get('content_preview', 'No preview available')}"
        """
                
                document_analysis += f"""
        
        Based on this content analysis, I can suggest the most appropriate template structure for your report.
        """
        
        # Craft the enhanced conversational prompt
        prompt = f"""
        You are an expert AI assistant specializing in creating professional report templates with document analysis capabilities.
        
        {chat_context}
        
        The user is asking for help creating a report on: "{query}"
        
        {content_context}
        
        {document_analysis}
        
        Respond in two parts:
        
        1. CONVERSATION: Engage with the user conversationally about their report needs. If they have uploaded documents, analyze what type of content they likely contain and suggest appropriate template structures. Ask clarifying questions if needed. Explain why certain sections would be valuable for this topic. Make this feel like a genuine consultation with a report writing expert who can see their documents.
        
        2. TEMPLATE: After your conversational response, provide a suggested template with 4-7 distinct sections formatted as a valid JSON array. Base the template on both the user's query and the type of documents they have uploaded.
        
        Example response format:
        
        CONVERSATION: [Your natural, helpful response here discussing the report structure, analyzing their uploaded documents, and asking any clarifying questions]
        
        TEMPLATE: ["Executive Summary", "Introduction", "Key Findings", "Recommendations", "Conclusion"]
        """
        
        # Generate the conversational template suggestion
        response = llm.invoke(prompt)
        
        # Extract the content from response
        content = response.content if hasattr(response, "content") else str(response)
        
        # Parse the response to extract conversation and template parts
        parts = content.split("TEMPLATE:")
        
        conversation = parts[0].replace("CONVERSATION:", "").strip()
        template_text = parts[1].strip() if len(parts) > 1 else "[]"
        
        # Clean up the template text to get just the JSON list
        if template_text.startswith("```"):
            # Remove code blocks if present
            template_text = "\n".join(template_text.split("\n")[1:-1])
        
        # Parse the JSON list
        import json
        try:
            sections = json.loads(template_text)
        except json.JSONDecodeError:
            # Fall back to regex extraction if JSON parsing fails
            import re
            match = re.search(r'\[(.*)\]', template_text)
            if match:
                # Extract items from the array format and clean them
                items_text = match.group(1)
                items = [item.strip().strip('"\'') for item in items_text.split(',')]
                sections = [item for item in items if item]  # Remove empty items
            else:
                sections = ["Executive Summary", "Key Findings", "Analysis", "Recommendations"]
        
        # Create a template from the suggestions
        template_id = str(uuid.uuid4())
        new_template = {
            "id": template_id,
            "template": sections,
            "query": query,
            "source_based": bool(source_context or available_sources)
        }
        
        # Store the template
        templates.append(new_template)
        
        return {
            "status": "created", 
            "template": new_template,
            "conversation": conversation,
            "message": f"Created template with {len(sections)} sections based on your query."
        }
    except Exception as e:
        print(f"Error suggesting template: {e}")
        
        # Fallback to default template
        default_sections = ["Executive Summary", "Key Findings", "Analysis", "Recommendations", "Conclusion"]
        return {
            "status": "fallback",
            "template": {
                "id": "fallback_" + str(uuid.uuid4())[:8],
                "template": default_sections,
                "query": query
            },
            "conversation": "I've created a standard report structure for you since I encountered an error with the custom template generation.",
            "error": str(e),
            "message": "Used default template due to an error in suggestion generation."
        }

def save_template(template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a custom template to the templates list and persist to file.
    """
    try:
        # Add the template to the global templates list
        templates.append(template)
        
        # Save to file for persistence
        templates_file = "templates.json"
        try:
            with open(templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, indent=2, ensure_ascii=False)
            print(f"💾 Templates saved to {templates_file}")
        except Exception as file_error:
            print(f"⚠️ Warning: Could not save templates to file: {file_error}")
        
        return {
            "status": "success",
            "message": f"Template '{template['name']}' saved successfully",
            "template": template
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to save template: {str(e)}",
            "error": str(e)
        }

def get_all_templates() -> List[Dict[str, Any]]:
    """
    Get all available templates.
    """
    return templates
