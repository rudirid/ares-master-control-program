"""Inspect ASX announcements page to find correct selectors."""
import asyncio
from playwright.async_api import async_playwright

async def inspect_asx():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Loading ASX announcements page...")
        await page.goto('https://www.asx.com.au/markets/trade-our-cash-market/todays-announcements.html', timeout=30000)

        await page.wait_for_load_state('networkidle')

        # Save page content
        html = await page.content()
        with open('asx_page_source.html', 'w', encoding='utf-8') as f:
            f.write(html)

        print("\n=== Page Structure ===")

        # Check for tables
        tables = await page.query_selector_all('table')
        print(f"Found {len(tables)} tables")

        # Check for announcement containers
        divs_with_announcement = await page.query_selector_all('div[class*="announcement"]')
        print(f"Found {len(divs_with_announcement)} divs with 'announcement' in class")

        # Check for data attributes
        data_elements = await page.query_selector_all('[data-announcement], [data-company], [data-ticker]')
        print(f"Found {len(data_elements)} elements with data attributes")

        # Try to find any text that looks like announcements
        text = await page.inner_text('body')
        if 'BHP' in text or 'CBA' in text:
            print("\n✓ Page contains company tickers")

        print("\n=== Saved page source to asx_page_source.html ===")
        print("Browser will stay open. Inspect the page and press Enter to close...")

        await asyncio.get_event_loop().run_in_executor(None, input)
        await browser.close()

asyncio.run(inspect_asx())
