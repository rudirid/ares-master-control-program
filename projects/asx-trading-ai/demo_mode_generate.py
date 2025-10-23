"""
DEMO MODE: Bypass all filters and force recommendations through.

This proves the full pipeline works:
Announcements → Recommendations → Trades → P&L

Once working, we'll re-enable filters one by one.
"""
import sqlite3
from datetime import datetime
import pytz
import yfinance as yf

DB_PATH = 'data/trading.db'
TZ = pytz.timezone('Australia/Sydney')

def get_price(ticker):
    """Get current price for ASX ticker."""
    try:
        symbol = f"{ticker}.AX"
        stock = yf.Ticker(symbol)
        hist = stock.history(period='1d')
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
        return None
    except:
        return None

def demo_generate_recommendations():
    """Generate forced recommendations from recent announcements."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*80)
    print("DEMO MODE: FORCING RECOMMENDATIONS THROUGH")
    print("="*80)
    print()

    # Get 10 most recent announcements with varied tickers
    cursor.execute('''
        SELECT id, ticker, title, price_sensitive
        FROM live_announcements
        WHERE ticker NOT IN (
            SELECT ticker FROM live_recommendations
        )
        ORDER BY detected_timestamp DESC
        LIMIT 20
    ''')

    announcements = cursor.fetchall()

    recommendations_created = 0
    target = 10

    for ann_id, ticker, title, price_sensitive in announcements:
        if recommendations_created >= target:
            break

        # Get price
        price = get_price(ticker)
        if not price:
            print(f"[SKIP] {ticker:6} - No price data available")
            continue

        # DEMO: Force as BUY with 0.65 confidence
        recommendation = 'BUY'
        confidence = 0.65
        sentiment = 'positive'
        sentiment_score = 0.7
        sentiment_confidence = 0.75

        now = datetime.now(TZ)

        # Insert recommendation
        cursor.execute('''
            INSERT INTO live_recommendations (
                announcement_id, ticker, recommendation, confidence, entry_price,
                sentiment, sentiment_score, sentiment_confidence,
                generated_timestamp, filters_passed, filters_failed, decision_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ann_id,
            ticker,
            recommendation,
            confidence,
            price,
            sentiment,
            sentiment_score,
            sentiment_confidence,
            now.strftime('%Y-%m-%d %H:%M:%S'),
            'DEMO_MODE',
            '',
            f'DEMO MODE: Forced {recommendation} recommendation for testing pipeline'
        ))

        rec_id = cursor.lastrowid
        recommendations_created += 1

        # Mark announcement as processed
        cursor.execute('''
            UPDATE live_announcements
            SET processed = 1, recommendation_generated = 1
            WHERE id = ?
        ''', (ann_id,))

        ps_marker = "[PS]" if price_sensitive else "    "
        print(f"[OK] {ps_marker} {ticker:6} {recommendation:4} @ ${price:7.2f} (conf: {confidence:.2f}) - {title[:50]}")

    conn.commit()
    conn.close()

    print()
    print("="*80)
    print(f"DEMO RECOMMENDATIONS CREATED: {recommendations_created}")
    print("="*80)
    print()
    print("Next: Run trade_tracker to create trades from these recommendations")
    print("="*80)

if __name__ == '__main__':
    demo_generate_recommendations()
