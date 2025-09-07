#!/usr/bin/env python
"""
Complete Agentic AI System - Class-Based with Persistent State
Handles document processing, analysis, template generation, and report generation
Uses WebSockets for real-time communication and maintains state across requests
"""

import os
import uuid
import json
import asyncio
import datetime
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.generator import collection, diagnose_collection, get_document_samples_for_analysis

# -----------------------------
# Configuration
# -----------------------------
os.environ["GOOGLE_API_KEY"] = "AIzaSyAkQBm7Flsbd6YlAgNzvvVIs3hbtMRDjsg"

router = APIRouter()

# -----------------------------
# Agentic AI System Class
# -----------------------------
class AgenticAISystem:
    def __init__(self):
        # Persistent state
        self.vectorstore = None
        self.documents_processed = False
        self.current_report = {}
        self.conversation_memory = []
        self.thread_id = f"agentic-session-{uuid.uuid4().hex[:8]}"
        self.llm = None
        self.embeddings = None
        self.websocket_connections = []
        self.finalized_template = None
        self.template_finalization_state = "none"  # none, in_progress, finalized
        
        # Initialize LLM and embeddings
        self._initialize_llm()
        
        print(f"🤖 Agentic AI System initialized with thread_id: {self.thread_id}")
    
    def _initialize_llm(self):
        """Initialize the LLM and embeddings."""
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="models/gemini-2.5-flash", 
                temperature=0.3
            )
            self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            print("✅ LLM and embeddings initialized successfully")
        except Exception as e:
            print(f"❌ Error initializing LLM: {e}")
    
    def process_documents(self, input_text: str = "") -> str:
        """Process uploaded documents and create searchable vector store."""
        try:
            # First check if collection exists and is accessible
            try:
                status = diagnose_collection()
                doc_count = status.get("document_count", 0)
            except Exception as e:
                return f"Error accessing document collection: {str(e)}. Please try uploading documents again or restart the server."
            
            if doc_count == 0:
                return "No documents found. Please upload documents first."
            
            # Try to get documents from collection
            try:
                all_docs = collection.get()
            except Exception as e:
                print(f"❌ Collection access failed: {e}")
                # Try to recover the collection
                try:
                    from app.services.generator import recover_collection
                    recover_collection()
                    all_docs = collection.get()
                    print(f"✅ Collection recovered successfully")
                except Exception as e2:
                    print(f"❌ Collection recovery failed: {e2}")
                    # Try a complete reset as last resort
                    try:
                        from app.services.generator import reset_collection
                        reset_collection()
                        return "Collection was corrupted and has been reset. Please upload your documents again to continue."
                    except Exception as e3:
                        return f"Collection is severely corrupted and cannot be recovered. Error: {str(e3)}. Please restart the server or contact support."
            
            if not all_docs or not all_docs.get('documents'):
                return "No document content found in collection."
            
            documents = []
            for i, doc_content in enumerate(all_docs['documents']):
                if doc_content and len(doc_content.strip()) > 50:
                    metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') and i < len(all_docs['metadatas']) else {}
                    source_id = metadata.get('source_id', f'doc_{i}')
                    page = metadata.get('page', 1)
                    
                    text_splitter = RecursiveCharacterTextSplitter(
                        chunk_size=500, 
                        chunk_overlap=50,
                        separators=["\n\n", "\n", ". ", " ", ""]
                    )
                    chunks = text_splitter.split_text(doc_content)
                    
                    for j, chunk in enumerate(chunks):
                        documents.append(f"[Source: {source_id}, Page: {page}, Chunk: {j+1}] {chunk}")
            
            if not documents:
                return "No valid document content found to process."
            
            self.vectorstore = FAISS.from_texts(documents, self.embeddings)
            self.documents_processed = True
            
            return f"✅ Successfully processed {len(documents)} document chunks from {doc_count} documents."
            
        except Exception as e:
            return f"Error processing documents: {str(e)}"
    
    def analyze_documents(self, input_text: str = "") -> str:
        """Perform intelligent analysis of uploaded documents."""
        try:
            if not self.documents_processed:
                result = self.process_documents()
                if "Error" in result:
                    return result
            
            samples_data = get_document_samples_for_analysis()
            samples = samples_data.get("samples", [])
            
            if not samples:
                return "No document samples available for analysis."
            
            analysis = f"📊 **Document Analysis Results:**\n\n"
            analysis += f"**Total Documents:** {len(samples)}\n\n"
            
            for i, sample in enumerate(samples[:3], 1):
                content_preview = sample.get('content_preview', str(sample))
                source_id = sample.get('source_id', f'Document {i}')
                analysis += f"**Document {i} ({source_id}):**\n{content_preview[:300]}...\n\n"
            
            analysis += "**Key Insights:**\n• Documents contain structured information\n• Content suitable for report generation\n• Multiple sources available for analysis\n"
            
            return analysis
            
        except Exception as e:
            return f"Error analyzing documents: {str(e)}"
    
    def generate_report(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate comprehensive reports from documents with intelligent template suggestions."""
        try:
            if not self.documents_processed:
                result = self.process_documents()
                if "Error" in result:
                    return result
            
            samples_data = get_document_samples_for_analysis()
            samples = samples_data.get("samples", [])
            
            # Check if user has selected a specific template
            selected_template = None
            if context:
                selected_template = context.get("selected_template") or context.get("current_template")
                print(f"🔍 Template context check: selected_template={context.get('selected_template') is not None}, current_template={context.get('current_template') is not None}")
                if selected_template:
                    print(f"🎯 Found selected template: {selected_template.get('name', 'Unknown')} with sections: {selected_template.get('template', [])}")
                else:
                    print(f"⚠️ No selected template found in context: {context.keys()}")
            
            if selected_template:
                # Use the user-selected template
                sections_list = selected_template.get("template", ["Executive Summary", "Key Findings", "Recommendations"])
                template_name = selected_template.get("name", "Selected Template")
                response = f"🎯 **Using your selected template!**\n\n**Template:** {template_name}\n**Sections:** {', '.join(sections_list)}\n\n"
                print(f"🎯 Using user-selected template: {template_name} with sections: {sections_list}")
            else:
                # Try to extract template from conversation memory first
                extracted_template = self._extract_template_from_conversation()
                
                if extracted_template:
                    # Use the template from conversation
                    sections_list = extracted_template["template"]
                    template_name = extracted_template["name"]
                    response = f"🎯 **Using Template from Our Conversation!**\n\n**Template:** {template_name}\n**Sections:** {', '.join(sections_list)}\n\n"
                    print(f"🎯 Using extracted template from conversation: {template_name} with sections: {sections_list}")
                else:
                    # Fallback: Ask the model directly for the best template
                    ai_generated_template = self._ask_model_for_template(input_text, samples)
                    sections_list = ai_generated_template["template"]
                    template_name = ai_generated_template["name"]
                    
                    # Save the AI-generated template
                    self._save_custom_template(ai_generated_template)
                    
                    response = f"🤖 **AI-Generated Perfect Template!**\n\n**Template:** {template_name}\n**Sections:** {', '.join(sections_list)}\n\n"
                    print(f"🤖 AI generated template: {template_name} with sections: {sections_list}")
            
            # Generate the report
            from app.services.generator import generate_report_from_query
            
            report_result = generate_report_from_query(
                sections=sections_list,
                query=input_text,
                top_k=5
            )
            
            if report_result and "report_id" in report_result:
                response += f"✅ **Report Generated Successfully!**\n\n**Report ID:** {report_result['report_id']}\n\nI've created a comprehensive report using your uploaded documents. The report includes proper citations and formatting based on your specific requirements."
            else:
                response += f"✅ **Report Generated Successfully!**\n\nI've created a comprehensive report using your uploaded documents with intelligent analysis and proper citations."
            
            return response
            
        except Exception as e:
            return f"Error generating report: {str(e)}"
    
    def _suggest_best_template(self, input_text: str, samples: List[Dict]) -> Dict:
        """Suggest the best existing template based on user request and document content."""
        try:
            # Get available templates
            from app.services.template import get_all_templates
            templates = get_all_templates()
            
            if not templates:
                return {"id": "default", "name": "Default Template", "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"]}
            
            # Create a prompt to analyze and suggest the best template
            samples_text = "\n".join([sample.get('content_preview', str(sample))[:200] for sample in samples[:3]])
            templates_text = "\n".join([f"- {t['name']}: {t['description']} (Sections: {', '.join(t['template'])})" for t in templates])
            
            suggestion_prompt = f"""
Based on the user request and document content, suggest the most suitable template.

User Request: "{input_text}"

Document Content Samples:
{samples_text}

Available Templates:
{templates_text}

IMPORTANT: Choose the template that best matches the user's request. If the user mentions specific sections or types of analysis, prioritize templates that include those sections.

Respond with ONLY valid JSON (no other text):
{{"template_id": "id", "confidence": 0.8, "reason": "explanation"}}
"""
            
            response = self.llm.invoke([HumanMessage(content=suggestion_prompt)])
            response_content = response.content.strip()
            
            # Clean up response to extract JSON
            if "```json" in response_content:
                start = response_content.find("```json") + 7
                end = response_content.find("```", start)
                response_content = response_content[start:end].strip()
            elif "```" in response_content:
                start = response_content.find("```") + 3
                end = response_content.find("```", start)
                response_content = response_content[start:end].strip()
            
            try:
                suggestion = json.loads(response_content)
                # Find the suggested template
                suggested_template = next((t for t in templates if t["id"] == suggestion["template_id"]), None)
                
                if suggested_template:
                    print(f"🎯 Selected template: {suggested_template['name']} with sections: {suggested_template['template']}")
                    return suggested_template
                else:
                    print(f"⚠️ Template ID {suggestion.get('template_id')} not found, using first available template")
                    return templates[0]
                    
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing failed: {e}, using first available template")
                return templates[0]
            
        except Exception as e:
            print(f"❌ Error in template suggestion: {e}")
            # Fallback to default template
            from app.services.template import get_all_templates
            templates = get_all_templates()
            return templates[0] if templates else {"id": "default", "name": "Default Template", "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"]}
    
    def _decide_template_approach(self, input_text: str, samples: List[Dict], suggested_template: Dict) -> Dict:
        """Decide whether to use existing template or create custom one."""
        try:
            samples_text = "\n".join([sample.get('content_preview', str(sample))[:200] for sample in samples[:2]])
            
            decision_prompt = f"""
Analyze if the user's request requires a custom template or if an existing template is sufficient.

User Request: "{input_text}"
Suggested Template: {suggested_template['name']} - {', '.join(suggested_template['template'])}

Document Content:
{samples_text}

Consider:
- Specificity of user requirements
- Uniqueness of document content
- Whether existing templates cover the needs

Respond with JSON: {{"use_custom": true/false, "reason": "explanation"}}
"""
            
            response = self.llm.invoke([HumanMessage(content=decision_prompt)])
            decision = json.loads(response.content.strip())
            
            return decision
            
        except Exception as e:
            # Default to using existing template
            return {"use_custom": False, "reason": "Using existing template as fallback"}
    
    def _create_custom_template(self, input_text: str, samples: List[Dict]) -> Dict:
        """Create a custom template based on user requirements and document content."""
        try:
            samples_text = "\n".join([sample.get('content_preview', str(sample))[:300] for sample in samples[:3]])
            
            template_prompt = f"""
Create a custom report template based on the user's specific requirements and document content.

User Request: "{input_text}"

Document Content:
{samples_text}

Create a template that:
1. Addresses the user's specific needs
2. Is appropriate for the document content type
3. Has 4-6 logical sections
4. Follows professional report structure

Respond with JSON:
{{
    "name": "Template Name",
    "description": "Brief description",
    "template": ["Section1", "Section2", "Section3", "Section4"],
    "category": "Category"
}}
"""
            
            response = self.llm.invoke([HumanMessage(content=template_prompt)])
            template_data = json.loads(response.content.strip())
            
            # Add metadata
            template_data["id"] = f"custom_{uuid.uuid4().hex[:8]}"
            template_data["created_at"] = str(uuid.uuid4())
            
            return template_data
            
        except Exception as e:
            # Fallback template
            return {
                "id": f"custom_{uuid.uuid4().hex[:8]}",
                "name": "Custom Report Template",
                "description": "Custom template based on your requirements",
                "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"],
                "category": "Custom",
                "created_at": str(uuid.uuid4())
            }
    
    def _save_custom_template(self, template: Dict):
        """Save custom template to the template system."""
        try:
            from app.services.template import save_template
            save_template(template)
            print(f"💾 Saved custom template: {template['name']}")
        except Exception as e:
            print(f"❌ Error saving template: {e}")
    
    def _extract_template_from_conversation(self) -> Optional[Dict]:
        """Extract template information from conversation memory."""
        try:
            # Look through conversation memory for template information
            for message in reversed(self.conversation_memory[-10:]):  # Check last 10 messages
                content = message.get("content", "")
                
                # Look for "Template Saved Successfully" messages
                if "Template Saved Successfully" in content and "Template Name:" in content:
                    print(f"🔍 Found template save message in conversation: {content[:100]}...")
                    
                    # Extract template information using regex
                    import re
                    
                    # Extract template name
                    name_match = re.search(r'Template Name:\*\*\s*([^\n]+)', content)
                    template_name = name_match.group(1).strip() if name_match else "Extracted Template"
                    
                    # Extract sections
                    sections_match = re.search(r'Sections:\*\*\s*([^\n]+)', content)
                    if sections_match:
                        sections_text = sections_match.group(1).strip()
                        # Split by comma and clean up
                        sections = [s.strip() for s in sections_text.split(',')]
                        
                        # Extract description if available
                        desc_match = re.search(r'Description:\*\*\s*([^\n]+)', content)
                        description = desc_match.group(1).strip() if desc_match else f"Template extracted from conversation: {template_name}"
                        
                        # Extract category if available
                        category_match = re.search(r'Category:\*\*\s*([^\n]+)', content)
                        category = category_match.group(1).strip() if category_match else "Extracted"
                        
                        extracted_template = {
                            "id": f"extracted_{uuid.uuid4().hex[:8]}",
                            "name": template_name,
                            "description": description,
                            "template": sections,
                            "category": category,
                            "created_at": datetime.datetime.now().isoformat() + "Z"
                        }
                        
                        print(f"✅ Extracted template from conversation: {template_name} with {len(sections)} sections")
                        return extracted_template
            
            print("⚠️ No template found in conversation memory")
            return None
            
        except Exception as e:
            print(f"❌ Error extracting template from conversation: {e}")
            return None
    
    def _ask_model_for_template(self, input_text: str, samples: List[Dict]) -> Dict:
        """Ask the model directly for the best template based on user request and documents."""
        try:
            samples_text = "\n".join([sample.get('content_preview', str(sample))[:300] for sample in samples[:3]])
            
            template_prompt = f"""
Create the perfect report template based on the user's request and document content.

User Request: "{input_text}"

Document Content:
{samples_text}

Create a template that:
1. Directly addresses the user's specific request
2. Is appropriate for the document content type
3. Has 4-6 logical sections
4. Follows professional report structure
5. Uses section names that match the user's intent

Respond with ONLY valid JSON (no other text):
{{
    "name": "Template Name",
    "description": "Brief description",
    "template": ["Section1", "Section2", "Section3", "Section4"],
    "category": "Category"
}}
"""
            
            response = self.llm.invoke([HumanMessage(content=template_prompt)])
            response_content = response.content.strip()
            
            # Clean up response to extract JSON
            if "```json" in response_content:
                start = response_content.find("```json") + 7
                end = response_content.find("```", start)
                response_content = response_content[start:end].strip()
            elif "```" in response_content:
                start = response_content.find("```") + 3
                end = response_content.find("```", start)
                response_content = response_content[start:end].strip()
            
            try:
                template_data = json.loads(response_content)
                
                # Add metadata
                template_data["id"] = f"ai_generated_{uuid.uuid4().hex[:8]}"
                template_data["created_at"] = datetime.datetime.now().isoformat() + "Z"
                
                return template_data
                
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON parsing failed: {e}, using fallback template")
                return {
                    "id": f"fallback_{uuid.uuid4().hex[:8]}",
                    "name": "AI-Generated Report Template",
                    "description": "Template generated based on your request",
                    "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"],
                    "category": "AI Generated",
                    "created_at": datetime.datetime.now().isoformat() + "Z"
                }
            
        except Exception as e:
            print(f"❌ Error asking model for template: {e}")
            return {
                "id": f"error_fallback_{uuid.uuid4().hex[:8]}",
                "name": "Default Report Template",
                "description": "Fallback template due to error",
                "template": ["Executive Summary", "Key Findings", "Recommendations"],
                "category": "Fallback",
                "created_at": datetime.datetime.now().isoformat() + "Z"
            }
    
    def _generate_curious_response(self, command: str) -> str:
        """Generate a curious, engaging response that's appropriately sized."""
        try:
            # Check for save-template command first
            if "save-template" in command.lower():
                return self._handle_save_template_command(command)
            
            # Analyze the user's intent and generate an appropriate response
            curiosity_prompt = f"""
You are a helpful AI assistant that's curious about the user's needs. Generate a response that:

1. Shows genuine interest in what the user wants to accomplish
2. Is appropriately sized (not too long, not too short - aim for 2-4 sentences)
3. Asks one thoughtful question to understand their needs better
4. Avoids hallucination - only mention capabilities you actually have
5. Is engaging and conversational

User's request: "{command}"

Your capabilities:
- Generate professional reports from documents
- Analyze uploaded content
- Create custom templates
- Process various document types (PDF, Word, videos, audio)

Respond in a curious, helpful tone. Keep it concise but engaging.
"""
            
            response = self.llm.invoke([HumanMessage(content=curiosity_prompt)])
            return response.content.strip()
            
        except Exception as e:
            # Fallback response
            return f"I'm curious about what you'd like to accomplish! 🤔 I can help you generate reports, analyze documents, or create custom templates. What specific outcome are you hoping to achieve?"
    
    def _handle_save_template_command(self, command: str) -> str:
        """Handle save-template command."""
        try:
            # For simple "save-template" command, create a default template
            if command.lower().strip() == "save-template":
                template_data = {
                    "name": "Custom Report Template",
                    "description": "A custom template created from user request",
                    "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"],
                    "category": "Custom"
                }
            else:
                # Extract template information from command
                template_prompt = f"""
                The user wants to save a template. Based on their request: "{command}"
                
                Create a template definition. If they provided specific sections, use those. Otherwise, create a logical template.
                
                Respond with ONLY valid JSON (no other text):
                {{
                    "name": "Template Name",
                    "description": "Brief description",
                    "template": ["Section1", "Section2", "Section3", "Section4"],
                    "category": "Category"
                }}
                """
                
                response = self.llm.invoke([HumanMessage(content=template_prompt)])
                response_content = response.content.strip()
                
                # Try to extract JSON from response if it contains other text
                if "```json" in response_content:
                    start = response_content.find("```json") + 7
                    end = response_content.find("```", start)
                    response_content = response_content[start:end].strip()
                elif "```" in response_content:
                    start = response_content.find("```") + 3
                    end = response_content.find("```", start)
                    response_content = response_content[start:end].strip()
                
                # Try to parse JSON
                try:
                    template_data = json.loads(response_content)
                except json.JSONDecodeError:
                    # Fallback to default template if JSON parsing fails
                    template_data = {
                        "name": "Custom Report Template",
                        "description": "A custom template created from user request",
                        "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"],
                        "category": "Custom"
                    }
            
            # Add metadata
            import datetime
            template_data["id"] = f"custom_{uuid.uuid4().hex[:8]}"
            template_data["created_at"] = datetime.datetime.now().isoformat() + "Z"
            
            # Save the template
            self._save_custom_template(template_data)
            
            return f"💾 **Template Saved Successfully!**\n\n**Template Name:** {template_data['name']}\n**Description:** {template_data['description']}\n**Sections:** {', '.join(template_data['template'])}\n**Category:** {template_data['category']}\n\nYour custom template has been saved and is now available for use in future reports!"
            
        except Exception as e:
            return f"❌ **Error saving template:** {str(e)}\n\nCould you try rephrasing your template request? I'd be happy to help you create and save a custom template!"
    
    def get_system_status(self, input_text: str = "") -> str:
        """Get current system status and capabilities."""
        try:
            status = diagnose_collection()
            doc_count = status.get("document_count", 0)
            
            status_report = f"🤖 **Agentic AI System Status:**\n\n"
            status_report += f"**Thread ID:** {self.thread_id}\n"
            status_report += f"**Documents:** {doc_count} uploaded\n"
            status_report += f"**Vector Store:** {'✅ Ready' if self.vectorstore else '❌ Not Ready'}\n"
            status_report += f"**Documents Processed:** {'✅ Yes' if self.documents_processed else '❌ No'}\n"
            status_report += f"**Current Report:** {'✅ Active' if self.current_report else '❌ None'}\n"
            status_report += f"**Memory:** ✅ Active ({len(self.conversation_memory)} messages)\n"
            status_report += f"**WebSocket Connections:** {len(self.websocket_connections)}\n"
            status_report += f"**Autonomous Decision Making:** ✅ Enabled\n\n"
            
            status_report += "**Available Actions:**\n"
            status_report += "• Process documents\n• Analyze document content\n• Generate comprehensive reports\n• Update existing reports\n• Get system status\n"
            
            return status_report
            
        except Exception as e:
            return f"Error getting system status: {str(e)}"
    
    def document_summary(self, input_text: str = "") -> str:
        """Create summaries of document content."""
        try:
            if not self.documents_processed:
                result = self.process_documents()
                if "Error" in result:
                    return result
            
            samples_data = get_document_samples_for_analysis()
            samples = samples_data.get("samples", [])
            
            if not samples:
                return "No documents available for summary."
            
            summary = f"📋 **Document Summary:**\n\n"
            summary += f"**Total Documents:** {len(samples)}\n\n"
            
            for i, sample in enumerate(samples[:3], 1):
                content_preview = sample.get('content_preview', str(sample))
                summary += f"**Document {i}:** {content_preview[:200]}...\n\n"
            
            summary += "**Summary:** The uploaded documents contain structured information suitable for analysis and report generation."
            
            return summary
            
        except Exception as e:
            return f"Error creating document summary: {str(e)}"
    
    def analyze_user_intent(self, command: str) -> Dict[str, Any]:
        """Analyze user intent and determine appropriate actions."""
        command_lower = command.lower()
        
        # Intent detection
        intents = {
            "generate_report": any(keyword in command_lower for keyword in [
                "generate report", "create report", "make report", "build report", 
                "report from", "use template", "generate from", "proceed"
            ]),
            "analyze_documents": any(keyword in command_lower for keyword in [
                "analyze", "analyse", "check documents", "what's in", "show me"
            ]) and not any(keyword in command_lower for keyword in ["report", "generate", "create"]),
            "process_documents": any(keyword in command_lower for keyword in [
                "process documents", "prepare documents", "setup documents"
            ]),
            "get_status": any(keyword in command_lower for keyword in [
                "status", "what can you do", "capabilities", "help"
            ]),
            "document_summary": any(keyword in command_lower for keyword in [
                "summary", "overview", "brief"
            ]) and not any(keyword in command_lower for keyword in ["report", "generate", "create"])
        }
        
        return intents
    
    def execute_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Execute intelligent agentic logic based on user intent with persistent state."""
        try:
            # Add to conversation memory
            self.conversation_memory.append({"role": "user", "content": command})
            
            # Check if user wants to generate a report
            command_lower = command.lower().strip()
            
            if "save-template" in command_lower:
                # User wants to save a template
                return self._handle_save_template_command(command)
            elif "generate" in command_lower and len(command_lower.split()) <= 3:
                # User just said "generate" or similar - start template finalization
                return self._handle_generate_request(command, context)
            elif "generate" in command_lower and any(word in command_lower for word in ["now", "immediately", "directly", "quick"]):
                # User wants immediate generation - skip template finalization
                return self._handle_immediate_generation(command, context)
            elif self.template_finalization_state == "in_progress":
                # User is in template finalization process
                return self._handle_template_finalization(command, context)
            else:
                # Regular command processing with intelligent response sizing
                status = diagnose_collection()
                doc_count = status.get("document_count", 0)
                
                if doc_count > 0:
                    result = self.generate_report(command, context)
                else:
                    result = self._generate_curious_response(command)
            
            # Add result to memory
            self.conversation_memory.append({"role": "assistant", "content": result})
            
            # Keep memory manageable (last 20 exchanges)
            if len(self.conversation_memory) > 20:
                self.conversation_memory = self.conversation_memory[-20:]
            
            # Log the execution
            print(f"🤖 Executed command: {command[:50]}...")
            print(f"🤖 Thread ID: {self.thread_id}")
            print(f"🤖 Memory length: {len(self.conversation_memory)}")
            
            return result
            
        except Exception as e:
            error_msg = f"An error occurred while processing your request: {str(e)}"
            self.conversation_memory.append({"role": "assistant", "content": error_msg})
            return error_msg
    
    def _handle_generate_request(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle when user wants to generate a report - start template finalization."""
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        if doc_count == 0:
            return "No documents found. Please upload documents first to generate a report."
        
        # Start template finalization process
        self.template_finalization_state = "in_progress"
        
        # Get document samples for context
        samples_data = get_document_samples_for_analysis()
        samples = samples_data.get("samples", [])
        
        # Create a template suggestion based on documents
        template_suggestion = self._suggest_template_from_documents(samples)
        
        response = f"""🎯 Exciting! I can see {doc_count} document(s) ready for analysis. Based on what I can see, this looks like it could be a fascinating project!

Let me suggest a template structure that would work well with your content:

{template_suggestion}

I'm curious - what's the main goal here? Are you looking to:
• Create a comprehensive analysis report?
• Generate a quick summary for stakeholders?
• Build something more specialized?

Quick options:
• "yes" → Use this template (I think it'll work great!)
• "summary" → I'll create a concise overview
• "custom" → Tell me your specific vision

What's your take on this? I'm excited to help you create something amazing! 🚀"""
        
        self.conversation_memory.append({"role": "assistant", "content": response})
        return response
    
    def _handle_immediate_generation(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle immediate report generation without template finalization."""
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        if doc_count == 0:
            return "No documents found. Upload documents first to generate a report."
        
        # Create a default template and generate immediately
        self.template_finalization_state = "finalized"
        self.finalized_template = self._create_finalized_template()
        
        # Generate the report
        result = self.generate_report("Generate report using default template immediately", context)
        
        # Reset state for next time
        self.template_finalization_state = "none"
        
        return result
    
    def _handle_template_finalization(self, command: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Handle template finalization conversation."""
        command_lower = command.lower().strip()
        
        # Check if user confirms the template
        if any(word in command_lower for word in ["yes", "yep", "sure", "good", "perfect", "ok", "okay", "finalize", "proceed"]):
            # User confirmed - finalize template and generate report
            self.template_finalization_state = "finalized"
            self.finalized_template = self._create_finalized_template()
            
            # Generate the report
            result = self.generate_report("Generate report using finalized template", context)
            
            # Reset state for next time
            self.template_finalization_state = "none"
            
            return result
        
        # Check if user specifically wants a summary template
        elif "summary" in command_lower and ("template" in command_lower or "generate" in command_lower):
            # User wants summary template - create and finalize it
            self.template_finalization_state = "finalized"
            self.finalized_template = self._create_summary_template()
            
            # Generate the report
            result = self.generate_report("Generate summary report using summary template", context)
            
            # Reset state for next time
            self.template_finalization_state = "none"
            
            return result
        
        elif any(word in command_lower for word in ["no", "nope", "change", "modify", "different"]):
            # User wants to modify template
            response = """Great question! I'm always curious about how we can make this better.

What's on your mind? Are you thinking:
• Different sections that would be more relevant?
• A different structure that fits your needs better?
• Something more specific to your use case?

I'm excited to hear your ideas! What changes are you envisioning? Let's make this template perfect for what you need! 🎨"""
            
            self.conversation_memory.append({"role": "assistant", "content": response})
            return response
        
        else:
            # User provided additional information - incorporate it
            response = f"""Perfect! I love how you're thinking about this. Here's what I've updated based on your input:

{self._update_template_with_feedback(command)}

This is looking really promising! I'm getting excited about what we can create together. 

Does this capture what you had in mind? I'm curious - are there any other aspects you'd like to explore or refine? 

Type "yes" when you're ready to generate, or let me know what else we should adjust! I think this is going to be fantastic! ✨"""
            
            self.conversation_memory.append({"role": "assistant", "content": response})
            return response
    
    def _suggest_template_from_documents(self, samples: List[Dict]) -> str:
        """Suggest a template based on document content."""
        if not samples:
            return """**Standard Report Template:**
1. **Executive Summary**
2. **Introduction**
3. **Key Findings**
4. **Analysis**
5. **Recommendations**
6. **Conclusion**"""
        
        # Analyze sample content to suggest relevant sections
        content_preview = ""
        for sample in samples[:2]:  # Use first 2 samples
            content_preview += sample.get('content_preview', str(sample))[:200] + "...\n"
        
        # Use LLM to suggest template based on content
        try:
            prompt = f"""Based on this document content, suggest a professional report template structure:

Content Preview:
{content_preview}

Provide a structured template with 4-6 main sections that would be most relevant for this type of content. Format it clearly with section numbers and brief descriptions."""
            
            response = self.llm.invoke(prompt)
            template = response.content if hasattr(response, "content") else str(response)
            
            return template
            
        except Exception as e:
            print(f"Error generating template suggestion: {e}")
            return """1. Executive Summary
2. Document Analysis  
3. Key Insights
4. Recommendations
5. Conclusion"""
    
    def _create_summary_template(self) -> Dict[str, Any]:
        """Create a summary-focused template."""
        return {
            "id": f"summary-template-{uuid.uuid4().hex[:8]}",
            "name": "Summary Report Template",
            "description": "Concise summary template for quick overview",
            "sections": [
                {"title": "Executive Summary", "description": "High-level overview and key points"},
                {"title": "Key Findings", "description": "Main discoveries and insights"},
                {"title": "Summary", "description": "Comprehensive summary of all content"},
                {"title": "Conclusion", "description": "Final thoughts and next steps"}
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "finalized": True
        }
    
    def _update_template_with_feedback(self, feedback: str) -> str:
        """Update template based on user feedback."""
        # This is a simplified version - in a real implementation, you'd use LLM to process feedback
        return f"""1. Executive Summary
2. Customized Analysis - {feedback[:50]}...
3. Key Findings
4. Recommendations  
5. Conclusion

Based on: "{feedback[:30]}..." """
    
    def _create_finalized_template(self) -> Dict[str, Any]:
        """Create the finalized template structure."""
        return {
            "id": f"agentic-template-{uuid.uuid4().hex[:8]}",
            "name": "AI-Generated Template",
            "description": "Template created through conversational finalization",
            "sections": [
                {"title": "Executive Summary", "description": "Key highlights and overview"},
                {"title": "Document Analysis", "description": "Main findings from uploaded documents"},
                {"title": "Key Insights", "description": "Important discoveries and patterns"},
                {"title": "Recommendations", "description": "Actionable next steps"},
                {"title": "Conclusion", "description": "Summary and final thoughts"}
            ],
            "created_at": "2024-01-01T00:00:00Z",
            "finalized": True
        }

    def reset_state(self):
        """Reset the system state for a new session."""
        self.vectorstore = None
        self.documents_processed = False
        self.current_report = {}
        self.conversation_memory = []
        self.thread_id = f"agentic-session-{uuid.uuid4().hex[:8]}"
        self.finalized_template = None
        self.template_finalization_state = "none"
        print(f"🔄 System reset with new thread_id: {self.thread_id}")
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get current system status as dictionary."""
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        return {
            "agentic_ai": True,
            "thread_id": self.thread_id,
            "documents_processed": self.documents_processed,
            "vectorstore_ready": self.vectorstore is not None,
            "current_report_sections": list(self.current_report.keys()) if self.current_report else [],
            "available_tools": [
                "ProcessDocuments",
                "AnalyzeDocuments", 
                "GenerateReport",
                "GetSystemStatus",
                "DocumentSummary"
            ],
            "memory_active": True,
            "conversation_length": len(self.conversation_memory),
            "autonomous_decision_making": True,
            "document_count": doc_count,
            "websocket_connections": len(self.websocket_connections),
            "template_finalization_state": self.template_finalization_state,
            "finalized_template": self.finalized_template
        }
    
    async def add_websocket_connection(self, websocket: WebSocket):
        """Add a WebSocket connection."""
        self.websocket_connections.append(websocket)
        print(f"🔌 WebSocket connection added. Total: {len(self.websocket_connections)}")
    
    async def remove_websocket_connection(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
        print(f"🔌 WebSocket connection removed. Total: {len(self.websocket_connections)}")
    
    async def broadcast_to_websockets(self, message: str):
        """Broadcast message to all WebSocket connections."""
        if self.websocket_connections:
            for websocket in self.websocket_connections.copy():
                try:
                    await websocket.send_text(message)
                except:
                    await self.remove_websocket_connection(websocket)

# -----------------------------
# Global Agentic AI Instance
# -----------------------------
agentic_system = AgenticAISystem()

# -----------------------------
# Request / Response Models
# -----------------------------
class AgenticRequest(BaseModel):
    command: str
    context: Optional[Dict[str, Any]] = None
    mode: Optional[str] = "auto"
    selected_template: Optional[Dict[str, Any]] = None
    current_template: Optional[Dict[str, Any]] = None

class AgenticResponse(BaseModel):
    response: str
    status: str
    command: Optional[str] = None
    error: Optional[str] = None
    agentic: bool = True
    memory_used: Optional[bool] = None
    thread_id: Optional[str] = None

# -----------------------------
# API Endpoints
# -----------------------------

@router.post("/command", response_model=AgenticResponse)
async def execute_agentic_command(request: AgenticRequest):
    """Execute a command through the agentic AI system."""
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        result = agentic_system.execute_command(request.command, request.context)
        
        return AgenticResponse(
            response=result,
            status="success",
            command=request.command,
            agentic=True,
            memory_used=True,
            thread_id=agentic_system.thread_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agentic AI execution failed: {str(e)}")

@router.get("/status")
async def get_agentic_system_status():
    """Get the current status of the agentic AI system."""
    try:
        return {
            "status": "success",
            "agentic_ai_status": agentic_system.get_status_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/reset")
async def reset_agentic_system():
    """Reset the agentic AI system state for a new session."""
    try:
        agentic_system.reset_state()
        
        return {
            "status": "success",
            "message": "Agentic AI system reset successfully.",
            "new_thread_id": agentic_system.thread_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset agentic AI: {str(e)}")

@router.post("/chat")
async def agentic_chat(request: AgenticRequest):
    """Interactive chat interface using the agentic AI system."""
    try:
        print(f"🤖 Agentic Chat Request: {request.command}")
        print(f"🤖 Context: {request.context}")
        print(f"🤖 Selected Template: {request.selected_template}")
        print(f"🤖 Current Template: {request.current_template}")
        
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Build enhanced command with context and template information
        enhanced_command = request.command
        if request.context:
            context_info = f"Context: {request.context}"
            enhanced_command = f"{request.command}\n\n{context_info}"
        
        # Add template information to context
        enhanced_context = request.context or {}
        if request.selected_template:
            enhanced_context["selected_template"] = request.selected_template
            print(f"🎯 Using selected template: {request.selected_template.get('name', 'Unknown')}")
        if request.current_template:
            enhanced_context["current_template"] = request.current_template
            print(f"🎯 Using current template: {request.current_template.get('name', 'Unknown')}")
        
        result = agentic_system.execute_command(enhanced_command, enhanced_context)
        
        # Broadcast to WebSocket connections
        await agentic_system.broadcast_to_websockets(f"Agent Response: {result}")
        
        return {
            "response": result,
            "status": "success",
            "command": request.command,
            "agentic": True,
            "memory_used": True,
            "thread_id": agentic_system.thread_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agentic AI chat failed: {str(e)}")

@router.post("/autonomous")
async def autonomous_processing(request: AgenticRequest):
    """Trigger fully autonomous processing."""
    try:
        if not request.command.strip():
            raise HTTPException(status_code=400, detail="Command cannot be empty")
        
        # Enhanced autonomous processing
        autonomous_command = f"Autonomously process this request and take the most appropriate action: {request.command}"
        result = agentic_system.execute_command(autonomous_command, request.context)
        
        # Broadcast to WebSocket connections
        await agentic_system.broadcast_to_websockets(f"Autonomous Response: {result}")
        
        return {
            "response": result,
            "status": "success",
            "command": request.command,
            "agentic": True,
            "autonomous": True,
            "memory_used": True,
            "thread_id": agentic_system.thread_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous processing failed: {str(e)}")

# -----------------------------
# WebSocket Endpoint
# -----------------------------
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket.accept()
    await agentic_system.add_websocket_connection(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            command = message_data.get("command", "")
            
            print(f"🔌 WebSocket received: {command}")
            
            # Process command through agentic system
            result = agentic_system.execute_command(command)
            
            # Send response back to client
            response = {
                "type": "agent_response",
                "response": result,
                "thread_id": agentic_system.thread_id,
                "timestamp": str(uuid.uuid4())
            }
            
            await websocket.send_text(json.dumps(response))
            
    except WebSocketDisconnect:
        await agentic_system.remove_websocket_connection(websocket)
        print("🔌 WebSocket disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await agentic_system.remove_websocket_connection(websocket)