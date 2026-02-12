"""
Fallback analyzer for when web scraping fails.
Uses AI to analyze company name and make educated guesses about their business.
"""
import google.generativeai as genai
import os
import json

def get_model():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.5-flash')

def analyze_company_name_fallback(company_name):
    """
    When website scraping fails, analyze the company name to make intelligent guesses
    about their industry, business type, and common pain points.
    """
    model = get_model()
    
    prompt = f"""
    Analyze this company name and make educated guesses about their business:
    
    Company Name: {company_name}
    
    Based on the name alone, provide your best analysis in JSON format:
    {{
        "likely_industry": "Most probable industry/sector",
        "sub_category": "Specific business category",
        "business_model": "B2B, B2C, or B2B2C",
        "what_they_likely_do": "Brief description of probable business activities",
        "common_pain_points": [
            "Pain point 1 common in this industry",
            "Pain point 2 common in this industry",
            "Pain point 3 common in this industry"
        ],
        "target_audience": "Likely target customer base",
        "confidence": "High/Medium/Low - how confident are you in this analysis"
    }}
    
    Be specific and practical. Focus on actionable insights even with limited information.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        
        # Clean JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        result = json.loads(content.strip())
        print(f"DEBUG: Fallback analysis for '{company_name}': {result.get('likely_industry')}")
        return result
        
    except Exception as e:
        print(f"Error in fallback analysis: {e}")
        return {
            "likely_industry": "General Business",
            "sub_category": "Unknown",
            "business_model": "B2B",
            "what_they_likely_do": "Business services",
            "common_pain_points": ["Lead Generation", "Online Visibility", "Customer Acquisition"],
            "target_audience": "Business owners",
            "confidence": "Low"
        }
