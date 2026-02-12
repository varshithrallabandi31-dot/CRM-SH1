import asyncio
import sys

# CRITICAL: Fix for Playwright + FastAPI on Windows: Enforce ProactorEventLoop
# Must be at the absolute top before other imports create/access the default loop.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import os
import uuid
import warnings

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import traceback

from fastapi import FastAPI, Request, Form, Depends, HTTPException, BackgroundTasks, Body, File, UploadFile
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, select, func, text
from dotenv import load_dotenv

# Database & Models
from database import (
    engine, 
    Company, 
    EmailLog,
    User,
    ClientProfile,
    Project,
    Remark,
    Document,
    ActivityLog,
    create_db_and_tables, 
    get_session
)

# AI & Scraping Modules
from modules.scraper import scrape_website
from modules.llm_engine import analyze_content, generate_email, analyze_document
from modules.market_analyzer import analyze_market, match_services
from modules.serp_hawk_email import generate_serp_hawk_email
from modules.fallback_analyzer import analyze_company_name_fallback
from modules.image_generator import generate_email_image
from modules.email_sender import send_email_outlook

# Load environment variables
load_dotenv()

# Configuration
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "padilla@dapros.com") # Default sender for UI
HOURLY_EMAIL_LIMIT = int(os.getenv("HOURLY_EMAIL_LIMIT", 50))
OUTLOOK_EMAIL = os.getenv('OUTLOOK_EMAIL')
OUTLOOK_PASSWORD = os.getenv('OUTLOOK_PASSWORD')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

# Create output directories
os.makedirs('static/generated_images', exist_ok=True)


# Custom Exceptions
class OutreachError(Exception):
    """Base exception for outreach eligibility errors"""
    pass


class DuplicateProspectError(OutreachError):
    """Raised when a prospect has already been contacted"""
    pass


class RateLimitExceededError(OutreachError):
    """Raised when hourly email limit is reached"""
    pass

