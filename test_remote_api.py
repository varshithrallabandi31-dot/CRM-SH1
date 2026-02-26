import requests
import json

BASE_URL = "https://crm-sh1-production.up.railway.app"

def test_remote_generate():
    print(f"Testing remote /generate at {BASE_URL}...")
    payload = {
        "urls": ["https://example.com"]
    }
    try:
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Data:", json.dumps(data, indent=2))
        else:
            print("Error:", response.text)
    except Exception as e:
        print("Exception:", e)

def test_remote_health():
    print(f"\nTesting remote /health at {BASE_URL}...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Status: {response.status_code}")
        print("Body:", response.json())
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test_remote_health()
    test_remote_generate()
