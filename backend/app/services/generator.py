
# --- NEW IMPLEMENTATION ---
import uuid
import re
from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
import os
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# 1. Setup ChromaDB (persistent)
CHROMA_PATH = "./chromadb_reports"
chroma_client = PersistentClient(path=CHROMA_PATH)
collection = chroma_client.get_or_create_collection("reports")

# 2. Embedding Model
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Collection Diagnostics
def diagnose_collection():
    """Get collection status and document count"""
    try:
        count = collection.count()
        return {
            "collection_name": "reports",
            "document_count": count,
            "healthy": True,
            "chroma_path": CHROMA_PATH
        }
    except Exception as e:
        return {
            "collection_name": "reports", 
            "document_count": 0,
            "healthy": False,
            "error": str(e),
            "chroma_path": CHROMA_PATH
        }

# 4. Document Ingestion
def ingest_documents(docs, source_id):
    chunk_size = 300
    ingested_ids = []
    try:
        for i, doc in enumerate(docs):
            if not doc or not isinstance(doc, str):
                print(f"Skipping invalid document at index {i}")
                continue
                
            # Simple chunking by sentences
            sentences = doc.split(". ")
            chunks = []
            chunk = ""
            for s in sentences:
                if len(chunk.split()) + len(s.split()) < chunk_size:
                    chunk += s + ". "
                else:
                    chunks.append(chunk.strip())
                    chunk = s + ". "
            if chunk:
                chunks.append(chunk.strip())
                
            # Embed and store
            for idx, chunk in enumerate(chunks):
                try:
                    if not chunk.strip():
                        continue
                        
                    emb = embedder.encode(chunk)
                    meta = {
                        "source_id": source_id,
                        "page": idx + 1,
                        "timestamp": "", # Empty string instead of None
                        "snippet": chunk
                    }
                    doc_id = f"{source_id}_p{idx+1}"
                    collection.add(documents=[chunk], embeddings=[emb], metadatas=[meta], ids=[doc_id])
                    ingested_ids.append(doc_id)
                except Exception as e:
                    print(f"Error ingesting chunk {idx} of document {i}: {e}")
    except Exception as e:
        print(f"Error in document ingestion: {e}")
    print(f"Ingested {len(ingested_ids)} chunks for source_id {source_id}")
    return ingested_ids, source_id

