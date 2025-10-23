"""
Paper Trading Scheduler

Automated scheduler for monitoring news, generating recommendations,
and sending daily summaries.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os
import logging
import time
from datetime import datetime, time as dt_time
import sqlite3
from typing import Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from paper_trading.recommendation_engine import RecommendationEngine
from paper_trading.paper_trader import PaperTrader
from paper_trading.daily_summary import DailySummaryGenerator
from paper_trading.risk_manager import RiskManager, RiskConfig

logger = logging.getLogger(__name__)


class PaperTradingScheduler:
    """
    Schedules and runs paper trading tasks automatically.
    """

    def __init__(
        self,
        db_path: str,
        min_confidence: float = 0.5,
        min_sentiment: float = 0.2,
        holding_days: int = 7,
        daily_summary_time: str = "17:00",  # 5 PM
        risk_config: Optional[RiskConfig] = None
    ):
        """
        Initialize the scheduler.

        Args:
            db_path: Path to database
            min_confidence: Minimum confidence threshold
            min_sentiment: Minimum sentiment threshold
            holding_days: Maximum holding period in days
            daily_summary_time: Time to send daily summary (HH:MM)
            risk_config: Risk management configuration
        """
        self.db_path = db_path
        self.min_confidence = min_confidence
        self.min_sentiment = min_sentiment
        self.holding_days = holding_days

        # Parse summary time
        hour, minute = map(int, daily_summary_time.split(':'))
        self.daily_summary_time = dt_time(hour, minute)

        self.engine = RecommendationEngine()
        self.paper_trader = PaperTrader(db_path)
        self.summary_generator = DailySummaryGenerator(db_path)

        # Initialize risk manager
        if risk_config is None:
            risk_config = RiskConfig(
                min_confidence=0.7,  # Override to 70% as per requirement
                stop_loss_pct=5.0,
                max_risk_per_trade_pct=2.0,
                max_positions_per_sector=3,
                daily_loss_limit_pct=5.0
            )
        self.risk_manager = RiskManager(db_path, risk_config)

        self.last_processed_article_id = self._get_last_processed_article()
        self.last_summary_date = None

        logger.info("Paper trading scheduler initialized with risk management")

    def _get_last_processed_article(self) -> int:
        """
        Get the ID of the last processed article.

        Returns:
            Last article ID or 0
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MAX(article_id)
                FROM paper_recommendations
                WHERE article_id IS NOT NULL
            """)

            result = cursor.fetchone()[0]
            conn.close()

            return result or 0

        except Exception as e:
            logger.error(f"Error getting last processed article: {e}")
            return 0

    def check_new_articles(self):
        """
        Check for new articles and generate recommendations.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get new articles since last check
            cursor.execute("""
                SELECT article_id, ticker, source, title, content, url
                FROM news_articles
                WHERE article_id > ?
                ORDER BY article_id ASC
            """, (self.last_processed_article_id,))

            new_articles = []
            for row in cursor.fetchall():
                new_articles.append({
                    'article_id': row[0],
                    'ticker': row[1],
                    'source': row[2],
                    'title': row[3],
                    'content': row[4],
                    'url': row[5]
                })

            conn.close()

            if not new_articles:
                logger.debug("No new articles found")
                return

            logger.info(f"Processing {len(new_articles)} new articles")

            # Generate recommendations
            recommendations = self.engine.generate_recommendations_batch(
                new_articles,
                self.min_confidence,
                self.min_sentiment
            )

            # Log recommendations and activate them
            for rec in recommendations:
                # Get current price
                current_price = self._get_current_price(rec['ticker'])
                if not current_price:
                    logger.warning(f"No price for {rec['ticker']}, skipping")
                    continue

                # Risk management checks
                is_allowed, reasons, risk_details = self.risk_manager.validate_new_position(
                    ticker=rec['ticker'],
                    confidence=rec['confidence'],
                    entry_price=current_price
                )

                if not is_allowed:
                    logger.info(
                        f"Position rejected for {rec['ticker']}: {', '.join(reasons)}"
                    )
                    self.risk_manager.log_risk_event(
                        event_type='POSITION_REJECTED',
                        severity='MEDIUM',
                        description=f"Recommendation rejected: {', '.join(reasons)}",
                        ticker=rec['ticker'],
                        details=risk_details
                    )
                    continue

                # Log recommendation
                self.paper_trader.log_recommendation(rec)

                # Activate with risk-adjusted position size
                self.paper_trader.activate_recommendation(
                    rec['recommendation_id'],
                    current_price
                )

                logger.info(
                    f"New recommendation: {rec['action']} {rec['ticker']} "
                    f"at ${current_price:.2f} (confidence: {rec['confidence']:.2f}, "
                    f"position: ${risk_details['position_size']:,.2f})"
                )

            # Update last processed
            if new_articles:
                self.last_processed_article_id = new_articles[-1]['article_id']

        except Exception as e:
            logger.error(f"Error checking new articles: {e}")

    def update_active_positions(self):
        """
        Update active positions and close if holding period reached or stop loss hit.
        """
        try:
            logger.info("Updating active positions")

            # Check stop losses first
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT recommendation_id, ticker
                FROM paper_recommendations
                WHERE status = 'ACTIVE'
            """)

            active_positions = cursor.fetchall()
            conn.close()

            for rec_id, ticker in active_positions:
                current_price = self._get_current_price(ticker)
                if current_price:
                    should_close, reason = self.risk_manager.check_stop_loss(rec_id, current_price)
                    if should_close:
                        logger.warning(f"Stop loss triggered for {ticker}: {reason}")
                        self.paper_trader.close_recommendation(
                            rec_id,
                            current_price,
                            outcome_details=reason
                        )

            # Check daily loss and circuit breaker
            daily_loss = self.risk_manager.calculate_daily_loss()
            if daily_loss <= -self.risk_manager.config.daily_loss_limit_pct:
                logger.critical(f"Daily loss limit exceeded: {daily_loss:.2f}%")
                self.risk_manager.activate_circuit_breaker(daily_loss)

            # Update regular holding period exits
            self.paper_trader.update_active_recommendations(
                max_holding_days=self.holding_days
            )

        except Exception as e:
            logger.error(f"Error updating active positions: {e}")

    def generate_daily_summary(self):
        """
        Generate and save daily summary.
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')

            if self.last_summary_date == today:
                logger.debug("Daily summary already generated today")
                return

            logger.info("Generating daily summary")

            summary = self.summary_generator.generate_summary()
            self.summary_generator.save_summary(summary)

            # Print summary to console
            print("\n" + "=" * 70)
            print(self.summary_generator.format_summary_text(summary))
            print("=" * 70 + "\n")

            self.last_summary_date = today

            logger.info("Daily summary generated and saved")

        except Exception as e:
            logger.error(f"Error generating daily summary: {e}")

    def _get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price for a ticker.

        Args:
            ticker: Stock ticker

        Returns:
            Current price or None
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

    def run_once(self):
        """
        Run all tasks once.
        """
        logger.info("Running scheduled tasks...")

        # Check for new articles
        self.check_new_articles()

        # Update active positions
        self.update_active_positions()

        # Check if it's time for daily summary
        current_time = datetime.now().time()
        if (current_time.hour == self.daily_summary_time.hour and
            current_time.minute >= self.daily_summary_time.minute):
            self.generate_daily_summary()

    def run_forever(self, check_interval: int = 300):
        """
        Run scheduler continuously.

        Args:
            check_interval: Seconds between checks (default: 300 = 5 minutes)
        """
        logger.info(f"Starting scheduler (checking every {check_interval} seconds)")
        logger.info(f"Daily summary time: {self.daily_summary_time}")

        print("\n" + "=" * 70)
        print("PAPER TRADING SCHEDULER")
        print("=" * 70)
        print(f"Monitoring for new articles...")
        print(f"Check interval: {check_interval} seconds")
        print(f"Daily summary: {self.daily_summary_time}")
        print(f"Min confidence: {self.min_confidence}")
        print(f"Min sentiment: {self.min_sentiment}")
        print(f"Holding period: {self.holding_days} days")
        print("\nPress Ctrl+C to stop\n")

        try:
            while True:
                self.run_once()
                time.sleep(check_interval)

        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            print("\nScheduler stopped.")


def main():
    """
    Run the paper trading scheduler.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Run paper trading scheduler')

    parser.add_argument(
        '--confidence',
        type=float,
        default=0.5,
        help='Minimum confidence threshold (default: 0.5)'
    )
    parser.add_argument(
        '--sentiment',
        type=float,
        default=0.2,
        help='Minimum sentiment score threshold (default: 0.2)'
    )
    parser.add_argument(
        '--holding-days',
        type=int,
        default=7,
        help='Maximum holding period in days (default: 7)'
    )
    parser.add_argument(
        '--summary-time',
        type=str,
        default='17:00',
        help='Daily summary time in HH:MM format (default: 17:00)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=300,
        help='Check interval in seconds (default: 300)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run once and exit (for testing or cron jobs)'
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    scheduler = PaperTradingScheduler(
        config.DATABASE_PATH,
        min_confidence=args.confidence,
        min_sentiment=args.sentiment,
        holding_days=args.holding_days,
        daily_summary_time=args.summary_time
    )

    if args.once:
        scheduler.run_once()
    else:
        scheduler.run_forever(check_interval=args.interval)


if __name__ == '__main__':
    main()
