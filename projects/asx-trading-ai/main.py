"""
ASX Stock Trading AI - Main Coordinator Script

This script orchestrates all data scrapers with comprehensive CLI arguments and logging.
It provides a unified interface for running individual scrapers or the entire data pipeline.

Usage Examples:
    # Run all scrapers
    python main.py --all

    # Run specific scrapers
    python main.py --stock-prices --announcements

    # Run with custom date range
    python main.py --all --days 30

    # Run for specific tickers
    python main.py --stock-prices --tickers BHP,CBA,CSL

    # Initialize database
    python main.py --init-db

    # Debug mode
    python main.py --all --log-level DEBUG

Author: ASX Stock Trading AI System
Date: 2025-10-09
"""

import argparse
import logging
import sys
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import time

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass  # Fallback to default encoding

# Import configuration
import config

# Import database initialization
from database.init_db import init_database

# Import scraper modules
from scrapers.stock_prices import download_stock_prices, get_asx200_tickers
from scrapers.asx_announcements import scrape_asx_announcements
from scrapers.afr_news import scrape_afr_news
from scrapers.director_trades import scrape_director_trades
from scrapers.hotcopper import scrape_hotcopper_sentiment
from scrapers.abc_news import scrape_abc_news
from scrapers.smh_news import scrape_smh_news


# Color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ScraperResult:
    """Container for scraper execution results."""

    def __init__(self, name: str, success: bool = False,
                 records: int = 0, duration: float = 0.0, error: Optional[str] = None):
        self.name = name
        self.success = success
        self.records = records
        self.duration = duration
        self.error = error
        self.timestamp = datetime.now()


def setup_logging(log_file: Optional[str] = None, log_level: str = 'INFO') -> logging.Logger:
    """
    Configure logging with both file and console handlers.

    Args:
        log_file: Path to log file. If None, generates timestamped filename.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    os.makedirs(config.LOG_DIR, exist_ok=True)

    # Generate log filename if not provided
    if log_file is None:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        log_file = os.path.join(config.LOG_DIR, f'trading_scraper_{timestamp}.log')
    else:
        # Ensure log file is in logs directory
        if not os.path.isabs(log_file):
            log_file = os.path.join(config.LOG_DIR, log_file)

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    # Create root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs

    # Clear any existing handlers
    logger.handlers.clear()

    # Create file handler (DEBUG level for detailed logs)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Create console handler (configurable level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)

    # Colorized console formatter
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with color support."""

        COLORS = {
            'DEBUG': Colors.OKBLUE,
            'INFO': Colors.OKGREEN,
            'WARNING': Colors.WARNING,
            'ERROR': Colors.FAIL,
            'CRITICAL': Colors.FAIL + Colors.BOLD,
        }

        def format(self, record):
            levelname = record.levelname
            if levelname in self.COLORS:
                levelname_color = f"{self.COLORS[levelname]}{levelname}{Colors.ENDC}"
                record.levelname = levelname_color
            return super().format(record)

    console_formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Store log file path for later reference
    logger.log_file_path = log_file

    return logger


def run_scraper(
    scraper_func: Callable,
    scraper_name: str,
    logger: logging.Logger,
    *args,
    **kwargs
) -> ScraperResult:
    """
    Wrapper to run and log scraper execution.

    Args:
        scraper_func: The scraper function to execute
        scraper_name: Display name for the scraper
        logger: Logger instance
        *args: Positional arguments for scraper function
        **kwargs: Keyword arguments for scraper function

    Returns:
        ScraperResult with execution details
    """
    logger.info("=" * 70)
    logger.info(f"{Colors.BOLD}Running: {scraper_name}{Colors.ENDC}")
    logger.info("=" * 70)

    start_time = time.time()

    try:
        # Execute scraper
        result = scraper_func(*args, **kwargs)

        # Calculate duration
        duration = time.time() - start_time

        # Extract record count (depends on scraper return format)
        records = 0
        if isinstance(result, dict):
            records = (
                result.get('total_rows_inserted', 0) or  # stock_prices
                result.get('announcements_scraped', 0) or  # asx_announcements
                result.get('articles_inserted', 0) or  # afr_news
                result.get('trades_scraped', 0) or  # director_trades
                result.get('total_posts', 0) or  # hotcopper
                result.get('records_inserted', 0) or
                result.get('total_records', 0) or
                len(result.get('successful_tickers', [])) or
                len(result.get('tickers_analyzed', []))
            )

        # Log success
        logger.info(f"{Colors.OKGREEN}✓ {scraper_name} completed successfully{Colors.ENDC}")
        logger.info(f"Records processed: {records}")
        logger.info(f"Duration: {duration:.2f} seconds")

        return ScraperResult(
            name=scraper_name,
            success=True,
            records=records,
            duration=duration
        )

    except Exception as e:
        # Calculate duration
        duration = time.time() - start_time

        # Log error
        error_msg = str(e)
        logger.error(f"{Colors.FAIL}✗ {scraper_name} failed: {error_msg}{Colors.ENDC}")
        logger.exception("Full error traceback:")

        return ScraperResult(
            name=scraper_name,
            success=False,
            records=0,
            duration=duration,
            error=error_msg
        )