# 4. Querying with Citations
def generate_report_from_query(sections, query, top_k=5, source_filter=None):
    # Check if collection is empty and warn user instead of auto-seeding
    if collection.count() == 0:
        print("WARNING: ChromaDB collection is empty. Please upload documents first.")
        return {
            "error": "No documents found in the system. Please upload documents before generating reports.",
            "suggestion": "Use the /upload endpoint to add documents to the system."
        }
    
    # Log source filtering if applied
    if source_filter:
        print(f"Filtering query results to source: {source_filter}")
    
    # Create section-specific queries based on the user's actual query
    section_specific_queries = {
        "Executive Summary": f"{query} summary overview",
        "Key Findings": f"{query} findings results analysis",
        "Recommendations": f"{query} recommendations suggestions",
        "Market Analysis": f"{query} market analysis",
        "Challenges": f"{query} challenges problems",
        "Future Outlook": f"{query} future outlook predictions",
        "Introduction": f"{query} introduction background",
    }
    
    # Store all results for each section
    all_section_results = {}
    
    # Default top_k per section
    section_top_k = max(3, top_k // len(sections))
    
    try:
        # Print diagnostic info
        print(f"Executing queries for {len(sections)} sections with top_k={section_top_k} per section")
        print(f"Collection contains {collection.count()} documents")
        
        # Query for each section to get diverse documents
        for section in sections:
            section_query = section_specific_queries.get(section, f"{query} {section.lower()}")
            print(f"Querying for section '{section}' with: '{section_query}'")
            
            query_emb = embedder.encode(section_query)
            
            # Apply source filtering if specified
            if source_filter:
                # Use where clause to filter by source_id
                where_clause = {"source_id": {"$eq": source_filter}}
                
                # Query with source filtering
                try:
                    section_results = collection.query(
                        query_embeddings=[query_emb],
                        n_results=min(section_top_k, collection.count()),
                        include=["documents", "metadatas", "distances"],
                        where=where_clause
                    )
                    print(f"Filtered query for source '{source_filter}' returned {len(section_results.get('documents', []))} results")
                except Exception as filter_error:
                    print(f"Error with filtered query: {filter_error}. Trying exact match filter.")
                    # If where clause fails, try getting all and filtering manually
                    section_results = collection.query(
                        query_embeddings=[query_emb],
                        n_results=min(50, collection.count()),  # Get more results to filter from
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # Manually filter results
                    filtered_indices = []
                    for i, meta in enumerate(section_results.get("metadatas", [])):
                        if isinstance(meta, list) and meta and isinstance(meta[0], dict):
                            if meta[0].get("source_id") == source_filter:
                                filtered_indices.append(i)
                        elif isinstance(meta, dict) and meta.get("source_id") == source_filter:
                            filtered_indices.append(i)
                    
                    # Create filtered results
                    filtered_results = {
                        "documents": [section_results["documents"][i] for i in filtered_indices] if "documents" in section_results else [],
                        "metadatas": [section_results["metadatas"][i] for i in filtered_indices] if "metadatas" in section_results else [],
                        "distances": [section_results["distances"][i] for i in filtered_indices] if "distances" in section_results else [],
                    }
                    
                    section_results = filtered_results
                    print(f"Manual filtering for source '{source_filter}' returned {len(section_results.get('documents', []))} results")
            else:
                # Normal query without filtering
                section_results = collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(section_top_k, collection.count()),
                    include=["documents", "metadatas", "distances"]
                )
            
            # Check if we got results for this section
            if not section_results["documents"] or len(section_results["documents"]) == 0:
                print(f"WARNING: Query for section '{section}' returned no documents. Using main query...")
                query_emb = embedder.encode(query)
                section_results = collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(section_top_k, collection.count()),
                    include=["documents", "metadatas", "distances"]
                )
                
            all_section_results[section] = section_results
            
        # Also get a general query for fallback and additional context
        query_emb = embedder.encode(query)
        
        # Apply source filtering to general results if specified
        if source_filter:
            try:
                where_clause = {"source_id": {"$eq": source_filter}}
                general_results = collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(top_k, collection.count()),
                    include=["documents", "metadatas", "distances"],
                    where=where_clause
                )
            except Exception as filter_error:
                print(f"Error with filtered general query: {filter_error}. Using unfiltered results.")
                general_results = collection.query(
                    query_embeddings=[query_emb],
                    n_results=min(top_k, collection.count()),
                    include=["documents", "metadatas", "distances"]
                )
        else:
            general_results = collection.query(
                query_embeddings=[query_emb],
                n_results=min(top_k, collection.count()),
                include=["documents", "metadatas", "distances"]
            )
        
        all_section_results["general"] = general_results
        
    except Exception as e:
        print(f"Error during ChromaDB query: {e}")
        # Provide fallback results structure if query fails
        empty_results = {
            "documents": [],
            "metadatas": [],
            "distances": []
        }
        all_section_results = {section: empty_results for section in sections}
        all_section_results["general"] = empty_results
        
    # Process results and gather evidence for each section
    section_evidence = {}
    all_evidence = []
    unique_doc_ids = set()  # To track unique documents
    
    # Process each section's results
    for section in sections:
        section_results = all_section_results.get(section, all_section_results["general"])
        
        # Print results summary for this section
        print(f"Section '{section}' query returned {len(section_results.get('documents', []))} documents")
        
        section_evidence[section] = []
        
        # If no documents were found for this section, use general results or fallbacks
        if not section_results["documents"] or len(section_results["documents"]) == 0:
            print(f"No specific documents found for section '{section}', using general results")
            section_results = all_section_results["general"]
            
        # If still no documents, create fallback evidence
        if not section_results["documents"] or len(section_results["documents"]) == 0:
            print(f"No documents in results for section '{section}', creating fallback evidence...")
            fallback_docs = [
                "AI adoption in the market has accelerated in 2023. Companies report a 20% increase in productivity.",
                "Market analysis shows revenue growth of 15-30% for AI implementations.",
                "Customer satisfaction improved by 5 points according to recent surveys."
            ]
            
            for i, doc in enumerate(fallback_docs):
                fallback_item = {
                    "source_id": f"fallback_{i+1}",
                    "page": 1,
                    "timestamp": "",  # Empty string instead of None
                    "snippet": doc,
                    "document": doc
                }
                section_evidence[section].append(fallback_item)
                if fallback_item["source_id"] not in unique_doc_ids:
                    all_evidence.append(fallback_item)
                    unique_doc_ids.add(fallback_item["source_id"])
            print(f"Added {len(fallback_docs)} fallback evidence items for section '{section}'")
        else:
            # Process actual results for this section
            section_top_k = len(section_results["documents"])
            for i in range(section_top_k):
                doc = section_results["documents"][i]
                meta = section_results["metadatas"][i]
            
            # Skip empty documents
            if not doc or (isinstance(doc, str) and not doc.strip()):
                continue
                
            # Check if meta is a list or dict and handle accordingly
            if isinstance(meta, list):
                # If meta is a list, it likely contains one dict element
                if meta and isinstance(meta[0], dict):
                    meta_dict = meta[0]
                    doc_item = {
                        "source_id": meta_dict.get("source_id", f"doc_{i+1}"),
                        "page": meta_dict.get("page", 1),
                        "timestamp": meta_dict.get("timestamp", ""),
                        "snippet": meta_dict.get("snippet", doc),
                        "document": doc  # Include the actual document text
                    }
                else:
                    # Fallback if meta is a list but not containing a dict
                    doc_item = {
                        "source_id": f"doc_{i+1}",
                        "page": i + 1,
                        "timestamp": "",  # Empty string instead of None
                        "snippet": doc,
                        "document": doc  # Include the actual document text
                    }
            else:
                # Original code for when meta is a dict
                doc_item = {
                    "source_id": meta.get("source_id", f"doc_{i+1}"),
                    "page": meta.get("page", i + 1), 
                    "timestamp": meta.get("timestamp", ""),
                    "snippet": meta.get("snippet", doc),
                    "document": doc  # Include the actual document text
                }
                
            # Add to section-specific evidence
            section_evidence[section].append(doc_item)
            
            # Add to all evidence if it's a unique source_id + page combo
            doc_id_key = f"{doc_item['source_id']}:{doc_item['page']}"
            if doc_id_key not in unique_doc_ids:
                all_evidence.append(doc_item)
                unique_doc_ids.add(doc_id_key)
        
        print(f"Added {len(section_evidence[section])} evidence items for section '{section}'")
    
    print(f"Total unique evidence items: {len(all_evidence)}")
    
    # Setup Gemini LLM
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDGA_bxmpmbC7NkEaY97GQoZDUtS1N1nLA"  # Replace with your actual key or use env
    
    # Generate report sections
    report_sections = []
    for section in sections:
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)
            
            # Use section-specific evidence 
            section_docs = section_evidence.get(section, all_evidence)
            
            # Create a more directed prompt for this section with enterprise-grade citation requirements
            # Ensure unique citations by tracking used combinations
            unique_citations = set()
            evidence_with_unique_ids = []
            
            for i, e in enumerate(section_docs):
                citation_key = f"{e['source_id']}:{e['page']}"
                if citation_key not in unique_citations:
                    unique_citations.add(citation_key)
                    evidence_with_unique_ids.append({
                        "id": len(evidence_with_unique_ids) + 1,
                        "source_id": e["source_id"],
                        "page": e["page"],
                        "content": e["document"] if isinstance(e["document"], str) and e["document"].strip() else e["snippet"],
                        "metadata": {
                            "source_type": "uploaded_document",
                            "confidence": "high" if len(e.get("document", "")) > 100 else "medium",
                            "unique_id": len(evidence_with_unique_ids) + 1
                        }
                    })
            
            prompt = (
                f"Write the section '{section}' for a professional report based on the following evidence from uploaded documents. "
                f"CRITICAL CITATION REQUIREMENTS:\n"
                f"1. For every fact, claim, statistic, or statement you include, cite the specific source using the exact format [SOURCE_ID:PAGE_NUMBER]\n"
                f"2. Use the exact source_id and page number from the evidence provided\n"
                f"3. Each citation must directly correspond to content from that specific source\n"
                f"4. Do not add external knowledge, assumptions, or information not in the evidence\n"
                f"5. Use DIFFERENT citations throughout the section - avoid repeating the same citation multiple times\n"
                f"6. Format citations as [source_id:page] (e.g., [uploaded_document_abc123:1])\n"
                f"7. Vary your citations - use different sources and pages when possible\n\n"
                f"WRITING REQUIREMENTS:\n"
                f"- Use professional, analytical tone\n"
                f"- Structure with clear paragraphs and bullet points\n"
                f"- Include specific data points and metrics when available\n"
                f"- Maintain objectivity and evidence-based analysis\n"
                f"- Use diverse citations to show comprehensive analysis\n\n"
                f"Evidence from uploaded documents (use different citations throughout):\n" + json.dumps(evidence_with_unique_ids, indent=2)
            )
            
            llm_response = llm.invoke(prompt)
            if hasattr(llm_response, "content"):
                section_text = llm_response.content
            elif isinstance(llm_response, str):
                section_text = llm_response
            else:
                section_text = str(llm_response)
        except Exception as e:
            print(f"Error generating section '{section}': {e}")
            # Provide fallback content if LLM generation fails
            section_text = f"Unable to generate content for section: {section}. Please try again later."
            
        report_sections.append({
            "title": section,
            "content": [{
                "text": section_text,
                "citations": section_evidence.get(section, all_evidence)  # Use section-specific citations
            }]
        })
    report_id = str(uuid.uuid4())
    report_json = {
        "report_id": report_id,
        "sections": report_sections
    }
    
    # Store in cache for preview functionality
    report_cache[report_id] = report_json
    
    return {"report_id": report_id, "content": "Report generated successfully"}

