import requests
import os

BASE_URL = "https://crm-sh1-production.up.railway.app"

def test_remote_ocr():
    print(f"Testing remote /documents/ocr at {BASE_URL}...")
    # Use a small dummy image or a remote image if possible, but we need to upload a file.
    # I'll create a 1x1 pixel image locally to test if the endpoint at least responds.
    from PIL import Image
    import io
    
    img = Image.new('RGB', (100, 100), color = (0, 0, 0))
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    files = {'file': ('test.jpg', img_byte_arr, 'image/jpeg')}
    try:
        response = requests.post(f"{BASE_URL}/documents/ocr", files=files, timeout=30)
        print(f"Status: {response.status_code}")
        print("Body:", response.json())
    except Exception as e:
        print("Exception:", e)

if __name__ == "__main__":
    test_remote_ocr()
