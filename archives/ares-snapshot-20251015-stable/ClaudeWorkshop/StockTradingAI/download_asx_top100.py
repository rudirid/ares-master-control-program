#!/usr/bin/env python3
"""
ASX Top 100 Historical Data Downloader

Downloads 2 years of historical stock price data for the ASX Top 100 companies.
Uses yfinance library for reliable data fetching.
Stores in the same SQLite database as news data with proper date indexing.

Features:
- Fetches OHLCV data (Open, High, Low, Close, Volume)
- Date range: 2 years historical
- Handles missing data and delisted stocks
- Progress tracking and error handling
- Database integration with existing news data
- Date alignment for multi-source analysis

Usage:
    python download_asx_top100.py

Author: Claude Code
Date: 2025-10-09
"""

import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Tuple
import sys
import os

# Import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from scrapers.utils import get_logger

# Initialize logger
logger = get_logger(__name__)

# ASX Top 100 Companies (as of 2024)
# Format: Ticker symbol (without .AX suffix, we'll add that)
ASX_TOP_100 = [
    # Top 10
    'BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'WDS', 'GMG',
    # 11-20
    'FMG', 'RIO', 'TCL', 'WOW', 'TLS', 'SCG', 'QBE', 'COL', 'STO', 'AMC',
    # 21-30
    'REA', 'QAN', 'ALL', 'ORG', 'WTC', 'S32', 'RHC', 'APA', 'IAG', 'SHL',
    # 31-40
    'NCM', 'ASX', 'CPU', 'ALX', 'SUN', 'LLC', 'AZJ', 'MIN', 'AMP', 'BXB',
    # 41-50
    'CHC', 'GPT', 'SOL', 'EVN', 'DXS', 'VCX', 'MGR', 'WOR', 'JHX', 'NXT',
    # 51-60
    'ALU', 'ILU', 'CIM', 'AGL', 'SEK', 'ORE', 'HVN', 'TWE', 'OZL', 'LYC',
    # 61-70
    'BEN', 'ANN', 'NST', 'IGO', 'WHC', 'PDL', 'ARB', 'IPL', 'CAR', 'IFL',
    # 71-80
    'EDV', 'SVW', 'JBH', 'BOQ', 'RMD', 'AWC', 'CHN', 'BSL', 'SUL', 'SGP',
    # 81-90
    'PLS', 'NHF', 'ALD', 'TPG', 'CIA', 'DMP', 'WHC', 'IEL', 'AVA', 'SGM',
    # 91-100
    'TNE', 'PME', 'LOV', 'BWP', 'MPL', 'CQR', 'CMW', 'JHG', 'NWS', 'SDF',
]


def get_asx_ticker(symbol: str) -> str:
    """
    Convert ASX symbol to yfinance format.

    Args:
        symbol: ASX ticker symbol (e.g., 'BHP')

    Returns:
        yfinance formatted ticker (e.g., 'BHP.AX')
    """
    return f"{symbol}.AX"


