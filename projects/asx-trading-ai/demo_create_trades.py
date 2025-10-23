"""
DEMO MODE: Create trades from recommendations and calculate initial P&L.
"""
import sqlite3
from datetime import datetime
import pytz

DB_PATH = 'data/trading.db'
TZ = pytz.timezone('Australia/Sydney')

def create_trades_from_recommendations():
    """Create trade entries from recommendations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*80)
    print("DEMO MODE: CREATING TRADES FROM RECOMMENDATIONS")
    print("="*80)
    print()

    # Get recommendations that don't have trades yet
    cursor.execute('''
        SELECT r.id, r.announcement_id, r.ticker, r.entry_price, r.generated_timestamp
        FROM live_recommendations r
        LEFT JOIN trade_outcomes t ON r.id = t.recommendation_id
        WHERE t.id IS NULL
    ''')

    recommendations = cursor.fetchall()

    trades_created = 0

    for rec_id, ann_id, ticker, entry_price, gen_ts in recommendations:
        if not entry_price or entry_price <= 0:
            print(f"[SKIP] {ticker:6} - Invalid entry price: ${entry_price}")
            continue

        now = datetime.now(TZ)
        entry_dt = datetime.strptime(gen_ts, '%Y-%m-%d %H:%M:%S')

        # Create trade outcome entry
        cursor.execute('''
            INSERT INTO trade_outcomes (
                recommendation_id, announcement_id, ticker,
                entry_price, entry_timestamp, current_price,
                peak_price, lowest_price, status, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        ''', (
            rec_id,
            ann_id,
            ticker,
            entry_price,
            gen_ts,
            entry_price,  # current = entry initially
            entry_price,  # peak = entry initially
            entry_price,  # lowest = entry initially
            now.strftime('%Y-%m-%d %H:%M:%S')
        ))

        trade_id = cursor.lastrowid
        trades_created += 1

        print(f"[OK] Trade #{trade_id:3} created: {ticker:6} @ ${entry_price:7.2f}")

    conn.commit()
    conn.close()

    print()
    print("="*80)
    print(f"TRADES CREATED: {trades_created}")
    print("="*80)
    print()
    print("Next: Update trades with current prices to calculate P&L")
    print("="*80)

if __name__ == '__main__':
    create_trades_from_recommendations()
