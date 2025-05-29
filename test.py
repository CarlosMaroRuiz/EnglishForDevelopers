# test_api.py - Script to test DeepSeek API connection
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

class DeepSeekClient:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com"):
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def chat_completions_create(self, model="deepseek-chat", messages=None, temperature=1.0, stream=False):
        """Create a chat completion using DeepSeek API"""
        if not self.api_key or self.api_key == "sk-dummy-key-replace-with-real-key":
            raise Exception("Invalid or missing API key. Please set DEEPSEEK_API_KEY in your .env file")
        
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages or [],
            "temperature": temperature,
            "stream": stream
        }
        
        print(f"Making request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Create a simple response object similar to OpenAI's format
            class Choice:
                def __init__(self, message_content):
                    self.message = type('Message', (), {'content': message_content})()
            
            class ChatCompletion:
                def __init__(self, choices):
                    self.choices = choices
            
            return ChatCompletion([Choice(data['choices'][0]['message']['content'])])
            
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            raise Exception(f"API request failed: {str(e)}")
        except KeyError as e:
            print(f"KeyError: {e}")
            raise Exception(f"Unexpected API response format: {str(e)}")
        except Exception as e:
            print(f"General error: {e}")
            raise Exception(f"Error calling DeepSeek API: {str(e)}")

def test_api():
    print("🧪 Testing DeepSeek API Connection...")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        print("❌ DEEPSEEK_API_KEY not found in environment!")
        print("Please create a .env file with your API key.")
        return False
    
    if api_key == "your_deepseek_api_key_here":
        print("❌ Please replace the dummy API key with your real key!")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        client = DeepSeekClient()
        
        # Test simple request
        print("\n🔄 Testing simple request...")
        response = client.chat_completions_create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond with a simple greeting."},
                {"role": "user", "content": "Hello"}
            ],
            temperature=1.0
        )
        
        content = response.choices[0].message.content
        print(f"✅ Simple test successful!")
        print(f"Response: {content}")
        
        # Test JSON format request
        print("\n🔄 Testing JSON format request...")
        system_prompt = """You are an English tutor. You MUST respond with valid JSON in exactly this format:
{
    "conversation_response": "Hello! I'm here to help you improve your English.",
    "corrections": [],
    "new_vocabulary": [],
    "suggestions": "Keep practicing!"
}

Do NOT include any other text before or after the JSON. Only return the JSON object."""
        
        response = client.chat_completions_create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Hello, I want to improve my English"}
            ],
            temperature=1.0
        )
        
        content = response.choices[0].message.content.strip()
        print(f"Raw response: {content}")
        
        # Clean up the response
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        # Try to parse JSON
        try:
            parsed = json.loads(content)
            print("✅ JSON parsing successful!")
            print(f"Parsed response: {json.dumps(parsed, indent=2)}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print(f"Content that failed to parse: {content}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_api()
    if success:
        print("\n🎉 All tests passed! Your API connection is working correctly.")
    else:
        print("\n💥 Tests failed. Please check your configuration.")