#!/usr/bin/env python
"""
Test script to verify the upload and report generation flow works correctly
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_upload_and_generate():
    """Test the complete flow: upload document -> generate report"""
    
    print("=== Testing Upload and Report Generation Flow ===\n")
    
    # Step 1: Check initial collection status
    print("1. Checking initial collection status...")
    try:
        response = requests.get(f"{BASE_URL}/documents/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   Collection status: {status}")
        else:
            print(f"   Error checking status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Step 2: Reset collection to start fresh
    print("\n2. Resetting collection to start fresh...")
    try:
        response = requests.delete(f"{BASE_URL}/documents/reset")
        if response.status_code == 200:
            result = response.json()
            print(f"   Reset result: {result}")
        else:
            print(f"   Error resetting: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Step 3: Create a test document
    print("\n3. Creating test document...")
    test_content = """
    This is a test document about artificial intelligence in healthcare.
    
    Executive Summary:
    AI is transforming healthcare by improving diagnostic accuracy, streamlining operations, and enhancing patient care. Recent studies show that AI-powered diagnostic tools can achieve 95% accuracy in detecting certain conditions.
    
    Key Findings:
    - AI reduces diagnostic time by 40% on average
    - Patient satisfaction increased by 25% with AI-assisted care
    - Cost savings of $2.3 billion annually in the healthcare sector
    
    Recommendations:
    1. Invest in AI training for medical staff
    2. Implement AI diagnostic tools in primary care
    3. Establish data governance frameworks for AI systems
    """
    
    # Save test content to a file
    with open("test_document.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # Step 4: Upload the test document
    print("\n4. Uploading test document...")
    try:
        with open("test_document.txt", "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            response = requests.post(f"{BASE_URL}/documents/upload", files=files)
        
        if response.status_code == 200:
            upload_result = response.json()
            print(f"   Upload successful: {upload_result}")
            source_id = upload_result.get("source_id")
        else:
            print(f"   Upload failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   Error uploading: {e}")
        return
    
    # Step 5: Check collection status after upload
    print("\n5. Checking collection status after upload...")
    try:
        response = requests.get(f"{BASE_URL}/documents/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   Collection status: {status}")
        else:
            print(f"   Error checking status: {response.status_code}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Step 6: Generate a report using the uploaded content
    print("\n6. Generating report from uploaded content...")
    try:
        report_data = {
            "sections": ["Executive Summary", "Key Findings", "Recommendations"],
            "query": "artificial intelligence healthcare benefits challenges",
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/reports/generate",
            headers={"Content-Type": "application/json"},
            data=json.dumps(report_data)
        )
        
        if response.status_code == 200:
            generate_result = response.json()
            print(f"   Report generation successful: {generate_result}")
            report_id = generate_result.get("report_id")
        else:
            print(f"   Report generation failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   Error generating report: {e}")
        return
    
    # Step 7: Preview the generated report
    print("\n7. Previewing generated report...")
    try:
        response = requests.get(f"{BASE_URL}/reports/preview/{report_id}")
        if response.status_code == 200:
            preview_result = response.json()
            print(f"   Preview successful!")
            
            # Display the report content
            if "preview" in preview_result:
                report = preview_result["preview"]
                print(f"\n   Report ID: {report.get('report_id', 'N/A')}")
                print(f"   Sections: {len(report.get('sections', []))}")
                
                for section in report.get("sections", []):
                    print(f"\n   === {section.get('title', 'Untitled')} ===")
                    for content_item in section.get("content", []):
                        text = content_item.get("text", "")
                        citations = content_item.get("citations", [])
                        print(f"   Content: {text[:200]}...")
                        print(f"   Citations: {len(citations)}")
                        for citation in citations[:2]:  # Show first 2 citations
                            print(f"     - {citation.get('source_id', 'N/A')} (Page {citation.get('page', 'N/A')})")
        else:
            print(f"   Preview failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error previewing report: {e}")
    
    # Step 8: Test export functionality
    print("\n8. Testing export functionality...")
    try:
        response = requests.get(f"{BASE_URL}/reports/export?report_id={report_id}&format=pdf")
        if response.status_code == 200:
            export_result = response.json()
            print(f"   Export successful: {export_result.get('status', 'N/A')}")
        else:
            print(f"   Export failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   Error exporting: {e}")
    
    # Cleanup
    import os
    if os.path.exists("test_document.txt"):
        os.remove("test_document.txt")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_upload_and_generate()
