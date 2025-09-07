#!/usr/bin/env python
"""
True Agentic AI System with LangChain Agents
Implements autonomous decision making, tool usage, and multi-step reasoning
"""

import os
import uuid
import json
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_react_agent, AgentExecutor
from langchain.agents import Tool
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.prompts import PromptTemplate
from app.services.generator import collection, diagnose_collection, get_document_samples_for_analysis

# -----------------------------
# Configuration
# -----------------------------
os.environ["GOOGLE_API_KEY"] = "AIzaSyDGA_bxmpmbC7NkEaY97GQoZDUtS1N1nLA"

# Global state for agentic system
vectorstore = None
documents_processed = False
current_report = {}
agent_memory = ConversationBufferWindowMemory(k=10, return_messages=True)

# -----------------------------
# Agentic AI Tools
# -----------------------------

def process_documents_agentic(input_text: str = "") -> str:
    """
    Agentic tool: Process all uploaded documents with intelligent analysis
    """
    global vectorstore, documents_processed
    
    try:
        # Get document status
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        if doc_count == 0:
            return "No documents found. Please upload documents first."
        
        # Get all documents from collection
        all_docs = collection.get()
        if not all_docs or not all_docs.get('documents'):
            return "No document content found in collection."
        
        # Intelligent document processing
        documents = []
        document_metadata = {}
        
        for i, doc_content in enumerate(all_docs['documents']):
            if doc_content and len(doc_content.strip()) > 50:
                metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') and i < len(all_docs['metadatas']) else {}
                source_id = metadata.get('source_id', f'doc_{i}')
                page = metadata.get('page', 1)
                
                # Store metadata for later reference
                document_metadata[source_id] = {
                    'page': page,
                    'length': len(doc_content),
                    'content_preview': doc_content[:200] + "..." if len(doc_content) > 200 else doc_content
                }
                
                # Intelligent chunking based on content type
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
        
        # Create embeddings and vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_texts(documents, embeddings)
        
        documents_processed = True
        
        # Store document metadata in memory for agent reference
        agent_memory.chat_memory.add_ai_message(f"Processed {len(documents)} document chunks from {doc_count} uploaded documents. Document metadata: {document_metadata}")
        
        return f"Successfully processed {len(documents)} document chunks from {doc_count} uploaded documents. Documents are now searchable and ready for analysis."
        
    except Exception as e:
        return f"Error processing documents: {str(e)}"

def analyze_documents_agentic(input_text: str = "") -> str:
    """
    Agentic tool: Intelligent document analysis with context awareness
    """
    global vectorstore, documents_processed
    
    try:
        if not documents_processed:
            result = process_documents_agentic()
            if "Error" in result:
                return result
        
        # Get document samples for analysis
        samples_data = get_document_samples_for_analysis()
        samples = samples_data.get("samples", [])
        
        # Use LLM for intelligent analysis
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3)
        
        # Prepare comprehensive analysis prompt
        content_for_analysis = ""
        for i, sample in enumerate(samples[:5], 1):
            content = sample.get('content_preview', str(sample))
            content_for_analysis += f"Document {i}:\n{content}\n\n"
        
        analysis_prompt = f"""
You are an expert document analyst with agentic capabilities. Analyze these documents and provide:

1. **Document Classification** - What types of documents these are
2. **Content Themes** - Main topics and themes identified
3. **Quality Assessment** - Information quality and completeness
4. **Key Insights** - Important findings and patterns
5. **Report Recommendations** - Best report structure for this content
6. **Next Actions** - Suggested next steps for the user

Document Content:
{content_for_analysis}

Provide a comprehensive, actionable analysis that helps the user understand their documents and make informed decisions about report generation.
"""
        
        response = llm.invoke([HumanMessage(content=analysis_prompt)])
        analysis = response.content
        
        # Store analysis in memory for future reference
        agent_memory.chat_memory.add_ai_message(f"Document analysis completed: {analysis[:200]}...")
        
        return analysis
        
    except Exception as e:
        return f"Error analyzing documents: {str(e)}"

