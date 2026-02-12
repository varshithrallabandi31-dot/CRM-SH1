import google.generativeai as genai
import os
import json

def get_model():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def analyze_content(text):
    """
    Analyzes website text to extract company info and MULTIPLE contacts using Gemini.
    """
    model = get_model()
    prompt = f"""
    Analyze the following website content (including subpages) and extract the following information in JSON format:
    
    Structure:
    {{
        "company_name": "Name of the company",
        "what_they_do": "Brief summary of their business (2-3 sentences)",
        "contacts": [
            {{
                "name": "Full Name",
                "role": "Job Title (e.g. CEO, CTO, Marketing Manager)",
                "email": "Email address if found, else null",
                "context": "Any specific context about this person from the page (e.g. 'wrote a blog post about X' or 'leads the engineering team') or null"
            }}
        ],
        "key_value_props": ["prop1", "prop2"]
    }}
    
    Instructions:
    - Look for "About Us", "Team", or "Contact" sections in the text.
    - Extract AS MANY specific people as possible, especially decision makers (C-level, Founders, Directors).
    - If no specific people are found, return an empty list for 'contacts'.
    - If emails are not explicitly found, leave them null.
    
    Website Content:
    {text}
    """
    
    try:
        print("DEBUG: Sending content to Gemini for analysis...")
        response = model.generate_content(prompt)
        content = response.text
        print(f"DEBUG: Received response from Gemini: {content[:200]}...")
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        result = json.loads(content.strip())
        print(f"DEBUG: Successfully parsed JSON. Company: {result.get('company_name')}")
        return result
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw content received: {content}")
        return {
            "company_name": "Unknown",
            "what_they_do": "Could not parse AI response",
            "contacts": [],
            "error": f"JSON parsing failed: {str(e)}"
        }
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        return {
            "company_name": "Unknown",
            "what_they_do": "Could not analyze content",
            "contacts": [],
            "error": str(e)
        }

def generate_email(analysis, contact=None):
    """
    Generates a personalized cold email. 
    If 'contact' is provided, tailors it to that person.
    """
    model = get_model()
    
    # Determine recipient context
    if contact:
        recipient_info = f"Recipient: {contact.get('name')} ({contact.get('role')})\nContext: {contact.get('context')}"
        salutation_instruction = f"Address them as 'Hi {contact.get('name').split()[0]}',"
    else:
        recipient_info = "Recipient: General Inbox / Decision Maker"
        salutation_instruction = "Address them as 'Hi {analysis['company_name']} Team',"

    prompt = f"""
    Write a personalized B2B cold email.
    
    Your Role: AI Automation Agency (specializing in efficiency, lead gen, and scraping).
    Target Company: {analysis.get('company_name')}
    What they do: {analysis.get('what_they_do')}
    
    {recipient_info}
    
    Goal:
    - If speaking to a technical person (CTO/Dev), mention technical benefits (API integration, clean data).
    - If speaking to a business person (CEO/Founder), mention ROI, time saving, and growth.
    - If general, keep it broad but valuable.
    
    Instructions:
    - {salutation_instruction}
    - Reference their specific business or value props: {', '.join(analysis.get('key_value_props', []))}
    - Keep it under 150 words.
    - Clear CTA (Book a 15-min call).
    - Subject Line MUST be catchy and relevant.
    
    Output Format:
    Return a JSON object with 'subject' and 'body' fields.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        return json.loads(content.strip())
    except Exception as e:
        return {
            "subject": "Error generating email",
            "body": f"Could not generate email. Error: {str(e)}"
        }

def analyze_document(image_bytes):
    """
    Analyzes an image (ID card, business card) to extract contact details.
    """
    model = get_model()
    
    prompt = """
    Analyze this image of a business card or ID card. Extract the following details in JSON format:
    {
        "name": "Full Name",
        "company_name": "Company Name",
        "mobile": "Mobile Number",
        "email": "Email Address",
        "website": "Website URL"
    }
    If a field is not found, return null.
    """
    
    try:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_bytes))
        
        response = model.generate_content([prompt, image])
        content = response.text
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        return json.loads(content.strip())
    except Exception as e:
        print(f"Error in document analysis: {e}")
        return {
            "error": str(e)
        }
