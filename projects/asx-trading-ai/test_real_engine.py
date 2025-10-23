"""
Test the REAL recommendation engine on a live announcement.
This demonstrates transparent reasoning vs DEMO mode stupidity.
"""

import sqlite3
import sys
from datetime import datetime
import pytz

# Import the REAL engine
from live_trading.live_recommendation_engine import LiveRecommendationEngine

DB_PATH = 'data/trading.db'
TZ = pytz.timezone('Australia/Sydney')

def test_real_engine(announcement_id):
    """Run REAL engine on a specific announcement and show full reasoning."""

    # Initialize the REAL engine
    print("="*80)
    print("REAL RECOMMENDATION ENGINE - TRANSPARENT REASONING TEST")
    print("="*80)
    print("\nInitializing engine with intelligent 8-step analysis...")

    engine = LiveRecommendationEngine(DB_PATH)

    # Get announcement details
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, ticker, title, price_sensitive, asx_timestamp, detected_timestamp
        FROM live_announcements
        WHERE id = ?
    ''', (announcement_id,))

    ann = cursor.fetchone()
    if not ann:
        print(f"Announcement #{announcement_id} not found")
        return

    ann_id, ticker, title, ps, asx_ts, detected = ann

    print(f"\nTEST ANNOUNCEMENT:")
    print(f"  ID: {ann_id}")
    print(f"  Ticker: {ticker}")
    print(f"  Title: {title}")
    print(f"  Price Sensitive: {'YES' if ps else 'NO'}")
    print(f"  Detected: {detected}")

    conn.close()

    print("\n" + "="*80)
    print("PROCESSING WITH REAL ENGINE...")
    print("="*80 + "\n")

    # Process with REAL engine
    result = engine.process_announcement(announcement_id)

    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)

    if result:
        print(f"\n[OK] RECOMMENDATION GENERATED")
        print(f"\n  Ticker: {result['ticker']}")
        print(f"  Recommendation: {result['recommendation']}")
        print(f"  Confidence: {result['confidence']:.1%}")
        print(f"  Entry Price: ${result['entry_price']:.2f}")
        print(f"  Sentiment: {result['sentiment']} (score: {result['sentiment_score']:.2f})")

        print(f"\n  FULL DECISION LOG:")
        print(f"  " + "-"*76)
        for line in result['decision_log'].split('\n'):
            print(f"  {line}")

    else:
        print("\n[X] NO RECOMMENDATION GENERATED")
        print("\nThis announcement was REJECTED by the intelligent filters.")
        print("The engine only generates recommendations when:")
        print("  - Announcement is fresh (< 30 minutes)")
        print("  - Material enough (price-sensitive, earnings, etc.)")
        print("  - Sentiment is strong enough")
        print("  - Technical indicators align")
        print("  - Bayesian confidence > 40%")

    print("\n" + "="*80)
    print("COMPARISON TO DEMO MODE:")
    print("="*80)
    print("\nDEMO MODE would have:")
    print("  - Auto-generated BUY recommendation (no analysis)")
    print("  - Fixed 65% confidence (no calculation)")
    print("  - No decision log (no transparency)")
    print("  - No filter validation (stupidity)")
    print("\nREAL ENGINE:")
    print("  - 8-step intelligent analysis")
    print("  - Bayesian confidence calculation")
    print("  - Full decision log with reasoning")
    print("  - Strict filter validation")
    print("="*80 + "\n")


if __name__ == '__main__':
    # Test with announcement #606
    test_real_engine(606)
