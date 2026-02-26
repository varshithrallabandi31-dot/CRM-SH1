import requests
import json

BASE_URL = "http://localhost:8000"

def test_generate():
    print("Testing /generate...")
    payload = {
        "urls": ["https://example.com"]
    }
    try:
        response = requests.post(f"{BASE_URL}/generate", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Response Data:", json.dumps(data, indent=2)[:500] + "...")
            return data
        else:
            print("Error:", response.text)
    except Exception as e:
        print("Exception:", e)
    return None

def test_activities():
    print("\nTesting /activities...")
    try:
        response = requests.get(f"{BASE_URL}/activities")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Activities:", json.dumps(data, indent=2))
        else:
            print("Error:", response.text)
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    result = test_generate()
    test_activities()
