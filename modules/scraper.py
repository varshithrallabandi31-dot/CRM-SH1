import re
import sys
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright
import asyncio
async def scrape_website(url):
    """
    Fetches the website content using Playwright to handle JS-heavy sites (Async Version).
    """
    if sys.platform == 'win32':
        loop = asyncio.get_event_loop()
        print(f"DEBUG: Current event loop type: {type(loop).__name__}")
        if 'Proactor' not in type(loop).__name__:
            print("WARNING: ProactorEventLoop is NOT being used. Playwright may fail on Windows.")

    if not url.startswith('http'):
        url = 'https://' + url
        
    print(f"DEBUG: Starting Async Playwright scrape for {url}")
    
    try:
        async with async_playwright() as p:
            # Launch browser (headless=True is default)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1280, 'height': 800}
            )
            page = await context.new_page()
            
            try:
                # Go to page and wait for load
                response = await page.goto(url, timeout=30000, wait_until='domcontentloaded')
                print(f"DEBUG: Main page status: {response.status if response else 'No Response'}")
                
                if response and response.status >= 400:
                    print(f"!!! Error: Page returned status {response.status}")
                    if response.status == 403:
                        return f"ERROR SCRAPING: Access Denied (Status 403). The website might be blocking scrapers."
                    elif response.status == 404:
                        return f"ERROR SCRAPING: Page not found (Status 404)."
                    else:
                        return f"ERROR SCRAPING: Website returned error status {response.status}."

                # Wait a bit extra for dynamic content causing network idle
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    pass # Continue even if network not fully idle
                
                # Get main content
                content = await page.content()
                
                # Setup regex extraction on RAW HTML first
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                found_emails = set(re.findall(email_pattern, content))

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                
                def clean_text(s):
                    for tag in s(["script", "style", "noscript", "svg", "iframe"]):
                        tag.extract()
                    text = s.get_text(separator=' ')
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    return '\n'.join(chunk for chunk in chunks if chunk)

                main_text = f"--- MAIN PAGE ({url}) ---\n" + clean_text(soup)

                # Find subpages
                subpages = []
                domain = urlparse(url).netloc
                
                links = soup.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    full_link = urljoin(url, href)
                    if urlparse(full_link).netloc != domain:
                        continue
                        
                    keywords = ['about', 'team', 'contact', 'people', 'leadership', 'board', 
                               'services', 'solutions', 'products', 'what-we-do', 'our-work']
                    if any(k in href.lower() for k in keywords):
                        if full_link not in subpages and full_link != url:
                            subpages.append(full_link)

                # Scrape more subpages
                combined_text = main_text
                for sub_url in subpages[:7]:
                    try:
                        print(f"DEBUG: Scraping subpage {sub_url}")
                        await page.goto(sub_url, timeout=15000, wait_until='domcontentloaded')
                        try:
                            await page.wait_for_load_state('networkidle', timeout=3000)
                        except:
                            pass
                        
                        sub_content = await page.content()
                        sub_soup = BeautifulSoup(sub_content, 'html.parser')
                        
                        sub_emails = re.findall(email_pattern, sub_content)
                        found_emails.update(sub_emails)
                        
                        combined_text += f"\n\n--- SUBPAGE ({sub_url}) ---\n" + clean_text(sub_soup)
                    except Exception as e:
                        print(f"Failed subpage {sub_url}: {e}")
            
            finally:
                await browser.close()

        # Debug Output
        if found_emails:
            print(f"DEBUG: Found {len(found_emails)} emails via Regex: {found_emails}")
            combined_text = f"--- DETECTED EMAILS (Regex): {', '.join(found_emails)} ---\n\n" + combined_text
        else:
            print("DEBUG: No emails found via Regex.")

        with open('last_scrape_debug.txt', 'w', encoding='utf-8') as f:
            f.write(combined_text)

        return combined_text[:50000]

    except Exception as e:
        print(f"!!! ERROR scraping {url}: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
        # Return more helpful error message
        error_msg = str(e).strip()
        if not error_msg:
            error_msg = f"An unknown error occurred during scraping ({type(e).__name__})."
            
        if "TimeoutError" in str(type(e)):
            error_msg = "Website took too long to load (timeout). Try again or check if the site is accessible."
        elif "SSL" in error_msg or "certificate" in error_msg:
            error_msg = "SSL certificate error. The website may have security issues."
        elif "Connection" in error_msg:
            error_msg = "Could not connect to website. Check if URL is correct and site is online."
        
        return f"ERROR SCRAPING: {error_msg}"
