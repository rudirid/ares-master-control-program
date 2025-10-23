"""
LIVE FULL SYSTEM: Real-time trading with auto-generation

This runs the COMPLETE pipeline:
1. Monitors ASX announcements every 10 seconds
2. Generates recommendations (DEMO MODE - bypasses filters for testing)
3. Creates trades automatically
4. Updates P&L every 60 seconds with real prices from yfinance
5. Auto-closes trades based on exit rules

Run for 48 hours to collect real data.
"""

import sqlite3
import time
import logging
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from live_trading.announcement_monitor import ASXAnnouncementMonitor
from live_trading.trade_tracker import TradeTracker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/live_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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
    except Exception as e:
        logger.debug(f"Price fetch error for {ticker}: {e}")
        return None


def generate_demo_recommendation(announcement_id, ticker, title, price_sensitive):
    """Generate a DEMO recommendation (bypass filters for testing)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if already has recommendation
        cursor.execute('''
            SELECT id FROM live_recommendations WHERE announcement_id = ?
        ''', (announcement_id,))

        if cursor.fetchone():
            return None

        # Get price
        price = get_price(ticker)
        if not price or price <= 0:
            logger.debug(f"[SKIP] {ticker} - No valid price")
            return None

        # Force BUY recommendation
        recommendation = 'BUY'
        confidence = 0.65
        sentiment = 'positive'

        now = datetime.now(TZ)

        cursor.execute('''
            INSERT INTO live_recommendations (
                announcement_id, ticker, recommendation, confidence, entry_price,
                sentiment, sentiment_score, sentiment_confidence,
                generated_timestamp, filters_passed, filters_failed, decision_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            announcement_id, ticker, recommendation, confidence, price,
            sentiment, 0.7, 0.75,
            now.strftime('%Y-%m-%d %H:%M:%S'),
            'DEMO_MODE_LIVE',
            '',
            f'LIVE DEMO: Auto-generated {recommendation} for real-time testing'
        ))

        rec_id = cursor.lastrowid

        # Mark announcement as processed
        cursor.execute('''
            UPDATE live_announcements
            SET processed = 1, recommendation_generated = 1
            WHERE id = ?
        ''', (announcement_id,))

        conn.commit()

        ps = "[PS]" if price_sensitive else "    "
        logger.info(f"  [REC] {ps} {ticker:6} {recommendation:4} @ ${price:7.2f} (conf: {confidence:.2f})")

        return rec_id

    finally:
        conn.close()


def create_trade_from_recommendation(rec_id):
    """Create trade from recommendation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if trade already exists
        cursor.execute('''
            SELECT id FROM trade_outcomes WHERE recommendation_id = ?
        ''', (rec_id,))

        if cursor.fetchone():
            return None

        # Get recommendation details
        cursor.execute('''
            SELECT announcement_id, ticker, entry_price, generated_timestamp
            FROM live_recommendations
            WHERE id = ?
        ''', (rec_id,))

        row = cursor.fetchone()
        if not row:
            return None

        announcement_id, ticker, entry_price, gen_ts = row

        if not entry_price or entry_price <= 0:
            return None

        now = datetime.now(TZ)

        cursor.execute('''
            INSERT INTO trade_outcomes (
                recommendation_id, announcement_id, ticker,
                entry_price, entry_timestamp, current_price,
                peak_price, lowest_price, status, last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        ''', (
            rec_id, announcement_id, ticker,
            entry_price, gen_ts, entry_price,
            entry_price, entry_price,
            now.strftime('%Y-%m-%d %H:%M:%S')
        ))

        trade_id = cursor.lastrowid
        conn.commit()

        logger.info(f"  [TRADE] #{trade_id:3} created: {ticker:6} @ ${entry_price:7.2f}")

        return trade_id

    finally:
        conn.close()


