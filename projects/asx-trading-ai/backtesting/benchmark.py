"""
Benchmark Calculator for Buy-and-Hold Comparison

Calculates returns from simple buy-and-hold strategies for comparison
against active trading strategies.

Author: Claude Code
Date: 2025-10-09
"""

import pandas as pd
import numpy as np
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class BenchmarkCalculator:
    """
    Calculates benchmark buy-and-hold returns for comparison.
    """

    def __init__(self, db_path: str):
        """
        Initialize the benchmark calculator.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def get_price_on_date(self, ticker: str, date: str) -> Optional[float]:
        """
        Get stock price on a specific date.

        Args:
            ticker: Stock ticker
            date: Date string (YYYY-MM-DD)

        Returns:
            Close price or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT close FROM stock_prices
                WHERE ticker = ? AND date >= ?
                ORDER BY date ASC
                LIMIT 1
            """
            result = pd.read_sql_query(query, conn, params=(ticker, date))
            conn.close()

            if len(result) > 0:
                return float(result['close'].iloc[0])
            return None

        except Exception as e:
            logger.error(f"Error getting price for {ticker} on {date}: {e}")
            return None

    def calculate_buy_and_hold(self, csv_path: str, initial_capital: float = 100000.0) -> Dict:
        """
        Calculate buy-and-hold returns over the same period as the backtest.

        Strategy: Buy equal-weight portfolio of all stocks mentioned in news
        at the start date and hold until end date.

        Args:
            csv_path: Path to news impact analysis CSV
            initial_capital: Starting capital

        Returns:
            Dictionary with benchmark results
        """
        logger.info("Calculating buy-and-hold benchmark...")

        try:
            # Load news data to get date range and tickers
            df = pd.read_csv(csv_path)
            df['article_date'] = pd.to_datetime(df['article_date'])
            df = df.sort_values('article_date').reset_index(drop=True)

            # Filter articles with price data
            df = df[df['price_change_pct_1d'].notna()].reset_index(drop=True)

            if len(df) == 0:
                return {'error': 'No articles with price data'}

            start_date = df['article_date'].min().strftime('%Y-%m-%d')
            end_date = df['article_date'].max().strftime('%Y-%m-%d')

            # Get unique tickers
            tickers = df['ticker'].unique().tolist()

            logger.info(f"Period: {start_date} to {end_date}")
            logger.info(f"Tickers: {len(tickers)} stocks")

            # Equal weight per stock
            capital_per_stock = initial_capital / len(tickers)

            positions = []

            for ticker in tickers:
                # Get entry price
                entry_price = self.get_price_on_date(ticker, start_date)
                if entry_price is None:
                    logger.warning(f"No entry price for {ticker}")
                    continue

                # Get exit price
                exit_price = self.get_price_on_date(ticker, end_date)
                if exit_price is None:
                    logger.warning(f"No exit price for {ticker}")
                    continue

                # Calculate shares (no fractional shares)
                shares = int(capital_per_stock / entry_price)
                if shares == 0:
                    continue

                # Calculate returns
                cost = shares * entry_price
                value = shares * exit_price
                profit = value - cost
                return_pct = (profit / cost) * 100

                positions.append({
                    'ticker': ticker,
                    'shares': shares,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'cost': cost,
                    'value': value,
                    'profit': profit,
                    'return_pct': return_pct
                })

            if len(positions) == 0:
                return {'error': 'No positions could be established'}

            # Calculate overall performance
            total_invested = sum(p['cost'] for p in positions)
            total_value = sum(p['value'] for p in positions)
            unused_cash = initial_capital - total_invested
            final_value = total_value + unused_cash

            total_return = ((final_value - initial_capital) / initial_capital) * 100

            # Calculate drawdown
            # Simplified: we don't have daily portfolio values, so estimate based on individual stocks
            max_drawdown = self._estimate_max_drawdown(positions, start_date, end_date)

            results = {
                'strategy': 'Buy and Hold',
                'initial_capital': initial_capital,
                'total_invested': round(total_invested, 2),
                'final_value': round(final_value, 2),
                'total_return_pct': round(total_return, 2),
                'max_drawdown_pct': round(max_drawdown, 2),
                'num_positions': len(positions),
                'start_date': start_date,
                'end_date': end_date,
                'winning_positions': len([p for p in positions if p['profit'] > 0]),
                'losing_positions': len([p for p in positions if p['profit'] <= 0]),
                'avg_return_pct': round(np.mean([p['return_pct'] for p in positions]), 2)
            }

            logger.info(f"Benchmark return: {total_return:+.2f}%")

            return results

        except Exception as e:
            logger.error(f"Error calculating benchmark: {e}")
            return {'error': str(e)}

    def _estimate_max_drawdown(self, positions: List[Dict], start_date: str, end_date: str) -> float:
        """
        Estimate maximum drawdown.

        Note: This is a simplified estimation. For accurate drawdown,
        we'd need daily portfolio values.

        Args:
            positions: List of position dictionaries
            start_date: Start date
            end_date: End date

        Returns:
            Estimated max drawdown percentage
        """
        try:
            # For simplicity, calculate max individual stock drawdown
            # and use the worst one as an estimate
            max_dd = 0

            for position in positions:
                ticker = position['ticker']

                # Get all prices in range
                conn = sqlite3.connect(self.db_path)
                query = """
                    SELECT date, close FROM stock_prices
                    WHERE ticker = ? AND date >= ? AND date <= ?
                    ORDER BY date ASC
                """
                prices = pd.read_sql_query(
                    query,
                    conn,
                    params=(ticker, start_date, end_date)
                )
                conn.close()

                if len(prices) < 2:
                    continue

                # Calculate drawdown
                peak = prices['close'].iloc[0]
                for price in prices['close']:
                    if price > peak:
                        peak = price
                    dd = ((peak - price) / peak) * 100
                    max_dd = max(max_dd, dd)

            return max_dd

        except Exception as e:
            logger.error(f"Error calculating drawdown: {e}")
            return 0.0

    def calculate_index_benchmark(
        self,
        start_date: str,
        end_date: str,
        initial_capital: float = 100000.0,
        index_ticker: str = "^AXJO"  # ASX200
    ) -> Dict:
        """
        Calculate returns from holding an index (e.g., ASX200).

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            initial_capital: Starting capital
            index_ticker: Index ticker (default: ASX200)

        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Calculating {index_ticker} index benchmark...")

        try:
            entry_price = self.get_price_on_date(index_ticker, start_date)
            exit_price = self.get_price_on_date(index_ticker, end_date)

            if entry_price is None or exit_price is None:
                return {'error': f'No price data for {index_ticker}'}

            # Calculate return
            price_return = ((exit_price - entry_price) / entry_price) * 100

            results = {
                'strategy': f'Buy and Hold {index_ticker}',
                'initial_capital': initial_capital,
                'final_value': round(initial_capital * (1 + price_return / 100), 2),
                'total_return_pct': round(price_return, 2),
                'start_date': start_date,
                'end_date': end_date,
                'entry_price': entry_price,
                'exit_price': exit_price
            }

            logger.info(f"Index return: {price_return:+.2f}%")

            return results

        except Exception as e:
            logger.error(f"Error calculating index benchmark: {e}")
            return {'error': str(e)}


def main():
    """
    Test the benchmark calculator.
    """
    import sys
    import os

    # Add project root to path
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import config

    print("\n" + "=" * 70)
    print("Benchmark Calculator Test")
    print("=" * 70 + "\n")

    csv_path = 'results/news_impact_analysis.csv'

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        print("Please run analyze_news_impact.py first")
        return

    calculator = BenchmarkCalculator(config.DATABASE_PATH)
    results = calculator.calculate_buy_and_hold(csv_path, initial_capital=100000)

    if 'error' not in results:
        print("Buy and Hold Results:")
        print(f"  Period: {results['start_date']} to {results['end_date']}")
        print(f"  Initial Capital: ${results['initial_capital']:,.2f}")
        print(f"  Total Invested: ${results['total_invested']:,.2f}")
        print(f"  Final Value: ${results['final_value']:,.2f}")
        print(f"  Total Return: {results['total_return_pct']:+.2f}%")
        print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")
        print(f"  Positions: {results['num_positions']}")
        print(f"  Winning: {results['winning_positions']}")
        print(f"  Losing: {results['losing_positions']}")
        print(f"  Avg Return per Stock: {results['avg_return_pct']:+.2f}%")
    else:
        print(f"Error: {results['error']}")

    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
