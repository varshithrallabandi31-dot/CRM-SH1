import os
import json
from openai import OpenAI

def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)

def analyze_company_name_fallback(company_name):
    """
    Fallback analysis using OpenAI when website scraping fails.
    """
    try:
        client = get_openai_client()
        prompt = f"""Analyze this company name and return a JSON object with your best guess about their business.
Company name: {company_name}

Return JSON with fields: likely_industry, sub_category, business_model, common_pain_points (list of strings), summary.
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Fallback analysis error: {e}")
        return {
            "likely_industry": "General Business",
            "sub_category": "",
            "business_model": "B2B",
            "common_pain_points": ["Lead Generation", "Online Visibility"],
            "summary": f"Company: {company_name}",
            "error": str(e)
        }
