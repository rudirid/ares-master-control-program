"""Test direct API calls to ASX endpoints."""
import requests
import json
from datetime import datetime


def test_asx_api():
    """Try different ASX API endpoints."""

    print("=" * 60)
    print("TESTING ASX API ENDPOINTS")
    print("=" * 60 + "\n")

    # Potential API endpoints based on ASX structure
    endpoints_to_test = [
        # Market announcements
        "https://asx.api.markitdigital.com/asx-research/1.0/announcements/",
        "https://asx.api.markitdigital.com/asx-research/1.0/companies/announcements",
        "https://www.asx.com.au/asx/1/company//announcements",
        "https://www.asx.com.au/asx/v2/statistics/announcements.csv",
        "https://www.asx.com.au/asx/1/announcement/recent",
        "https://asx.api.markitdigital.com/asx-research-auth/1.0/announcements",

        # Try with date params
        f"https://www.asx.com.au/asx/statistics/announcements.do?timeframe=D&year={datetime.now().year}",

        # Research API
        "https://www.asx.com.au/asx/1/share/BHP/company-announcements",
        "https://asx.api.markitdigital.com/asx-research/1.0/companies/BHP/announcements",
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.asx.com.au/markets/trade-our-cash-market/todays-announcements.html'
    }

    for i, url in enumerate(endpoints_to_test, 1):
        print(f"\n[{i}] Testing: {url}")

        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"    Status: {response.status_code}")

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                print(f"    Content-Type: {content_type}")

                # Try to parse as JSON
                if 'json' in content_type:
                    try:
                        data = response.json()
                        print(f"    JSON Response: {json.dumps(data, indent=2)[:500]}...")

                        # Check if it contains announcement data
                        if isinstance(data, dict):
                            if 'data' in data or 'announcements' in data or 'results' in data:
                                print("    [SUCCESS] Found announcement data!")
                                print(f"    Full response saved to: asx_api_response_{i}.json")
                                with open(f'asx_api_response_{i}.json', 'w') as f:
                                    json.dump(data, f, indent=2)
                    except json.JSONDecodeError:
                        print("    [!] Not valid JSON")
                        print(f"    Text preview: {response.text[:200]}...")
                else:
                    print(f"    Text preview: {response.text[:200]}...")

                    # Check for CSV
                    if '.csv' in url or 'text/csv' in content_type:
                        print("    [CSV] Saving to file...")
                        with open(f'asx_api_response_{i}.csv', 'w', encoding='utf-8') as f:
                            f.write(response.text)

            elif response.status_code == 404:
                print("    [404] Not found")
            elif response.status_code == 401:
                print("    [401] Unauthorized - needs authentication")
            elif response.status_code == 403:
                print("    [403] Forbidden")
            else:
                print(f"    [!] Error: {response.status_code}")

        except requests.RequestException as e:
            print(f"    [!] Request failed: {e}")
        except Exception as e:
            print(f"    [!] Error: {e}")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    test_asx_api()
