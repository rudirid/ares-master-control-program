"""
Live Paper Trading Orchestrator

Coordinates announcement monitoring and recommendation generation for 5-day
live paper trading simulation.

This is the main entry point for the live trading system.

Author: Claude Code
Date: 2025-10-10
"""

import logging
import time
import argparse
import sys
import os
from datetime import datetime, timedelta
from typing import Optional
import threading
import signal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live_trading.announcement_monitor import ASXAnnouncementMonitor
from live_trading.live_recommendation_engine import LiveRecommendationEngine
import config

logger = logging.getLogger(__name__)


class LivePaperTrader:
    """
    Orchestrates live paper trading system.

    Responsibilities:
    1. Monitor ASX for announcements
    2. Generate recommendations in real-time
    3. Track performance metrics
    4. Run for specified duration
    """

    def __init__(
        self,
        db_path: str,
        data_source: str = 'asx_web',
        check_interval_seconds: int = 10,
        duration_days: Optional[int] = None
    ):
        """
        Initialize live paper trader.

        Args:
            db_path: Database path
            data_source: 'asx_web', 'api', or 'test'
            check_interval_seconds: How often to check for new announcements (default: 10s for 30-90s alpha window)
            duration_days: Run for this many trading days (None = indefinite)
        """
        self.db_path = db_path
        self.data_source = data_source
        self.check_interval = check_interval_seconds
        self.duration_days = duration_days
        self.running = False

        # Initialize components
        self.monitor = ASXAnnouncementMonitor(
            db_path=db_path,
            check_interval_seconds=check_interval_seconds,
            data_source=data_source
        )

        self.recommendation_engine = LiveRecommendationEngine(db_path=db_path)

        # Stats tracking
        self.stats = {
            'announcements_detected': 0,
            'announcements_new': 0,
            'recommendations_generated': 0,
            'filters_passed': 0,
            'filters_failed': 0,
            'start_time': None,
            'end_time': None
        }

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("\nReceived shutdown signal. Stopping gracefully...")
        self.stop()

    def run_monitoring_cycle(self):
        """
        Run one monitoring cycle:
        1. Fetch announcements
        2. Store new ones
        3. Generate recommendations for unprocessed announcements
        """
        # Fetch announcements
        announcements = self.monitor.fetch_announcements()
        self.stats['announcements_detected'] += len(announcements)

        if not announcements:
            logger.info("No announcements found this cycle")
            return

        logger.info(f"Found {len(announcements)} announcements")

        # Store new announcements
        new_count = 0
        for announcement in announcements:
            if self.monitor.store_announcement(announcement):
                new_count += 1
                self.stats['announcements_new'] += 1

        logger.info(f"Stored {new_count} new announcements")

        # Process unprocessed announcements
        if new_count > 0:
            logger.info(f"\nProcessing {new_count} new announcements...")
            recommendations = self.recommendation_engine.process_unprocessed_announcements()

            self.stats['recommendations_generated'] += len(recommendations)

            if recommendations:
                logger.info(f"\n{'='*80}")
                logger.info(f"GENERATED {len(recommendations)} RECOMMENDATIONS")
                logger.info(f"{'='*80}\n")

                for rec in recommendations:
                    logger.info(
                        f"[REC] {rec['recommendation']} {rec['ticker']} @ "
                        f"${rec['entry_price']:.2f} (Confidence: {rec['confidence']:.2f})"
                    )
            else:
                logger.info("No recommendations generated (announcements filtered)")

    def run(self):
        """
        Run live paper trading system.

        Continuous loop:
        1. Check if market hours
        2. Fetch announcements
        3. Generate recommendations
        4. Wait for next cycle
        5. Repeat until duration reached
        """
        self.running = True
        self.stats['start_time'] = datetime.now()

        # Calculate end time if duration specified
        end_time = None
        if self.duration_days:
            end_time = datetime.now() + timedelta(days=self.duration_days)

        logger.info("\n" + "="*80)
        logger.info("LIVE PAPER TRADING SYSTEM STARTED")
        logger.info("="*80)
        logger.info(f"Data Source: {self.data_source}")
        logger.info(f"Check Interval: {self.check_interval}s")
        logger.info(f"Start Time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")

        if end_time:
            logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')} ({self.duration_days} days)")
        else:
            logger.info("Duration: Indefinite (Ctrl+C to stop)")

        logger.info("="*80 + "\n")

        cycle_count = 0

        try:
            while self.running:
                # Check if duration exceeded
                if end_time and datetime.now() >= end_time:
                    logger.info(f"\nDuration limit reached ({self.duration_days} days)")
                    break

                # Check if market hours
                if not self.monitor.is_market_hours():
                    now = datetime.now(self.monitor.tz)
                    logger.info(
                        f"[{now.strftime('%H:%M:%S')}] Outside market hours - "
                        f"waiting 5 minutes..."
                    )
                    time.sleep(300)  # Check every 5 min when market closed
                    continue

                cycle_count += 1
                logger.info(f"\n{'='*80}")
                logger.info(f"CYCLE #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'='*80}\n")

                # Run one monitoring cycle
                self.run_monitoring_cycle()

                # Display stats
                self._display_stats()

                # Wait for next cycle
                logger.info(f"\nWaiting {self.check_interval}s until next cycle...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("\nMonitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
        finally:
            self.stop()

    def _display_stats(self):
        """Display current statistics."""
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        elapsed_hours = elapsed / 3600

        logger.info(f"\n{'='*80}")
        logger.info("SESSION STATISTICS")
        logger.info(f"{'='*80}")
        logger.info(f"Elapsed Time: {elapsed_hours:.1f} hours")
        logger.info(f"Announcements Detected: {self.stats['announcements_detected']}")
        logger.info(f"New Announcements: {self.stats['announcements_new']}")
        logger.info(f"Recommendations Generated: {self.stats['recommendations_generated']}")

        if self.stats['announcements_new'] > 0:
            pass_rate = (self.stats['recommendations_generated'] / self.stats['announcements_new']) * 100
            logger.info(f"Filter Pass Rate: {pass_rate:.1f}%")

        logger.info(f"{'='*80}\n")

    def stop(self):
        """Stop the trading system."""
        self.running = False
        self.stats['end_time'] = datetime.now()

        logger.info("\n" + "="*80)
        logger.info("LIVE PAPER TRADING SYSTEM STOPPED")
        logger.info("="*80)

        self._display_final_report()

    def _display_final_report(self):
        """Display final session report."""
        if not self.stats['start_time']:
            return

        end_time = self.stats['end_time'] or datetime.now()
        elapsed = (end_time - self.stats['start_time']).total_seconds()
        elapsed_hours = elapsed / 3600

        logger.info(f"\nSession Duration: {elapsed_hours:.1f} hours")
        logger.info(f"Total Announcements Detected: {self.stats['announcements_detected']}")
        logger.info(f"New Announcements Stored: {self.stats['announcements_new']}")
        logger.info(f"Recommendations Generated: {self.stats['recommendations_generated']}")

        if self.stats['announcements_new'] > 0:
            pass_rate = (self.stats['recommendations_generated'] / self.stats['announcements_new']) * 100
            logger.info(f"Filter Pass Rate: {pass_rate:.1f}%")

            recs_per_hour = self.stats['recommendations_generated'] / elapsed_hours if elapsed_hours > 0 else 0
            logger.info(f"Recommendations per Hour: {recs_per_hour:.1f}")

        logger.info("\n" + "="*80)
        logger.info("Next Steps:")
        logger.info("1. Run: python live_trading/check_stats.py (to view detailed stats)")
        logger.info("2. Run: python live_trading/daily_report.py (for daily performance)")
        logger.info("3. After 5 days: python analysis/performance_attribution_live.py")
        logger.info("="*80 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Live Paper Trading System for ASX Stock Trading AI'
    )

    parser.add_argument(
        '--data-source',
        type=str,
        default='asx_web',
        choices=['asx_web', 'test', 'api'],
        help='Data source for announcements (default: asx_web)'
    )

    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Check interval in seconds (default: 10 - captures 30-90s alpha window)'
    )

    parser.add_argument(
        '--duration-days',
        type=int,
        default=5,
        help='Run for this many days (default: 5)'
    )

    parser.add_argument(
        '--test-mode',
        action='store_true',
        help='Run in test mode with simulated announcements'
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'live_trading_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )

    # Override data source if test mode
    data_source = 'test' if args.test_mode else args.data_source

    # Create and run trader
    trader = LivePaperTrader(
        db_path=config.DATABASE_PATH,
        data_source=data_source,
        check_interval_seconds=args.interval,
        duration_days=args.duration_days
    )

    trader.run()


if __name__ == '__main__':
    main()
