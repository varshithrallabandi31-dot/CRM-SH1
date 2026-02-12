"""
SERP Hawk email generator - creates personalized cold emails based on market analysis.
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

def generate_serp_hawk_email(company_info, market_analysis, service_matches, contact=None, draft_type="outreach"):
    """
    Generates a personalized B2B email for SERP Hawk.
    
    Args:
        company_info: Dict with company_name, what_they_do, contacts, etc.
        market_analysis: Dict with industry, growth_potential, competitors, etc.
        service_matches: Dict with recommended_services and email_hook
        contact: Optional specific contact person to address
        draft_type: "outreach" (offering our services) or "inbound" (requesting their services)
    
    Returns:
        Dict with subject and body (HTML format)
    """
    model = get_model()
    
    company_name = company_info.get('company_name', 'your company')
    industry = market_analysis.get('industry', 'your industry')
    
    # Prepare recipient context
    if contact and contact.get('name'):
        recipient_name = contact.get('name', '').split()[0]
        recipient_role = contact.get('role', 'Team Member')
        salutation = f"Hi {recipient_name},"
    else:
        salutation = f"Hi {company_name} Team,"
    
    if draft_type == "inbound":
        # Draft Type 1: Requesting THEIR service as a customer
        prompt = f"""
        Write a professional INBOUND inquiry email to {company_name}. 
        We are SERP Hawk, and we are interested in potentially hiring THEM for what they do.
        
        Context:
        - Target Company: {company_name}
        - What they do: {company_info.get('what_they_do', 'their services')}
        
        Instructions:
        - Be professional and curious.
        - Mention that we saw their website and are interested in their {industry} services.
        - Ask a specific question about their process or availability.
        - Keep it very short (under 100 words).
        - Signature: Brajesh Kumar, SERP Hawk.
        
        Output Format (JSON):
        {{
            "subject": "Inquiry regarding {company_name} services",
            "body_html": "HTML formatted email content"
        }}
        """
    else:
        # Draft Type 2: Offering OUR services (Outreach) - Transformation focused
        services = service_matches.get('recommended_services', [])[:3]
        service_descriptions = ""
        for i, svc in enumerate(services, 1):
            service_descriptions += f"\n{i}. **{svc.get('service_name')}**: {svc.get('why_relevant')}\n   Expected Impact: {svc.get('expected_impact')}"
        
        pain_points = market_analysis.get('pain_points', [])
        growth_potential = market_analysis.get('growth_potential', '')

        prompt = f"""
        Write a RESULTS-FOCUSED, transformation-driven sales email from SERP Hawk to {company_name}.
        
        CRITICAL STYLE REQUIREMENTS:
        - DO NOT talk about "who we are" or company history
        - FOCUS 100% on RESULTS, BENEFITS, and TRANSFORMATION
        - Use "Imagine..." storytelling to paint the outcome
        - Highlight what they GET, not what we do
        - Make it feel like a game-changer, not a service pitch
        
        Context:
        - Company: {company_name}
        - Industry: {industry}
        - Pain Points: {json.dumps(pain_points)}
        - Growth Potential: {growth_potential}
        
        Our Solutions:
        {service_descriptions}
        
        Email Structure:
        1. Opening: "Imagine..." scenario showing the transformation
        2. The Problem (briefly): Reference their specific pain points
        3. The Introduction: Briefly mention SERP Hawk's readiness to provide these outcomes.
        4. The Solution Details: 2-3 specific OUTCOMES they'll get (numbers/tangible results)
        5. CTA: Simple and direct (Reply 'INTERESTED' or call 089213 81769)
        6. P.S.: Urgency or bonus insight
        
        Output Format (JSON):
        {{
            "subject": "Curiosity-driven subject line",
            "body_html": "HTML email focusing on RESULTS and TRANSFORMATION"
        }}
        """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        email_data = json.loads(content.strip())
        
        # Ensure we have HTML formatting
        if 'body_html' not in email_data and 'body' in email_data:
            email_data['body_html'] = format_plain_to_html(email_data['body'])
        
        return email_data
        
    except Exception as e:
        print(f"Error generating SERP Hawk email ({draft_type}): {e}")
        # Simplistic fallback
        return {
            "subject": f"Question for the {company_name} team" if draft_type == "inbound" else f"Growth for {company_name}",
            "body_html": f"<p>{salutation}</p><p>I had a quick question about your business. Can we chat?</p>"
        }

def format_plain_to_html(plain_text):
    """
    Converts plain text email to HTML format.
    """
    # Split into paragraphs
    paragraphs = plain_text.split('\n\n')
    html_paragraphs = [f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()]
    return '\n'.join(html_paragraphs)
