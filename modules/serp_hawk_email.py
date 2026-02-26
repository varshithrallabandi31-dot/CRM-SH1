import os
import json
from openai import OpenAI

def get_openai_client():
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return OpenAI(api_key=api_key)

def generate_serp_hawk_email(company_info, market_analysis, service_matches, contact=None, draft_type="outreach"):
    """
    Generates a personalized B2B email using OpenAI.
    """
    try:
        client = get_openai_client()
        
        company_name = company_info.get('company_name', 'your company')
        industry = market_analysis.get('industry', 'your industry')
        services = service_matches.get('recommended_services', [])[:3]
        
        service_descriptions = ""
        for i, svc in enumerate(services, 1):
            service_descriptions += f"\n{i}. **{svc.get('service_name')}**: {svc.get('why_relevant')}\n   Expected Impact: {svc.get('expected_impact')}"
        
        salutation = f"Hi {contact.get('name').split()[0]}," if contact and contact.get('name') else f"Hi {company_name} Team,"
        
        if draft_type == "inbound":
            prompt = f"Write a professional inquiry email to {company_name} reflecting interest in their {industry} services. Signature: Brajesh Kumar, SERP Hawk."
        else:
            prompt = f"Write a results-focused sales email from SERP Hawk to {company_name}. Focus on outcomes: {service_descriptions}."

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional email copywriter for SERP Hawk. Return ONLY JSON with 'subject' and 'body_html'."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        email_data = json.loads(response.choices[0].message.content)
        return email_data
        
    except Exception as e:
        print(f"Error in OpenAI email generation: {e}")
        return {
            "subject": f"Growth for {company_name}",
            "body_html": f"<p>Error: {str(e)}</p>"
        }