def get_database_stats(db_path: str, logger: logging.Logger) -> Dict[str, Any]:
    """
    Query database for record counts and statistics.

    Args:
        db_path: Path to SQLite database
        logger: Logger instance

    Returns:
        Dictionary with database statistics
    """
    try:
        if not os.path.exists(db_path):
            logger.warning("Database file does not exist")
            return {
                'exists': False,
                'size_bytes': 0,
                'size_mb': 0,
                'tables': {}
            }

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]

        # Get record count for each table
        table_stats = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_stats[table] = count

        # Get database size
        db_size = os.path.getsize(db_path)

        conn.close()

        return {
            'exists': True,
            'size_bytes': db_size,
            'size_mb': db_size / (1024 * 1024),
            'tables': table_stats,
            'total_records': sum(table_stats.values())
        }

    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return {
            'exists': False,
            'error': str(e),
            'tables': {}
        }


def print_summary(results: List[ScraperResult], total_duration: float,
                  db_stats: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Display formatted summary of scraper execution.

    Args:
        results: List of ScraperResult objects
        total_duration: Total execution time in seconds
        db_stats: Database statistics dictionary
        logger: Logger instance
    """
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.HEADER}EXECUTION SUMMARY{Colors.ENDC}")
    print("=" * 70)

    # Overall statistics
    successful = sum(1 for r in results if r.success)
    failed = sum(1 for r in results if not r.success)
    total_records = sum(r.records for r in results)

    print(f"\n{Colors.BOLD}Overall Statistics:{Colors.ENDC}")
    print(f"  Total Scrapers Run: {len(results)}")
    print(f"  {Colors.OKGREEN}Successful: {successful}{Colors.ENDC}")
    print(f"  {Colors.FAIL}Failed: {failed}{Colors.ENDC}")
    print(f"  Total Records Collected: {total_records:,}")
    print(f"  Total Execution Time: {total_duration:.2f} seconds")

    # Individual scraper results
    print(f"\n{Colors.BOLD}Scraper Results:{Colors.ENDC}")
    for result in results:
        status_icon = f"{Colors.OKGREEN}✓{Colors.ENDC}" if result.success else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"  {status_icon} {result.name}")
        print(f"      Records: {result.records:,}")
        print(f"      Duration: {result.duration:.2f}s")
        if result.error:
            print(f"      {Colors.FAIL}Error: {result.error}{Colors.ENDC}")

    # Database statistics
    print(f"\n{Colors.BOLD}Database Statistics:{Colors.ENDC}")
    if db_stats.get('exists'):
        print(f"  Location: {config.DATABASE_PATH}")
        print(f"  Size: {db_stats['size_mb']:.2f} MB ({db_stats['size_bytes']:,} bytes)")
        print(f"  Total Records: {db_stats.get('total_records', 0):,}")
        print(f"\n  {Colors.BOLD}Records per table:{Colors.ENDC}")
        for table, count in db_stats.get('tables', {}).items():
            print(f"    - {table}: {count:,}")
    else:
        print(f"  {Colors.WARNING}Database not found or empty{Colors.ENDC}")

    # Log file location
    if hasattr(logger, 'log_file_path'):
        print(f"\n{Colors.BOLD}Log File:{Colors.ENDC}")
        print(f"  {logger.log_file_path}")

    print("\n" + "=" * 70 + "\n")


def parse_ticker_list(ticker_string: str) -> List[str]:
    """
    Parse comma-separated ticker list.

    Args:
        ticker_string: Comma-separated string of tickers

    Returns:
        List of uppercase ticker symbols
    """
    return [t.strip().upper() for t in ticker_string.split(',') if t.strip()]


def main():
    """
    Main execution function.
    Parses arguments, sets up logging, and orchestrates scraper execution.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='ASX Stock Trading AI - Data Collection System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all scrapers
  python main.py --all

  # Run specific scrapers
  python main.py --stock-prices --announcements

  # Run with custom date range
  python main.py --all --days 30

  # Run for specific tickers
  python main.py --stock-prices --tickers BHP,CBA,CSL

  # Initialize database
  python main.py --init-db

  # Debug mode
  python main.py --all --log-level DEBUG

For automated daily execution:
  # Windows Task Scheduler
  - Open Task Scheduler
  - Create Basic Task
  - Set trigger to Daily at desired time
  - Action: Start a program
  - Program: python.exe
  - Arguments: C:\\path\\to\\main.py --all
  - Start in: C:\\path\\to\\StockTradingAI

  # Linux/Mac cron
  - Edit crontab: crontab -e
  - Add line: 0 18 * * * cd /path/to/StockTradingAI && python main.py --all
  - This runs daily at 6 PM
        """
    )

    # Scraper selection arguments
    parser.add_argument('--all', action='store_true',
                        help='Run all scrapers')
    parser.add_argument('--stock-prices', action='store_true',
                        help='Run stock prices scraper')
    parser.add_argument('--announcements', action='store_true',
                        help='Run ASX announcements scraper')
    parser.add_argument('--news', action='store_true',
                        help='Run AFR news scraper')
    parser.add_argument('--director-trades', action='store_true',
                        help='Run director trades scraper')
    parser.add_argument('--sentiment', action='store_true',
                        help='Run HotCopper sentiment scraper')
    parser.add_argument('--abc', action='store_true',
                        help='Run ABC News scraper')
    parser.add_argument('--smh', action='store_true',
                        help='Run Sydney Morning Herald scraper')
    parser.add_argument('--all-news', action='store_true',
                        help='Run all news scrapers (AFR, ABC, SMH)')

    # Database initialization
    parser.add_argument('--init-db', action='store_true',
                        help='Initialize database (create tables)')

    # Configuration arguments
    parser.add_argument('--days', type=int, default=config.DEFAULT_LOOKBACK_DAYS,
                        help=f'Number of days to look back (default: {config.DEFAULT_LOOKBACK_DAYS})')
    parser.add_argument('--tickers', type=str, default=None,
                        help='Comma-separated list of tickers (default: ASX200)')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--log-file', type=str, default=None,
                        help='Log file path (default: logs/trading_scraper_YYYY-MM-DD_HH-MM-SS.log)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be scraped without actually scraping')

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_file, args.log_level)

    # Print header
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}{Colors.HEADER}ASX Stock Trading AI - Data Collection System{Colors.ENDC}")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Log Level: {args.log_level}")
    print(f"Log File: {logger.log_file_path}")
    print("=" * 70 + "\n")

    logger.info("=" * 70)
    logger.info("ASX Stock Trading AI - Starting Data Collection")
    logger.info("=" * 70)
    logger.info(f"Configuration:")
    logger.info(f"  Database: {config.DATABASE_PATH}")
    logger.info(f"  Lookback Days: {args.days}")
    logger.info(f"  Log Level: {args.log_level}")

    # Start timing
    start_time = time.time()

    # Check if any scraper was selected
    any_scraper_selected = (
        args.all or args.stock_prices or args.announcements or
        args.news or args.director_trades or args.sentiment or
        args.abc or args.smh or args.all_news
    )

    # If only --init-db is specified, just initialize and exit
    if args.init_db and not any_scraper_selected:
        logger.info("Initializing database...")
        success = init_database(config.DATABASE_PATH)

        if success:
            print(f"\n{Colors.OKGREEN}✓ Database initialized successfully!{Colors.ENDC}")
            print(f"Location: {config.DATABASE_PATH}\n")
            return 0
        else:
            print(f"\n{Colors.FAIL}✗ Database initialization failed!{Colors.ENDC}\n")
            return 1

    # If no arguments provided, show help
    if not any_scraper_selected and not args.init_db:
        parser.print_help()
        return 0

    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        success = init_database(config.DATABASE_PATH)
        if not success:
            logger.error("Database initialization failed. Exiting.")
            return 1
        logger.info("Database initialized successfully")

    # Parse ticker list
    if args.tickers:
        tickers = parse_ticker_list(args.tickers)
        logger.info(f"Using custom ticker list: {', '.join(tickers)}")
    else:
        tickers = get_asx200_tickers()
        logger.info(f"Using default ticker list ({len(tickers)} tickers)")

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=args.days)
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")

    # Dry run mode
    if args.dry_run:
        print(f"\n{Colors.WARNING}{Colors.BOLD}DRY RUN MODE - No data will be collected{Colors.ENDC}\n")
        print(f"Would scrape data for:")
        print(f"  Tickers: {', '.join(tickers[:10])}{'...' if len(tickers) > 10 else ''}")
        print(f"  Total tickers: {len(tickers)}")
        print(f"  Date range: {start_date.date()} to {end_date.date()}")
        print(f"  Days: {args.days}")
        print(f"\nScrapers that would run:")
        if args.all or args.stock_prices:
            print("  - Stock Prices")
        if args.all or args.announcements:
            print("  - ASX Announcements")
        if args.all or args.news:
            print("  - AFR News")
        if args.all or args.director_trades:
            print("  - Director Trades")
        if args.all or args.sentiment:
            print("  - HotCopper Sentiment")
        print()
        return 0

    # Execute scrapers
    results = []

    try:
        # Stock Prices Scraper
        if args.all or args.stock_prices:
            result = run_scraper(
                download_stock_prices,
                "Stock Prices Scraper",
                logger,
                tickers=tickers,
                start_date=start_date,
                end_date=end_date,
                db_path=config.DATABASE_PATH
            )
            results.append(result)

        # ASX Announcements Scraper
        if args.all or args.announcements:
            result = run_scraper(
                scrape_asx_announcements,
                "ASX Announcements Scraper",
                logger,
                date_from=start_date,
                date_to=end_date,
                db_path=config.DATABASE_PATH,
                tickers=tickers,
                fetch_content=False
            )
            results.append(result)

        # AFR News Scraper
        if args.all or args.news:
            result = run_scraper(
                scrape_afr_news,
                "AFR News Scraper",
                logger,
                lookback_days=args.days,
                tickers=tickers,
                db_path=config.DATABASE_PATH
            )
            results.append(result)

        # Director Trades Scraper
        if args.all or args.director_trades:
            result = run_scraper(
                scrape_director_trades,
                "Director Trades Scraper",
                logger,
                date_from=start_date,
                date_to=end_date,
                db_path=config.DATABASE_PATH,
                tickers=tickers
            )
            results.append(result)

        # HotCopper Sentiment Scraper
        if args.all or args.sentiment:
            result = run_scraper(
                scrape_hotcopper_sentiment,
                "HotCopper Sentiment Scraper",
                logger,
                tickers=tickers,
                lookback_days=args.days,
                db_path=config.DATABASE_PATH
            )
            results.append(result)

        # ABC News Scraper
        if args.all or args.all_news or args.abc:
            result = run_scraper(
                scrape_abc_news,
                "ABC News Scraper",
                logger,
                lookback_days=args.days,
                tickers=tickers,
                db_path=config.DATABASE_PATH
            )
            results.append(result)

        # SMH News Scraper
        if args.all or args.all_news or args.smh:
            result = run_scraper(
                scrape_smh_news,
                "SMH News Scraper",
                logger,
                lookback_days=args.days,
                tickers=tickers,
                db_path=config.DATABASE_PATH
            )
            results.append(result)

    except KeyboardInterrupt:
        logger.warning("\nExecution interrupted by user")
        print(f"\n{Colors.WARNING}Execution interrupted by user{Colors.ENDC}\n")
        return 130  # Standard exit code for SIGINT

    # Calculate total duration
    total_duration = time.time() - start_time

    # Get database statistics
    db_stats = get_database_stats(config.DATABASE_PATH, logger)

    # Print summary
    print_summary(results, total_duration, db_stats, logger)

    # Log completion
    logger.info("=" * 70)
    logger.info("Data collection completed")
    logger.info(f"Total duration: {total_duration:.2f} seconds")
    logger.info(f"Successful scrapers: {sum(1 for r in results if r.success)}/{len(results)}")
    logger.info(f"Total records collected: {sum(r.records for r in results):,}")
    logger.info("=" * 70)

    # Determine exit code
    if all(r.success for r in results):
        return 0  # All scrapers successful
    elif any(r.success for r in results):
        return 1  # Some scrapers failed
    else:
        return 2  # All scrapers failed


if __name__ == '__main__':
    sys.exit(main())
