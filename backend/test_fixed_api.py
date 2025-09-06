import requests
import json

# Test script to validate the fixed API functionality

BASE_URL = "http://localhost:8000"  # Adjust if your server uses a different port

def test_generate_report():
    """Test the generate report endpoint which was having the 500 error"""
    print("\n==== Testing Generate Report API ====")
    
    # First get available templates
    response = requests.get(f"{BASE_URL}/templates")
    if response.status_code == 200:
        templates = response.json()
        if templates and len(templates) > 0:
            template_id = templates[0]["id"]
            print(f"Found template with ID: {template_id}")
            
            # Test generate with template
            data = {
                "template_id": template_id,
                "query": "Benefits of renewable energy"
            }
            
            print(f"\nGenerating report with template_id: {template_id}")
            response = requests.post(f"{BASE_URL}/generate", json=data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("Success! Report generated with ID:", result.get("report_id", "unknown"))
            else:
                print("Error:", response.text)
        else:
            print("No templates found. Creating a test template...")
            
            # Create a test template
            template_data = {
                "template": ["Executive Summary", "Key Findings", "Analysis", "Recommendations"]
            }
            
            response = requests.post(f"{BASE_URL}/templates", json=template_data)
            if response.status_code == 200:
                template = response.json()["template"]
                template_id = template["id"]
                print(f"Created template with ID: {template_id}")
                
                # Test generate with template
                data = {
                    "template_id": template_id,
                    "query": "Benefits of renewable energy"
                }
                
                print(f"\nGenerating report with template_id: {template_id}")
                response = requests.post(f"{BASE_URL}/generate", json=data)
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    print("Success! Report generated with ID:", result.get("report_id", "unknown"))
                else:
                    print("Error:", response.text)
            else:
                print("Error creating template:", response.text)
    else:
        print(f"Error listing templates: {response.status_code} - {response.text}")
        
        # Try generating without a template
        data = {
            "query": "Benefits of renewable energy",
            "sections": ["Executive Summary", "Key Findings", "Recommendations"]
        }
        
        print("\nGenerating report without template (using sections directly)")
        response = requests.post(f"{BASE_URL}/generate", json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("Success! Report generated with ID:", result.get("report_id", "unknown"))
        else:
            print("Error:", response.text)

def test_template_apis():
    """Test the template API endpoints"""
    print("\n==== Testing Template APIs ====")
    
    # Test listing templates
    print("\nListing templates:")
    response = requests.get(f"{BASE_URL}/templates")
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        templates = response.json()
        print(f"Found {len(templates)} templates")
    else:
        print("Error:", response.text)
    
    # Test template suggestion
    print("\nSuggesting a template:")
    data = {
        "query": "Impact of AI on healthcare"
    }
    
    response = requests.post(f"{BASE_URL}/templates/suggest", json=data)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Template suggestion successful with ID: {result.get('template', {}).get('id', 'unknown')}")
    else:
        print("Error:", response.text)

if __name__ == "__main__":
    print("Testing Fixed API Endpoints")
    print("=" * 50)
    
    # Test template APIs
    test_template_apis()
    
    # Test generate report (which had the 500 error)
    test_generate_report()