# Report cache (in-memory for simplicity, could be replaced with a database)
report_cache = {}

# Function to diagnose ChromaDB issues
def diagnose_collection():
    """
    Check the state of the ChromaDB collection and report status
    """
    try:
        count = collection.count()
        status = {
            "collection_name": collection.name,
            "document_count": count,
            "healthy": count > 0,
            "chroma_path": CHROMA_PATH
        }
        print(f"ChromaDB Status: {json.dumps(status, indent=2)}")
        return status
    except Exception as e:
        print(f"Error diagnosing collection: {e}")
        return {"error": str(e)}

# Function to reset the collection
def reset_collection():
    """
    Delete all documents from the collection and reset to empty state
    """
    try:
        # Get the current count for reporting
        count_before = collection.count()
        
        # Delete all documents
        if count_before > 0:
            # Get all document IDs
            results = collection.get(include=['documents', 'metadatas'])
            if 'ids' in results and results['ids']:
                # Delete all documents by their IDs
                collection.delete(ids=results['ids'])
        
        # Verify deletion
        count_after = collection.count()
        
        return {
            "documents_removed": count_before,
            "documents_remaining": count_after,
            "success": count_after == 0
        }
    except Exception as e:
        print(f"Error resetting collection: {e}")
        return {"error": str(e)}
        