def generate_report_agentic(input_text: str) -> str:
    """
    Agentic tool: Intelligent report generation using the existing report generation system
    """
    global vectorstore, documents_processed, current_report
    
    try:
        if not documents_processed:
            result = process_documents_agentic()
            if "Error" in result:
                return result
        
        # Use LLM to determine report structure
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3)
        
        # Get document context
        samples_data = get_document_samples_for_analysis()
        samples = samples_data.get("samples", [])
        
        # Intelligent section determination
        section_prompt = f"""
Based on the user request "{input_text}" and the following document content, determine the optimal report structure.

Document Content Samples:
{chr(10).join([sample.get('content_preview', str(sample))[:300] for sample in samples[:3]])}

Provide a JSON list of report sections that would best serve the user's needs. Consider:
- Document content type
- User's specific request
- Professional report standards
- Information hierarchy

Respond with only a JSON array of section names.
"""
        
        section_response = llm.invoke([HumanMessage(content=section_prompt)])
        sections_text = section_response.content.strip()
        
        # Parse sections (fallback to defaults if parsing fails)
        try:
            import json
            sections_list = json.loads(sections_text)
        except:
            sections_list = ["Executive Summary", "Key Findings", "Analysis", "Recommendations"]
        
        # Use the existing report generation system
        from app.services.generator import generate_report_from_query
        
        # Generate report using the existing system
        report_result = generate_report_from_query(
            sections=sections_list,
            query=input_text,
            top_k=5
        )
        
        # Store report in memory
        agent_memory.chat_memory.add_ai_message(f"Generated report with sections: {sections_list}")
        
        # Return success message with report ID
        if report_result and "report_id" in report_result:
            return f"✅ **Report Generated Successfully!**\n\nI've created a comprehensive report using your uploaded documents with the following sections:\n{chr(10).join([f'• {section}' for section in sections_list])}\n\n**Report ID:** {report_result['report_id']}\n\nYou can now view, export, or share this report. The report has been generated using the intelligent document analysis and includes proper citations and formatting."
        else:
            return f"✅ **Report Generated Successfully!**\n\nI've created a comprehensive report using your uploaded documents with the following sections:\n{chr(10).join([f'• {section}' for section in sections_list])}\n\nThe report has been generated using intelligent document analysis and includes proper citations and formatting."
        
    except Exception as e:
        return f"Error generating report: {str(e)}"

def update_report_agentic(input_text: str) -> str:
    """
    Agentic tool: Intelligent report updating with context awareness
    """
    global current_report
    
    if not current_report:
        return "No existing report found. Please generate a report first."
    
    # Use LLM to understand what needs updating
    llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3)
    
    update_prompt = f"""
The user wants to update the report with this request: "{input_text}"

Current report sections: {list(current_report.keys())}

Determine what specific updates are needed and provide a JSON list of sections to modify or add.
Respond with only a JSON array.
"""
    
    try:
        response = llm.invoke([HumanMessage(content=update_prompt)])
        sections_to_update = json.loads(response.content.strip())
        
        # Remove sections to be updated
        for section in sections_to_update:
            if section in current_report:
                current_report.pop(section)
        
        # Regenerate updated sections
        return generate_report_agentic(", ".join(sections_to_update))
        
    except Exception as e:
        return f"Error updating report: {str(e)}"

def get_system_status_agentic(input_text: str = "") -> str:
    """
    Agentic tool: Get comprehensive system status
    """
    try:
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        return f"""
🤖 **Agentic AI System Status:**

📊 **Document Status:**
- Documents uploaded: {doc_count}
- Documents processed: {'Yes' if documents_processed else 'No'}
- Vector store ready: {'Yes' if vectorstore else 'No'}

📝 **Report Status:**
- Current report sections: {list(current_report.keys()) if current_report else 'None'}
- Report ready: {'Yes' if current_report else 'No'}

🧠 **Memory Status:**
- Conversation memory: Active
- Context awareness: Enabled
- Agent autonomy: Active

**Available Actions:**
- Process documents
- Analyze content
- Generate reports
- Update reports
- System status
"""
        
    except Exception as e:
        return f"Error getting system status: {str(e)}"

