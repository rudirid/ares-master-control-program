"""
Trade Outcome Tracker

Links announcements → recommendations → trade outcomes
Calculates win/loss performance and tracks actual returns.

Author: Claude Code
Date: 2025-10-15
"""

import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import logging

logger = logging.getLogger(__name__)


class TradeTracker:
    """Track trade outcomes and calculate win/loss performance."""

    def __init__(self, db_path='data/trading.db'):
        self.db_path = db_path
        self.tz = pytz.timezone('Australia/Sydney')
        self._create_outcomes_table()

    def _create_outcomes_table(self):
        """Create trade outcomes table if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trade_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id INTEGER NOT NULL,
                announcement_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                entry_price REAL NOT NULL,
                entry_timestamp TIMESTAMP NOT NULL,

                -- Exit data
                current_price REAL,
                peak_price REAL,
                lowest_price REAL,
                exit_price REAL,
                exit_timestamp TIMESTAMP,
                exit_reason TEXT,

                -- Performance metrics
                return_pct REAL,
                return_dollars REAL,
                holding_days INTEGER,
                max_gain_pct REAL,
                max_drawdown_pct REAL,

                -- Status
                status TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED, STOPPED
                outcome TEXT,  -- WIN, LOSS, BREAKEVEN

                -- Metadata
                last_updated TIMESTAMP,

                FOREIGN KEY (recommendation_id) REFERENCES live_recommendations(id),
                FOREIGN KEY (announcement_id) REFERENCES live_announcements(id)
            )
        ''')

        conn.commit()
        conn.close()

        logger.info("Trade outcomes table ready")

    def create_trade_from_recommendation(self, recommendation_id):
        """
        Create a new trade tracking entry from a recommendation.

        Args:
            recommendation_id: ID from live_recommendations table

        Returns:
            Trade ID or None if already exists
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get recommendation details
            cursor.execute('''
                SELECT announcement_id, ticker, entry_price, generated_timestamp
                FROM live_recommendations
                WHERE id = ?
            ''', (recommendation_id,))

            row = cursor.fetchone()
            if not row:
                logger.warning(f"Recommendation {recommendation_id} not found")
                return None

            announcement_id, ticker, entry_price, generated_ts = row

            # Check if trade already exists
            cursor.execute('''
                SELECT id FROM trade_outcomes
                WHERE recommendation_id = ?
            ''', (recommendation_id,))

            if cursor.fetchone():
                logger.info(f"Trade already exists for recommendation {recommendation_id}")
                return None

            # Create trade
            now = datetime.now(self.tz)

            cursor.execute('''
                INSERT INTO trade_outcomes (
                    recommendation_id, announcement_id, ticker,
                    entry_price, entry_timestamp, current_price,
                    peak_price, lowest_price, status, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
            ''', (
                recommendation_id, announcement_id, ticker,
                entry_price, generated_ts, entry_price,
                entry_price, entry_price, now.strftime('%Y-%m-%d %H:%M:%S')
            ))

            trade_id = cursor.lastrowid
            conn.commit()

            logger.info(f"Created trade {trade_id} for {ticker} @ ${entry_price}")
            return trade_id

        finally:
            conn.close()

    def update_open_trades(self):
        """
        Update all open trades with current market prices.

        Returns:
            Number of trades updated
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get all open trades
            cursor.execute('''
                SELECT id, ticker, entry_price, entry_timestamp
                FROM trade_outcomes
                WHERE status = 'OPEN'
            ''')

            trades = cursor.fetchall()
            updated_count = 0

            for trade_id, ticker, entry_price, entry_ts in trades:
                try:
                    # Fetch current price
                    current_price = self._get_current_price(ticker)

                    if current_price is None:
                        logger.warning(f"Could not fetch price for {ticker}")
                        continue

                    # Calculate metrics
                    entry_dt = datetime.strptime(entry_ts, '%Y-%m-%d %H:%M:%S')
                    entry_dt = self.tz.localize(entry_dt)
                    now = datetime.now(self.tz)
                    holding_days = (now - entry_dt).days

                    return_pct = ((current_price - entry_price) / entry_price) * 100
                    return_dollars = current_price - entry_price

                    # Update peak and lowest
                    cursor.execute('''
                        SELECT peak_price, lowest_price
                        FROM trade_outcomes
                        WHERE id = ?
                    ''', (trade_id,))

                    peak, lowest = cursor.fetchone()

                    new_peak = max(peak or entry_price, current_price)
                    new_lowest = min(lowest or entry_price, current_price)

                    max_gain_pct = ((new_peak - entry_price) / entry_price) * 100
                    max_drawdown_pct = ((new_lowest - entry_price) / entry_price) * 100

                    # Update trade
                    cursor.execute('''
                        UPDATE trade_outcomes
                        SET current_price = ?,
                            peak_price = ?,
                            lowest_price = ?,
                            return_pct = ?,
                            return_dollars = ?,
                            holding_days = ?,
                            max_gain_pct = ?,
                            max_drawdown_pct = ?,
                            last_updated = ?
                        WHERE id = ?
                    ''', (
                        current_price, new_peak, new_lowest,
                        return_pct, return_dollars, holding_days,
                        max_gain_pct, max_drawdown_pct,
                        now.strftime('%Y-%m-%d %H:%M:%S'),
                        trade_id
                    ))

                    updated_count += 1

                    # Auto-close trade based on rules
                    self._check_exit_conditions(trade_id, ticker, entry_price,
                                                current_price, return_pct,
                                                holding_days, cursor)

                except Exception as e:
                    logger.error(f"Error updating trade {trade_id} ({ticker}): {e}")
                    continue

            conn.commit()
            logger.info(f"Updated {updated_count} open trades")
            return updated_count

        finally:
            conn.close()

    def _get_current_price(self, ticker):
        """Fetch current price for ASX ticker."""
        try:
            # Add .AX for ASX tickers
            asx_ticker = f"{ticker}.AX"
            stock = yf.Ticker(asx_ticker)

            # Try to get latest price
            info = stock.info
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')

            if current_price:
                return current_price

            # Fallback: get last close from history
            hist = stock.history(period='1d')
            if not hist.empty:
                return hist['Close'].iloc[-1]

            return None

        except Exception as e:
            logger.warning(f"Error fetching price for {ticker}: {e}")
            return None

    def _check_exit_conditions(self, trade_id, ticker, entry_price, current_price,
                               return_pct, holding_days, cursor):
        """
        Check if trade should be closed based on exit rules.

        Exit Rules:
        1. Take profit: +10% gain
        2. Stop loss: -5% loss
        3. Time stop: 7 days holding
        4. Trailing stop: -3% from peak
        """
        exit_reason = None
        should_exit = False

        # Rule 1: Take profit
        if return_pct >= 10.0:
            exit_reason = "TAKE_PROFIT_10PCT"
            should_exit = True

        # Rule 2: Stop loss
        elif return_pct <= -5.0:
            exit_reason = "STOP_LOSS_5PCT"
            should_exit = True

        # Rule 3: Time stop
        elif holding_days >= 7:
            exit_reason = "TIME_STOP_7DAYS"
            should_exit = True

        # Rule 4: Trailing stop (fetch peak)
        else:
            cursor.execute('SELECT peak_price FROM trade_outcomes WHERE id = ?', (trade_id,))
            peak_price = cursor.fetchone()[0]

            if peak_price and current_price:
                drawdown_from_peak = ((current_price - peak_price) / peak_price) * 100

                if drawdown_from_peak <= -3.0:
                    exit_reason = "TRAILING_STOP_3PCT"
                    should_exit = True

        if should_exit:
            self._close_trade(trade_id, current_price, exit_reason, cursor)

    def _close_trade(self, trade_id, exit_price, exit_reason, cursor):
        """Close a trade and mark outcome."""
        now = datetime.now(self.tz)

        # Fetch entry price to determine outcome
        cursor.execute('''
            SELECT entry_price, return_pct
            FROM trade_outcomes
            WHERE id = ?
        ''', (trade_id,))

        entry_price, return_pct = cursor.fetchone()

        # Determine outcome
        if return_pct > 0.5:
            outcome = 'WIN'
        elif return_pct < -0.5:
            outcome = 'LOSS'
        else:
            outcome = 'BREAKEVEN'

        cursor.execute('''
            UPDATE trade_outcomes
            SET status = 'CLOSED',
                exit_price = ?,
                exit_timestamp = ?,
                exit_reason = ?,
                outcome = ?,
                last_updated = ?
            WHERE id = ?
        ''', (
            exit_price,
            now.strftime('%Y-%m-%d %H:%M:%S'),
            exit_reason,
            outcome,
            now.strftime('%Y-%m-%d %H:%M:%S'),
            trade_id
        ))

        logger.info(f"Closed trade {trade_id}: {outcome} ({return_pct:+.2f}%) - {exit_reason}")

    def get_performance_summary(self):
        """
        Get overall performance summary.

        Returns:
            Dictionary with performance metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Total trades
            cursor.execute('SELECT COUNT(*) FROM trade_outcomes')
            total_trades = cursor.fetchone()[0]

            # Win/Loss counts
            cursor.execute('''
                SELECT
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN outcome = 'BREAKEVEN' THEN 1 END) as breakeven,
                    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades
                FROM trade_outcomes
            ''')

            wins, losses, breakeven, open_trades = cursor.fetchone()

            # Average returns
            cursor.execute('''
                SELECT
                    AVG(return_pct) as avg_return,
                    AVG(CASE WHEN outcome = 'WIN' THEN return_pct END) as avg_win,
                    AVG(CASE WHEN outcome = 'LOSS' THEN return_pct END) as avg_loss,
                    MAX(return_pct) as best_trade,
                    MIN(return_pct) as worst_trade
                FROM trade_outcomes
                WHERE status = 'CLOSED'
            ''')

            avg_return, avg_win, avg_loss, best, worst = cursor.fetchone()

            # Win rate
            closed_trades = wins + losses + breakeven
            win_rate = (wins / closed_trades * 100) if closed_trades > 0 else 0

            return {
                'total_trades': total_trades,
                'open_trades': open_trades,
                'closed_trades': closed_trades,
                'wins': wins or 0,
                'losses': losses or 0,
                'breakeven': breakeven or 0,
                'win_rate': round(win_rate, 1),
                'avg_return': round(avg_return, 2) if avg_return else 0,
                'avg_win': round(avg_win, 2) if avg_win else 0,
                'avg_loss': round(avg_loss, 2) if avg_loss else 0,
                'best_trade': round(best, 2) if best else 0,
                'worst_trade': round(worst, 2) if worst else 0
            }

        finally:
            conn.close()


def main():
    """Test the trade tracker."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    logging.basicConfig(level=logging.INFO)

    tracker = TradeTracker()

    print("="*60)
    print("TRADE OUTCOME TRACKER")
    print("="*60)
    print()

    # Update open trades
    print("Updating open trades...")
    updated = tracker.update_open_trades()
    print(f"Updated {updated} trades")
    print()

    # Get performance summary
    print("Performance Summary:")
    print("-"*60)
    summary = tracker.get_performance_summary()

    for key, value in summary.items():
        print(f"{key:20} {value}")

    print("="*60)


if __name__ == '__main__':
    import os
    main()
