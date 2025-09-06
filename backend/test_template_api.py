import requests
import json

# This is a test script to validate the dynamic template generation functionality

BASE_URL = "http://localhost:8000"  # Adjust if your server uses a different port

def test_suggest_template():
    """Test the template suggestion endpoint"""
    # Test case 1: Basic template suggestion
    data = {
        "query": "Benefits of renewable energy sources in the power grid",
    }
    
    response = requests.post(f"{BASE_URL}/templates/suggest", json=data)
    print("Basic Template Suggestion Response:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("\n" + "-"*50 + "\n")
    
    # Test case 2: Template suggestion with source context
    data = {
        "query": "AI applications in healthcare",
        "source_id": "healthcare_docs",
        "context": {
            "sources": [
                {"source_id": "healthcare_docs", "count": 3},
                {"source_id": "tech_papers", "count": 5}
            ]
        }
    }
    
    response = requests.post(f"{BASE_URL}/templates/suggest", json=data)
    print("Template Suggestion with Source Context Response:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("\n" + "-"*50 + "\n")
    
    # Test case 3: List available templates
    response = requests.get(f"{BASE_URL}/templates/list")
    print("List Templates Response:")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

def test_generate_with_template():
    """Test generating a report with a suggested template"""
    # First, suggest a template
    suggest_response = requests.post(
        f"{BASE_URL}/templates/suggest", 
        json={"query": "Impact of climate change on agriculture"}
    )
    
    if suggest_response.status_code == 200:
        template_data = suggest_response.json()
        template_id = template_data.get("template", {}).get("id")
        
        if template_id:
            # Generate report using the template
            generate_data = {
                "query": "Impact of climate change on agriculture",
                "template_id": template_id
            }
            
            response = requests.post(f"{BASE_URL}/generate", json=generate_data)
            print("Generate Report with Template Response:")
            print(f"Status Code: {response.status_code}")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Failed to get template_id from suggestion")
    else:
        print(f"Template suggestion failed with status code: {suggest_response.status_code}")

if __name__ == "__main__":
    print("Testing Dynamic Template Generation API")
    print("=" * 50)
    test_suggest_template()
    print("\nTesting Report Generation with Template")
    print("=" * 50)
    test_generate_with_template()
