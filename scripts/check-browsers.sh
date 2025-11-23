#!/bin/bash
set -e

echo "=== BROWSER ENVIRONMENT CHECK ==="

# Check Playwright installation
echo "Playwright version:"
python -c "import playwright; print(playwright.__version__)" 2>/dev/null || echo "Playwright not installed"

# Check browser cache
echo "Browser cache:"
ls -la ~/.cache/ms-playwright/ 2>/dev/null || echo "No browser cache found"

# Check if browsers are installed
echo "Installed browsers:"
playwright install --dry-run 2>/dev/null || echo "Cannot check browsers"

# Test basic browser functionality
echo "Testing browser launch..."
python -c "
import asyncio
from playwright.async_api import async_playwright

async def test_browser():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto('about:blank')
            await browser.close()
            print('✅ Browser test passed')
    except Exception as e:
        print(f'❌ Browser test failed: {e}')

asyncio.run(test_browser())
" 2>/dev/null || echo "Browser test skipped"

echo "=== BROWSER CHECK COMPLETE ==="
