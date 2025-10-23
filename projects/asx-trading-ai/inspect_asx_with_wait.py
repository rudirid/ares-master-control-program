"""Inspect ASX page with proper JavaScript wait to find data source."""
import asyncio
from playwright.async_api import async_playwright
import json


async def inspect_with_wait():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        print("Loading ASX announcements page...")
        await page.goto('https://www.asx.com.au/markets/trade-our-cash-market/todays-announcements.html')

        # Wait for dynamic content to load
        print("Waiting for page to fully render...")
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(5000)

        print("\n=== Checking for announcement data ===" )

        # Try to find announcement rows after JavaScript execution
        selectors_to_try = [
            'tr[data-ticker]',
            'tr.announcement-row',
            'div.announcement-item',
            'tbody tr',
            '[data-announcement]',
            '.asx-announcement'
        ]

        for selector in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"\n[OK] Found {len(elements)} elements with selector: {selector}")

                    # Get first few for inspection
                    for i, elem in enumerate(elements[:3]):
                        html = await elem.inner_html()
                        print(f"\nElement {i+1} HTML preview:")
                        print(html[:300])
            except:
                pass

        # Check page text for company tickers
        print("\n=== Checking page text ===")
        text = await page.inner_text('body')

        # Look for common ASX tickers
        test_tickers = ['BHP', 'CBA', 'CSL', 'WBC', 'NAB', 'RIO', 'ANZ']
        found_tickers = [t for t in test_tickers if t in text]

        if found_tickers:
            print(f"[OK] Found tickers in page: {found_tickers}")
        else:
            print("[!] No common tickers found in page text")

        # Try to extract data from window object
        print("\n=== Checking JavaScript window object ===")
        try:
            window_data = await page.evaluate('''() => {
                // Look for common data patterns
                const keys = Object.keys(window).filter(k =>
                    k.toLowerCase().includes('announcement') ||
                    k.toLowerCase().includes('data') ||
                    k.toLowerCase().includes('asx')
                );

                return {
                    keys: keys,
                    hasReact: typeof window.__REACT_DEVTOOLS_GLOBAL_HOOK__ !== 'undefined',
                    hasAngular: typeof window.angular !== 'undefined',
                    hasVue: typeof window.__VUE__ !== 'undefined'
                };
            }''')

            print(f"Framework: React={window_data['hasReact']}, Angular={window_data['hasAngular']}, Vue={window_data['hasVue']}")
            if window_data['keys']:
                print(f"Window keys with 'announcement'/'data'/'asx': {window_data['keys']}")
        except Exception as e:
            print(f"[!] Error checking window: {e}")

        # Save page source after JavaScript execution
        html = await page.content()
        with open('asx_page_after_js.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("\n[OK] Saved rendered HTML to: asx_page_after_js.html")

        print("\n=== Manual Inspection ===")
        print("Browser will stay open for 2 minutes.")
        print("Open DevTools (F12) and:")
        print("1. Go to Network tab, filter by 'XHR' or 'Fetch'")
        print("2. Refresh the page")
        print("3. Look for API calls returning announcement data")
        print("4. Check Elements tab to find the table/list structure")

        await page.wait_for_timeout(120000)
        await browser.close()


asyncio.run(inspect_with_wait())