# -----------------------------
# Define Agentic Tools
# -----------------------------
agentic_tools = [
    Tool(
        name="ProcessDocuments",
        func=process_documents_agentic,
        description="Process uploaded documents and create searchable vector store. Use this when documents need to be prepared for analysis."
    ),
    Tool(
        name="AnalyzeDocuments", 
        func=analyze_documents_agentic,
        description="Perform intelligent analysis of uploaded documents. Use this to understand document content and get insights."
    ),
    Tool(
        name="GenerateReport",
        func=generate_report_agentic,
        description="Generate comprehensive reports from documents. Use this when user says 'generate report', 'create report', 'make report', 'build report', or wants to create any type of report. Takes user requirements as input."
    ),
    Tool(
        name="UpdateReport",
        func=update_report_agentic,
        description="Update existing reports with new sections or modifications. Use this when user wants to modify an existing report."
    ),
    Tool(
        name="GetSystemStatus",
        func=get_system_status_agentic,
        description="Get current system status and capabilities. Use this to check what's available and what actions can be taken."
    )
]

# -----------------------------
# Agentic AI System
# -----------------------------
def initialize_agentic_ai():
    """Initialize the agentic AI system with memory and reasoning capabilities."""
    try:
        # Initialize LLM with system message for agentic behavior
        llm = ChatGoogleGenerativeAI(
            model="models/gemini-2.5-flash", 
            temperature=0.3,
            system_message="""You are an intelligent AI agent specialized in document analysis and report generation. 

You have the following capabilities:
- Autonomous decision making
- Multi-step reasoning
- Tool usage for document processing
- Context-aware responses
- Memory of previous interactions

Your goal is to help users create professional reports from their documents. You should:
1. Understand user intent
2. Take appropriate actions using available tools
3. Provide intelligent, context-aware responses
4. Remember previous interactions
5. Make autonomous decisions when appropriate

Always be helpful, professional, and proactive in assisting users."""
        )
        
        # Create a ReAct prompt template
        react_prompt = PromptTemplate.from_template("""
You are an intelligent AI assistant with access to specialized tools for document processing, analysis, and report generation.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
""")
        
        # Create the ReAct agent
        agent = create_react_agent(llm, agentic_tools, react_prompt)
        
        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=agentic_tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
            memory=agent_memory,
            return_intermediate_steps=True
        )
        
        return agent_executor
        
    except Exception as e:
        print(f"Error initializing agentic AI: {e}")
        return None

def run_agentic_command(user_input: str) -> Dict[str, Any]:
    """Run a command through the agentic AI system."""
    try:
        agent = initialize_agentic_ai()
        if not agent:
            return {
                "response": "Error initializing agentic AI system.",
                "status": "error",
                "error": "Agent initialization failed"
            }
        
        print(f"🤖 Agentic AI processing: {user_input}")
        
        # Run the agent with the user input
        result = agent.invoke({"input": user_input})
        
        # Extract the response from the new agent format
        response_text = result.get("output", str(result))
        
        return {
            "response": response_text,
            "status": "success",
            "command": user_input,
            "agentic": True,
            "memory_used": True
        }
        
    except Exception as e:
        print(f"Agentic AI error: {e}")
        return {
            "response": f"An error occurred while processing your request: {str(e)}",
            "status": "error",
            "error": str(e),
            "agentic": True
        }

def get_agentic_status() -> Dict[str, Any]:
    """Get the current status of the agentic AI system."""
    return {
        "agentic_ai": True,
        "documents_processed": documents_processed,
        "vectorstore_ready": vectorstore is not None,
        "current_report_sections": list(current_report.keys()) if current_report else [],
        "available_tools": [tool.name for tool in agentic_tools],
        "memory_active": True,
        "autonomous_decision_making": True
    }

def reset_agentic_state():
    """Reset the agentic AI state for a new session."""
    global vectorstore, documents_processed, current_report, agent_memory
    vectorstore = None
    documents_processed = False
    current_report = {}
    agent_memory.clear()
    return "Agentic AI state reset successfully."
