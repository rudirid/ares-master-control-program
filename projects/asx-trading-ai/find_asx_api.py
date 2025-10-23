"""Find ASX announcements API by monitoring network requests."""
import asyncio
from playwright.async_api import async_playwright

async def find_api():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Track API calls
        api_urls = []

        async def log_request(request):
            if 'announcement' in request.url.lower() or 'company' in request.url.lower():
                print(f"\n[API] {request.method} {request.url}")
                api_urls.append(request.url)

        page.on('request', log_request)

        print("Loading ASX page and monitoring network...")
        await page.goto('https://www.asx.com.au/markets/trade-our-cash-market/todays-announcements.html', wait_until='networkidle')

        # Wait longer for all API calls to complete
        print("Waiting for all API calls to complete...")
        await page.wait_for_timeout(15000)

        # Try interacting with page to trigger more API calls
        print("Scrolling page to trigger lazy loading...")
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(5000)

        print("\n\n=== FOUND API ENDPOINTS ===")
        for url in set(api_urls):
            print(url)

        with open('asx_api_endpoints.txt', 'w') as f:
            for url in set(api_urls):
                f.write(url + '\n')

        print("\nSaved to asx_api_endpoints.txt")

        if api_urls:
            print("\nNow testing API endpoint directly...")
            # Try to fetch from the most promising endpoint
            for url in set(api_urls):
                if 'announcement' in url.lower():
                    print(f"\nTesting: {url}")
                    response = await page.request.get(url)
                    print(f"Status: {response.status}")
                    if response.status == 200:
                        text = await response.text()
                        print(f"Response preview: {text[:500]}...")

        print("\nBrowser stays open - inspect Network tab")
        await page.wait_for_timeout(60000)
        await browser.close()

asyncio.run(find_api())
