import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def main():
    print(f"DEBUG: HOME={os.getenv('HOME')}")
    print(f"DEBUG: USERPROFILE={os.getenv('USERPROFILE')}")
    print(f"DEBUG: sys.platform={sys.platform}")
    
    try:
        print("DEBUG: Launching async Playwright...")
        async with async_playwright() as p:
            print("DEBUG: Context manager entered.")
            browser = await p.chromium.launch(headless=True)
            print("DEBUG: Browser launched successfully!")
            page = await browser.new_page()
            await page.goto("https://www.google.com")
            print(f"DEBUG: Page title: {await page.title()}")
            await browser.close()
    except Exception as e:
        print(f"!!! Error in Async Playwright: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    asyncio.run(main())
