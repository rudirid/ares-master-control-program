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
            # Get statistics
            cursor.execute('SELECT COUNT(DISTINCT ticker) as count FROM stock_prices')
            total_stocks = cursor.fetchone()['count']

            cursor.execute('SELECT COUNT(*) as count FROM stock_prices')
            price_records = cursor.fetchone()['count']

            cursor.execute('SELECT COUNT(*) as count FROM news_articles')
            news_articles = cursor.fetchone()['count']

            cursor.execute('SELECT COUNT(*) as count FROM asx_announcements')
            announcements = cursor.fetchone()['count']

            # Get list of tickers
            cursor.execute('SELECT DISTINCT ticker FROM stock_prices ORDER BY ticker')
            tickers = [row['ticker'] for row in cursor.fetchall()]

            # Get stock prices (last 100 days for each ticker)
            cursor.execute('''
                SELECT ticker, date, close, open, high, low, volume
                FROM stock_prices
                WHERE date >= date('now', '-100 days')
                ORDER BY ticker, date
            ''')
            stock_prices = [dict(row) for row in cursor.fetchall()]

            # Get recent news
            cursor.execute('''
                SELECT source, ticker, title,
                       COALESCE(datetime, created_at) as datetime
                FROM news_articles
                ORDER BY created_at DESC
                LIMIT 20
            ''')
            news = [dict(row) for row in cursor.fetchall()]

            # Calculate performance metrics (7-day)
            performance = []
            for ticker in tickers:
                cursor.execute('''
                    SELECT
                        close,
                        date,
                        MAX(high) as high,
                        MIN(low) as low
                    FROM stock_prices
                    WHERE ticker = ?
                    AND date >= date('now', '-7 days')
                    GROUP BY ticker
                    ORDER BY date DESC
                ''', (ticker,))

                rows = cursor.fetchall()
                if rows:
                    latest = rows[0]

                    # Get price from 7 days ago
                    cursor.execute('''
                        SELECT close
                        FROM stock_prices
                        WHERE ticker = ?
                        AND date <= date('now', '-7 days')
                        ORDER BY date DESC
                        LIMIT 1
                    ''', (ticker,))

                    week_ago_row = cursor.fetchone()
                    week_ago = week_ago_row['close'] if week_ago_row else latest['close']

                    performance.append({
                        'ticker': ticker,
                        'latest': latest['close'],
                        'high': latest['high'],
                        'low': latest['low'],
                        'week_ago': week_ago
                    })

            # Sort by absolute change
            performance.sort(key=lambda x: abs(x['latest'] - x['week_ago']), reverse=True)

            return {
                'stats': {
                    'total_stocks': total_stocks,
                    'price_records': price_records,
                    'news_articles': news_articles,
                    'announcements': announcements
                },
                'tickers': tickers,
                'stock_prices': stock_prices,
                'news': news,
                'performance': performance
            }

        except Exception as e:
            print(f"Error fetching data: {e}")
            return {
                'error': str(e),
                'stats': {
                    'total_stocks': 0,
                    'price_records': 0,
                    'news_articles': 0,
                    'announcements': 0
                },
                'tickers': [],
                'stock_prices': [],
                'news': [],
                'performance': []
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
