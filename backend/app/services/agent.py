#!/usr/bin/env python
"""
AI Agent-based document processing and report generation
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from app.services.generator import collection, diagnose_collection, get_document_samples_for_analysis

# -----------------------------
# Configuration
# -----------------------------
os.environ["GOOGLE_API_KEY"] = "AIzaSyDGA_bxmpmbC7NkEaY97GQoZDUtS1N1nLA"

# Global state for agent
vectorstore = None
documents_processed = False
current_report = {}

# -----------------------------
# Tool: Process Documents
# -----------------------------
def process_documents_tool(_ignored_input=None) -> str:
    """Process all uploaded documents and build vector store."""
    global vectorstore, documents_processed
    
    try:
        # Get document status
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        if doc_count == 0:
            return "⚠ No documents found. Please upload documents first."
        
        print(f"\n🔧 Processing {doc_count} documents and building vector store... Please wait...")
        
        # Get all documents from collection
        all_docs = collection.get()
        if not all_docs or not all_docs.get('documents'):
            return "⚠ No document content found in collection."
        
        # Prepare documents for vector store
        documents = []
        for i, doc_content in enumerate(all_docs['documents']):
            if doc_content and len(doc_content.strip()) > 50:
                # Add metadata
                metadata = all_docs['metadatas'][i] if all_docs.get('metadatas') and i < len(all_docs['metadatas']) else {}
                source_id = metadata.get('source_id', f'doc_{i}')
                page = metadata.get('page', 1)
                
                # Split long documents
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
                chunks = text_splitter.split_text(doc_content)
                
                for chunk in chunks:
                    documents.append(f"[Source: {source_id}, Page: {page}] {chunk}")
        
        if not documents:
            return "⚠ No valid document content found to process."
        
        # Create embeddings and vector store
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        vectorstore = FAISS.from_texts(documents, embeddings)
        
        documents_processed = True
        return f"✅ Successfully processed {len(documents)} document chunks from {doc_count} uploaded documents."
        
    except Exception as e:
        return f"⚠ Error processing documents: {str(e)}"

# -----------------------------
# Tool: Extract Sections
# -----------------------------
def extract_sections_tool(user_input: str) -> List[str]:
    """Extract report section names from user input."""
    try:
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0)
        prompt = f"""
You are an intelligent assistant. Extract and return only the report section names from this user input:
'{user_input}'

Common report sections include: Executive Summary, Introduction, Methodology, Key Findings, Analysis, Recommendations, Conclusion, etc.

Respond as a simple comma-separated list of section names.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        cleaned = response.content.strip().replace("\n", " ").replace("'", "").replace('"', "")
        sections = [sec.strip() for sec in cleaned.split(",") if sec.strip()]
        return sections
    except Exception as e:
        print(f"Error extracting sections: {e}")
        return []

# -----------------------------
# Tool: Generate Report
# -----------------------------
def generate_report_tool(user_input: str) -> str:
    """Generate a comprehensive report from uploaded documents."""
    global vectorstore, documents_processed, current_report
    
    try:
        # Check if documents are processed
        if not documents_processed:
            print("💡 I notice we haven't processed the documents yet. I'll process them now for you.")
            result = process_documents_tool()
            if "⚠" in result:
                return result
            print("✅ Documents processed successfully. Let's generate your report.")
        
        # Extract sections from user input
        sections_list = extract_sections_tool(user_input)
        if not sections_list:
            # Default sections if none specified
            sections_list = ["Executive Summary", "Key Findings", "Analysis", "Recommendations"]
        
        # Set up retriever and LLM
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3)
        
        # Generate each section
        current_report = {}
        for section in sections_list:
            print(f"📝 Generating section: {section}")
            
            # Retrieve relevant documents
            retrieved_docs = retriever.get_relevant_documents(section)
            combined_content = "\n".join([doc.page_content for doc in retrieved_docs])
            
            if not combined_content.strip():
                combined_content = "No specific content found for this section."
            
            # Generate section content
            prompt = f"""
You are a professional report writer. Write a detailed, professional section titled exactly as '{section}'.

Use the following content extracted from the uploaded documents as evidence:
{combined_content}

Requirements:
- Write in a professional, analytical tone
- Include specific details and insights from the source material
- Reference sources when possible (e.g., "According to the document...")
- Make it comprehensive and well-structured
- Length: 200-400 words per section
"""
            response = llm.invoke([HumanMessage(content=prompt)])
            current_report[section] = response.content
        
        # Format the complete report
        report_output = f"# AI-Generated Report\n\n"
        report_output += f"**Generated on:** {os.popen('date').read().strip()}\n"
        report_output += f"**Sections:** {len(sections_list)}\n\n"
        
        for section, content in current_report.items():
            report_output += f"## {section}\n\n{content}\n\n"
        
        # Add engagement message
        report_output += "\n---\n\n💡 **Report Generated Successfully!**\n"
        report_output += "Would you like to:\n"
        report_output += "- Add more sections?\n"
        report_output += "- Update existing sections?\n"
        report_output += "- Generate a different type of report?\n"
        
        return report_output
        
    except Exception as e:
        return f"⚠ Error generating report: {str(e)}"

