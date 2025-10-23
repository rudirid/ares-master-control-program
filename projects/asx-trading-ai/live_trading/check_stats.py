"""
Live Trading Statistics Checker

Quick dashboard for monitoring live paper trading progress.

Usage:
    python live_trading/check_stats.py

Author: Claude Code
Date: 2025-10-10
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config


class LiveStatsChecker:
    """Check and display live trading statistics."""

    def __init__(self, db_path: str):
        """
        Initialize stats checker.

        Args:
            db_path: Database path
        """
        self.db_path = db_path

    def get_overall_stats(self) -> Dict:
        """Get overall statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total announcements
        cursor.execute("SELECT COUNT(*) FROM live_announcements")
        total_announcements = cursor.fetchone()[0]

        # Total recommendations
        cursor.execute("SELECT COUNT(*) FROM live_recommendations")
        total_recommendations = cursor.fetchone()[0]

        # Pass rate
        pass_rate = (total_recommendations / total_announcements * 100) if total_announcements > 0 else 0

        # Average confidence
        cursor.execute("SELECT AVG(confidence) FROM live_recommendations")
        avg_confidence = cursor.fetchone()[0] or 0

        # Time range
        cursor.execute("SELECT MIN(detected_timestamp), MAX(detected_timestamp) FROM live_announcements")
        start_time, end_time = cursor.fetchone()

        # BUY vs SELL
        cursor.execute("SELECT recommendation, COUNT(*) FROM live_recommendations GROUP BY recommendation")
        rec_counts = dict(cursor.fetchall())

        conn.close()

        return {
            'total_announcements': total_announcements,
            'total_recommendations': total_recommendations,
            'pass_rate': pass_rate,
            'avg_confidence': avg_confidence,
            'start_time': start_time,
            'end_time': end_time,
            'buy_count': rec_counts.get('BUY', 0),
            'sell_count': rec_counts.get('SELL', 0)
        }

    def get_daily_stats(self) -> pd.DataFrame:
        """Get daily breakdown of announcements and recommendations."""
        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT
            DATE(detected_timestamp) as date,
            COUNT(*) as announcements,
            SUM(CASE WHEN recommendation_generated = 1 THEN 1 ELSE 0 END) as recommendations,
            CAST(SUM(CASE WHEN recommendation_generated = 1 THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100 as pass_rate
        FROM live_announcements
        GROUP BY DATE(detected_timestamp)
        ORDER BY date DESC
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def get_top_recommendations(self, limit: int = 10) -> pd.DataFrame:
        """Get top recommendations by confidence."""
        conn = sqlite3.connect(self.db_path)

        query = f"""
        SELECT
            ticker,
            recommendation,
            confidence,
            entry_price,
            sentiment,
            sentiment_score,
            generated_timestamp
        FROM live_recommendations
        ORDER BY confidence DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def get_filter_analysis(self) -> Dict:
        """Analyze which filters are most restrictive."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all announcements that were filtered
        cursor.execute("""
            SELECT COUNT(*)
            FROM live_announcements
            WHERE processed = 1 AND recommendation_generated = 0
        """)
        total_filtered = cursor.fetchone()[0]

        # Would need to parse filters_failed from recommendations to get breakdown
        # For now, just return basic stats
        conn.close()

        return {
            'total_filtered': total_filtered
        }

    def get_ticker_performance(self) -> pd.DataFrame:
        """Get recommendation counts by ticker."""
        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT
            ticker,
            COUNT(*) as recommendation_count,
            AVG(confidence) as avg_confidence,
            MIN(entry_price) as min_price,
            MAX(entry_price) as max_price
        FROM live_recommendations
        GROUP BY ticker
        HAVING COUNT(*) >= 2
        ORDER BY recommendation_count DESC
        LIMIT 15
        """

        df = pd.read_sql_query(query, conn)
        conn.close()

        return df

    def display_dashboard(self):
        """Display comprehensive dashboard."""
        print("\n" + "="*80)
        print("LIVE PAPER TRADING STATISTICS DASHBOARD")
        print("="*80 + "\n")

        # Overall stats
        stats = self.get_overall_stats()

        print("OVERALL STATISTICS")
        print("-"*80)
        print(f"Period: {stats['start_time']} to {stats['end_time']}")
        print(f"Total Announcements Detected: {stats['total_announcements']}")
        print(f"Total Recommendations Generated: {stats['total_recommendations']}")
        print(f"Filter Pass Rate: {stats['pass_rate']:.1f}%")
        print(f"Average Confidence: {stats['avg_confidence']:.3f}")
        print(f"BUY Recommendations: {stats['buy_count']}")
        print(f"SELL Recommendations: {stats['sell_count']}")
        print()

        # Daily breakdown
        daily = self.get_daily_stats()
        if not daily.empty:
            print("DAILY BREAKDOWN")
            print("-"*80)
            print(daily.to_string(index=False))
            print()

        # Top recommendations
        top_recs = self.get_top_recommendations(limit=10)
        if not top_recs.empty:
            print("TOP 10 RECOMMENDATIONS (by confidence)")
            print("-"*80)
            print(top_recs.to_string(index=False))
            print()

        # Ticker performance
        ticker_perf = self.get_ticker_performance()
        if not ticker_perf.empty:
            print("MOST RECOMMENDED TICKERS")
            print("-"*80)
            print(ticker_perf.to_string(index=False))
            print()

        # Progress toward 300 target
        target = 300
        progress = (stats['total_recommendations'] / target) * 100 if target > 0 else 0

        print("PROGRESS TOWARD TARGET")
        print("-"*80)
        print(f"Target: {target} recommendations")
        print(f"Current: {stats['total_recommendations']} recommendations")
        print(f"Progress: {progress:.1f}%")

        if stats['total_recommendations'] < target and stats['start_time']:
            # Estimate remaining time
            start = datetime.strptime(stats['start_time'], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(stats['end_time'], '%Y-%m-%d %H:%M:%S') if stats['end_time'] else datetime.now()
            elapsed_hours = (end - start).total_seconds() / 3600

            if elapsed_hours > 0:
                recs_per_hour = stats['total_recommendations'] / elapsed_hours
                remaining_recs = target - stats['total_recommendations']
                estimated_hours = remaining_recs / recs_per_hour if recs_per_hour > 0 else 0

                print(f"Recommendations per Hour: {recs_per_hour:.1f}")
                print(f"Estimated Hours to Target: {estimated_hours:.1f}")

        print()
        print("="*80 + "\n")

    def quick_summary(self):
        """Display quick one-line summary."""
        stats = self.get_overall_stats()
        target = 300
        progress = (stats['total_recommendations'] / target) * 100

        print(
            f"[LIVE STATS] {stats['total_announcements']} announcements | "
            f"{stats['total_recommendations']} recommendations | "
            f"{stats['pass_rate']:.1f}% pass rate | "
            f"{progress:.1f}% toward target"
        )


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Check live trading statistics')
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show quick summary only'
    )

    args = parser.parse_args()

    checker = LiveStatsChecker(config.DATABASE_PATH)

    if args.summary:
        checker.quick_summary()
    else:
        checker.display_dashboard()


if __name__ == '__main__':
    main()