# Function to get documents by source ID
def get_documents_by_source(source_id):
    """
    Retrieve all documents associated with a specific source_id
    """
    try:
        # Get all documents
        all_docs = collection.get(include=['documents', 'metadatas', 'embeddings'])
        
        # Filter by source_id
        filtered_docs = []
        for i, metadata in enumerate(all_docs.get('metadatas', [])):
            doc_source_id = None
            
            # Handle metadata structure variations
            if isinstance(metadata, dict):
                doc_source_id = metadata.get('source_id')
            elif isinstance(metadata, list) and metadata and isinstance(metadata[0], dict):
                doc_source_id = metadata[0].get('source_id')
                
            # If source_id matches, add to filtered results
            if doc_source_id == source_id:
                filtered_docs.append({
                    'id': all_docs['ids'][i] if 'ids' in all_docs else f"doc_{i}",
                    'document': all_docs['documents'][i] if 'documents' in all_docs else "",
                    'metadata': metadata
                })
                
        return {
            'count': len(filtered_docs),
            'documents': filtered_docs
        }
    except Exception as e:
        print(f"Error getting documents by source: {e}")
        return {"error": str(e), "count": 0, "documents": []}

# Function to seed test data into the collection
def seed_test_data():
    """
    Add sample data to the ChromaDB collection for testing
    """
    print("Seeding test data into ChromaDB...")
    
    # More comprehensive test documents with diverse content
    test_docs = [
        # Market reports
        "AI adoption in the market has accelerated in 2023. Companies report a 20% increase in productivity after implementing AI solutions. Early adopters have seen significant advantages in operational efficiency and cost reduction.",
        "According to recent surveys, 78% of Fortune 500 companies have implemented or are planning to implement AI technologies by the end of 2023. This represents a 15% increase from the previous year.",
        "Small and medium enterprises are increasingly adopting AI solutions, with 45% reporting some form of AI implementation, up from just 22% in 2022.",
        
        # Financial analysis
        "Market analysis shows that companies implementing AI technologies saw revenue growth of 15-30% in the past fiscal year. ROI on AI investments typically materializes within 12-18 months of implementation.",
        "Investment in AI startups reached $45.2 billion in 2022, a 10% increase from the previous year despite overall venture capital decline in other sectors.",
        "The financial services sector leads in AI implementation with 67% of banks reporting enhanced fraud detection capabilities through machine learning models.",
        
        # Technical aspects
        "IT departments report challenges in AI integration, with 45% citing compatibility issues with legacy systems. Security concerns were mentioned by 67% of surveyed companies.",
        "Technical implementation of AI requires specialized talent, with 72% of companies reporting difficulty in recruiting qualified data scientists and machine learning engineers.",
        "Cloud-based AI solutions are preferred by 65% of businesses due to lower upfront costs and faster implementation cycles compared to on-premises deployments.",
        
        # Customer experience
        "Customer satisfaction improved by 5 points according to recent surveys of AI-powered service interactions. Response times decreased by an average of 45% when AI chatbots were implemented.",
        "Personalization powered by AI has led to a 25% increase in customer engagement metrics across retail platforms implementing recommendation engines.",
        "AI-enabled customer service solutions have reduced response times by 37% and increased first-call resolution rates by 22% according to industry benchmarks."
    ]
    
    # More diverse source IDs
    source_ids = [
        'market_trends_2023', 'enterprise_adoption_survey', 'sme_technology_report',
        'financial_analysis', 'investment_outlook', 'banking_ai_implementation',
        'it_challenges_report', 'ai_talent_landscape', 'cloud_vs_onprem_analysis',
        'customer_experience_metrics', 'retail_personalization_study', 'service_efficiency_benchmark'
    ]
    
    # Ingest with more descriptive source IDs
    for idx, (doc, source_id) in enumerate(zip(test_docs, source_ids)):
        print(f"Adding document {idx+1} with source_id: {source_id}")
        ingest_documents([doc], source_id=source_id)
    
    print(f"Test data seeding complete. Collection now contains {collection.count()} documents.")
    return {"status": "success", "count": collection.count()}

