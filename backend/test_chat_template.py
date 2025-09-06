import requests
import json

# Test script for the conversational template generation API

BASE_URL = "http://localhost:8000"  # Adjust if your server uses a different port

def test_chat_template_generation():
    """Test the conversational template generation API"""
    
    # Initialize chat history
    chat_history = []
    
    # First message - Initial query
    message = "I need to create a report about renewable energy technologies"
    
    print(f"USER: {message}")
    response = requests.post(
        f"{BASE_URL}/templates/chat",
        json={"message": message}
    )
    
    if response.status_code == 200:
        result = response.json()
        assistant_response = result.get("response", "")
        chat_history = result.get("chat_history", [])
        
        print(f"ASSISTANT: {assistant_response}")
        print("-" * 50)
        
        # Second message - Follow-up question
        message = "I want to focus particularly on solar and wind energy. Can you adjust the template?"
        print(f"USER: {message}")
        
        response = requests.post(
            f"{BASE_URL}/templates/chat",
            json={
                "message": message,
                "chat_history": chat_history
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get("response", "")
            chat_history = result.get("chat_history", [])
            
            print(f"ASSISTANT: {assistant_response}")
            print("-" * 50)
            
            # Third message - Generate final template
            message = "That sounds good. Can you now generate a complete template for my report?"
            print(f"USER: {message}")
            
            response = requests.post(
                f"{BASE_URL}/templates/suggest",
                json={
                    "query": "renewable energy with focus on solar and wind technologies",
                    "chat_history": chat_history
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                template = result.get("template", {})
                conversation = result.get("conversation", "")
                
                print(f"CONVERSATION RESPONSE:\n{conversation}")
                print("\nGENERATED TEMPLATE:")
                print(json.dumps(template, indent=2))
            else:
                print(f"Error generating template: {response.status_code}")
                print(response.text)
        else:
            print(f"Error in chat: {response.status_code}")
            print(response.text)
    else:
        print(f"Error starting chat: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("Testing Conversational Template Generation")
    print("=" * 50)
    test_chat_template_generation()
