from playwright.sync_api import sync_playwright
import os

print(f"DEBUG: HOME={os.getenv('HOME')}")
print(f"DEBUG: USERPROFILE={os.getenv('USERPROFILE')}")

try:
    with sync_playwright() as p:
        print("DEBUG: Launching browser...")
        browser = p.chromium.launch(headless=True)
        print("DEBUG: Browser launched successfully!")
        page = browser.new_page()
        page.goto("https://www.google.com")
        print(f"DEBUG: Page title: {page.title()}")
        browser.close()
except Exception as e:
    print(f"!!! Error in Playwright: {e}")
    import traceback
    traceback.print_exc()
