"""
Stock Prices Scraper for ASX stocks using yfinance.
Downloads OHLCV (Open, High, Low, Close, Volume) data and stores it in SQLite database.
"""
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yfinance as yf
import pandas as pd

import config
from scrapers.utils import get_logger

# Configure logging
logger = get_logger(__name__)


# SQL query to create stock_prices table
CREATE_STOCK_PRICES_TABLE = """
CREATE TABLE IF NOT EXISTS stock_prices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume INTEGER,
    adj_close REAL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ticker, date)
)
"""

# Create index for faster queries
CREATE_INDEX_QUERY = """
CREATE INDEX IF NOT EXISTS idx_ticker_date ON stock_prices(ticker, date DESC)
"""


def _get_db_connection(db_path: str) -> sqlite3.Connection:
    """
    Create and return a database connection.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table_exists(conn: sqlite3.Connection, table_name: str, create_query: str) -> None:
    """
    Ensure a table exists in the database, create it if it doesn't.

    Args:
        conn: Database connection
        table_name: Name of the table to check
        create_query: SQL CREATE TABLE query
    """
    cursor = conn.cursor()
    cursor.execute(f"""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name=?
    """, (table_name,))

    if not cursor.fetchone():
        logger.info(f"Creating table: {table_name}")
        cursor.execute(create_query)
        conn.commit()
    else:
        logger.debug(f"Table {table_name} already exists")


def _execute_batch_insert(
    conn: sqlite3.Connection,
    query: str,
    data: List[tuple],
    batch_size: int = 1000
) -> int:
    """
    Execute batch insert operation for better performance.

    Args:
        conn: Database connection
        query: SQL INSERT query with placeholders
        data: List of tuples containing data to insert
        batch_size: Number of rows to insert per batch

    Returns:
        int: Total number of rows inserted
    """
    cursor = conn.cursor()
    total_inserted = 0

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        cursor.executemany(query, batch)
        total_inserted += cursor.rowcount

    conn.commit()
    logger.debug(f"Inserted {total_inserted} rows in batches of {batch_size}")
    return total_inserted


def _parse_date_input(date_input: Union[str, datetime]) -> datetime:
    """
    Parse date input to datetime object.

    Args:
        date_input: Date as string or datetime

    Returns:
        datetime object
    """
    if isinstance(date_input, datetime):
        return date_input

    if isinstance(date_input, str):
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_input, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Could not parse date: {date_input}")
        except Exception as e:
            logger.error(f"Error parsing date {date_input}: {e}")
            raise

    raise TypeError(f"Unsupported date type: {type(date_input)}")


def download_stock_prices(
    tickers: List[str],
    start_date: Optional[Union[datetime, str]] = None,
    end_date: Optional[Union[datetime, str]] = None,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download stock price data for ASX tickers using yfinance.

    Args:
        tickers: List of ASX ticker symbols (without .AX suffix)
        start_date: Start date for data download (default: 2 years ago)
        end_date: End date for data download (default: today)
        db_path: Path to SQLite database (default: from config)

    Returns:
        Dict with summary statistics:
            - successful_tickers: List of successfully downloaded tickers
            - failed_tickers: List of failed tickers with error messages
            - total_rows_inserted: Total number of price records inserted
            - date_range: Tuple of (start_date, end_date)

    Example:
        >>> tickers = ['BHP', 'CBA', 'CSL']
        >>> result = download_stock_prices(tickers)
        >>> print(f"Downloaded {result['total_rows_inserted']} records")
    """
    # Set default parameters
    if db_path is None:
        db_path = config.DATABASE_PATH

    if end_date is None:
        end_date = datetime.now()
    else:
        end_date = _parse_date_input(end_date) if isinstance(end_date, str) else end_date

    if start_date is None:
        # Use STOCK_PRICE_YEARS from config
        start_date = end_date - timedelta(days=365 * config.STOCK_PRICE_YEARS)
    else:
        start_date = _parse_date_input(start_date) if isinstance(start_date, str) else start_date

    logger.info(f"Starting download for {len(tickers)} tickers from {start_date.date()} to {end_date.date()}")

    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Initialize database
    conn = _get_db_connection(db_path)
    _ensure_table_exists(conn, 'stock_prices', CREATE_STOCK_PRICES_TABLE)
    conn.execute(CREATE_INDEX_QUERY)
    conn.commit()

    # Track results
    successful_tickers = []
    failed_tickers = []
    total_rows_inserted = 0

    # Process each ticker
    for ticker in tickers:
        try:
            logger.info(f"Downloading data for {ticker}...")

            # Add .AX suffix for ASX stocks
            yf_ticker = f"{ticker}.AX"

            # Download data from yfinance
            stock = yf.Ticker(yf_ticker)
            df = stock.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"No data available for {ticker}")
                failed_tickers.append({
                    'ticker': ticker,
                    'error': 'No data available'
                })
                continue

            # Reset index to get date as a column
            df = df.reset_index()

            # Convert DataFrame to database format
            rows_inserted = _save_price_data_to_db(conn, ticker, df)

            total_rows_inserted += rows_inserted
            successful_tickers.append(ticker)

            logger.info(f"Successfully downloaded {rows_inserted} records for {ticker}.AX")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to download data for {ticker}: {error_msg}")
            failed_tickers.append({
                'ticker': ticker,
                'error': error_msg
            })
            continue

    conn.close()

    # Prepare summary
    summary = {
        'successful_tickers': successful_tickers,
        'failed_tickers': failed_tickers,
        'total_rows_inserted': total_rows_inserted,
        'date_range': (start_date.date(), end_date.date())
    }

    logger.info(f"Download complete: {len(successful_tickers)} successful, {len(failed_tickers)} failed")
    logger.info(f"Total rows inserted: {total_rows_inserted}")

    return summary


