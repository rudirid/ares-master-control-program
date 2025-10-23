"""
Stock Price Change Analyzer

Calculates price changes following news article publication dates.
Compares stock prices at 1, 3, and 7 days after article publication.

Author: Claude Code
Date: 2025-10-09
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class PriceAnalyzer:
    """
    Analyzes stock price changes following news events.
    """

    def __init__(self, db_path: str):
        """
        Initialize the price analyzer.

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path

    def get_price_on_date(self, ticker: str, target_date: str) -> Optional[float]:
        """
        Get the closing price for a ticker on a specific date.

        If exact date not available, returns the next available trading day's price.

        Args:
            ticker: Stock ticker symbol
            target_date: Date string in YYYY-MM-DD format

        Returns:
            Closing price or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Try exact date first
            cursor.execute("""
                SELECT close FROM stock_prices
                WHERE ticker = ? AND date = ?
            """, (ticker, target_date))

            result = cursor.fetchone()

            if result:
                conn.close()
                return float(result[0])

            # If exact date not found, get the next available trading day
            cursor.execute("""
                SELECT close, date FROM stock_prices
                WHERE ticker = ? AND date >= ?
                ORDER BY date ASC
                LIMIT 1
            """, (ticker, target_date))

            result = cursor.fetchone()
            conn.close()

            if result:
                logger.debug(f"Using date {result[1]} for target {target_date}")
                return float(result[0])

            return None

        except Exception as e:
            logger.error(f"Error getting price for {ticker} on {target_date}: {e}")
            return None

    def get_price_change(self, ticker: str, start_date: str, days_after: int) -> Optional[Dict]:
        """
        Calculate price change from start_date to days_after.

        Args:
            ticker: Stock ticker symbol
            start_date: Starting date (article publication) in YYYY-MM-DD format
            days_after: Number of days after start_date

        Returns:
            Dictionary with:
                - start_price: Price at start_date
                - end_price: Price after N days
                - price_change: Absolute change
                - price_change_pct: Percentage change
                - days_actual: Actual trading days used
            Or None if data not available
        """
        try:
            # Get start price
            start_price = self.get_price_on_date(ticker, start_date)
            if start_price is None:
                logger.debug(f"No start price for {ticker} on {start_date}")
                return None

            # Calculate target end date
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = start_dt + timedelta(days=days_after)
            end_date = end_dt.strftime('%Y-%m-%d')

            # Get end price
            end_price = self.get_price_on_date(ticker, end_date)
            if end_price is None:
                logger.debug(f"No end price for {ticker} on {end_date}")
                return None

            # Calculate changes
            price_change = end_price - start_price
            price_change_pct = (price_change / start_price) * 100

            return {
                'start_price': round(start_price, 2),
                'end_price': round(end_price, 2),
                'price_change': round(price_change, 2),
                'price_change_pct': round(price_change_pct, 2),
                'start_date': start_date,
                'end_date': end_date,
                'days_after': days_after
            }

        except Exception as e:
            logger.error(f"Error calculating price change: {e}")
            return None

    def analyze_article_impact(self, ticker: str, article_date: str) -> Dict:
        """
        Analyze stock price impact at 1, 3, and 7 days after article publication.

        Args:
            ticker: Stock ticker symbol
            article_date: Article publication date (YYYY-MM-DD or datetime string)

        Returns:
            Dictionary with price changes for 1, 3, and 7 days
        """
        try:
            # Parse date if it's a datetime string
            if ' ' in article_date:
                article_date = article_date.split(' ')[0]

            result = {
                'ticker': ticker,
                'article_date': article_date,
                'day_1': None,
                'day_3': None,
                'day_7': None
            }

            # Calculate changes for each time period
            for days in [1, 3, 7]:
                change = self.get_price_change(ticker, article_date, days)
                if change:
                    result[f'day_{days}'] = change

            return result

        except Exception as e:
            logger.error(f"Error analyzing article impact: {e}")
            return {
                'ticker': ticker,
                'article_date': article_date,
                'day_1': None,
                'day_3': None,
                'day_7': None,
                'error': str(e)
            }

    def get_baseline_volatility(self, ticker: str, start_date: str, days: int = 30) -> Optional[float]:
        """
        Calculate baseline volatility (standard deviation of daily returns)
        for comparison purposes.

        Args:
            ticker: Stock ticker symbol
            start_date: Starting date
            days: Number of days to look back

        Returns:
            Standard deviation of daily returns (%) or None
        """
        try:
            conn = sqlite3.connect(self.db_path)

            # Get historical prices
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            lookback_dt = start_dt - timedelta(days=days)
            lookback_date = lookback_dt.strftime('%Y-%m-%d')

            query = """
                SELECT date, close
                FROM stock_prices
                WHERE ticker = ?
                AND date >= ?
                AND date < ?
                ORDER BY date ASC
            """

            df = pd.read_sql_query(query, conn, params=(ticker, lookback_date, start_date))
            conn.close()

            if len(df) < 5:
                return None

            # Calculate daily returns
            df['returns'] = df['close'].pct_change() * 100

            # Return standard deviation
            return round(df['returns'].std(), 2)

        except Exception as e:
            logger.error(f"Error calculating baseline volatility: {e}")
            return None


def test_price_analyzer():
    """
    Test the price analyzer with sample data.
    """
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

    print("\n" + "=" * 70)
    print("Testing Price Analyzer")
    print("=" * 70 + "\n")

    analyzer = PriceAnalyzer(config.DATABASE_PATH)

    # Test with a sample date and ticker
    test_ticker = "BHP"
    test_date = "2025-07-01"

    print(f"Testing price analysis for {test_ticker} on {test_date}")
    print("-" * 70)

    # Test getting a single price
    price = analyzer.get_price_on_date(test_ticker, test_date)
    print(f"Price on {test_date}: ${price:.2f}" if price else "No price data available")

    # Test price changes
    for days in [1, 3, 7]:
        change = analyzer.get_price_change(test_ticker, test_date, days)
        if change:
            print(f"\n{days}-day change:")
            print(f"  Start: ${change['start_price']:.2f}")
            print(f"  End: ${change['end_price']:.2f}")
            print(f"  Change: ${change['price_change']:.2f} ({change['price_change_pct']:+.2f}%)")
        else:
            print(f"\n{days}-day change: No data available")

    # Test full article impact analysis
    print("\n" + "-" * 70)
    print("Full article impact analysis:")
    print("-" * 70)

    impact = analyzer.analyze_article_impact(test_ticker, test_date)

    for days in [1, 3, 7]:
        key = f'day_{days}'
        if impact[key]:
            data = impact[key]
            print(f"\nDay {days}:")
            print(f"  Price change: ${data['price_change']:+.2f} ({data['price_change_pct']:+.2f}%)")
        else:
            print(f"\nDay {days}: No data")

    # Test baseline volatility
    print("\n" + "-" * 70)
    volatility = analyzer.get_baseline_volatility(test_ticker, test_date, days=30)
    if volatility:
        print(f"30-day baseline volatility: {volatility:.2f}%")
    else:
        print("Baseline volatility: No data")

    print("\n" + "=" * 70)
    print("Testing complete!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    test_price_analyzer()
