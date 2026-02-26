import requests

try:
    response = requests.get('http://localhost:8000/')
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
