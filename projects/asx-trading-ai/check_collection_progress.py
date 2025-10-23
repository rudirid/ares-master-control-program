"""Quick progress check for ongoing data collection."""
import sqlite3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from datetime import datetime, timedelta
import pytz

tz = pytz.timezone('Australia/Sydney')

def check_progress():
    """Check current collection progress."""
    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()

    print("=" * 60)
    print("ASX ANNOUNCEMENT COLLECTION PROGRESS")
    print("=" * 60 + "\n")

    # Total count
    cursor.execute("SELECT COUNT(*) FROM live_announcements")
    total = cursor.fetchone()[0]

    # Price sensitive count
    cursor.execute("SELECT COUNT(*) FROM live_announcements WHERE price_sensitive = 1")
    sensitive = cursor.fetchone()[0]

    # Unique companies
    cursor.execute("SELECT COUNT(DISTINCT ticker) FROM live_announcements")
    companies = cursor.fetchone()[0]

    print(f"Total Announcements: {total}")
    print(f"Price Sensitive: {sensitive} ({sensitive/total*100:.1f}%)")
    print(f"Unique Companies: {companies}")
    print()

    # Recent announcements (last 10)
    print("=" * 60)
    print("LATEST 10 ANNOUNCEMENTS")
    print("=" * 60 + "\n")

    cursor.execute("""
        SELECT ticker, title, price_sensitive, age_minutes, detected_timestamp
        FROM live_announcements
        ORDER BY detected_timestamp DESC
        LIMIT 10
    """)

    for i, (ticker, title, ps, age, detected) in enumerate(cursor.fetchall(), 1):
        ps_flag = "[PRICE SENSITIVE]" if ps else ""
        print(f"{i}. {ticker:6} {ps_flag}")
        print(f"   {title[:60]}...")
        print(f"   Age: {age:.1f} min | Detected: {detected}")
        print()

    # Age distribution
    print("=" * 60)
    print("AGE DISTRIBUTION")
    print("=" * 60 + "\n")

    cursor.execute("""
        SELECT
            COUNT(CASE WHEN age_minutes < 5 THEN 1 END) as fresh,
            COUNT(CASE WHEN age_minutes BETWEEN 5 AND 15 THEN 1 END) as recent,
            COUNT(CASE WHEN age_minutes BETWEEN 15 AND 30 THEN 1 END) as older,
            COUNT(CASE WHEN age_minutes > 30 THEN 1 END) as old
        FROM live_announcements
    """)

    fresh, recent, older, old = cursor.fetchone()

    print(f"Fresh (< 5 min):     {fresh:3} - Optimal alpha window")
    print(f"Recent (5-15 min):   {recent:3} - Good alpha")
    print(f"Older (15-30 min):   {older:3} - Some alpha")
    print(f"Old (> 30 min):      {old:3} - Limited alpha")
    print()

    # Collection timeline
    print("=" * 60)
    print("COLLECTION TIMELINE")
    print("=" * 60 + "\n")

    cursor.execute("""
        SELECT MIN(detected_timestamp), MAX(detected_timestamp)
        FROM live_announcements
    """)

    start, end = cursor.fetchone()
    if start and end:
        start_dt = datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
        duration = (end_dt - start_dt).total_seconds() / 3600

        print(f"Collection Started: {start}")
        print(f"Last Announcement:  {end}")
        print(f"Duration: {duration:.1f} hours")
        print()

    # Target progress
    target = 50
    progress_pct = (total / target) * 100

    print("=" * 60)
    print("TARGET PROGRESS")
    print("=" * 60 + "\n")

    print(f"Target: {target} announcements")
    print(f"Current: {total} announcements")
    print(f"Progress: {progress_pct:.1f}%")

    if total >= target:
        print("\n✓ TARGET REACHED!")
        print("You have enough data to calculate IC after 7-day holding period.")
    else:
        remaining = target - total
        print(f"\nRemaining: {remaining} announcements needed")

    print()

    # Market status
    now = datetime.now(tz)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    hours_left = (market_close - now).total_seconds() / 3600

    print("=" * 60)
    print("MARKET STATUS")
    print("=" * 60 + "\n")

    print(f"Current Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Market Close: 4:00 PM AEST")

    if hours_left > 0:
        print(f"Time Remaining: {hours_left:.1f} hours")
        print("\nCollection is ACTIVE and running in background.")
    else:
        print("\nMarket is CLOSED. Collection will resume tomorrow.")

    print()

    conn.close()

if __name__ == '__main__':
    check_progress()
