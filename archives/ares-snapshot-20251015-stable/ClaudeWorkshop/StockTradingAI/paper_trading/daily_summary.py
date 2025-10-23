"""
Daily Summary Generator

Generates daily summary reports of paper trading recommendations
and performance.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paper_trading.paper_trader import PaperTrader

logger = logging.getLogger(__name__)


class DailySummaryGenerator:
    """
    Generates daily summary reports for paper trading.
    """

    def __init__(self, db_path: str):
        """
        Initialize the summary generator.

        Args:
            db_path: Path to database
        """
        self.paper_trader = PaperTrader(db_path)

    def generate_summary(self, date: str = None) -> Dict:
        """
        Generate daily summary for a given date.

        Args:
            date: Date string (YYYY-MM-DD), defaults to today

        Returns:
            Summary dictionary
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        logger.info(f"Generating summary for {date}")

        import sqlite3
        conn = sqlite3.connect(self.paper_trader.db_path)
        cursor = conn.cursor()

        # Get recommendations made today
        cursor.execute("""
            SELECT
                recommendation_id, ticker, action, confidence,
                sentiment, sentiment_score, themes, reasoning,
                entry_price, status
            FROM paper_recommendations
            WHERE DATE(timestamp) = ?
            ORDER BY confidence DESC
        """, (date,))

        today_recs = []
        for row in cursor.fetchall():
            today_recs.append({
                'id': row[0],
                'ticker': row[1],
                'action': row[2],
                'confidence': row[3],
                'sentiment': row[4],
                'sentiment_score': row[5],
                'themes': json.loads(row[6]) if row[6] else [],
                'reasoning': row[7],
                'entry_price': row[8],
                'status': row[9]
            })

        # Get closed positions today
        cursor.execute("""
            SELECT
                recommendation_id, ticker, action, confidence,
                entry_price, exit_price, actual_return_pct,
                outcome, holding_days
            FROM paper_recommendations
            WHERE DATE(exit_date) = ?
            ORDER BY actual_return_pct DESC
        """, (date,))

        closed_today = []
        for row in cursor.fetchall():
            closed_today.append({
                'id': row[0],
                'ticker': row[1],
                'action': row[2],
                'confidence': row[3],
                'entry_price': row[4],
                'exit_price': row[5],
                'return_pct': row[6],
                'outcome': row[7],
                'holding_days': row[8]
            })

        # Get active positions
        cursor.execute("""
            SELECT
                recommendation_id, ticker, action, confidence,
                entry_price, entry_date,
                (julianday('now') - julianday(entry_date)) as days_held
            FROM paper_recommendations
            WHERE status = 'ACTIVE'
            ORDER BY confidence DESC
        """)

        active_positions = []
        for row in cursor.fetchall():
            active_positions.append({
                'id': row[0],
                'ticker': row[1],
                'action': row[2],
                'confidence': row[3],
                'entry_price': row[4],
                'entry_date': row[5],
                'days_held': int(row[6])
            })

        conn.close()

        # Get performance metrics
        performance_7d = self.paper_trader.get_performance_summary(days=7)
        performance_30d = self.paper_trader.get_performance_summary(days=30)

        summary = {
            'date': date,
            'generated_at': datetime.now().isoformat(),

            'today': {
                'new_recommendations': len(today_recs),
                'recommendations': today_recs,
                'positions_closed': len(closed_today),
                'closed_positions': closed_today
            },

            'active': {
                'total_positions': len(active_positions),
                'positions': active_positions
            },

            'performance': {
                '7_day': performance_7d,
                '30_day': performance_30d
            }
        }

        return summary

    def format_summary_text(self, summary: Dict) -> str:
        """
        Format summary as readable text.

        Args:
            summary: Summary dictionary

        Returns:
            Formatted text
        """
        lines = []
        lines.append("=" * 70)
        lines.append(f"PAPER TRADING DAILY SUMMARY - {summary['date']}")
        lines.append("=" * 70)
        lines.append("")

        # Today's activity
        lines.append("TODAY'S ACTIVITY")
        lines.append("-" * 70)
        lines.append(f"New Recommendations: {summary['today']['new_recommendations']}")
        lines.append(f"Positions Closed: {summary['today']['positions_closed']}")
        lines.append("")

        # New recommendations
        if summary['today']['recommendations']:
            lines.append("New Recommendations:")
            for rec in summary['today']['recommendations']:
                lines.append(f"  • {rec['action']} {rec['ticker']} - Confidence: {rec['confidence']:.2f}")
                lines.append(f"    Sentiment: {rec['sentiment']} ({rec['sentiment_score']:+.2f})")
                if rec['themes']:
                    lines.append(f"    Themes: {', '.join(rec['themes'])}")
                lines.append(f"    Reasoning: {rec['reasoning']}")
                lines.append(f"    Status: {rec['status']}")
                lines.append("")

        # Closed positions
        if summary['today']['closed_positions']:
            lines.append("Positions Closed Today:")
            for pos in summary['today']['closed_positions']:
                lines.append(
                    f"  • {pos['ticker']} - {pos['outcome']} - "
                    f"Return: {pos['return_pct']:+.2f}% "
                    f"(${pos['entry_price']:.2f} → ${pos['exit_price']:.2f})"
                )
                lines.append(f"    Held for {pos['holding_days']} days")
                lines.append("")

        # Active positions
        lines.append("")
        lines.append("ACTIVE POSITIONS")
        lines.append("-" * 70)
        lines.append(f"Total Active: {summary['active']['total_positions']}")
        lines.append("")

        if summary['active']['positions']:
            for pos in summary['active']['positions']:
                lines.append(
                    f"  • {pos['action']} {pos['ticker']} - "
                    f"Confidence: {pos['confidence']:.2f} - "
                    f"Day {pos['days_held']}"
                )
                lines.append(f"    Entry: ${pos['entry_price']:.2f} on {pos['entry_date']}")
                lines.append("")

        # Performance
        lines.append("")
        lines.append("PERFORMANCE METRICS")
        lines.append("-" * 70)

        perf_7d = summary['performance']['7_day']
        if perf_7d.get('total_recommendations', 0) > 0:
            lines.append("Last 7 Days:")
            lines.append(f"  Total Recommendations: {perf_7d['total_recommendations']}")
            lines.append(f"  Closed Positions: {perf_7d['closed_positions']}")
            lines.append(f"  Win Rate: {perf_7d['win_rate']}%")
            lines.append(f"  Average Return: {perf_7d['avg_return_pct']:+.2f}%")
            lines.append(f"  Total Return: {perf_7d['total_return_pct']:+.2f}%")
            if perf_7d.get('high_confidence_count', 0) > 0:
                lines.append(f"  High Confidence Win Rate: {perf_7d['high_confidence_win_rate']}%")
            lines.append("")

        perf_30d = summary['performance']['30_day']
        if perf_30d.get('total_recommendations', 0) > 0:
            lines.append("Last 30 Days:")
            lines.append(f"  Total Recommendations: {perf_30d['total_recommendations']}")
            lines.append(f"  Closed Positions: {perf_30d['closed_positions']}")
            lines.append(f"  Win Rate: {perf_30d['win_rate']}%")
            lines.append(f"  Average Return: {perf_30d['avg_return_pct']:+.2f}%")
            lines.append(f"  Total Return: {perf_30d['total_return_pct']:+.2f}%")
            if perf_30d.get('high_confidence_count', 0) > 0:
                lines.append(f"  High Confidence Win Rate: {perf_30d['high_confidence_win_rate']}%")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def format_summary_html(self, summary: Dict) -> str:
        """
        Format summary as HTML.

        Args:
            summary: Summary dictionary

        Returns:
            HTML string
        """
        html_parts = []

        html_parts.append("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; border-bottom: 2px solid #007bff; }
                h2 { color: #555; margin-top: 30px; }
                .metric { background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #007bff; }
                .recommendation { background: #e7f3ff; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .buy { border-left: 4px solid #28a745; }
                .sell { border-left: 4px solid #dc3545; }
                .win { color: #28a745; font-weight: bold; }
                .loss { color: #dc3545; font-weight: bold; }
                .neutral { color: #6c757d; }
                table { border-collapse: collapse; width: 100%; margin: 20px 0; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #007bff; color: white; }
            </style>
        </head>
        <body>
        """)

        html_parts.append(f"<h1>Paper Trading Daily Summary - {summary['date']}</h1>")

        # Today's activity
        html_parts.append("<h2>Today's Activity</h2>")
        html_parts.append(f"<p><strong>New Recommendations:</strong> {summary['today']['new_recommendations']}</p>")
        html_parts.append(f"<p><strong>Positions Closed:</strong> {summary['today']['positions_closed']}</p>")

        # New recommendations
        if summary['today']['recommendations']:
            html_parts.append("<h3>New Recommendations</h3>")
            for rec in summary['today']['recommendations']:
                action_class = 'buy' if rec['action'] == 'BUY' else 'sell'
                html_parts.append(f'<div class="recommendation {action_class}">')
                html_parts.append(f"<strong>{rec['action']} {rec['ticker']}</strong> - Confidence: {rec['confidence']:.2f}<br>")
                html_parts.append(f"Sentiment: {rec['sentiment']} ({rec['sentiment_score']:+.2f})<br>")
                if rec['themes']:
                    html_parts.append(f"Themes: {', '.join(rec['themes'])}<br>")
                html_parts.append(f"Reasoning: {rec['reasoning']}<br>")
                html_parts.append(f"Status: {rec['status']}")
                html_parts.append("</div>")

        # Closed positions
        if summary['today']['closed_positions']:
            html_parts.append("<h3>Positions Closed Today</h3>")
            html_parts.append("<table>")
            html_parts.append("<tr><th>Ticker</th><th>Outcome</th><th>Return</th><th>Entry</th><th>Exit</th><th>Days</th></tr>")
            for pos in summary['today']['closed_positions']:
                outcome_class = 'win' if pos['outcome'] == 'WIN' else ('loss' if pos['outcome'] == 'LOSS' else 'neutral')
                html_parts.append(f"<tr>")
                html_parts.append(f"<td>{pos['ticker']}</td>")
                html_parts.append(f'<td class="{outcome_class}">{pos["outcome"]}</td>')
                html_parts.append(f'<td class="{outcome_class}">{pos["return_pct"]:+.2f}%</td>')
                html_parts.append(f"<td>${pos['entry_price']:.2f}</td>")
                html_parts.append(f"<td>${pos['exit_price']:.2f}</td>")
                html_parts.append(f"<td>{pos['holding_days']}</td>")
                html_parts.append("</tr>")
            html_parts.append("</table>")

        # Active positions
        html_parts.append("<h2>Active Positions</h2>")
        html_parts.append(f"<p><strong>Total Active:</strong> {summary['active']['total_positions']}</p>")

        if summary['active']['positions']:
            html_parts.append("<table>")
            html_parts.append("<tr><th>Action</th><th>Ticker</th><th>Confidence</th><th>Entry Price</th><th>Entry Date</th><th>Days Held</th></tr>")
            for pos in summary['active']['positions']:
                html_parts.append("<tr>")
                html_parts.append(f"<td>{pos['action']}</td>")
                html_parts.append(f"<td>{pos['ticker']}</td>")
                html_parts.append(f"<td>{pos['confidence']:.2f}</td>")
                html_parts.append(f"<td>${pos['entry_price']:.2f}</td>")
                html_parts.append(f"<td>{pos['entry_date']}</td>")
                html_parts.append(f"<td>{pos['days_held']}</td>")
                html_parts.append("</tr>")
            html_parts.append("</table>")

        # Performance
        html_parts.append("<h2>Performance Metrics</h2>")

        perf_7d = summary['performance']['7_day']
        if perf_7d.get('total_recommendations', 0) > 0:
            html_parts.append('<div class="metric">')
            html_parts.append("<h3>Last 7 Days</h3>")
            html_parts.append(f"<p>Total Recommendations: {perf_7d['total_recommendations']}</p>")
            html_parts.append(f"<p>Win Rate: {perf_7d['win_rate']}%</p>")
            html_parts.append(f"<p>Average Return: {perf_7d['avg_return_pct']:+.2f}%</p>")
            html_parts.append(f"<p>Total Return: {perf_7d['total_return_pct']:+.2f}%</p>")
            html_parts.append("</div>")

        perf_30d = summary['performance']['30_day']
        if perf_30d.get('total_recommendations', 0) > 0:
            html_parts.append('<div class="metric">')
            html_parts.append("<h3>Last 30 Days</h3>")
            html_parts.append(f"<p>Total Recommendations: {perf_30d['total_recommendations']}</p>")
            html_parts.append(f"<p>Win Rate: {perf_30d['win_rate']}%</p>")
            html_parts.append(f"<p>Average Return: {perf_30d['avg_return_pct']:+.2f}%</p>")
            html_parts.append(f"<p>Total Return: {perf_30d['total_return_pct']:+.2f}%</p>")
            html_parts.append("</div>")

        html_parts.append("</body></html>")

        return "\n".join(html_parts)

    def save_summary(self, summary: Dict, output_dir: str = 'results/daily_summaries'):
        """
        Save summary to file.

        Args:
            summary: Summary dictionary
            output_dir: Output directory
        """
        os.makedirs(output_dir, exist_ok=True)

        date = summary['date']

        # Save JSON
        json_path = os.path.join(output_dir, f'summary_{date}.json')
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved JSON summary to {json_path}")

        # Save text
        text_path = os.path.join(output_dir, f'summary_{date}.txt')
        with open(text_path, 'w') as f:
            f.write(self.format_summary_text(summary))
        logger.info(f"Saved text summary to {text_path}")

        # Save HTML
        html_path = os.path.join(output_dir, f'summary_{date}.html')
        with open(html_path, 'w') as f:
            f.write(self.format_summary_html(summary))
        logger.info(f"Saved HTML summary to {html_path}")

    def send_email(
        self,
        summary: Dict,
        to_email: str,
        smtp_config: Dict
    ):
        """
        Send summary via email.

        Args:
            summary: Summary dictionary
            to_email: Recipient email
            smtp_config: SMTP configuration dict with keys:
                         host, port, username, password, from_email
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Paper Trading Summary - {summary['date']}"
            msg['From'] = smtp_config['from_email']
            msg['To'] = to_email

            # Plain text version
            text_part = MIMEText(self.format_summary_text(summary), 'plain')
            msg.attach(text_part)

            # HTML version
            html_part = MIMEText(self.format_summary_html(summary), 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls()
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)

            logger.info(f"Sent email summary to {to_email}")

        except Exception as e:
            logger.error(f"Error sending email: {e}")


def main():
    """
    Generate and display daily summary.
    """
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

    logging.basicConfig(level=logging.INFO)

    generator = DailySummaryGenerator(config.DATABASE_PATH)

    # Generate summary
    summary = generator.generate_summary()

    # Display text version
    print(generator.format_summary_text(summary))

    # Save to files
    generator.save_summary(summary)

    print(f"\nSummary saved to results/daily_summaries/")


if __name__ == '__main__':
    main()
