"""
Paper Trading Dashboard Server

HTTP server that provides data for the paper trading dashboard.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timedelta
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from paper_trading.paper_trader import PaperTrader

logger = logging.getLogger(__name__)


class PaperTradingAPIHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for paper trading API.
    """

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/api/paper-trading-data':
            self.serve_paper_trading_data()
        else:
            self.send_error(404, 'Not Found')

    def serve_paper_trading_data(self):
        """Serve paper trading data as JSON."""
        try:
            paper_trader = PaperTrader(config.DATABASE_PATH)

            # Get performance metrics
            metrics = paper_trader.get_performance_summary(days=30)

            # Get performance history
            performance_history = self.get_performance_history(paper_trader)

            # Get win rate analysis
            win_rate_analysis = self.get_win_rate_analysis(paper_trader)

            # Get recommendations
            recommendations = paper_trader.get_recent_recommendations(limit=50)

            # Get backtest comparison
            backtest_comparison = self.get_backtest_comparison(paper_trader)

            data = {
                'metrics': metrics,
                'performance_history': performance_history,
                'win_rate_analysis': win_rate_analysis,
                'recommendations': recommendations,
                'backtest_comparison': backtest_comparison
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())

        except Exception as e:
            logger.error(f"Error serving data: {e}")
            self.send_error(500, str(e))

    def get_performance_history(self, paper_trader: PaperTrader) -> list:
        """
        Get performance history over time.

        Args:
            paper_trader: PaperTrader instance

        Returns:
            List of performance data points
        """
        try:
            conn = sqlite3.connect(paper_trader.db_path)
            cursor = conn.cursor()

            # Get closed recommendations by exit date
            cursor.execute("""
                SELECT
                    DATE(exit_date) as date,
                    SUM(actual_return_pct) as daily_return
                FROM paper_recommendations
                WHERE status = 'CLOSED'
                AND exit_date IS NOT NULL
                GROUP BY DATE(exit_date)
                ORDER BY date ASC
            """)

            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return []

            # Calculate cumulative return
            history = []
            cumulative = 0

            for date, daily_return in rows:
                cumulative += daily_return or 0
                history.append({
                    'date': date,
                    'daily_return': round(daily_return or 0, 2),
                    'cumulative_return': round(cumulative, 2)
                })

            return history

        except Exception as e:
            logger.error(f"Error getting performance history: {e}")
            return []

    def get_win_rate_analysis(self, paper_trader: PaperTrader) -> dict:
        """
        Get win rate breakdown by different categories.

        Args:
            paper_trader: PaperTrader instance

        Returns:
            Win rate analysis dictionary
        """
        try:
            conn = sqlite3.connect(paper_trader.db_path)
            cursor = conn.cursor()

            # All trades
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM paper_recommendations
                WHERE status = 'CLOSED'
            """)
            row = cursor.fetchone()
            all_total, all_wins = row
            all_win_rate = (all_wins / all_total * 100) if all_total > 0 else 0

            # High confidence trades
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM paper_recommendations
                WHERE status = 'CLOSED'
                AND confidence >= 0.7
            """)
            row = cursor.fetchone()
            hc_total, hc_wins = row
            hc_win_rate = (hc_wins / hc_total * 100) if hc_total > 0 else 0

            # Pattern-based trades
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM paper_recommendations
                WHERE status = 'CLOSED'
                AND pattern_based = 1
            """)
            row = cursor.fetchone()
            pb_total, pb_wins = row
            pb_win_rate = (pb_wins / pb_total * 100) if pb_total > 0 else 0

            # Sentiment-only trades
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins
                FROM paper_recommendations
                WHERE status = 'CLOSED'
                AND pattern_based = 0
            """)
            row = cursor.fetchone()
            so_total, so_wins = row
            so_win_rate = (so_wins / so_total * 100) if so_total > 0 else 0

            conn.close()

            return {
                'all_trades': round(all_win_rate, 1),
                'high_confidence': round(hc_win_rate, 1),
                'pattern_based': round(pb_win_rate, 1),
                'sentiment_only': round(so_win_rate, 1)
            }

        except Exception as e:
            logger.error(f"Error getting win rate analysis: {e}")
            return {
                'all_trades': 0,
                'high_confidence': 0,
                'pattern_based': 0,
                'sentiment_only': 0
            }

    def get_backtest_comparison(self, paper_trader: PaperTrader) -> dict:
        """
        Compare live paper trading vs backtest results.

        Args:
            paper_trader: PaperTrader instance

        Returns:
            Comparison dictionary
        """
        try:
            # Get live performance
            live_summary = paper_trader.get_performance_summary(days=30)

            # Try to load backtest results
            backtest_path = 'results/backtest_results.json'
            if os.path.exists(backtest_path):
                with open(backtest_path, 'r') as f:
                    backtest_data = json.load(f)
            else:
                # Default backtest values (user should run backtest first)
                backtest_data = {
                    'win_rate': 0,
                    'avg_win': 0,
                    'total_return_pct': 0
                }

            return {
                'live': {
                    'win_rate': live_summary.get('win_rate', 0),
                    'avg_return': live_summary.get('avg_return_pct', 0),
                    'total_return': live_summary.get('total_return_pct', 0)
                },
                'backtest': {
                    'win_rate': backtest_data.get('win_rate', 0),
                    'avg_return': (backtest_data.get('avg_win', 0) + backtest_data.get('avg_loss', 0)) / 2,
                    'total_return': backtest_data.get('total_return_pct', 0)
                }
            }

        except Exception as e:
            logger.error(f"Error getting backtest comparison: {e}")
            return {
                'live': {'win_rate': 0, 'avg_return': 0, 'total_return': 0},
                'backtest': {'win_rate': 0, 'avg_return': 0, 'total_return': 0}
            }

    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


def run_server(port: int = 8001):
    """
    Run the paper trading API server.

    Args:
        port: Port number
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, PaperTradingAPIHandler)

    print("=" * 70)
    print("PAPER TRADING DASHBOARD SERVER")
    print("=" * 70)
    print(f"\nServer running on http://localhost:{port}")
    print(f"Dashboard: Open paper_trading_dashboard.html in your browser")
    print("\nPress Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    parser = argparse.ArgumentParser(description='Run paper trading dashboard server')
    parser.add_argument('--port', type=int, default=8001, help='Port number (default: 8001)')

    args = parser.parse_args()

    run_server(args.port)
