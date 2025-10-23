"""
SQLite Database Initialization Script for ASX Stock Trading Analysis System

This script creates and initializes the trading.db database with all required tables,
indexes, and constraints for the ASX stock trading analysis system.

Database: data/trading.db
Tables: asx_announcements, stock_prices, news_articles, director_trades, hotcopper_sentiment
"""

import sqlite3
import logging
import os
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_asx_announcements_table(cursor):
    """Create the asx_announcements table for storing ASX company announcements."""
    logger.info("Creating asx_announcements table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asx_announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            announcement_type TEXT,
            title TEXT,
            datetime TIMESTAMP,
            price_sensitive BOOLEAN,
            url TEXT UNIQUE,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for efficient querying
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_asx_announcements_ticker
        ON asx_announcements(ticker)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_asx_announcements_datetime
        ON asx_announcements(datetime)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_asx_announcements_price_sensitive
        ON asx_announcements(price_sensitive)
    """)

    logger.info("✓ asx_announcements table created successfully")


def create_stock_prices_table(cursor):
    """Create the stock_prices table for storing historical stock price data."""
    logger.info("Creating stock_prices table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date DATE NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            adj_close REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, date)
        )
    """)

    # Create indexes for efficient querying
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker
        ON stock_prices(ticker)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_prices_date
        ON stock_prices(date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_prices_ticker_date
        ON stock_prices(ticker, date)
    """)

    logger.info("✓ stock_prices table created successfully")


def create_news_articles_table(cursor):
    """Create the news_articles table for storing news articles about stocks."""
    logger.info("Creating news_articles table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            ticker TEXT,
            title TEXT,
            datetime TIMESTAMP,
            content TEXT,
            url TEXT UNIQUE,
            sentiment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for efficient querying
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_articles_ticker
        ON news_articles(ticker)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_articles_datetime
        ON news_articles(datetime)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_articles_source
        ON news_articles(source)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_news_articles_sentiment
        ON news_articles(sentiment)
    """)

    logger.info("✓ news_articles table created successfully")


def create_director_trades_table(cursor):
    """Create the director_trades table for storing director trading activity."""
    logger.info("Creating director_trades table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS director_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            company_name TEXT,
            director_name TEXT,
            trade_type TEXT CHECK(trade_type IN ('buy', 'sell')),
            shares INTEGER,
            price REAL,
            value REAL,
            trade_date DATE,
            notice_date DATE,
            url TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create indexes for efficient querying
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_director_trades_ticker
        ON director_trades(ticker)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_director_trades_trade_date
        ON director_trades(trade_date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_director_trades_trade_type
        ON director_trades(trade_type)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_director_trades_notice_date
        ON director_trades(notice_date)
    """)

    logger.info("✓ director_trades table created successfully")


def create_hotcopper_sentiment_table(cursor):
    """Create the hotcopper_sentiment table for storing Hotcopper forum sentiment data."""
    logger.info("Creating hotcopper_sentiment table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hotcopper_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            post_title TEXT,
            post_count INTEGER,
            sentiment_score REAL CHECK(sentiment_score >= -1 AND sentiment_score <= 1),
            date DATE,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(ticker, date)
        )
    """)

    # Create indexes for efficient querying
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_hotcopper_sentiment_ticker
        ON hotcopper_sentiment(ticker)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_hotcopper_sentiment_date
        ON hotcopper_sentiment(date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_hotcopper_sentiment_score
        ON hotcopper_sentiment(sentiment_score)
    """)

    logger.info("✓ hotcopper_sentiment table created successfully")


def check_existing_tables(cursor):
    """Check which tables already exist in the database."""
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table'
        ORDER BY name
    """)

    existing_tables = [row[0] for row in cursor.fetchall()]

    if existing_tables:
        logger.info(f"Existing tables found: {', '.join(existing_tables)}")
    else:
        logger.info("No existing tables found. Creating new database schema...")

    return existing_tables


def init_database(db_path):
    """
    Initialize the SQLite database with all required tables and indexes.

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Create data directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created directory: {db_dir}")

        # Connect to database
        logger.info(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check existing tables
        existing_tables = check_existing_tables(cursor)

        # Create all tables
        logger.info("=" * 60)
        logger.info("Starting database initialization...")
        logger.info("=" * 60)

        create_asx_announcements_table(cursor)
        create_stock_prices_table(cursor)
        create_news_articles_table(cursor)
        create_director_trades_table(cursor)
        create_hotcopper_sentiment_table(cursor)

        # Commit changes
        conn.commit()

        # Verify table creation
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        all_tables = [row[0] for row in cursor.fetchall()]

        logger.info("=" * 60)
        logger.info("Database initialization completed successfully!")
        logger.info(f"Total tables created: {len(all_tables)}")
        logger.info(f"Tables: {', '.join(all_tables)}")
        logger.info("=" * 60)

        # Get database size
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path)
            logger.info(f"Database size: {db_size:,} bytes ({db_size / 1024:.2f} KB)")

        # Close connection
        conn.close()
        logger.info("Database connection closed")

        return True

    except sqlite3.Error as e:
        logger.error(f"SQLite error occurred: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")
        return False


def get_table_info(db_path):
    """
    Display information about all tables in the database.

    Args:
        db_path (str): Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        logger.info("\n" + "=" * 60)
        logger.info("DATABASE SCHEMA INFORMATION")
        logger.info("=" * 60)

        for table in tables:
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()

            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]

            logger.info(f"\nTable: {table}")
            logger.info(f"Rows: {row_count}")
            logger.info("Columns:")
            for col in columns:
                col_id, col_name, col_type, not_null, default_val, pk = col
                pk_str = " [PRIMARY KEY]" if pk else ""
                not_null_str = " NOT NULL" if not_null else ""
                default_str = f" DEFAULT {default_val}" if default_val else ""
                logger.info(f"  - {col_name}: {col_type}{not_null_str}{default_str}{pk_str}")

            # Get indexes
            cursor.execute(f"PRAGMA index_list({table})")
            indexes = cursor.fetchall()
            if indexes:
                logger.info("Indexes:")
                for idx in indexes:
                    logger.info(f"  - {idx[1]}")

        logger.info("=" * 60 + "\n")

        conn.close()

    except Exception as e:
        logger.error(f"Error getting table info: {e}")


if __name__ == "__main__":
    """Main execution block for standalone script execution."""

    # Define database path (relative to project root)
    DB_PATH = "data/trading.db"

    # Get absolute path for clarity
    abs_db_path = os.path.abspath(DB_PATH)

    logger.info("=" * 60)
    logger.info("ASX Stock Trading Analysis System - Database Initialization")
    logger.info("=" * 60)
    logger.info(f"Target database: {abs_db_path}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60 + "\n")

    # Initialize database
    success = init_database(DB_PATH)

    if success:
        logger.info("\n✓ Database initialization completed successfully!\n")

        # Display table information
        get_table_info(DB_PATH)

        logger.info("Next steps:")
        logger.info("1. Implement data collection scripts for each data source")
        logger.info("2. Set up automated data pipelines")
        logger.info("3. Build analysis and reporting tools")
        logger.info("4. Configure backup and maintenance procedures")
    else:
        logger.error("\n✗ Database initialization failed. Please check the error messages above.\n")