def download_stock_data(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Download historical stock data using yfinance.

    Args:
        ticker: Stock ticker symbol (ASX format, e.g., 'BHP')
        start_date: Start date for historical data
        end_date: End date for historical data

    Returns:
        DataFrame with OHLCV data, or None if download fails
    """
    try:
        yf_ticker = get_asx_ticker(ticker)
        logger.info(f"Downloading data for {ticker} ({yf_ticker})...")

        stock = yf.Ticker(yf_ticker)
        df = stock.history(start=start_date, end=end_date, auto_adjust=False)

        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return None

        # Reset index to make date a column
        df.reset_index(inplace=True)

        # Rename columns to match our database schema
        df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adj_close',
        }, inplace=True)

        # Add ticker column
        df['ticker'] = ticker

        # Convert date to string format (YYYY-MM-DD)
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')

        # Select only the columns we need
        df = df[['ticker', 'date', 'open', 'high', 'low', 'close', 'volume', 'adj_close']]

        logger.info(f"Successfully downloaded {len(df)} records for {ticker}")
        return df

    except Exception as e:
        logger.error(f"Error downloading data for {ticker}: {e}")
        return None


def save_to_database(df: pd.DataFrame, db_path: str) -> Tuple[int, int]:
    """
    Save stock data to database.

    Uses INSERT OR REPLACE to handle duplicates.

    Args:
        df: DataFrame with stock data
        db_path: Path to SQLite database

    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    if df is None or df.empty:
        return 0, 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        inserted = 0
        skipped = 0

        for _, row in df.iterrows():
            try:
                # Check if record already exists
                cursor.execute("""
                    SELECT id FROM stock_prices
                    WHERE ticker = ? AND date = ?
                """, (row['ticker'], row['date']))

                exists = cursor.fetchone()

                if exists:
                    skipped += 1
                    continue

                # Insert new record
                cursor.execute("""
                    INSERT INTO stock_prices
                    (ticker, date, open, high, low, close, volume, adj_close, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """, (
                    row['ticker'],
                    row['date'],
                    row['open'],
                    row['high'],
                    row['low'],
                    row['close'],
                    row['volume'],
                    row['adj_close']
                ))

                inserted += 1

            except Exception as e:
                logger.error(f"Error inserting row: {e}")
                skipped += 1

        conn.commit()
        conn.close()

        return inserted, skipped

    except Exception as e:
        logger.error(f"Database error: {e}")
        return 0, 0


def download_all_stocks(tickers: List[str], start_date: datetime, end_date: datetime,
                       db_path: str, delay: float = 0.5) -> Dict:
    """
    Download historical data for all tickers.

    Args:
        tickers: List of ticker symbols
        start_date: Start date for historical data
        end_date: End date for historical data
        db_path: Path to SQLite database
        delay: Delay between requests in seconds (to be respectful)

    Returns:
        Dictionary with download statistics
    """
    logger.info("=" * 70)
    logger.info("ASX Top 100 Historical Data Download")
    logger.info("=" * 70)
    logger.info(f"Tickers to download: {len(tickers)}")
    logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info(f"Database: {db_path}")
    logger.info("=" * 70)

    successful_tickers = []
    failed_tickers = []
    total_records = 0
    total_inserted = 0
    total_skipped = 0

    for idx, ticker in enumerate(tickers, 1):
        logger.info(f"\n[{idx}/{len(tickers)}] Processing {ticker}...")

        # Download data
        df = download_stock_data(ticker, start_date, end_date)

        if df is not None and not df.empty:
            # Save to database
            inserted, skipped = save_to_database(df, db_path)

            successful_tickers.append(ticker)
            total_records += len(df)
            total_inserted += inserted
            total_skipped += skipped

            logger.info(f"  ✓ {ticker}: {inserted} inserted, {skipped} skipped (total: {len(df)} records)")
        else:
            failed_tickers.append(ticker)
            logger.warning(f"  ✗ {ticker}: Failed to download")

        # Rate limiting (be respectful to yfinance)
        if idx < len(tickers):
            time.sleep(delay)

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total tickers: {len(tickers)}")
    logger.info(f"Successful: {len(successful_tickers)}")
    logger.info(f"Failed: {len(failed_tickers)}")
    logger.info(f"Total records downloaded: {total_records}")
    logger.info(f"Records inserted: {total_inserted}")
    logger.info(f"Records skipped (duplicates): {total_skipped}")

    if failed_tickers:
        logger.warning(f"\nFailed tickers: {', '.join(failed_tickers[:20])}")
        if len(failed_tickers) > 20:
            logger.warning(f"  ... and {len(failed_tickers) - 20} more")

    # Database statistics
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM stock_prices')
        total_db_records = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT ticker) FROM stock_prices')
        unique_tickers = cursor.fetchone()[0]

        cursor.execute('SELECT MIN(date), MAX(date) FROM stock_prices')
        date_range = cursor.fetchone()

        conn.close()

        logger.info("\n" + "=" * 70)
        logger.info("DATABASE STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total records in database: {total_db_records:,}")
        logger.info(f"Unique tickers: {unique_tickers}")
        logger.info(f"Date range: {date_range[0]} to {date_range[1]}")
        logger.info("=" * 70)

    except Exception as e:
        logger.error(f"Error getting database statistics: {e}")

    return {
        'successful': successful_tickers,
        'failed': failed_tickers,
        'total_records': total_records,
        'inserted': total_inserted,
        'skipped': total_skipped,
    }


def main():
    """
    Main execution function.
    """
    print("\n" + "=" * 70)
    print("ASX Top 100 Historical Data Downloader")
    print("=" * 70 + "\n")

    # Configuration
    db_path = config.DATABASE_PATH
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years

    # Check if database exists
    if not os.path.exists(db_path):
        logger.error(f"Database not found at {db_path}")
        logger.error("Please run the database initialization script first.")
        return

    print(f"Configuration:")
    print(f"  Database: {db_path}")
    print(f"  Start date: {start_date.strftime('%Y-%m-%d')}")
    print(f"  End date: {end_date.strftime('%Y-%m-%d')}")
    print(f"  Tickers: {len(ASX_TOP_100)}")
    print()

    # Confirm before proceeding
    response = input("Proceed with download? This may take 10-15 minutes. (y/n): ")
    if response.lower() != 'y':
        print("Download cancelled.")
        return

    # Start download
    start_time = time.time()

    result = download_all_stocks(
        tickers=ASX_TOP_100,
        start_date=start_date,
        end_date=end_date,
        db_path=db_path,
        delay=0.5  # 500ms delay between requests
    )

    elapsed_time = time.time() - start_time

    # Final summary
    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)
    print(f"Time elapsed: {elapsed_time:.1f} seconds ({elapsed_time / 60:.1f} minutes)")
    print(f"Successful downloads: {len(result['successful'])}/{len(ASX_TOP_100)}")
    print(f"Total records: {result['total_records']:,}")
    print(f"New records inserted: {result['inserted']:,}")
    print(f"Duplicates skipped: {result['skipped']:,}")

    if result['failed']:
        print(f"\nFailed tickers ({len(result['failed'])}): {', '.join(result['failed'][:10])}")
        if len(result['failed']) > 10:
            print(f"  ... and {len(result['failed']) - 10} more")

    print("\n" + "=" * 70)
    print("Data is now ready for analysis!")
    print("Date indexing matches the news database for temporal alignment.")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
