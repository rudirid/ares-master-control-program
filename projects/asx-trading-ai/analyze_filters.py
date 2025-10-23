"""Analyze why announcements are being filtered out."""
import sqlite3
from collections import Counter

conn = sqlite3.connect('data/trading.db')
cursor = conn.cursor()

# Note: We don't store the filter reason in the database currently
# So let's re-run the engine with detailed logging on just one announcement

from live_trading.live_recommendation_engine import LiveRecommendationEngine
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

engine = LiveRecommendationEngine('data/trading.db')

# Get one price-sensitive announcement
cursor.execute('''
    SELECT id, ticker, title, price_sensitive
    FROM live_announcements
    WHERE price_sensitive = 1
    ORDER BY detected_timestamp DESC
    LIMIT 1
''')

row = cursor.fetchone()
if row:
    ann_id, ticker, title, ps = row
    print("="*80)
    print(f"TESTING ANNOUNCEMENT: {ticker} - {title}")
    print(f"Price Sensitive: {ps}")
    print("="*80)
    print()

    result = engine.process_announcement(ann_id)

    if result:
        print()
        print("="*80)
        print("RESULT: RECOMMENDATION GENERATED!")
        print(f"{result['ticker']} {result['recommendation']} @ ${result['entry_price']:.2f}")
        print(f"Confidence: {result['confidence']:.2f}")
        print("="*80)
    else:
        print()
        print("="*80)
        print("RESULT: NO RECOMMENDATION")
        print("(Check logs above for filter failure reason)")
        print("="*80)

conn.close()
