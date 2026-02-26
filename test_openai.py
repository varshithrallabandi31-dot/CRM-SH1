import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)

def test_openai_key():
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"Testing local OpenAI API key: {api_key[:15]}...")
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