def sync_scrape_website_wrapper(url):
    """
    Wrapper to run the async scraper in a fresh nested loop.
    This fixes the NotImplementedError on Windows by ensuring a ProactorEventLoop is used.
    """
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Import here to avoid circular dependencies if any
    from modules.scraper import scrape_website
    return asyncio.run(scrape_website(url))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan - creates tables on startup
    """
    print("🚀 Starting Cold Outreach CRM...")
    
    # Debug loop type
    try:
        loop = asyncio.get_running_loop()
        print(f"DEBUG: FastAPI is running on loop: {type(loop).__name__}")
        if sys.platform == 'win32' and 'Proactor' not in type(loop).__name__:
            print("WARNING: ProactorEventLoop NOT detected. Playwright might fail.")
    except Exception as e:
        print(f"DEBUG: Could not check loop type: {e}")

    print("📊 Creating database tables...")
    create_db_and_tables()
    
    # Simple migrations for client_profiles and companies
    try:
        with engine.connect() as conn:
            # Companies migration
            conn.execute(text("ALTER TABLE companies ADD COLUMN IF NOT EXISTS recommended_services VARCHAR(1000)"))
            
            # ClientProfile migrations
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN IF NOT EXISTS \"nextMilestone\" VARCHAR(255)"))
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN IF NOT EXISTS \"nextMilestoneDate\" VARCHAR(255)"))
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN IF NOT EXISTS recommended_services VARCHAR(1000)"))
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN IF NOT EXISTS \"projectId\" INTEGER"))
            conn.execute(text("ALTER TABLE remarks ADD COLUMN IF NOT EXISTS \"projectId\" INTEGER"))
            
            conn.commit()
            print("✅ Database schema updated (milestones, recommended_services, projects)")
    except Exception as e:
        print(f"⚠️ Schema update note: {e}")

    print("✅ Database ready!")
    
    # Try to install playwright browsers if needed (optional check)
    # print("Checking Playwright browsers...")
    # os.system("playwright install chromium") 
    
    yield
    print("👋 Shutting down Cold Outreach CRM...")


# Initialize FastAPI app
app = FastAPI(
    title="Cold Outreach CRM",
    description="A simple CRM for managing cold email outreach",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ClientCreate(BaseModel):
    companyName: str
    websiteUrl: str
    email: str
    projectName: Optional[str] = None
    gmbName: Optional[str] = None
    seoStrategy: Optional[str] = None
    tagline: Optional[str] = None
    targetKeywords: Optional[List[str]] = None
    recommended_services: Optional[str] = None

class ActivityAdd(BaseModel):
    method: str
    content: str

class RemarkAdd(BaseModel):
    content: str

class EmailSend(BaseModel):
    subject: str
    body: str

class LoginRequest(BaseModel):
    email: str
    password: str

class ClientUpdate(BaseModel):
    status: Optional[str] = None
    nextMilestone: Optional[str] = None
    nextMilestoneDate: Optional[str] = None
    projectName: Optional[str] = None
    websiteUrl: Optional[str] = None
    gmbName: Optional[str] = None
    seoStrategy: Optional[str] = None
    tagline: Optional[str] = None
    recommended_services: Optional[str] = None

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[str] = "Planning"
    progress: Optional[int] = 0
    employeeIds: Optional[List[int]] = []
    internIds: Optional[List[int]] = []
    clientIds: Optional[List[int]] = []

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    employeeIds: Optional[List[int]] = None
    internIds: Optional[List[int]] = None
    clientIds: Optional[List[int]] = None

class ProjectRemarkAdd(BaseModel):
    content: str
    isInternal: Optional[bool] = True

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

# ============================================================================
# BUSINESS LOGIC - The "Gatekeeper" Middleware
# ============================================================================

def check_outreach_eligibility(session: Session, website_url: str) -> dict:
    """
    Gatekeeper function that checks if we can send an outreach email.
    """
    result = {
        "eligible": True,
        "existing_company": None,
        "emails_sent_last_hour": 0
    }
    
    # Normalize URL for comparison
    normalized_url = website_url.strip().lower()
    if not normalized_url.startswith(('http://', 'https://')):
        normalized_url = 'https://' + normalized_url
    
    # Rule A: Duplicate Check
    statement = select(Company).where(Company.website_url == normalized_url)
    existing_company = session.exec(statement).first()
    
    if existing_company:
        result["existing_company"] = existing_company
        if existing_company.email_sent_status:
            raise DuplicateProspectError(
                f"❌ Prospecting email already sent to {existing_company.company_name} "
                f"({existing_company.website_url}) on {existing_company.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
    
    # Rule B: Rate Limiter
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    rate_limit_statement = select(func.count(EmailLog.id)).where(
        EmailLog.sender_email == SENDER_EMAIL,
        EmailLog.sent_at > one_hour_ago
    )
    emails_sent_count = session.exec(rate_limit_statement).one()
    result["emails_sent_last_hour"] = emails_sent_count
    
    if emails_sent_count >= HOURLY_EMAIL_LIMIT:
        raise RateLimitExceededError(
            f"⏳ Hourly email limit ({HOURLY_EMAIL_LIMIT}) reached. "
            f"You've sent {emails_sent_count} emails in the last hour. "
            f"Please wait before sending more."
        )
    
    return result


# ============================================================================
# ROUTES - API
# ============================================================================

@app.get("/")
async def root():
    """
    Root endpoint - indicates API is running.
    """
    return {
        "message": "Cold Outreach CRM API is running",
        "frontend": "http://localhost:3000",
        "docs": "/docs"
    }




# ============================================================================
# PROCESS ROUTES - Add Lead & Send Email (CRM Style)
# ============================================================================

@app.post("/login")
async def login(data: LoginRequest, session: Session = Depends(get_session)):
    """Simple database login for CRM"""
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()
    
    if user and user.password == data.password:
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role
            }
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid email or password")

@app.post("/draft-lead")
async def draft_lead(
    company_name: str = Form(...),
    website_url: str = Form(...),
    primary_email: str = Form(...),
    session: Session = Depends(get_session)
):
    """
    Step 1: Check eligibility, analyze URL, and return Draft (NO SENDING)
    """
    try:
        # Normalize URL
        normalized_url = website_url.strip().lower()
        if not normalized_url.startswith(('http://', 'https://')):
            normalized_url = 'https://' + normalized_url
        
        # Check eligibility (just for info, but don't block drafting yet? Or do block?)
        # Let's BLOCK if already sent, to warn user.
        eligibility = check_outreach_eligibility(session, normalized_url)
        
        print(f"🧐 Analyzing {normalized_url} for personalization...")
        
        # Scrape & Analyze
        scraped_text = await run_in_threadpool(scrape_website, normalized_url)
        
        subject = f"Partnership Opportunity with {company_name}"
        body_html = f"<p>Hi {company_name} Team,</p><p>We'd love to partner.</p>" 
        
        if scraped_text and not scraped_text.startswith("ERROR SCRAPING"):
            company_info = await run_in_threadpool(analyze_content, scraped_text)
            market_analysis = await run_in_threadpool(analyze_market, scraped_text, company_name)
            service_matches = await run_in_threadpool(match_services, market_analysis, company_info)
        else:
            print(f"⚠️ Scraping failed/empty: {scraped_text[:100] if scraped_text else 'None'}. Generating intelligent fallback draft.")
            # Enhanced fallback: Use AI to analyze company name for industry hints
            company_info = await run_in_threadpool(analyze_company_name_fallback, company_name)
            market_analysis = {
                'industry': company_info.get('likely_industry', 'Unknown'), 
                'sub_category': company_info.get('sub_category', ''),
                'business_model': company_info.get('business_model', 'B2B'),
                'pain_points': company_info.get('common_pain_points', ['Lead Generation', 'Online Visibility']), 
                'growth_potential': 'High',
                'online_presence': {'seo_status': 'Needs improvement'}
            }
            service_matches = {
                'recommended_services': [
                    {'service_name': 'Organic SEO', 'why_relevant': 'Improve online visibility and search rankings', 'expected_impact': 'More qualified leads from search'},
                    {'service_name': 'Local SEO', 'why_relevant': 'Dominate local search results', 'expected_impact': 'Increased local customer acquisition'}
                ], 
                'email_hook': f'Growth opportunities for {company_info.get("likely_industry", "your business")}',
                'package_suggestion': 'Growth'
            }

        contact = {'name': company_name, 'email': primary_email, 'role': 'Decision Maker'}
        email_draft = await run_in_threadpool(
            generate_serp_hawk_email,
            company_info, market_analysis, service_matches, contact
        )
        
        if email_draft:
            subject = email_draft.get('subject', subject)
            body_html = email_draft.get('body_html', body_html)

        # Get services string
        services = service_matches.get('recommended_services', [])
        service_names = [s.get('service_name') for s in services]
        recommended_services_str = ", ".join(service_names) if service_names else None

        return JSONResponse({
            'success': True,
            'draft': {
                'subject': subject,
                'body': body_html,
                'company_name': company_name,
                'website_url': normalized_url,
                'primary_email': primary_email,
                'recommended_services': recommended_services_str
            }
        })

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.post("/send-lead")
async def send_lead(
    request: Request,
    data: dict,
    session: Session = Depends(get_session)
):
    """
    Step 2: Send the approved draft
    """
    try:
        to_email = data.get('primary_email')
        subject = data.get('subject')
        body_html = data.get('body')
        company_name = data.get('company_name')
        website_url = data.get('website_url')
        recommended_services = data.get('recommended_services')

        # Check eligibility/Rate Limit "just in case" (final gate)
        # Note: We skip duplicate check here if user forces send, or re-check.
        # Let's do a re-check to be safe.
        normalized_url = website_url.strip().lower()
        check_outreach_eligibility(session, normalized_url)

        # Send Email (Skip if manual)
        is_manual = data.get('manual', False)
        if not is_manual:
            if OUTLOOK_EMAIL and OUTLOOK_PASSWORD:
                print(f"Sending email to {to_email} via Outlook...")
                await run_in_threadpool(
                    send_email_outlook,
                    to_email=to_email,
                    subject=subject,
                    body=body_html,
                    sender_email=OUTLOOK_EMAIL,
                    sender_password=OUTLOOK_PASSWORD,
                    smtp_server=SMTP_SERVER,
                    smtp_port=SMTP_PORT,
                    html=True
                )
            else:
                 print(f"SIMULATING email to {to_email}: {subject}")
        else:
            print(f"MANUAL log for {to_email}: {subject}")

        # DB Operations (Create Company + Log)
        # Check if company exists first
        stmt = select(Company).where(Company.website_url == normalized_url)
        company = session.exec(stmt).first()
        
        if not company:
            company = Company(
                company_name=company_name,
                website_url=normalized_url,
                primary_email=to_email,
                email_sender=SENDER_EMAIL,
                email_sent_status=True,
                recommended_services=recommended_services
            )
            session.add(company)
        else:
            company.email_sent_status = True
            company.primary_email = to_email # Update email if changed
            if recommended_services:
                company.recommended_services = recommended_services
            session.add(company)
            
        session.commit()
        session.refresh(company)

        # 1. Ensure User exists for this email
        user_stmt = select(User).where(User.email == to_email)
        user = session.exec(user_stmt).first()
        if not user:
            user = User(
                email=to_email,
                password="password123", # Default password
                name=company_name,
                role="Client"
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        # 2. Ensure Client Profile exists and is linked
        profile_stmt = select(ClientProfile).where(ClientProfile.userId == user.id)
        profile = session.exec(profile_stmt).first()
        if not profile:
            profile = ClientProfile(
                userId=user.id,
                companyName=company_name,
                websiteUrl=normalized_url,
                status="Active",
                recommended_services=recommended_services
            )
            session.add(profile)
        else:
            # Update background profile info too
            if recommended_services:
                profile.recommended_services = recommended_services
            session.add(profile)
            
        session.commit()

        # Log EmailActivity
        log = EmailLog(
            company_id=company.id,
            sender_email=SENDER_EMAIL,
            sent_at=datetime.utcnow()
        )
        session.add(log)
        session.commit()
        
        return JSONResponse({'success': True})

    except Exception as e:
        traceback.print_exc()
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.get("/activities")
async def get_activities(limit: int = 10, session: Session = Depends(get_session)):
    """
    Fetch recent email activities
    """
    statement = (
        select(EmailLog, Company)
        .join(Company, EmailLog.company_id == Company.id)
        .order_by(EmailLog.sent_at.desc())
        .limit(limit)
    )
    results = session.exec(statement).all()
    
    activities = []
    for log, comp in results:
        activities.append({
            'id': str(log.id), # Convert UUID to string
            'company_name': comp.company_name,
            'website_url': comp.website_url,
            'email': comp.primary_email,
            'sent_at': log.sent_at.isoformat(),
            'status': 'Sent',
            'recommended_services': comp.recommended_services
        })
        
    return JSONResponse({'activities': activities})


# ============================================================================
# AI ROUTES - SERP Hawk Logic
# ============================================================================

@app.post("/generate")
async def generate_ai_analysis(data: dict):
    """
    Complete SERP Hawk outreach workflow:
    1. Scrape website
    2. Analyze company
    3. Analyze market & competitors
    4. Match services
    5. Generate email
    6. Create image
    """
    urls = data.get('urls', [])
    results = []

    for url in urls:
        try:
            print(f"Processing: {url}")
            
            # Step 1: Scrape (run in threadpool with fresh loop for Windows compatibility)
            scraped_text = await run_in_threadpool(sync_scrape_website_wrapper, url)
            
            if not scraped_text or scraped_text.startswith("ERROR SCRAPING"):
                error_message = scraped_text if scraped_text else "Failed to scrape website"
                results.append({'url': url, 'error': error_message})
                continue

            # Step 2: Analyze company
            company_info = await run_in_threadpool(analyze_content, scraped_text)
            company_name = company_info.get('company_name', 'Unknown Company')

            # Step 3: Market analysis
            market_analysis = await run_in_threadpool(analyze_market, scraped_text, company_name)

            # Step 4: Match services
            service_matches = await run_in_threadpool(match_services, market_analysis, company_info)

            # Step 5: Generate email
            contacts = company_info.get('contacts', [])
            generated_emails = []
            
            if contacts:
                for contact in contacts:
                    # Type 1: Outreach (Offering)
                    outreach_draft = await run_in_threadpool(
                        generate_serp_hawk_email,
                        company_info, market_analysis, service_matches, contact, "outreach"
                    )
                    # Type 2: Inbound (Requesting)
                    inbound_draft = await run_in_threadpool(
                        generate_serp_hawk_email,
                        company_info, market_analysis, service_matches, contact, "inbound"
                    )
                    
                    generated_emails.append({
                        'to_email': contact.get('email', ''),
                        'recipient_name': contact.get('name'),
                        'role': contact.get('role'),
                        'outreach': {
                            'subject': outreach_draft.get('subject'),
                            'body': outreach_draft.get('body_html')
                        },
                        'inbound': {
                            'subject': inbound_draft.get('subject'),
                            'body': inbound_draft.get('body_html')
                        }
                    })
            else:
                # Type 1: Outreach (Offering)
                outreach_draft = await run_in_threadpool(
                    generate_serp_hawk_email,
                    company_info, market_analysis, service_matches, None, "outreach"
                )
                # Type 2: Inbound (Requesting)
                inbound_draft = await run_in_threadpool(
                    generate_serp_hawk_email,
                    company_info, market_analysis, service_matches, None, "inbound"
                )
                
                generated_emails.append({
                    'to_email': '', 
                    'recipient_name': 'General',
                    'role': 'N/A',
                    'outreach': {
                        'subject': outreach_draft.get('subject'),
                        'body': outreach_draft.get('body_html')
                    },
                    'inbound': {
                        'subject': inbound_draft.get('subject'),
                        'body': inbound_draft.get('body_html')
                    }
                })

            # Step 6: Generate beautiful email image
            services = service_matches.get('recommended_services', [])
            
            safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_company_name = safe_company_name.replace(' ', '_')[:50]
            
            image_filename = f"{safe_company_name}_email_image.html"
            image_path = os.path.join('static', 'generated_images', image_filename)
            
            generated_image = await run_in_threadpool(
                generate_email_image,
                company_name, services, image_path
            )

            results.append({
                'url': url,
                'analysis': {
                    'company_name': company_name,
                    'what_they_do': company_info.get('summary', 'Analysis available'),
                    'contacts': contacts
                },
                'emails': generated_emails,
                'image_url': f'/static/generated_images/{image_filename}' if generated_image else None
            })

        except Exception as e:
            traceback.print_exc()
            results.append({'url': url, 'error': str(e)})

    return JSONResponse(results)


@app.post("/send")
async def send_email_api(data: dict, session: Session = Depends(get_session)):
    """
    Send email using credentials and log to DB (AI Outreach version)
    """
    email_data = data.get('email_data')
    if not email_data:
        return JSONResponse({'success': False, 'error': 'No email data provided'}, status_code=400)

    sender_email = OUTLOOK_EMAIL
    sender_password = OUTLOOK_PASSWORD
    
    if not sender_email or not sender_password:
        return JSONResponse({'success': False, 'error': 'Email credentials not configured in .env'}), 500

    try:
        # Check eligibility/rate limit before sending
        # Note: We need a URL to check duplicates, but the AI UI sends email_data directly.
        # We'll treat this as "Ad-hoc" send, but still rate limit.
        
        # Rate Limit Check
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        rate_statement = select(func.count(EmailLog.id)).where(
            EmailLog.sender_email == SENDER_EMAIL,
            EmailLog.sent_at > one_hour_ago
        )
        emails_sent_count = session.exec(rate_statement).one()
        
        if emails_sent_count >= HOURLY_EMAIL_LIMIT:
             return JSONResponse({'success': False, 'error': 'Hourly rate limit exceeded'}, status_code=429)

        # Send Email
        await run_in_threadpool(
            send_email_outlook,
            to_email=email_data['to_email'],
            subject=email_data['subject'],
            body=email_data['body'],
            sender_email=sender_email,
            sender_password=sender_password,
            smtp_server=SMTP_SERVER,
            smtp_port=SMTP_PORT,
            html=True
        )
        
        # Log to DB
        # We might not have a Company ID if it came from the AI tool randomly.
        # For now, we'll try to find a company by email or create a "clean" one if needed.
        # But to avoid complexity, we can just log the rate limit and maybe create a minimal company.
        
        # Try to find company by email
        statement = select(Company).where(Company.primary_email == email_data['to_email'])
        company = session.exec(statement).first()
        
        if not company:
            # Create a shell company entry for logging purposes
            company = Company(
                company_name="AI Outreach Contact",
                website_url=f"ai-generated-{uuid.uuid4()}@example.com", # Placeholder
                primary_email=email_data['to_email'],
                email_sender=SENDER_EMAIL,
                email_sent_status=True
            )
            session.add(company)
            session.commit()
            session.refresh(company)
        else:
            company.email_sent_status = True
            session.add(company)
            session.commit()

        # Log
        email_log = EmailLog(
            company_id=company.id,
            sender_email=SENDER_EMAIL,
            sent_at=datetime.utcnow()
        )
        session.add(email_log)
        session.commit()

        return JSONResponse({'success': True})
        
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({'success': False, 'error': str(e)}, status_code=500)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    loop_type = "Unknown"
    try:
        loop_type = type(asyncio.get_running_loop()).__name__
    except:
        pass
        
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Cold Outreach CRM + AI",
        "loop": loop_type,
        "platform": sys.platform
    }


@app.get("/dashboard-stats")
async def get_dashboard_stats(role: str, email: str, session: Session = Depends(get_session)):
    """Fetch stats for the dashboard based on role"""
    if role == 'Admin':
        total_clients = session.exec(select(func.count(ClientProfile.id))).one()
        active_clients = session.exec(select(func.count(ClientProfile.id)).where(ClientProfile.status == 'Active')).one()
        pending_clients = session.exec(select(func.count(ClientProfile.id)).where(ClientProfile.status == 'Pending')).one()
        hold_clients = session.exec(select(func.count(ClientProfile.id)).where(ClientProfile.status == 'Hold')).one()
        
        return {
            "total": total_clients,
            "active": active_clients,
            "pending": pending_clients,
            "hold": hold_clients
        }
    else:
        # Client specific stats
        profile_stmt = select(ClientProfile).join(User).where(User.email == email)
        profile = session.exec(profile_stmt).first()
        if not profile:
            return {"error": "Profile not found"}
            
        # Return real profile data for the dashboard
        return {
            "isClient": True,
            "companyName": profile.companyName,
            "projectName": profile.projectName,
            "website": profile.websiteUrl,
            "status": profile.status,
            "seoStrategy": profile.seoStrategy,
            "recommended_services": profile.recommended_services,
            "targetKeywords": profile.targetKeywords or [],
            "nextMilestone": profile.nextMilestone,
            "nextMilestoneDate": profile.nextMilestoneDate,
            # Placeholder metrics for the dynamic dashboard visual
            "metrics": {
                "successRate": "87.5%",
                "failed": 539,
                "successful": 5231,
                "suspended": 15,
                "totalLive": 1,
                "goal": "$212,943,433",
                "backers": 582160,
                "pledged": "$41,264,435"
            }
        }


# ============================================================================
# CLIENT PROFILE ROUTES
# ============================================================================

@app.get("/clients")
async def list_clients(status: Optional[str] = None, session: Session = Depends(get_session)):
    """List all client profiles with filters"""
    statement = select(ClientProfile)
    if status and status != 'All':
        statement = statement.where(ClientProfile.status == status)
    
    profiles = session.exec(statement).all()
    results = []
    for p in profiles:
        # Get latest email sent
        user_email = p.user.email if p.user else "N/A"
        results.append({
            "id": p.id,
            "projectName": p.projectName or p.companyName,
            "category": p.seoStrategy or "Software Training Institute", # Placeholder category
            "email": user_email,
            "status": p.status,
            "keywords": p.targetKeywords or [],
            "website": p.websiteUrl
        })
    return {"clients": results}

@app.get("/employees")
async def list_employees(session: Session = Depends(get_session)):
    """List all users with role 'Employee' or 'Admin'"""
    statement = select(User).where(User.role.in_(['Employee', 'Admin']))
    users = session.exec(statement).all()
    return {"employees": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]}

@app.put("/clients/{client_id}/assign-employee")
async def assign_employee(client_id: int, employee_id: int = Body(..., embed=True), session: Session = Depends(get_session)):
    """Assign an employee to a client"""
    client = session.get(ClientProfile, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    employee = session.get(User, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    client.assignedEmployeeId = employee_id
    session.add(client)
    session.commit()
    return {"success": True, "assigned_to": employee.name}

@app.get("/projects")
async def list_projects(session: Session = Depends(get_session)):
    """List all projects with basic details"""
    statement = select(Project)
    projects = session.exec(statement).all()
    return {"projects": projects}

@app.post("/projects")
async def create_project(data: ProjectCreate, session: Session = Depends(get_session)):
    """Create a new advanced project"""
    project = Project(**data.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@app.get("/projects/{project_id}")
async def get_project_detail_view(project_id: int, session: Session = Depends(get_session)):
    """Get full details of a project including remarks and team"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    # Get remarks
    remarks_stmt = select(Remark).where(Remark.projectId == project_id).order_by(Remark.createdAt.desc())
    remarks_list = session.exec(remarks_stmt).all()
    
    # Get assigned team details
    employees = session.exec(select(User).where(User.id.in_(project.employeeIds))).all() if project.employeeIds else []
    interns = session.exec(select(User).where(User.id.in_(project.internIds))).all() if project.internIds else []
    
    return {
        "project": project,
        "remarks": remarks_list,
        "team": {
            "employees": [{"id": e.id, "name": e.name, "email": e.email} for e in employees],
            "interns": [{"id": i.id, "name": i.name, "email": i.email} for i in interns]
        }
    }

