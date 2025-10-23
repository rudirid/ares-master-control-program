"""
Risk Dashboard Server

HTTP server that provides risk data for the risk management dashboard.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from paper_trading.risk_manager import RiskManager, RiskConfig, SECTOR_MAP

logger = logging.getLogger(__name__)


class RiskDashboardAPIHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for risk dashboard API.
    """

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/api/risk-data':
            self.serve_risk_data()
        else:
            self.send_error(404, 'Not Found')

    def serve_risk_data(self):
        """Serve risk management data as JSON."""
        try:
            # Initialize risk manager
            risk_config = RiskConfig(
                portfolio_value=100000,
                min_confidence=0.7,
                stop_loss_pct=5.0,
                max_risk_per_trade_pct=2.0,
                max_positions_per_sector=3,
                daily_loss_limit_pct=5.0
            )
            risk_manager = RiskManager(config.DATABASE_PATH, risk_config)

            # Get risk summary
            summary = risk_manager.get_risk_summary()

            # Get enhanced metrics
            metrics = {
                'portfolio_value': summary['portfolio_value'],
                'total_exposure': summary['total_exposure'],
                'exposure_pct': summary['exposure_pct'],
                'available_capital': summary['available_capital'],
                'active_positions_count': summary['active_positions_count'],
                'daily_loss_pct': summary['daily_loss_pct'],
                'limits': summary['risk_limits']
            }

            # Circuit breaker
            circuit_breaker = summary['circuit_breaker']

            # Exposure breakdown
            exposure_breakdown = self.calculate_exposure_breakdown(
                summary['total_exposure'],
                summary['available_capital'],
                risk_config.max_risk_per_trade_pct,
                summary['active_positions_count']
            )

            # Active positions with current prices
            active_positions = self.get_active_positions_with_prices(summary['active_positions'])

            # Correlation matrix
            correlation_matrix = self.calculate_correlation_matrix(summary['active_positions'])

            # Worst case scenario
            worst_case = self.calculate_worst_case_scenario(
                summary['active_positions'],
                risk_config.portfolio_value,
                risk_config.stop_loss_pct
            )

            data = {
                'metrics': metrics,
                'circuit_breaker': circuit_breaker,
                'exposure_breakdown': exposure_breakdown,
                'sector_exposure': summary['sector_exposure'],
                'active_positions': active_positions,
                'correlation_matrix': correlation_matrix,
                'worst_case': worst_case,
                'risk_events': summary['recent_events']
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data, default=str).encode())

        except Exception as e:
            logger.error(f"Error serving risk data: {e}")
            self.send_error(500, str(e))

    def calculate_exposure_breakdown(
        self,
        total_exposure: float,
        available_capital: float,
        max_risk_per_trade_pct: float,
        num_positions: int
    ) -> dict:
        """Calculate exposure breakdown."""
        total = total_exposure + available_capital
        reserved_for_risk = (total * (max_risk_per_trade_pct / 100)) * num_positions

        return {
            'deployed': round(total_exposure, 2),
            'available': round(available_capital, 2),
            'reserved_for_risk': round(reserved_for_risk, 2)
        }

    def get_active_positions_with_prices(self, positions: list) -> list:
        """Get active positions with current prices and P/L."""
        conn = sqlite3.connect(config.DATABASE_PATH)
        cursor = conn.cursor()

        enhanced_positions = []

        for pos in positions:
            ticker = pos['ticker']

            # Get current price
            cursor.execute("""
                SELECT close FROM stock_prices
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT 1
            """, (ticker,))

            row = cursor.fetchone()
            current_price = row[0] if row else pos['entry_price']

            # Calculate current P/L
            current_pl_pct = ((current_price - pos['entry_price']) / pos['entry_price']) * 100

            # Calculate stop loss price
            stop_loss_pct = 5.0  # From config
            stop_loss_price = pos['entry_price'] * (1 - stop_loss_pct / 100)

            enhanced_positions.append({
                'ticker': ticker,
                'sector': pos['sector'],
                'entry_price': pos['entry_price'],
                'current_price': current_price,
                'current_pl_pct': round(current_pl_pct, 2),
                'stop_loss_price': round(stop_loss_price, 2),
                'stop_loss_pct': stop_loss_pct,
                'confidence': pos['confidence']
            })

        conn.close()

        return enhanced_positions

    def calculate_correlation_matrix(self, positions: list) -> list:
        """Calculate correlation between positions."""
        if len(positions) < 2:
            return []

        conn = sqlite3.connect(config.DATABASE_PATH)

        correlations = []
        tickers = [p['ticker'] for p in positions]

        for i, ticker1 in enumerate(tickers):
            for ticker2 in tickers[i+1:]:
                # Get price history for both tickers
                query = """
                    SELECT date, close FROM stock_prices
                    WHERE ticker = ?
                    AND date >= date('now', '-30 days')
                    ORDER BY date ASC
                """

                df1 = []
                for row in conn.execute(query, (ticker1,)):
                    df1.append(row[1])

                df2 = []
                for row in conn.execute(query, (ticker2,)):
                    df2.append(row[1])

                if len(df1) > 5 and len(df2) > 5 and len(df1) == len(df2):
                    # Calculate correlation
                    corr = np.corrcoef(df1, df2)[0, 1]

                    correlations.append({
                        'ticker1': ticker1,
                        'ticker2': ticker2,
                        'correlation': round(float(corr), 3)
                    })

        conn.close()

        return correlations

    def calculate_worst_case_scenario(
        self,
        positions: list,
        portfolio_value: float,
        stop_loss_pct: float
    ) -> dict:
        """Calculate worst case scenario if all positions hit stop loss."""
        if not positions:
            return {
                'total_capital_at_risk': 0,
                'max_loss': 0,
                'max_loss_pct': 0,
                'portfolio_value_after': portfolio_value,
                'recovery_pct_needed': 0
            }

        # Calculate total capital at risk
        total_at_risk = sum(p['position_value'] for p in positions)

        # Worst case: all positions hit stop loss
        max_loss = total_at_risk * (stop_loss_pct / 100)
        max_loss_pct = (max_loss / portfolio_value) * 100
        portfolio_value_after = portfolio_value - max_loss

        # Recovery percentage needed
        recovery_pct_needed = (max_loss / portfolio_value_after) * 100

        return {
            'total_capital_at_risk': round(total_at_risk, 2),
            'max_loss': round(max_loss, 2),
            'max_loss_pct': round(max_loss_pct, 2),
            'portfolio_value_after': round(portfolio_value_after, 2),
            'recovery_pct_needed': round(recovery_pct_needed, 2)
        }

    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


def run_server(port: int = 8002):
    """
    Run the risk dashboard API server.

    Args:
        port: Port number
    """
    server_address = ('', port)
    httpd = HTTPServer(server_address, RiskDashboardAPIHandler)

    print("=" * 70)
    print("RISK DASHBOARD SERVER")
    print("=" * 70)
    print(f"\nServer running on http://localhost:{port}")
    print(f"Dashboard: Open risk_dashboard.html in your browser")
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

    parser = argparse.ArgumentParser(description='Run risk dashboard server')
    parser.add_argument('--port', type=int, default=8002, help='Port number (default: 8002)')

    args = parser.parse_args()

    run_server(args.port)
