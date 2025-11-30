import os
import sys

print("=== CI DIAGNOSTICS ===")
print(f"Python: {sys.version}")
print(f"OS: {os.uname() if hasattr(os, 'uname') else 'N/A'}")
print(f"Current dir: {os.getcwd()}")
print(f"Files in current dir: {os.listdir('.')}")

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        print("✅ Playwright browsers work")
        browser.close()
except Exception as e:
    print(f"❌ Playwright failed: {e}")

try:
    import src
    print("✅ Source imports work")
except Exception as e:
    print(f"❌ Source import failed: {e}")
