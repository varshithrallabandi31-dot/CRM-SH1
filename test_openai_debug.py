import os
from openai import OpenAI
from dotenv import load_dotenv

# Force reload from the specific .env file in the current directory
load_dotenv(dotenv_path=".env", override=True)

def test_openai_key():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("OPENAI_API_KEY not found in environment!")
        return
    
    print(f"Key from ENV starts with: {api_key[:15]}...")
    print(f"Key from ENV ends with: ...{api_key[-15:]}")
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say hello"}]
        )
        print(f"Status: SUCCESS")
        print(f"Response: {response.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"Status: FAILED")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_openai_key()