def run_live_system(duration_hours=48):
    """
    Run the full live system.

    Args:
        duration_hours: How long to run (default 48h = 2 days)
    """
    logger.info("="*80)
    logger.info("LIVE FULL TRADING SYSTEM")
    logger.info("="*80)
    logger.info(f"Duration: {duration_hours} hours (2 days)")
    logger.info("Pipeline: Announcements → Recommendations → Trades → P&L")
    logger.info("Mode: DEMO (auto-generate for testing)")
    logger.info("Dashboard: http://localhost:8000")
    logger.info("="*80)
    logger.info("")

    # Initialize components
    monitor = ASXAnnouncementMonitor(
        db_path=DB_PATH,
        check_interval_seconds=5,  # 5 seconds (2x faster - well within API limits)
        data_source='asx_web'
    )
    tracker = TradeTracker(DB_PATH)

    start_time = time.time()
    end_time = start_time + (duration_hours * 3600)

    cycle = 0
    total_new_announcements = 0
    total_recommendations = 0
    total_trades = 0

    last_pnl_update = time.time()
    PNL_UPDATE_INTERVAL = 10  # Update P&L every 10 seconds (6x faster than before)

    try:
        while time.time() < end_time:
            cycle += 1
            now = datetime.now(TZ)

            logger.info(f"\n{'='*80}")
            logger.info(f"CYCLE #{cycle} - {now.strftime('%H:%M:%S')}")
            logger.info(f"{'='*80}")

            # Step 1: Fetch announcements
            announcements = monitor.fetch_announcements()

            if announcements:
                logger.info(f"[ANNOUNCEMENTS] Fetched {len(announcements)} from ASX")

                # Step 2: Store new ones
                new_announcements = []
                for ann in announcements:
                    if monitor.store_announcement(ann):
                        new_announcements.append(ann)
                        total_new_announcements += 1

                if new_announcements:
                    logger.info(f"[NEW] {len(new_announcements)} new announcements")

                    # Step 3: Generate recommendations (DEMO MODE)
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()

                    for ann in new_announcements:
                        # Get announcement details from DB
                        cursor.execute('''
                            SELECT id, ticker, title, price_sensitive
                            FROM live_announcements
                            WHERE ticker = ? AND title = ?
                            ORDER BY detected_timestamp DESC
                            LIMIT 1
                        ''', (ann['ticker'], ann['title']))

                        row = cursor.fetchone()
                        if row:
                            ann_id, ticker, title, price_sensitive = row

                            rec_id = generate_demo_recommendation(ann_id, ticker, title, price_sensitive)

                            if rec_id:
                                total_recommendations += 1

                                # Step 4: Create trade immediately
                                trade_id = create_trade_from_recommendation(rec_id)
                                if trade_id:
                                    total_trades += 1

                    conn.close()

            # Step 5: Update P&L periodically
            if time.time() - last_pnl_update >= PNL_UPDATE_INTERVAL:
                logger.info("\n[P&L] Updating prices...")
                updated = tracker.update_open_trades()

                if updated > 0:
                    logger.info(f"[P&L] Updated {updated} trades")

                    # Show current P&L
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT
                            COUNT(*) as open_trades,
                            SUM(return_dollars) as total_pnl,
                            AVG(return_pct) as avg_return
                        FROM trade_outcomes
                        WHERE status = 'OPEN'
                    ''')
                    open_trades, total_pnl, avg_return = cursor.fetchone()
                    total_pnl = total_pnl or 0
                    avg_return = avg_return or 0

                    cursor.execute('''
                        SELECT COUNT(*), outcome
                        FROM trade_outcomes
                        WHERE status = 'CLOSED'
                        GROUP BY outcome
                    ''')
                    closed = dict(cursor.fetchall())
                    conn.close()

                    wins = closed.get('WIN', 0)
                    losses = closed.get('LOSS', 0)

                    logger.info(f"[P&L] Open: {open_trades} | Total: ${total_pnl:+.2f} | Avg: {avg_return:+.2f}%")
                    if wins or losses:
                        logger.info(f"[P&L] Closed: {wins} wins, {losses} losses")

                last_pnl_update = time.time()

            # Stats
            elapsed_hours = (time.time() - start_time) / 3600
            remaining_hours = (end_time - time.time()) / 3600

            logger.info(f"\n[STATS] Elapsed: {elapsed_hours:.1f}h | Remaining: {remaining_hours:.1f}h")
            logger.info(f"[STATS] New Announcements: {total_new_announcements} | Recs: {total_recommendations} | Trades: {total_trades}")

            # Wait 5 seconds before next cycle (2x faster monitoring)
            time.sleep(5)

    except KeyboardInterrupt:
        logger.info("\n\nStopped by user (Ctrl+C)")

    finally:
        # Final stats
        elapsed_hours = (time.time() - start_time) / 3600

        logger.info("\n" + "="*80)
        logger.info("LIVE SYSTEM STOPPED")
        logger.info("="*80)
        logger.info(f"Duration: {elapsed_hours:.2f} hours")
        logger.info(f"New Announcements: {total_new_announcements}")
        logger.info(f"Recommendations: {total_recommendations}")
        logger.info(f"Trades: {total_trades}")

        # Final P&L
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                COUNT(*) as open_trades,
                SUM(return_dollars) as total_pnl
            FROM trade_outcomes
            WHERE status = 'OPEN'
        ''')
        open_trades, total_pnl = cursor.fetchone()
        total_pnl = total_pnl or 0

        cursor.execute('''
            SELECT COUNT(*), outcome
            FROM trade_outcomes
            WHERE status = 'CLOSED'
            GROUP BY outcome
        ''')

        closed_trades = cursor.fetchall()
        conn.close()

        logger.info(f"\nOpen Trades: {open_trades} (P&L: ${total_pnl:+.2f})")
        for count, outcome in closed_trades:
            logger.info(f"Closed {outcome}: {count}")

        logger.info("="*80)
        logger.info("\nView dashboard: http://localhost:8000")
        logger.info("="*80)


if __name__ == '__main__':
    # Run for 48 hours (2 days)
    run_live_system(duration_hours=48)
