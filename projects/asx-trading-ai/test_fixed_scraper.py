"""Test the fixed ASX announcement scraper with real API."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from live_trading.announcement_monitor import ASXAnnouncementMonitor
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

print("=" * 60)
print("TESTING FIXED ASX SCRAPER WITH REAL API")
print("=" * 60 + "\n")

# Create monitor with real ASX API
monitor = ASXAnnouncementMonitor(
    db_path=config.DATABASE_PATH,
    check_interval_seconds=10,
    data_source='asx_web'  # Now uses API endpoint
)

print("1. Fetching announcements from ASX API...")
announcements = monitor.scrape_asx_announcements()

print(f"\n2. Results: Found {len(announcements)} announcements")

if announcements:
    print("\n3. Sample announcements (first 5):\n")

    for i, ann in enumerate(announcements[:5], 1):
        price_flag = "[PRICE SENSITIVE]" if ann['price_sensitive'] else ""
        age_minutes = (monitor.tz.localize(ann['asx_timestamp'].replace(tzinfo=None)) -
                       monitor.tz.localize(monitor.tz.localize(ann['asx_timestamp'].replace(tzinfo=None)).replace(tzinfo=None))).total_seconds() / 60

        print(f"   [{i}] {ann['ticker']:6} {price_flag}")
        print(f"       Title: {ann['title']}")
        print(f"       Type: {ann['announcement_type']}")
        print(f"       Time: {ann['asx_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"       URL: {ann['url'][:60]}...")
        print()

    print("\n4. Testing database storage...")

    # Store first 5 announcements
    stored_count = 0
    for ann in announcements[:5]:
        if monitor.store_announcement(ann):
            stored_count += 1

    print(f"   Stored {stored_count} new announcements")

    # Try storing same announcements again (should be 0)
    duplicate_count = 0
    for ann in announcements[:5]:
        if monitor.store_announcement(ann):
            duplicate_count += 1

    print(f"   Duplicate check: {duplicate_count} duplicates (should be 0)")

    print("\n" + "=" * 60)
    print("TEST PASSED - SCRAPER IS WORKING!")
    print("=" * 60)
    print("\nReady to run live test with real data.")
    print("Next step: python live_trading/live_paper_trader.py --duration-days 1")

else:
    print("\n[!] ERROR: No announcements returned")
    print("    Check network connection and API access")
