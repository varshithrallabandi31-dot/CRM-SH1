import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_local_key():
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"Testing local API key: {api_key[:10]}...")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say hello")
        print(f"Status: SUCCESS")
        print(f"Response: {response.text.strip()}")
    except Exception as e:
        print(f"Status: FAILED")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_local_key()
