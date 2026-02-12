"""
Market analysis module for analyzing website business, growth, and competitors.
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

def analyze_market(website_content, company_name):
    """
    Analyzes the market position, growth potential, and competitors.
    """
    model = get_model()
    
    prompt = f"""
    Analyze this company's website content and provide a comprehensive market analysis.
    
    Company: {company_name}
    Website Content: {website_content[:10000]}
    
    Provide analysis in JSON format with the following structure:
    {{
        "industry": "Primary industry/sector",
        "sub_category": "More specific business category within the industry",
        "niche": "Specialized focus area or unique positioning",
        "business_type": "Type of business (e.g., E-commerce, SaaS, Service Provider, etc.)",
        "business_model": "Revenue model (B2B, B2C, B2B2C, Marketplace, etc.)",
        "market_size": "Estimated market size and description",
        "growth_potential": "High/Medium/Low with detailed explanation",
        "growth_indicators": [
            "Indicator 1: explanation",
            "Indicator 2: explanation"
        ],
        "target_audience": "Description of their target audience",
        "online_presence": {{  
            "website_quality": "Assessment of current website",
            "seo_status": "Visible SEO optimization level",
            "social_signals": "Any social media presence detected"
        }},
        "competitors": [
            {{
                "name": "Competitor name",
                "website": "competitor.com (if identifiable)",
                "why_competitor": "Brief explanation"
            }}
        ],
        "pain_points": [
            "Potential challenge 1",
            "Potential challenge 2"
        ],
        "opportunities": [
            "Growth opportunity 1",
            "Growth opportunity 2"
        ]
    }}
    
    Be specific and insightful. Focus on actionable intelligence.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        return parse_json_safely(content)
    except Exception as e:
        print(f"Error in market analysis: {e}")
        return {
            "industry": "Unknown",
            "business_type": "Unknown",
            "growth_potential": "Unable to analyze",
            "error": str(e)
        }

def match_services(market_analysis, company_info):
    """
    Matches SERP Hawk services to the company's needs based on market analysis.
    Returns prioritized list of relevant services with explanations.
    """
    model = get_model()
    
    serp_hawk_services = """
    1. Local SEO - Dominate local search results and attract customers in your area with targeted local SEO strategies. Includes GMB optimization, local keyword targeting, citation building, and review management.
    2. Organic SEO - Improve your website's search engine rankings and drive organic traffic with comprehensive SEO strategies. Includes keyword research, on-page optimization, technical SEO audits, and link building.
    3. Social Media Management - Build your brand presence and engage with your audience across all major social media platforms. Includes content creation, scheduling, community management, and analytics.
    4. Meta Ad Management - Maximize your ROI with expertly managed Facebook and Instagram advertising campaigns. Includes campaign setup, audience targeting, creative development, and tracking.
    5. Google Ad Management - Drive qualified traffic and conversions with professionally managed Google Ads campaigns. Includes search/display campaigns, keyword optimization, and conversion tracking.
    6. Digital Marketing Consulting - Get expert guidance and strategic insights to optimize your digital marketing efforts. Includes strategy development, marketing audits, and growth planning.
    7. WordPress Web Development - Create stunning, responsive WordPress websites that convert visitors into customers. Includes custom design, mobile-responsive layouts, and performance optimization.
    8. App Development - Build powerful mobile applications that engage users and drive business growth. Includes iOS & Android development, UX design, and maintenance.
    9. Automation Services - Streamline your business processes and increase efficiency with smart automation solutions. Includes workflow automation, marketing automation, and CRM integration.
    """
    
    prompt = f"""
    Based on this company's profile and market analysis, recommend the TOP 3-4 most relevant SERP Hawk services.
    
    Company: {company_info.get('company_name')}
    Industry: {market_analysis.get('industry')}
    Business Type: {market_analysis.get('business_type')}
    Growth Potential: {market_analysis.get('growth_potential')}
    Pain Points: {json.dumps(market_analysis.get('pain_points', []))}
    Opportunities: {json.dumps(market_analysis.get('opportunities', []))}
    Current Online Presence: {json.dumps(market_analysis.get('online_presence', {}))}
    
    Available Services:
    {serp_hawk_services}
    
    Return JSON format:
    {{
        "recommended_services": [
            {{
                "service_name": "Service Name",
                "priority": "High/Medium",
                "relevance_score": 85,
                "why_relevant": "Detailed explanation of why this service would help them",
                "expected_impact": "What results they can expect",
                "use_case": "Specific use case for their business"
            }}
        ],
        "package_suggestion": "Starter/Growth/Enterprise - based on their business size and needs",
        "quick_wins": ["Service 1 for immediate impact", "Service 2 for quick results"],
        "long_term_strategy": ["Service 1 for sustained growth", "Service 2 for competitive advantage"],
        "email_hook": "A compelling opening line for the email that references their specific situation"
    }}
    
    Be specific and compelling. Show deep understanding of their business.
    """
    
    try:
        response = model.generate_content(prompt)
        content = response.text
        return parse_json_safely(content)
    except Exception as e:
        print(f"Error in service matching: {e}")
        return {
            "recommended_services": [],
            "error": str(e)
        }

def parse_json_safely(content):
    """
    Robustly cleans and parses JSON content from LLM output.
    """
    try:
        # 1. Strip markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
            
        content = content.strip()
        
        # 2. Remove control characters (newlines within strings are common issues)
        # This is a basic strict=False equivalent but more aggressive if needed
        return json.loads(content, strict=False)
    except json.JSONDecodeError:
        # If standard parsing fails, try cleaning control characters
        import re
        # Remove control characters that are not standard whitespace
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        return json.loads(content, strict=False)
