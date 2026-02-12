
import os
import google.generativeai as genai
import json

def get_model():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def extract_services(email_body: str) -> str:
    """
    Analyzes an email body to extract specific services mentioned.
    Returns a comma-separated string of services.
    """
    if not email_body:
        return ""
        
    try:
        model = get_model()
        prompt = f"""
        Analyze the following email content and extract a list of specific services that are being offered or requested.
        Return ONLY a comma-separated list of services. Do not include any other text, explanation, or introductions.
        
        Example Output: SEO Audit, Content Marketing, Google Ads
        
        Email Content:
        {email_body}
        """
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up if AI adds extra formatting
        if text.startswith("Services:"):
            text = text.replace("Services:", "").strip()
            
        return text
    except Exception as e:
        print(f"Error extracting services: {e}")
        return ""