@app.patch("/projects/{project_id}")
async def update_project(project_id: int, data: ProjectUpdate, session: Session = Depends(get_session)):
    """Update project progress, status, or assignments"""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    
    project.updatedAt = datetime.utcnow()
    session.add(project)
    session.commit()
    session.refresh(project)
    return project

@app.post("/projects/{project_id}/remarks")
async def add_project_remark(project_id: int, data: ProjectRemarkAdd, author_id: int = Body(..., embed=True), session: Session = Depends(get_session)):
    """Add a comment/remark to a project"""
    remark = Remark(
        content=data.content,
        projectId=project_id,
        authorId=author_id,
        isInternal=data.isInternal
    )
    session.add(remark)
    session.commit()
    session.refresh(remark)
    return remark

@app.get("/interns")
async def list_interns(session: Session = Depends(get_session)):
    """List all users with role 'Intern'"""
    statement = select(User).where(User.role == 'Intern')
    users = session.exec(statement).all()
    return {"interns": [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]}

@app.post("/users")
async def create_user(data: UserCreate, session: Session = Depends(get_session)):
    """Create a new user (Intern/Employee/Admin)"""
    # Check if user exists
    stmt = select(User).where(User.email == data.email)
    existing = session.exec(stmt).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = User(
        name=data.name,
        email=data.email,
        password=data.password, # Note: Should be hashed in real app
        role=data.role
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, session: Session = Depends(get_session)):
    """Delete a user"""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"success": True}

