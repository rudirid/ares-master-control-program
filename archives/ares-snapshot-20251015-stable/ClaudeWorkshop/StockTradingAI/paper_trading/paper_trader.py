"""
Paper Trading System

Tracks trade recommendations and monitors their performance without
executing real trades.

Author: Claude Code
Date: 2025-10-09
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


class PaperTrader:
    """
    Manages paper trading recommendations and tracks their performance.
    """

    def __init__(self, db_path: str):
        """
        Initialize the paper trader.

        Args:
            db_path: Path to database
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """
        Initialize paper trading tables.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_recommendations (
                recommendation_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                confidence_explanation TEXT,

                sentiment TEXT,
                sentiment_score REAL,
                sentiment_confidence REAL,

                article_id INTEGER,
                article_title TEXT,
                article_source TEXT,
                article_url TEXT,

                themes TEXT,
                theme_performance TEXT,

                reasoning TEXT,
                pattern_based INTEGER,

                entry_price REAL,
                entry_date TEXT,

                exit_price REAL,
                exit_date TEXT,

                status TEXT,
                holding_days INTEGER,

                actual_return_pct REAL,
                expected_return_pct REAL,

                outcome TEXT,
                outcome_details TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create performance tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_performance (
                date TEXT PRIMARY KEY,
                total_recommendations INTEGER,
                active_positions INTEGER,
                closed_positions INTEGER,

                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,

                total_return_pct REAL,
                avg_return_pct REAL,

                high_confidence_count INTEGER,
                high_confidence_win_rate REAL,

                summary_text TEXT,

                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

        logger.info("Paper trading database initialized")

    def log_recommendation(self, recommendation: Dict) -> bool:
        """
        Log a new trade recommendation.

        Args:
            recommendation: Recommendation dictionary

        Returns:
            True if logged successfully
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO paper_recommendations (
                    recommendation_id, timestamp, ticker, action, confidence,
                    confidence_explanation, sentiment, sentiment_score,
                    sentiment_confidence, article_id, article_title,
                    article_source, article_url, themes, theme_performance,
                    reasoning, pattern_based, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation['recommendation_id'],
                recommendation['timestamp'],
                recommendation['ticker'],
                recommendation['action'],
                recommendation['confidence'],
                recommendation['confidence_explanation'],
                recommendation['sentiment'],
                recommendation['sentiment_score'],
                recommendation['sentiment_confidence'],
                recommendation.get('article_id'),
                recommendation.get('article_title', ''),
                recommendation.get('article_source', ''),
                recommendation.get('article_url', ''),
                json.dumps(recommendation.get('themes', [])),
                json.dumps(recommendation.get('theme_performance', {})),
                recommendation.get('reasoning', ''),
                1 if recommendation.get('pattern_based', False) else 0,
                'PENDING'
            ))

            conn.commit()
            conn.close()

            logger.info(f"Logged recommendation {recommendation['recommendation_id']}")
            return True

        except Exception as e:
            logger.error(f"Error logging recommendation: {e}")
            return False

    def activate_recommendation(
        self,
        recommendation_id: str,
        entry_price: float,
        entry_date: Optional[str] = None
    ) -> bool:
        """
        Activate a pending recommendation with entry price.

        Args:
            recommendation_id: Recommendation ID
            entry_price: Entry price
            entry_date: Entry date (defaults to now)

        Returns:
            True if activated successfully
        """
        if entry_date is None:
            entry_date = datetime.now().strftime('%Y-%m-%d')

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE paper_recommendations
                SET status = 'ACTIVE',
                    entry_price = ?,
                    entry_date = ?
                WHERE recommendation_id = ?
            """, (entry_price, entry_date, recommendation_id))

            conn.commit()
            conn.close()

            logger.info(f"Activated recommendation {recommendation_id} at ${entry_price}")
            return True

        except Exception as e:
            logger.error(f"Error activating recommendation: {e}")
            return False

    def close_recommendation(
        self,
        recommendation_id: str,
        exit_price: float,
        exit_date: Optional[str] = None,
        outcome_details: Optional[str] = None
    ) -> bool:
        """
        Close an active recommendation and calculate outcome.

        Args:
            recommendation_id: Recommendation ID
            exit_price: Exit price
            exit_date: Exit date (defaults to now)
            outcome_details: Optional outcome details

        Returns:
            True if closed successfully
        """
        if exit_date is None:
            exit_date = datetime.now().strftime('%Y-%m-%d')

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recommendation details
            cursor.execute("""
                SELECT entry_price, entry_date, action, expected_return_pct
                FROM paper_recommendations
                WHERE recommendation_id = ?
            """, (recommendation_id,))

            row = cursor.fetchone()
            if not row:
                logger.error(f"Recommendation {recommendation_id} not found")
                return False

            entry_price, entry_date_str, action, expected_return = row

            if entry_price is None:
                logger.error(f"Recommendation {recommendation_id} not activated")
                return False

            # Calculate return
            price_change_pct = ((exit_price - entry_price) / entry_price) * 100

            # For SELL/AVOID recommendations, we track what would have happened
            # if we had inverse exposure
            if action == 'SELL/AVOID':
                actual_return = -price_change_pct  # Benefit from price decline
            else:
                actual_return = price_change_pct

            # Determine outcome
            if actual_return > 0.5:
                outcome = 'WIN'
            elif actual_return < -0.5:
                outcome = 'LOSS'
            else:
                outcome = 'NEUTRAL'

            # Calculate holding days
            entry_dt = datetime.strptime(entry_date_str, '%Y-%m-%d')
            exit_dt = datetime.strptime(exit_date, '%Y-%m-%d')
            holding_days = (exit_dt - entry_dt).days

            # Update recommendation
            cursor.execute("""
                UPDATE paper_recommendations
                SET status = 'CLOSED',
                    exit_price = ?,
                    exit_date = ?,
                    actual_return_pct = ?,
                    outcome = ?,
                    outcome_details = ?,
                    holding_days = ?
                WHERE recommendation_id = ?
            """, (
                exit_price,
                exit_date,
                round(actual_return, 2),
                outcome,
                outcome_details,
                holding_days,
                recommendation_id
            ))

            conn.commit()
            conn.close()

            logger.info(
                f"Closed recommendation {recommendation_id}: "
                f"{outcome} with {actual_return:+.2f}% return"
            )
            return True

        except Exception as e:
            logger.error(f"Error closing recommendation: {e}")
            return False

    def update_active_recommendations(self, max_holding_days: int = 7):
        """
        Check and update all active recommendations with current prices.

        Args:
            max_holding_days: Maximum holding period before auto-close
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get active recommendations
            cursor.execute("""
                SELECT recommendation_id, ticker, entry_price, entry_date
                FROM paper_recommendations
                WHERE status = 'ACTIVE'
            """)

            active_recs = cursor.fetchall()
            conn.close()

            if not active_recs:
                logger.info("No active recommendations to update")
                return

            logger.info(f"Updating {len(active_recs)} active recommendations")

            for rec_id, ticker, entry_price, entry_date_str in active_recs:
                # Get current price
                current_price = self._get_latest_price(ticker)

                if current_price is None:
                    logger.warning(f"No price data for {ticker}")
                    continue

                # Check holding period
                entry_dt = datetime.strptime(entry_date_str, '%Y-%m-%d')
                days_held = (datetime.now() - entry_dt).days

                if days_held >= max_holding_days:
                    # Auto-close
                    self.close_recommendation(
                        rec_id,
                        current_price,
                        outcome_details=f"Auto-closed after {max_holding_days} days"
                    )
                    logger.info(f"Auto-closed {rec_id} after {days_held} days")

        except Exception as e:
            logger.error(f"Error updating active recommendations: {e}")

    def _get_latest_price(self, ticker: str) -> Optional[float]:
        """
        Get the latest available price for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Latest close price or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT close FROM stock_prices
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT 1
            """, (ticker,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return float(row[0])
            return None

        except Exception as e:
            logger.error(f"Error getting price for {ticker}: {e}")
            return None

    def get_performance_summary(self, days: int = 30) -> Dict:
        """
        Get performance summary for recent period.

        Args:
            days: Number of days to look back

        Returns:
            Performance summary dictionary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

            # Get closed recommendations
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                    AVG(actual_return_pct) as avg_return,
                    SUM(actual_return_pct) as total_return,
                    SUM(CASE WHEN confidence >= 0.7 THEN 1 ELSE 0 END) as high_conf_total,
                    SUM(CASE WHEN confidence >= 0.7 AND outcome = 'WIN' THEN 1 ELSE 0 END) as high_conf_wins
                FROM paper_recommendations
                WHERE status = 'CLOSED'
                AND timestamp >= ?
            """, (cutoff_date,))

            row = cursor.fetchone()

            total = row[0] or 0
            wins = row[1] or 0
            losses = row[2] or 0
            avg_return = row[3] or 0.0
            total_return = row[4] or 0.0
            high_conf_total = row[5] or 0
            high_conf_wins = row[6] or 0

            win_rate = (wins / total * 100) if total > 0 else 0
            high_conf_win_rate = (high_conf_wins / high_conf_total * 100) if high_conf_total > 0 else 0

            # Get active count
            cursor.execute("""
                SELECT COUNT(*)
                FROM paper_recommendations
                WHERE status = 'ACTIVE'
            """)
            active_count = cursor.fetchone()[0]

            conn.close()

            return {
                'period_days': days,
                'total_recommendations': total,
                'active_positions': active_count,
                'closed_positions': total,
                'winning_trades': wins,
                'losing_trades': losses,
                'win_rate': round(win_rate, 1),
                'avg_return_pct': round(avg_return, 2),
                'total_return_pct': round(total_return, 2),
                'high_confidence_count': high_conf_total,
                'high_confidence_win_rate': round(high_conf_win_rate, 1)
            }

        except Exception as e:
            logger.error(f"Error getting performance summary: {e}")
            return {}

    def get_recent_recommendations(self, limit: int = 10) -> List[Dict]:
        """
        Get recent recommendations.

        Args:
            limit: Maximum number to return

        Returns:
            List of recommendation dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT *
                FROM paper_recommendations
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            recommendations = []
            for row in rows:
                rec = dict(row)
                # Parse JSON fields
                rec['themes'] = json.loads(rec['themes']) if rec['themes'] else []
                rec['theme_performance'] = json.loads(rec['theme_performance']) if rec['theme_performance'] else {}
                recommendations.append(rec)

            return recommendations

        except Exception as e:
            logger.error(f"Error getting recent recommendations: {e}")
            return []


def main():
    """
    Test the paper trader.
    """
    import config

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 70)
    print("PAPER TRADER TEST")
    print("=" * 70 + "\n")

    trader = PaperTrader(config.DATABASE_PATH)

    # Test recommendation
    test_rec = {
        'recommendation_id': 'TEST_001',
        'timestamp': datetime.now().isoformat(),
        'ticker': 'BHP',
        'action': 'BUY',
        'confidence': 0.75,
        'confidence_explanation': 'Test recommendation',
        'sentiment': 'positive',
        'sentiment_score': 0.6,
        'sentiment_confidence': 0.8,
        'article_title': 'Test Article',
        'article_source': 'TEST',
        'themes': ['earnings'],
        'theme_performance': {'expected_move_pct': 2.5},
        'reasoning': 'Testing paper trader',
        'pattern_based': True
    }

    # Log recommendation
    print("Logging test recommendation...")
    trader.log_recommendation(test_rec)

    # Activate
    print("Activating recommendation...")
    trader.activate_recommendation('TEST_001', 45.50)

    # Get performance
    print("\nPerformance Summary:")
    summary = trader.get_performance_summary(days=7)
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Get recent
    print("\nRecent Recommendations:")
    recent = trader.get_recent_recommendations(limit=5)
    for rec in recent:
        print(f"  {rec['ticker']} - {rec['action']} - {rec['status']} - Confidence: {rec['confidence']:.2f}")

    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