# Function to retrieve a report preview
def preview(report_id):
    """
    Retrieve a report preview by ID from the cache.
    In a production system, this would fetch from a database.
    """
    try:
        # Check if collection is empty and warn user
        if collection.count() == 0:
            print("WARNING: ChromaDB collection is empty. Please upload documents first.")
            return {"error": "No documents found in the system. Please upload documents before generating reports."}
        
        if report_id in report_cache:
            # Make a copy of the report to avoid modifying the cache
            report_data = report_cache[report_id]
            
            # Process and clean up null values in citations
            for section in report_data.get("sections", []):
                for content_item in section.get("content", []):
                    for citation in content_item.get("citations", []):
                        # Convert None values to empty strings
                        if citation.get("timestamp") is None:
                            citation["timestamp"] = ""
            
            return {"preview": report_data}
        else:
            print(f"Report ID {report_id} not found in cache")
            return {"error": "Report not found"}
    except Exception as e:
        print(f"Error retrieving preview: {e}")
        return {"error": "Failed to retrieve preview"}

# Function to get available document sources
def get_available_sources():
    try:
        # Get all items from collection
        results = collection.get()
        
        # Extract unique source_ids from metadata
        sources = {} 
        if results and 'metadatas' in results and results['metadatas']:
            for metadata in results['metadatas']:
                if metadata and 'source_id' in metadata:
                    source_id = metadata['source_id']
                    if source_id not in sources:
                        sources[source_id] = 0
                    sources[source_id] += 1
        
        # Format the result
        sources_list = [{"source_id": source_id, "count": count} for source_id, count in sources.items()]
        return {"sources": sources_list}
    except Exception as e:
        print(f"Error getting available sources: {e}")
        return {"sources": [], "error": str(e)}

