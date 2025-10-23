#!/usr/bin/env python3
"""
Simple HTTP server to serve dashboard data from the SQLite database.
Run with: python dashboard_server.py
"""

import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime, timedelta
import os

# Configuration
DATABASE_PATH = 'data/trading.db'
PORT = 8000


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)

        # Enable CORS
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if parsed_path.path == '/api/data':
            data = self.get_dashboard_data()
            self.wfile.write(json.dumps(data).encode())
        else:
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def get_dashboard_data(self):
        """Fetch all data needed for the dashboard"""
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            # Get live announcements statistics
            cursor.execute('''
                SELECT COUNT(*) as total,
                       SUM(price_sensitive) as sensitive,
                       COUNT(DISTINCT ticker) as companies
                FROM live_announcements
            ''')
            row = cursor.fetchone()
            total_announcements = row['total'] or 0
            price_sensitive = row['sensitive'] or 0
            unique_companies = row['companies'] or 0

            # Alpha window metrics
            cursor.execute('''
                SELECT
                    COUNT(CASE WHEN age_minutes < 5 THEN 1 END) as ultra_fresh,
                    COUNT(CASE WHEN age_minutes BETWEEN 5 AND 15 THEN 1 END) as fresh,
                    COUNT(CASE WHEN age_minutes > 30 THEN 1 END) as stale
                FROM live_announcements
            ''')
            alpha = cursor.fetchone()

            # Recommendations count
            cursor.execute('SELECT COUNT(*) as count FROM live_recommendations')
            recommendations_count = cursor.fetchone()['count'] or 0

            # Get recent announcements
            cursor.execute('''
                SELECT ticker, title, announcement_type, price_sensitive,
                       age_minutes, detected_timestamp, processed
                FROM live_announcements
                ORDER BY detected_timestamp DESC
                LIMIT 50
            ''')
            recent_announcements = [dict(row) for row in cursor.fetchall()]

            # Get trade outcomes with full details (announcement -> recommendation -> outcome)
            cursor.execute('''
                SELECT
                    t.id, t.ticker, t.entry_price, t.exit_price, t.return_pct,
                    t.return_dollars, t.holding_days, t.outcome, t.exit_reason,
                    t.entry_timestamp, t.exit_timestamp, t.peak_price, t.lowest_price,
                    r.recommendation, r.confidence, r.sentiment,
                    a.title as announcement_title, a.announcement_type, a.detected_timestamp
                FROM trade_outcomes t
                JOIN live_recommendations r ON t.recommendation_id = r.id
                JOIN live_announcements a ON t.announcement_id = a.id
                ORDER BY t.entry_timestamp DESC
                LIMIT 50
            ''')
            trade_outcomes = [dict(row) for row in cursor.fetchall()]

            # P&L Summary
            cursor.execute('''
                SELECT
                    COUNT(*) as total_trades,
                    COUNT(CASE WHEN outcome = 'WIN' THEN 1 END) as wins,
                    COUNT(CASE WHEN outcome = 'LOSS' THEN 1 END) as losses,
                    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_trades,
                    SUM(return_dollars) as total_pnl,
                    AVG(return_pct) as avg_return,
                    MAX(return_pct) as best_trade,
                    MIN(return_pct) as worst_trade
                FROM trade_outcomes
                WHERE status = 'CLOSED'
            ''')
            pnl = cursor.fetchone()

            total_trades = pnl['total_trades'] or 0
            wins = pnl['wins'] or 0
            losses = pnl['losses'] or 0

            pnl_summary = {
                'total_trades': total_trades,
                'wins': wins,
                'losses': losses,
                'open_trades': pnl['open_trades'] or 0,
                'win_rate': round((wins / total_trades * 100) if total_trades > 0 else 0, 1),
                'total_pnl': round(pnl['total_pnl'], 2) if pnl['total_pnl'] else 0,
                'avg_return': round(pnl['avg_return'], 2) if pnl['avg_return'] else 0,
                'best_trade': round(pnl['best_trade'], 2) if pnl['best_trade'] else 0,
                'worst_trade': round(pnl['worst_trade'], 2) if pnl['worst_trade'] else 0
            }

            # Cumulative P&L over time
            cursor.execute('''
                SELECT entry_timestamp, return_dollars, ticker
                FROM trade_outcomes
                WHERE status = 'CLOSED'
                ORDER BY entry_timestamp ASC
            ''')
            cumulative_data = []
            cumulative_pnl = 0
            for row in cursor.fetchall():
                cumulative_pnl += row['return_dollars'] or 0
                cumulative_data.append({
                    'timestamp': row['entry_timestamp'],
                    'ticker': row['ticker'],
                    'pnl': round(cumulative_pnl, 2)
                })

            return {
                'stats': {
                    'total_announcements': total_announcements,
                    'price_sensitive': price_sensitive,
                    'price_sensitive_pct': round((price_sensitive / total_announcements * 100) if total_announcements else 0, 1),
                    'unique_companies': unique_companies,
                    'ultra_fresh': alpha['ultra_fresh'] or 0,
                    'ultra_fresh_pct': round((alpha['ultra_fresh'] / total_announcements * 100) if total_announcements else 0, 1),
                    'fresh': alpha['fresh'] or 0,
                    'stale': alpha['stale'] or 0,
                    'recommendations': recommendations_count,
                    'filter_pass_rate': round((recommendations_count / total_announcements * 100) if total_announcements else 0, 1)
                },
                'pnl_summary': pnl_summary,
                'trade_outcomes': trade_outcomes,
                'cumulative_pnl': cumulative_data,
                'announcements': recent_announcements
            }

        except Exception as e:
            print(f"Error fetching data: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'stats': {
                    'total_announcements': 0,
                    'price_sensitive': 0,
                    'price_sensitive_pct': 0,
                    'unique_companies': 0,
                    'ultra_fresh': 0,
                    'ultra_fresh_pct': 0,
                    'fresh': 0,
                    'stale': 0,
                    'recommendations': 0,
                    'filter_pass_rate': 0
                },
                'pnl_summary': {
                    'total_trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'open_trades': 0,
                    'win_rate': 0,
                    'total_pnl': 0,
                    'avg_return': 0,
                    'best_trade': 0,
                    'worst_trade': 0
                },
                'trade_outcomes': [],
                'cumulative_pnl': [],
                'announcements': []
            }
        finally:
            conn.close()

    def log_message(self, format, *args):
        """Custom log format"""
        print(f"{self.address_string()} - [{self.log_date_time_string()}] {format % args}")


def run_server():
    """Start the HTTP server"""
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"ERROR: Database not found at {DATABASE_PATH}")
        print("Please run the scrapers first to create the database.")
        return

    server_address = ('', PORT)
    httpd = HTTPServer(server_address, DashboardHandler)

    print("=" * 70)
    print(f"ASX Trading Dashboard Server")
    print("=" * 70)
    print(f"Server running on: http://localhost:{PORT}")
    print(f"Database: {os.path.abspath(DATABASE_PATH)}")
    print(f"\nOpen your browser and navigate to:")
    print(f"  file:///{os.path.abspath('dashboard.html')}")
    print(f"\nPress Ctrl+C to stop the server")
    print("=" * 70)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        httpd.shutdown()


if __name__ == '__main__':
    run_server()
