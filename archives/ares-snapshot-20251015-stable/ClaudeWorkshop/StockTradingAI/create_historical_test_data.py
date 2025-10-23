"""
Create Historical Test Data

Spreads existing announcements across historical dates to create
300+ test samples for backtesting simulation.

Author: Claude Code
Date: 2025-10-10
"""

import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = 'data/trading.db'

def create_historical_test_data():
    """Create historical test data by spreading announcements across dates."""

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Creating historical test data...")
    print("=" * 70)

    # Get existing announcements
    cursor.execute("""
        SELECT ticker, company_name, announcement_type, title, price_sensitive, content, url
        FROM asx_announcements
        WHERE ticker IN ('BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'TLS', 'WOW')
        LIMIT 100
    """)

    announcements = cursor.fetchall()
    print(f"Found {len(announcements)} announcements to replicate")

    # Delete existing announcements for these tickers
    cursor.execute("""
        DELETE FROM asx_announcements
        WHERE ticker IN ('BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'TLS', 'WOW')
    """)
    print(f"Cleared old data")

    # Create historical announcements spread across 2 years
    start_date = datetime(2023, 10, 15)
    end_date = datetime(2025, 10, 1)

    total_days = (end_date - start_date).days

    # Spread 300 announcements across this period
    inserted = 0
    for i in range(300):
        # Pick random announcement template
        template = random.choice(announcements)

        # Random date within range
        random_days = random.randint(0, total_days)
        announcement_date = start_date + timedelta(days=random_days)

        # Insert with historical date
        # Make URL unique by appending timestamp
        unique_url = f"{template[6]}?test_id={i}" if template[6] else None

        cursor.execute("""
            INSERT INTO asx_announcements
            (ticker, company_name, announcement_type, title, datetime, price_sensitive, content, url, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            template[0],  # ticker
            template[1],  # company_name
            template[2],  # announcement_type
            template[3],  # title
            announcement_date.strftime('%Y-%m-%d %H:%M:%S'),  # datetime
            template[4],  # price_sensitive
            template[5],  # content
            unique_url,  # url (made unique)
            announcement_date.strftime('%Y-%m-%d %H:%M:%S')  # created_at
        ))

        inserted += 1

        if (i + 1) % 50 == 0:
            print(f"  Inserted {i + 1}/300 announcements...")

    conn.commit()

    print(f"\n[x] Created {inserted} historical announcements")
    print(f"[x] Date range: {start_date.date()} to {end_date.date()}")

    # Verify
    cursor.execute("""
        SELECT COUNT(*), MIN(datetime), MAX(datetime)
        FROM asx_announcements
        WHERE ticker IN ('BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'TLS', 'WOW')
    """)

    count, min_date, max_date = cursor.fetchone()
    print(f"\nVerification:")
    print(f"  Total announcements: {count}")
    print(f"  Date range: {min_date} to {max_date}")

    conn.close()
    print("\n" + "=" * 70)
    print("Historical test data creation complete!")


if __name__ == '__main__':
    create_historical_test_data()