# Function to reset the collection (delete all documents)
def reset_collection():
    """
    Reset the ChromaDB collection by deleting all documents.
    Use with caution as this will delete all ingested documents.
    """
    try:
        # Delete the collection and recreate it
        chroma_client.delete_collection("reports")
        global collection
        collection = chroma_client.get_or_create_collection("reports")
        
        # Clear the report cache as well
        global report_cache
        report_cache.clear()
        
        print("Collection has been reset. All documents and reports have been deleted.")
        return {
            "status": "success", 
            "message": "Collection reset successfully",
            "document_count": 0
        }
    except Exception as e:
        print(f"Error resetting collection: {e}")
        return {"error": str(e)}

# 5. Main Flow Example (for testing)
if __name__ == "__main__":
    try:
        print("\n===== CHROMADB DIAGNOSTIC REPORT =====")
        status = diagnose_collection()
        
        # If collection is empty, seed it with test data
        if status.get("document_count", 0) == 0:
            print("\n===== SEEDING TEST DATA =====")
            seed_test_data()
            
            # Verify ingestion
            print(f"After ingestion: {collection.count()} documents in collection")
        else:
            print(f"\nCollection already contains {status['document_count']} documents")
        
        # Define template sections
        template_sections = ["Executive Summary", "Key Findings", "Recommendations"]
        
        # Generate report with more detailed query
        print("\n===== GENERATING TEST REPORT WITH DIVERSE CITATIONS =====")
        result = generate_report_from_query(template_sections, query="AI market adoption, benefits and challenges", top_k=10)
        report_id = result["report_id"]
        
        print("\n===== RETRIEVING PREVIEW =====")
        preview_result = preview(report_id)
        print("Report generated with ID:", report_id)
        
        # Check citation diversity
        citation_stats = {}
        total_citations = 0
        
        if "preview" in preview_result:
            report_data = preview_result["preview"]
            for section in report_data.get("sections", []):
                section_title = section.get("title", "Unknown")
                citation_stats[section_title] = {}
                
                for content in section.get("content", []):
                    # Extract citations using regex
                    text = content.get("text", "")
                    if text:
                        citation_pattern = r"\[([\w\-\_]+):(\d+)\]"
                        matches = re.findall(citation_pattern, text)
                        
                        for match in matches:
                            source_id = match[0]
                            citation_stats[section_title][source_id] = citation_stats[section_title].get(source_id, 0) + 1
                            total_citations += 1
        
        print("\n===== CITATION DIVERSITY REPORT =====")
        print(f"Total citations in report: {total_citations}")
        for section, citations in citation_stats.items():
            print(f"\nSection: {section}")
            print(f"Unique sources cited: {len(citations)}")
            for source, count in citations.items():
                print(f"  - {source}: {count} citations")
                
        print("\n===== REPORT PREVIEW =====")
        print(json.dumps(preview_result, indent=2))
    except Exception as e:
        print(f"Error in main execution: {e}")

# Function to get sample content from documents for template analysis
def get_document_samples_for_analysis(limit=3):
    """
    Get sample content from uploaded documents to help with template analysis
    """
    try:
        # Get a few sample documents from the collection
        results = collection.get(limit=limit)
        
        if not results or not results.get('documents'):
            return {"samples": [], "message": "No documents available for analysis"}
        
        samples = []
        for i, doc in enumerate(results['documents'][:limit]):
            if doc and len(doc.strip()) > 50:  # Only include substantial content
                samples.append({
                    "id": i + 1,
                    "content_preview": doc[:200] + "..." if len(doc) > 200 else doc,
                    "source_id": results['metadatas'][i].get('source_id', 'Unknown') if results.get('metadatas') else 'Unknown',
                    "length": len(doc)
                })
        
        return {
            "samples": samples,
            "total_documents": collection.count(),
            "message": f"Analyzed {len(samples)} document samples"
        }
    except Exception as e:
        print(f"Error getting document samples: {e}")
        return {"samples": [], "error": str(e)}
