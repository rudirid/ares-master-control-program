"""
Generate Sample Recommendations and Trade Outcomes

Creates realistic sample data for demonstration purposes showing:
- Announcements → Recommendations → Trade Outcomes → P&L

Author: Claude Code
Date: 2025-10-15
"""

import sqlite3
from datetime import datetime, timedelta
import random
import pytz

DB_PATH = 'data/trading.db'
TZ = pytz.timezone('Australia/Sydney')


def generate_sample_data():
    """Generate sample recommendations and outcomes."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Sample ASX stocks with realistic prices
    stocks = [
        ('BHP', 45.20, 'Quarterly Production Report', True, 0.82),
        ('CBA', 108.50, 'Trading Update - FY25', True, 0.75),
        ('WES', 62.30, 'Earnings Beat Expectations', True, 0.88),
        ('RIO', 122.40, 'Iron Ore Price Increase Announcement', True, 0.71),
        ('CSL', 289.60, 'New Product Approval', True, 0.79),
        ('WOW', 38.90, 'Sales Update Q3', True, 0.65),
        ('NAB', 32.15, 'Dividend Increase Announced', True, 0.73),
        ('FMG', 22.80, 'Production Guidance Upgrade', True, 0.81),
        ('ANZ', 28.45, 'Strategic Partnership Announcement', True, 0.68),
        ('TLS', 4.12, 'Major Contract Win', True, 0.76),
    ]

    base_time = datetime.now(TZ) - timedelta(days=3)  # 3 days ago

    print("="*80)
    print("GENERATING SAMPLE TRADE DATA")
    print("="*80)
    print()

    # Get some recent announcements to link to
    cursor.execute('''
        SELECT id, ticker, title
        FROM live_announcements
        WHERE price_sensitive = 1
        LIMIT 20
    ''')
    announcements = cursor.fetchall()

    if not announcements:
        print("No price-sensitive announcements found. Using synthetic announcements.")
        # Create synthetic announcements
        for i, (ticker, price, title, ps, conf) in enumerate(stocks):
            ann_time = base_time + timedelta(hours=i*2)
            cursor.execute('''
                INSERT INTO live_announcements (
                    ticker, title, announcement_type, price_sensitive,
                    asx_timestamp, detected_timestamp, age_minutes, processed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ticker, title, 'Progress Report', 1,
                ann_time.strftime('%Y-%m-%d %H:%M:%S'),
                ann_time.strftime('%Y-%m-%d %H:%M:%S'),
                2.5, 1
            ))
        conn.commit()

        # Re-fetch
        cursor.execute('SELECT id, ticker, title FROM live_announcements ORDER BY id DESC LIMIT 10')
        announcements = cursor.fetchall()

    # Generate recommendations
    recommendations_created = 0

    for i, (ticker, entry_price, title, ps, confidence) in enumerate(stocks[:10]):
        if i < len(announcements):
            ann_id, ann_ticker, ann_title = announcements[i]
        else:
            continue

        # Use announcement's ticker if available, otherwise use stock ticker
        use_ticker = ann_ticker if ann_ticker else ticker

        rec_time = base_time + timedelta(hours=i*2, minutes=5)

        # Determine recommendation type (80% BUY for demonstration)
        recommendation = 'BUY' if random.random() < 0.8 else 'SELL'
        sentiment = 'POSITIVE' if recommendation == 'BUY' else 'NEGATIVE'

        cursor.execute('''
            INSERT INTO live_recommendations (
                announcement_id, ticker, recommendation, confidence,
                entry_price, sentiment, sentiment_score, sentiment_confidence,
                generated_timestamp, filters_passed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ann_id, use_ticker, recommendation, confidence,
            entry_price, sentiment, 0.85, 0.92,
            rec_time.strftime('%Y-%m-%d %H:%M:%S'),
            'TIME,MATERIALITY,SENTIMENT,TECHNICAL'
        ))

        rec_id = cursor.lastrowid
        recommendations_created += 1

        # Generate trade outcome
        # Simulate realistic price movements
        days_held = random.randint(1, 5)

        # 60% win rate simulation
        is_winner = random.random() < 0.6

        if is_winner:
            # Winning trade: 2% to 15% gain
            return_pct = random.uniform(2.0, 15.0)
            exit_price = entry_price * (1 + return_pct/100)
            outcome = 'WIN'
            exit_reason = 'TAKE_PROFIT_10PCT' if return_pct >= 10 else 'TIME_STOP_7DAYS'
        else:
            # Losing trade: -1% to -5% loss
            return_pct = random.uniform(-5.0, -1.0)
            exit_price = entry_price * (1 + return_pct/100)
            outcome = 'LOSS'
            exit_reason = 'STOP_LOSS_5PCT' if return_pct <= -4 else 'TIME_STOP_7DAYS'

        return_dollars = exit_price - entry_price

        # Peak and lowest during trade
        if is_winner:
            peak_pct = random.uniform(return_pct, return_pct + 3)
            lowest_pct = random.uniform(-2, return_pct * 0.3)
        else:
            peak_pct = random.uniform(0, 2)
            lowest_pct = random.uniform(return_pct, return_pct * 1.2)

        peak_price = entry_price * (1 + peak_pct/100)
        lowest_price = entry_price * (1 + lowest_pct/100)

        exit_time = rec_time + timedelta(days=days_held)

        cursor.execute('''
            INSERT INTO trade_outcomes (
                recommendation_id, announcement_id, ticker,
                entry_price, entry_timestamp, current_price,
                peak_price, lowest_price, exit_price, exit_timestamp,
                exit_reason, return_pct, return_dollars, holding_days,
                max_gain_pct, max_drawdown_pct, status, outcome, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            rec_id, ann_id, use_ticker,
            entry_price, rec_time.strftime('%Y-%m-%d %H:%M:%S'),
            exit_price, peak_price, lowest_price, exit_price,
            exit_time.strftime('%Y-%m-%d %H:%M:%S'),
            exit_reason, return_pct, return_dollars, days_held,
            peak_pct, lowest_pct, 'CLOSED', outcome,
            exit_time.strftime('%Y-%m-%d %H:%M:%S')
        ))

        print(f"[OK] {use_ticker:6} {recommendation:4} @ ${entry_price:7.2f} -> ${exit_price:7.2f} "
              f"= {return_pct:+6.2f}% ({outcome}) [{days_held}d]")

    conn.commit()
    conn.close()

    print()
    print("="*80)
    print(f"SAMPLE DATA GENERATED")
    print("="*80)
    print(f"Recommendations: {recommendations_created}")
    print(f"Trade Outcomes: {recommendations_created}")
    print()
    print("Run the dashboard to see P&L results!")
    print("="*80)


if __name__ == '__main__':
    generate_sample_data()