def _save_price_data_to_db(
    conn: sqlite3.Connection,
    ticker: str,
    df: pd.DataFrame
) -> int:
    """
    Save price data from DataFrame to database.

    Args:
        conn: Database connection
        ticker: Stock ticker symbol
        df: DataFrame with price data from yfinance

    Returns:
        int: Number of rows inserted/updated
    """
    # Prepare data for insertion
    insert_query = """
    INSERT OR REPLACE INTO stock_prices
    (ticker, date, open, high, low, close, volume, adj_close)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    rows = []
    for _, row in df.iterrows():
        # Extract date (handle both Timestamp and datetime)
        date_value = row['Date']
        if isinstance(date_value, pd.Timestamp):
            date_str = date_value.strftime('%Y-%m-%d')
        else:
            date_str = pd.to_datetime(date_value).strftime('%Y-%m-%d')

        # Prepare row data
        row_data = (
            ticker,
            date_str,
            float(row['Open']) if pd.notna(row['Open']) else None,
            float(row['High']) if pd.notna(row['High']) else None,
            float(row['Low']) if pd.notna(row['Low']) else None,
            float(row['Close']) if pd.notna(row['Close']) else None,
            int(row['Volume']) if pd.notna(row['Volume']) else None,
            float(row['Close']) if pd.notna(row['Close']) else None  # Using Close as adj_close
        )
        rows.append(row_data)

    # Execute batch insert
    rows_inserted = _execute_batch_insert(conn, insert_query, rows, batch_size=500)

    return rows_inserted


def get_asx200_tickers() -> List[str]:
    """
    Get list of major ASX stocks for testing.

    Note: This is a small subset for testing purposes.
    In production, this should be replaced with the full ASX200 list
    or loaded from an external source.

    Returns:
        List of ASX ticker symbols (without .AX suffix)
    """
    # Major ASX stocks for testing
    # TODO: Replace with full ASX200 ticker list from official source
    # Consider scraping from ASX website or using a financial data API

    test_tickers = [
        'BHP',   # BHP Group (Mining)
        'CBA',   # Commonwealth Bank (Banking)
        'CSL',   # CSL Limited (Healthcare)
        'NAB',   # National Australia Bank (Banking)
        'WBC',   # Westpac Banking (Banking)
        'ANZ',   # ANZ Banking Group (Banking)
        'WES',   # Wesfarmers (Retail)
        'MQG',   # Macquarie Group (Financial Services)
        'TLS',   # Telstra (Telecommunications)
        'WOW',   # Woolworths (Retail)
    ]

    logger.info(f"Using test ticker list with {len(test_tickers)} stocks")
    logger.warning("This is a test list. Replace get_asx200_tickers() with full ASX200 for production")

    return test_tickers


def get_price_statistics(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about the stored price data.

    Args:
        db_path: Path to SQLite database (default: from config)

    Returns:
        Dict with statistics including:
            - total_records: Total number of price records
            - unique_tickers: Number of unique tickers
            - date_range: Earliest and latest dates
            - records_per_ticker: Count of records per ticker
    """
    if db_path is None:
        db_path = config.DATABASE_PATH

    conn = _get_db_connection(db_path)
    cursor = conn.cursor()

    # Total records
    cursor.execute("SELECT COUNT(*) FROM stock_prices")
    total_records = cursor.fetchone()[0]

    # Unique tickers
    cursor.execute("SELECT COUNT(DISTINCT ticker) FROM stock_prices")
    unique_tickers = cursor.fetchone()[0]

    # Date range
    cursor.execute("SELECT MIN(date), MAX(date) FROM stock_prices")
    date_range = cursor.fetchone()

    # Records per ticker
    cursor.execute("""
        SELECT ticker, COUNT(*) as count
        FROM stock_prices
        GROUP BY ticker
        ORDER BY count DESC
    """)
    records_per_ticker = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()

    return {
        'total_records': total_records,
        'unique_tickers': unique_tickers,
        'date_range': date_range,
        'records_per_ticker': records_per_ticker
    }


if __name__ == '__main__':
    """
    Main execution block for testing the scraper.
    Downloads data for test tickers and displays summary statistics.
    """
    logger.info("=" * 60)
    logger.info("Stock Prices Scraper - ASX Data Download")
    logger.info("=" * 60)

    # Get test tickers
    tickers = get_asx200_tickers()

    # Download stock prices
    result = download_stock_prices(tickers)

    # Display results
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Date Range: {result['date_range'][0]} to {result['date_range'][1]}")
    print(f"Successful: {len(result['successful_tickers'])} tickers")
    print(f"Failed: {len(result['failed_tickers'])} tickers")
    print(f"Total Records Inserted: {result['total_rows_inserted']}")

    if result['successful_tickers']:
        print(f"\nSuccessful tickers: {', '.join(result['successful_tickers'])}")

    if result['failed_tickers']:
        print("\nFailed tickers:")
        for failed in result['failed_tickers']:
            print(f"  - {failed['ticker']}: {failed['error']}")

    # Get and display database statistics
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    stats = get_price_statistics()
    print(f"Total Records: {stats['total_records']}")
    print(f"Unique Tickers: {stats['unique_tickers']}")
    print(f"Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")

    print("\nRecords per ticker:")
    for ticker, count in stats['records_per_ticker'].items():
        print(f"  {ticker}: {count} records")

    print("\n" + "=" * 60)
    print("Download complete! Database location:")
    print(config.DATABASE_PATH)
    print("=" * 60)