@app.patch("/clients/{client_id}")
async def update_client_profile(client_id: int, data: ClientUpdate, session: Session = Depends(get_session)):
    """Update specific fields of a client profile"""
    profile = session.get(ClientProfile, client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
        
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
        
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile

@app.post("/clients/{client_id}/keywords")
async def add_keyword(client_id: int, keyword: str = Body(..., embed=True), session: Session = Depends(get_session)):
    """Add a target keyword to client profile"""
    client = session.get(ClientProfile, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    current_keywords = list(client.targetKeywords) if client.targetKeywords else []
    if keyword not in current_keywords:
        current_keywords.append(keyword)
        client.targetKeywords = current_keywords
        session.add(client)
        session.commit()
        
    return {"success": True, "keywords": client.targetKeywords}

@app.delete("/clients/{client_id}/keywords")
async def remove_keyword(client_id: int, keyword: str = Body(..., embed=True), session: Session = Depends(get_session)):
    """Remove a target keyword from client profile"""
    client = session.get(ClientProfile, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    current_keywords = list(client.targetKeywords) if client.targetKeywords else []
    if keyword in current_keywords:
        current_keywords.remove(keyword)
        client.targetKeywords = current_keywords
        session.add(client)
        session.commit()
        
    return {"success": True, "keywords": client.targetKeywords}

@app.get("/clients/{client_id}")
async def get_client_detail(client_id: int, session: Session = Depends(get_session)):
    """Get detailed profile for a specific client"""
    profile = session.get(ClientProfile, client_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get assigned employee details
    assigned_employee = None
    if profile.assignedEmployeeId:
        emp = session.get(User, profile.assignedEmployeeId)
        if emp:
            assigned_employee = {"id": emp.id, "name": emp.name, "email": emp.email}

    return {
        "id": profile.id,
        "companyName": profile.companyName,
        "website": profile.websiteUrl,
        "address": profile.address,
        "phone": profile.phone,
        "email": profile.user.email if profile.user else "",
        "seoStrategy": profile.seoStrategy,
        "tagline": profile.tagline,
        "projectName": profile.projectName,
        "gmbName": profile.gmbName,
        "targetKeywords": profile.targetKeywords or [],
        "assignedEmployee": assigned_employee,
        "status": profile.status,
        "recommended_services": profile.recommended_services,
        "nextMilestone": profile.nextMilestone,
        "nextMilestoneDate": profile.nextMilestoneDate
    }

# ============================================================================
# DOCUMENT OCR ROUTES
# ============================================================================

from modules.llm_engine import analyze_document

@app.post("/documents/ocr")
async def ocr_document(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Upload an image and extract details using OCR"""
    try:
        contents = await file.read()
        result = analyze_document(contents)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/clients")
async def create_client(
    data: ClientCreate,
    session: Session = Depends(get_session)
):
    """Manually create a new client and user"""
    # 1. Ensure User exists
    user_stmt = select(User).where(User.email == data.email)
    user = session.exec(user_stmt).first()
    if not user:
        user = User(email=data.email, password="password123", name=data.companyName, role="Client")
        session.add(user)
        session.commit()
        session.refresh(user)
    
    # 2. Create Profile
    profile = ClientProfile(
        userId=user.id,
        companyName=data.companyName,
        websiteUrl=data.websiteUrl,
        customFields={},
        status="Active",
        projectName=data.projectName,
        gmbName=data.gmbName,
        seoStrategy=data.seoStrategy,
        tagline=data.tagline,
        recommended_services=data.recommended_services,
        targetKeywords=data.targetKeywords or []
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    return {"id": profile.id, "companyName": profile.companyName, "status": "created"}

@app.post("/clients/{client_id}/activities")
async def add_client_activity(
    client_id: int,
    data: ActivityAdd,
    session: Session = Depends(get_session)
):
    """Add a manual activity for a client"""
    activity = ActivityLog(
        clientId=client_id,
        userId=None,
        action="Manual Activity",
        method=data.method,
        content=data.content,
        createdAt=datetime.utcnow()
    )
    session.add(activity)
    session.commit()
    return {"success": True}

@app.get("/clients/{client_id}/activities")
async def get_client_activities(
    client_id: int, 
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get activities for a specific client with pagination"""
    statement = select(ActivityLog).where(ActivityLog.clientId == client_id).order_by(ActivityLog.createdAt.desc()).limit(limit)
    activities = session.exec(statement).all()
    return {"activities": [
        {
            "id": a.id,
            "method": a.method,
            "content": a.content,
            "createdAt": a.createdAt.isoformat()
        } for a in activities
    ]}

@app.post("/clients/{client_id}/remarks")
async def add_remark(client_id: int, data: RemarkAdd, session: Session = Depends(get_session)):
    """Add a remark for a client"""
    remark = Remark(
        content=data.content,
        clientId=client_id,
        authorId=None,
        isInternal=True
    )
    session.add(remark)
    session.commit()
    return {"success": True}

@app.get("/clients/{client_id}/remarks")
async def get_client_remarks(
    client_id: int, 
    limit: int = 50,
    session: Session = Depends(get_session)
):
    """Get remarks for a specific client with pagination"""
    statement = select(Remark).where(Remark.clientId == client_id).order_by(Remark.createdAt.desc()).limit(limit)
    remarks = session.exec(statement).all()
    return {"remarks": [
        {
            "id": r.id,
            "content": r.content,
            "createdAt": r.createdAt.isoformat()
        } for r in remarks
    ]}


@app.post("/clients/{client_id}/send-email")
async def send_client_email(
    client_id: int,
    data: EmailSend,
    session: Session = Depends(get_session)
):
    """Send an email to a client and log it as an activity"""
    profile = session.get(ClientProfile, client_id)
    if not profile or not profile.user:
        raise HTTPException(status_code=404, detail="Client or user not found")
    
    # In a real app, this would use an email service (SMTP/SendGrid)
    # For now we'll simulate success and log it
    print(f"📧 Sending email to {profile.user.email}...")
    print(f"Subject: {data.subject}")
    
    # Log as activity
    activity = ActivityLog(
        clientId=client_id,
        action="Manual Activity",
        method="Email",
        content=f"Sent Email: {data.subject}\n\n{data.body}",
        createdAt=datetime.utcnow()
    )
    session.add(activity)
    session.commit()
    
    return {"success": True}


if __name__ == "__main__":
    # Aggressively enforce ProactorEventLoop for Windows
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        loop="asyncio" # Explicitly use asyncio loop which respects policy
    )