# -----------------------------
# Tool: Update Report
# -----------------------------
def update_report_tool(user_input: str) -> str:
    """Update existing report sections."""
    global current_report
    
    if not current_report:
        return "⚠ We don't have a report yet. Let's generate one first using the 'GenerateReport' tool."
    
    sections_list = extract_sections_tool(user_input)
    if not sections_list:
        return "⚠ I couldn't identify the sections to update. Could you clarify them?"
    
    # Remove sections to be updated
    for section in sections_list:
        if section in current_report:
            print(f"💡 Updating section: '{section}' as requested.")
            current_report.pop(section)
    
    # Regenerate the specified sections
    return generate_report_tool(", ".join(sections_list))

# -----------------------------
# Tool: Document Summary
# -----------------------------
def document_summary_tool(_ignored_input=None) -> str:
    """Provide a comprehensive summary of uploaded documents."""
    global vectorstore, documents_processed
    
    try:
        # Check if documents are processed
        if not documents_processed:
            result = process_documents_tool()
            if "⚠" in result:
                return result
        
        # Get document status
        status = diagnose_collection()
        doc_count = status.get("document_count", 0)
        
        # Get document samples
        samples_data = get_document_samples_for_analysis()
        samples = samples_data.get("samples", [])
        
        # Create summary using LLM
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3)
        
        # Prepare content for analysis
        content_for_analysis = ""
        for i, sample in enumerate(samples[:5], 1):
            content = sample.get('content_preview', str(sample))
            content_for_analysis += f"Document {i}:\n{content}\n\n"
        
        prompt = f"""
You are an expert document analyst. I have {doc_count} uploaded documents. Please provide a comprehensive summary including:

1. **Document Overview** - What types of documents these are
2. **Key Topics** - Main subjects and themes covered
3. **Content Quality** - Assessment of information quality
4. **Key Insights** - Important findings or patterns
5. **Report Recommendations** - What type of report would best suit this content

Document Content Samples:
{content_for_analysis}

Provide a detailed, professional analysis.
"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        return f"⚠ Error generating document summary: {str(e)}"

# -----------------------------
# Define Tools
# -----------------------------
tools = [
    Tool(
        name="ProcessDocuments", 
        func=process_documents_tool, 
        description="Process all uploaded documents and build a searchable vector store."
    ),
    Tool(
        name="GenerateReport", 
        func=generate_report_tool, 
        description="Generate a comprehensive report from uploaded documents. Specify sections or use defaults."
    ),
    Tool(
        name="UpdateReport", 
        func=update_report_tool, 
        description="Update existing report sections or add new ones."
    ),
    Tool(
        name="DocumentSummary", 
        func=document_summary_tool, 
        description="Provide a comprehensive summary and analysis of uploaded documents."
    )
]

# -----------------------------
# Initialize Agent
# -----------------------------
def initialize_agent_system():
    """Initialize the LangChain agent system."""
    try:
        llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", temperature=0.3)
        
        agent = initialize_agent(
            tools=tools,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        return agent
    except Exception as e:
        print(f"Error initializing agent: {e}")
        return None

# -----------------------------
# Agent Interface
# -----------------------------
def run_agent_command(user_input: str) -> Dict[str, Any]:
    """Run a command through the agent system."""
    try:
        agent = initialize_agent_system()
        if not agent:
            return {
                "response": "⚠ Error initializing agent system.",
                "status": "error",
                "error": "Agent initialization failed"
            }
        
        print(f"🤖 Processing command: {user_input}")
        result = agent.run(user_input)
        
        return {
            "response": result,
            "status": "success",
            "command": user_input
        }
        
    except Exception as e:
        print(f"Agent error: {e}")
        return {
            "response": f"⚠ An error occurred while processing your request: {str(e)}",
            "status": "error",
            "error": str(e)
        }

# -----------------------------
# Helper Functions
# -----------------------------
def get_agent_status() -> Dict[str, Any]:
    """Get the current status of the agent system."""
    return {
        "documents_processed": documents_processed,
        "vectorstore_ready": vectorstore is not None,
        "current_report_sections": list(current_report.keys()) if current_report else [],
        "available_tools": [tool.name for tool in tools]
    }

def reset_agent_state():
    """Reset the agent state for a new session."""
    global vectorstore, documents_processed, current_report
    vectorstore = None
    documents_processed = False
    current_report = {}
    return "Agent state reset successfully."
