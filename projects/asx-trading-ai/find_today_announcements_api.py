"""Find API endpoint for today's announcements across all companies."""
import requests
import json
from datetime import datetime, timedelta


def test_today_announcements():
    """Test endpoints for today's announcements."""

    print("=" * 60)
    print("FINDING TODAY'S ANNOUNCEMENTS API")
    print("=" * 60 + "\n")

    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    endpoints = [
        # Try different variations
        "https://asx.api.markitdigital.com/asx-research/1.0/announcements/recent",
        f"https://asx.api.markitdigital.com/asx-research/1.0/announcements/today",
        f"https://asx.api.markitdigital.com/asx-research/1.0/announcements/date/{today}",
        f"https://asx.api.markitdigital.com/asx-research/1.0/announcements?from={today}",
        f"https://asx.api.markitdigital.com/asx-research/1.0/announcements?date={today}",

        # Try market data endpoints
        "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements",
        "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements/recent",
        "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements/today",

        # Try feed endpoints
        "https://asx.api.markitdigital.com/asx-research/1.0/feed/announcements",
        "https://asx.api.markitdigital.com/asx-research/1.0/feed/announcements/latest",

        # Try search endpoint
        f"https://asx.api.markitdigital.com/asx-research/1.0/search/announcements?date={today}",

        # Try old ASX direct endpoints with date
        f"https://www.asx.com.au/asx/statistics/announcements.do?by=asxCode&timeframe=D&year={datetime.now().year}",

        # Try without authentication header (public endpoint)
        "https://asx.api.markitdigital.com/asx-research/1.0/companies",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.asx.com.au/markets/trade-our-cash-market/todays-announcements.html',
        'Origin': 'https://www.asx.com.au'
    }

    success_count = 0

    for i, url in enumerate(endpoints, 1):
        print(f"\n[{i}] {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            status = response.status_code

            if status == 200:
                content_type = response.headers.get('Content-Type', '')

                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"    [OK] Status 200 - JSON response")

                        # Check structure
                        if isinstance(data, dict):
                            keys = list(data.keys())[:5]
                            print(f"    Keys: {keys}")

                            # Look for announcement indicators
                            if any(k in str(data) for k in ['announcement', 'items', 'data', 'results']):
                                print("    [SUCCESS] Contains announcement data!")
                                success_count += 1

                                filename = f'today_announcements_{success_count}.json'
                                with open(filename, 'w') as f:
                                    json.dump(data, f, indent=2)
                                print(f"    Saved to: {filename}")

                                # Show preview
                                preview = json.dumps(data, indent=2)[:300]
                                print(f"    Preview:\n{preview}...")

                        elif isinstance(data, list):
                            print(f"    [OK] List with {len(data)} items")
                            if data:
                                print(f"    First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'Not a dict'}")

                    except json.JSONDecodeError:
                        print(f"    [!] Not valid JSON")
                else:
                    text_preview = response.text[:150]
                    print(f"    [OK] Status 200 - {content_type}")
                    print(f"    Preview: {text_preview}...")

            elif status == 401:
                print("    [401] Unauthorized")
            elif status == 403:
                print("    [403] Forbidden")
            elif status == 404:
                print("    [404] Not found")
            else:
                print(f"    [{status}] {response.reason}")

        except requests.RequestException as e:
            print(f"    [!] Error: {e}")

    print("\n" + "=" * 60)
    print(f"FOUND {success_count} WORKING ENDPOINTS")
    print("=" * 60)

    if success_count == 0:
        print("\nNone of the tested endpoints returned announcement data.")
        print("The API likely requires either:")
        print("1. Authentication token/API key")
        print("2. Different endpoint structure")
        print("3. Access from ASX website context only")
        print("\nRecommendation: Use Playwright to scrape the rendered page")


if __name__ == '__main__':
    test_today_announcements()
