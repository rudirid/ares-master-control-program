"""
Daily Performance Report

Generates a daily summary of live paper trading performance.

Usage:
    python live_trading/daily_report.py
    python live_trading/daily_report.py --date 2025-10-15

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


class DailyReporter:
    """Generate daily performance reports."""

    def __init__(self, db_path: str):
        """
        Initialize daily reporter.

        Args:
            db_path: Database path
        """
        self.db_path = db_path

    def get_daily_announcement_stats(self, date: str) -> Dict:
        """
        Get announcement statistics for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            Statistics dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total announcements
        cursor.execute("""
            SELECT COUNT(*)
            FROM live_announcements
            WHERE DATE(detected_timestamp) = ?
        """, (date,))
        total = cursor.fetchone()[0]

        # Recommendations generated
        cursor.execute("""
            SELECT COUNT(*)
            FROM live_announcements
            WHERE DATE(detected_timestamp) = ?
            AND recommendation_generated = 1
        """, (date,))
        recs = cursor.fetchone()[0]

        # Average age
        cursor.execute("""
            SELECT AVG(age_minutes)
            FROM live_announcements
            WHERE DATE(detected_timestamp) = ?
        """, (date,))
        avg_age = cursor.fetchone()[0] or 0

        # Price sensitive count
        cursor.execute("""
            SELECT COUNT(*)
            FROM live_announcements
            WHERE DATE(detected_timestamp) = ?
            AND price_sensitive = 1
        """, (date,))
        price_sensitive = cursor.fetchone()[0]

        conn.close()

        return {
            'date': date,
            'total_announcements': total,
            'recommendations_generated': recs,
            'pass_rate': (recs / total * 100) if total > 0 else 0,
            'avg_age_minutes': avg_age,
            'price_sensitive_count': price_sensitive
        }

    def get_daily_recommendations(self, date: str) -> pd.DataFrame:
        """
        Get all recommendations for a specific date.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            DataFrame of recommendations
        """
        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT
            ticker,
            recommendation,
            confidence,
            entry_price,
            sentiment,
            sentiment_score,
            generated_timestamp
        FROM live_recommendations
        WHERE DATE(generated_timestamp) = ?
        ORDER BY confidence DESC
        """

        df = pd.read_sql_query(query, conn, params=(date,))
        conn.close()

        return df

    def get_hourly_distribution(self, date: str) -> pd.DataFrame:
        """
        Get hourly distribution of announcements.

        Args:
            date: Date string (YYYY-MM-DD)

        Returns:
            DataFrame with hourly counts
        """
        conn = sqlite3.connect(self.db_path)

        query = """
        SELECT
            CAST(strftime('%H', detected_timestamp) AS INTEGER) as hour,
            COUNT(*) as announcement_count,
            SUM(CASE WHEN recommendation_generated = 1 THEN 1 ELSE 0 END) as recommendation_count
        FROM live_announcements
        WHERE DATE(detected_timestamp) = ?
        GROUP BY hour
        ORDER BY hour
        """

        df = pd.read_sql_query(query, conn, params=(date,))
        conn.close()

        return df

    def generate_daily_report(self, date: str = None, save_to_file: bool = False) -> str:
        """
        Generate daily performance report.

        Args:
            date: Date string (YYYY-MM-DD) or None for today
            save_to_file: Whether to save report to file

        Returns:
            Report text
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        report = []
        report.append("="*80)
        report.append(f"DAILY PERFORMANCE REPORT - {date}")
        report.append("="*80 + "\n")

        # Get statistics
        stats = self.get_daily_announcement_stats(date)

        # Overall stats
        report.append("DAILY SUMMARY")
        report.append("-"*80)
        report.append(f"Date: {stats['date']}")
        report.append(f"Total Announcements Detected: {stats['total_announcements']}")
        report.append(f"Recommendations Generated: {stats['recommendations_generated']}")
        report.append(f"Filter Pass Rate: {stats['pass_rate']:.1f}%")
        report.append(f"Average Announcement Age: {stats['avg_age_minutes']:.1f} minutes")
        report.append(f"Price-Sensitive Announcements: {stats['price_sensitive_count']}")
        report.append("")

        # Recommendations breakdown
        recs_df = self.get_daily_recommendations(date)

        if not recs_df.empty:
            report.append("RECOMMENDATIONS GENERATED")
            report.append("-"*80)

            # BUY vs SELL
            buy_count = len(recs_df[recs_df['recommendation'] == 'BUY'])
            sell_count = len(recs_df[recs_df['recommendation'] == 'SELL'])
            report.append(f"BUY: {buy_count} | SELL: {sell_count}")

            # Average confidence
            avg_conf = recs_df['confidence'].mean()
            report.append(f"Average Confidence: {avg_conf:.3f}")

            # Sentiment breakdown
            sentiment_counts = recs_df['sentiment'].value_counts()
            report.append(f"Sentiment: {sentiment_counts.to_dict()}")
            report.append("")

            # Top 5 recommendations
            report.append("TOP 5 RECOMMENDATIONS (by confidence)")
            report.append("-"*80)
            for idx, row in recs_df.head(5).iterrows():
                report.append(
                    f"{row['ticker']:8s} | {row['recommendation']:4s} | "
                    f"Conf: {row['confidence']:.3f} | Price: ${row['entry_price']:8.2f} | "
                    f"Sentiment: {row['sentiment']}"
                )
            report.append("")

        else:
            report.append("NO RECOMMENDATIONS GENERATED")
            report.append("")

        # Hourly distribution
        hourly = self.get_hourly_distribution(date)

        if not hourly.empty:
            report.append("HOURLY DISTRIBUTION")
            report.append("-"*80)
            report.append(f"{'Hour':>4s} | {'Announcements':>13s} | {'Recommendations':>15s} | {'Pass Rate':>9s}")
            report.append("-"*80)

            for idx, row in hourly.iterrows():
                hour = int(row['hour'])
                ann_count = int(row['announcement_count'])
                rec_count = int(row['recommendation_count'])
                pass_rate = (rec_count / ann_count * 100) if ann_count > 0 else 0

                report.append(
                    f"{hour:02d}:00 | {ann_count:13d} | {rec_count:15d} | {pass_rate:8.1f}%"
                )

            report.append("")

        # Progress tracking
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM live_recommendations")
        total_recs = cursor.fetchone()[0]
        conn.close()

        target = 300
        progress = (total_recs / target * 100) if target > 0 else 0

        report.append("CUMULATIVE PROGRESS")
        report.append("-"*80)
        report.append(f"Total Recommendations (all days): {total_recs}")
        report.append(f"Target: {target}")
        report.append(f"Progress: {progress:.1f}%")
        report.append("")

        # Insights
        report.append("KEY INSIGHTS")
        report.append("-"*80)

        if stats['total_announcements'] == 0:
            report.append("- No announcements detected today (market closed or system offline)")
        elif stats['recommendations_generated'] == 0:
            report.append("- All announcements filtered (no tradeable signals detected)")
        elif stats['pass_rate'] < 10:
            report.append(f"- Very low pass rate ({stats['pass_rate']:.1f}%) - filters may be too strict")
        elif stats['pass_rate'] > 30:
            report.append(f"- High pass rate ({stats['pass_rate']:.1f}%) - many tradeable signals")

        if stats['avg_age_minutes'] > 30:
            report.append(f"- Average announcement age is high ({stats['avg_age_minutes']:.1f} min)")
            report.append("  - Consider improving data source refresh rate")

        if not recs_df.empty:
            if avg_conf < 0.65:
                report.append(f"- Low average confidence ({avg_conf:.3f}) - signals are marginal")
            elif avg_conf > 0.75:
                report.append(f"- High average confidence ({avg_conf:.3f}) - strong signals today")

        report.append("")
        report.append("="*80 + "\n")

        report_text = '\n'.join(report)

        if save_to_file:
            filename = f"daily_report_{date}.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"[OK] Report saved to: {filename}\n")

        return report_text


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate daily performance report')
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Date to report on (YYYY-MM-DD), default: today'
    )
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save report to file'
    )

    args = parser.parse_args()

    reporter = DailyReporter(config.DATABASE_PATH)

    report = reporter.generate_daily_report(
        date=args.date,
        save_to_file=args.save
    )

    print(report)


if __name__ == '__main__':
    main()
