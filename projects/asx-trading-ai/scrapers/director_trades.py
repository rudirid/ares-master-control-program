"""
Scraper for collecting Change of Director's Interest Notices (Appendix 3Y) from ASX.

This module scrapes director trading notices from the ASX announcements platform,
extracting information about insider buy/sell transactions by company directors.
"""

import sqlite3
import logging
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Import configuration and utilities
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DATABASE_PATH, ASX_RATE_LIMIT, USER_AGENT
from scrapers.utils import get_logger, rate_limit_wait, safe_request


# Initialize logger
logger = get_logger(__name__)


# ASX URLs
ASX_ANNOUNCEMENTS_URL = "https://www.asx.com.au/asx/statistics/announcements.do"
ASX_COMPANY_ANNOUNCEMENTS_API = "https://www.asx.com.au/asx/1/company/{ticker}/announcements"
ASX_ANNOUNCEMENTS_BASE = "https://www.asx.com.au"


def determine_trade_type(text: str) -> Optional[str]:
    """
    Determine if a transaction is a buy or sell based on text content.

    Args:
        text: Text content from notice

    Returns:
        'buy', 'sell', or None if cannot determine
    """
    text_lower = text.lower()

    # Buy indicators
    buy_keywords = [
        'acquisition', 'purchase', 'purchased', 'acquired',
        'on-market purchase', 'on-market buy', 'issue', 'issued',
        'allotment', 'grant', 'granted', 'exercise of options'
    ]

    # Sell indicators
    sell_keywords = [
        'disposal', 'disposed', 'sale', 'sold', 'on-market sale',
        'on-market sell', 'transfer', 'transferred'
    ]

    # Count occurrences
    buy_count = sum(1 for keyword in buy_keywords if keyword in text_lower)
    sell_count = sum(1 for keyword in sell_keywords if keyword in text_lower)

    # Determine based on which has more matches
    if buy_count > sell_count:
        return 'buy'
    elif sell_count > buy_count:
        return 'sell'

    return None


def clean_numeric_value(value_string: str) -> Optional[float]:
    """
    Clean and convert currency/number strings to float.

    Args:
        value_string: String containing numeric value (may have $, commas, etc.)

    Returns:
        Float value or None if parsing fails
    """
    if not value_string:
        return None

    try:
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r'[$,\s]', '', str(value_string))

        # Handle negative values in parentheses
        if cleaned.startswith('(') and cleaned.endswith(')'):
            cleaned = '-' + cleaned[1:-1]

        # Convert to float
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def extract_shares_from_text(text: str) -> Optional[int]:
    """
    Extract number of shares from text.

    Args:
        text: Text containing share quantity

    Returns:
        Number of shares or None
    """
    # Look for patterns like "10,000 shares" or "10000 ordinary shares"
    patterns = [
        r'([\d,]+)\s*(?:ordinary\s*)?shares?',
        r'(?:number|quantity)[\s:]*\s*([\d,]+)',
        r'(\d{1,3}(?:,\d{3})*)\s*(?:ordinary|securities)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            shares_str = match.group(1).replace(',', '')
            try:
                return int(shares_str)
            except ValueError:
                continue

    return None


def extract_price_from_text(text: str) -> Optional[float]:
    """
    Extract price per share from text.

    Args:
        text: Text containing price information

    Returns:
        Price per share or None
    """
    # Look for patterns like "$1.50 per share" or "at $1.50"
    patterns = [
        r'\$\s*([\d,]+(?:\.\d+)?)\s*per\s*share',
        r'at\s*\$\s*([\d,]+(?:\.\d+)?)',
        r'price[\s:]*\$\s*([\d,]+(?:\.\d+)?)',
        r'consideration[\s:]*\$\s*([\d,]+(?:\.\d+)?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return float(price_str)
            except ValueError:
                continue

    return None


def extract_director_name_from_text(text: str) -> Optional[str]:
    """
    Extract director name from notice text.

    Args:
        text: Text containing director name

    Returns:
        Director name or None
    """
    # Look for patterns like "Name of Director: John Smith"
    patterns = [
        r'(?:name\s*of\s*)?director[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
        r'(?:given\s*name|surname)[\s:]+([A-Z][a-z]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def parse_date_flexible(date_string: str) -> Optional[datetime]:
    """
    Parse date string in various formats.

    Args:
        date_string: Date string to parse

    Returns:
        Datetime object or None
    """
    # Common date formats
    formats = [
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y-%m-%d',
        '%d %B %Y',
        '%d %b %Y',
        '%B %d, %Y',
        '%b %d, %Y',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except (ValueError, AttributeError):
            continue

    # Try using dateutil parser as fallback
    try:
        from dateutil import parser
        return parser.parse(date_string)
    except (ValueError, TypeError, ImportError):
        return None


def extract_trade_details_from_html(html_content: str, url: str) -> List[Dict[str, Any]]:
    """
    Extract trade details from HTML announcement content.

    Args:
        html_content: HTML content of announcement
        url: URL of the announcement

    Returns:
        List of trade detail dictionaries
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()

    # Extract basic information
    trade_type = determine_trade_type(text)
    shares = extract_shares_from_text(text)
    price = extract_price_from_text(text)
    director_name = extract_director_name_from_text(text)

    # Calculate value if we have both shares and price
    value = None
    if shares and price:
        value = shares * price

    # If we found any useful information, return it
    if trade_type or shares or director_name:
        return [{
            'director_name': director_name,
            'trade_type': trade_type,
            'shares': shares,
            'price': price,
            'value': value,
            'trade_date': None,  # Often not in HTML, in PDF
        }]

    return []


def extract_trade_details_from_pdf(pdf_url: str) -> List[Dict[str, Any]]:
    """
    Extract trade details from PDF notice.

    Note: This is a placeholder for PDF parsing. Full implementation would
    require pdfplumber or PyPDF2 library.

    Args:
        pdf_url: URL of PDF document

    Returns:
        List of trade detail dictionaries
    """
    logger.warning(f"PDF parsing not fully implemented. Skipping: {pdf_url}")

    # TODO: Implement PDF parsing with pdfplumber
    # try:
    #     import pdfplumber
    #     response = safe_request(pdf_url)
    #     if response:
    #         with pdfplumber.open(io.BytesIO(response.content)) as pdf:
    #             text = ""
    #             for page in pdf.pages:
    #                 text += page.extract_text()
    #             # Parse text similar to HTML
    # except ImportError:
    #     logger.warning("pdfplumber not installed. Cannot parse PDFs.")

    return []


def get_company_announcements(
    ticker: str,
    date_from: datetime,
    date_to: datetime
) -> List[Dict[str, Any]]:
    """
    Get announcements for a specific company from ASX.

    Args:
        ticker: ASX stock code
        date_from: Start date
        date_to: End date

    Returns:
        List of announcement dictionaries
    """
    announcements = []

    # Try using the ASX API endpoint first
    api_url = ASX_COMPANY_ANNOUNCEMENTS_API.format(ticker=ticker)

    logger.info(f"Fetching announcements for {ticker} from {date_from.date()} to {date_to.date()}")

    response = safe_request(api_url)

    if response:
        try:
            data = response.json()

            # Parse announcements from API response
            if 'data' in data:
                for item in data['data']:
                    # Filter by date and announcement type
                    announcement_date = parse_date_flexible(item.get('document_date', ''))

                    if announcement_date and date_from <= announcement_date <= date_to:
                        # Check if it's an Appendix 3Y
                        title = item.get('header', '').lower()
                        if 'appendix 3y' in title or "director's interest" in title or "change of director" in title:
                            announcements.append({
                                'ticker': ticker,
                                'company_name': item.get('issuer_name', ''),
                                'title': item.get('header', ''),
                                'notice_date': announcement_date,
                                'url': item.get('url', ''),
                                'document_release_date': item.get('document_release_date', ''),
                            })
        except (ValueError, KeyError) as e:
            logger.error(f"Error parsing API response for {ticker}: {e}")

    return announcements


def get_all_director_notices(date_from: datetime, date_to: datetime) -> List[Dict[str, Any]]:
    """
    Get all Appendix 3Y notices for the specified date range.

    This function searches across all companies for director trading notices.

    Args:
        date_from: Start date
        date_to: End date

    Returns:
        List of notice dictionaries
    """
    notices = []

    # Use ASX announcements search page
    # This is a simplified approach - in production, you'd want to:
    # 1. Get list of all ASX tickers
    # 2. Query each ticker's announcements
    # 3. Or use the general announcements search with filters

    logger.info(f"Searching for director notices from {date_from.date()} to {date_to.date()}")

    # For now, we'll implement a basic approach that searches the announcements page
    # In a production system, you'd want to iterate through all tickers or use
    # a more comprehensive search mechanism

    search_url = f"{ASX_ANNOUNCEMENTS_URL}?by=asxCode&timeframe=D"

    response = safe_request(search_url)

    if response:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for announcement rows
        # Note: This is a simplified parser - actual ASX page structure may vary
        announcement_rows = soup.find_all('tr', class_='announcement')

        for row in announcement_rows:
            try:
                # Extract data from row
                ticker_elem = row.find('td', class_='code')
                title_elem = row.find('td', class_='title')
                date_elem = row.find('td', class_='date')

                if ticker_elem and title_elem:
                    ticker = ticker_elem.get_text(strip=True)
                    title = title_elem.get_text(strip=True)

                    # Check if it's an Appendix 3Y
                    if 'appendix 3y' in title.lower() or "director's interest" in title.lower():
                        # Extract URL
                        link = title_elem.find('a')
                        url = urljoin(ASX_ANNOUNCEMENTS_BASE, link['href']) if link else None

                        # Extract date
                        notice_date = None
                        if date_elem:
                            notice_date = parse_date_flexible(date_elem.get_text(strip=True))

                        # Filter by date range
                        if notice_date and date_from <= notice_date <= date_to:
                            notices.append({
                                'ticker': ticker,
                                'title': title,
                                'notice_date': notice_date,
                                'url': url,
                            })
            except Exception as e:
                logger.warning(f"Error parsing announcement row: {e}")
                continue

    logger.info(f"Found {len(notices)} director notices")
    return notices


def scrape_director_trades(
    date_from: Optional[Any] = None,
    date_to: Optional[Any] = None,
    db_path: Optional[str] = None,
    tickers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Scrape ASX director trading notices (Appendix 3Y forms).

    Args:
        date_from: Start date (datetime or string, default: 30 days ago)
        date_to: End date (datetime or string, default: today)
        db_path: Path to database (default: from config)
        tickers: Optional list of specific tickers to scrape (default: search all)

    Returns:
        Dictionary with:
            - trades_scraped: Number of trades scraped
            - total_buys: Number of buy transactions
            - total_sells: Number of sell transactions
            - total_value: Total value of all trades
            - tickers_processed: List of tickers processed
    """
    logger.info("Starting director trades scraper")

    # Handle date parameters
    if date_to is None:
        date_to = datetime.now()
    elif isinstance(date_to, str):
        date_to = parse_date_flexible(date_to)

    if date_from is None:
        date_from = date_to - timedelta(days=30)
    elif isinstance(date_from, str):
        date_from = parse_date_flexible(date_from)

    # Use default database path if not provided
    if db_path is None:
        db_path = DATABASE_PATH

    logger.info(f"Scraping director trades from {date_from.date()} to {date_to.date()}")

    # Initialize statistics
    trades_scraped = 0
    total_buys = 0
    total_sells = 0
    total_value = 0.0
    tickers_processed = set()

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get notices
        if tickers:
            # Scrape specific tickers
            all_notices = []
            for ticker in tickers:
                logger.info(f"Fetching notices for {ticker}")
                notices = get_company_announcements(ticker, date_from, date_to)
                all_notices.extend(notices)
                rate_limit_wait(ASX_RATE_LIMIT)
        else:
            # Search all notices
            all_notices = get_all_director_notices(date_from, date_to)

        logger.info(f"Processing {len(all_notices)} notices")

        # Process each notice
        for notice in all_notices:
            try:
                ticker = notice.get('ticker', '')
                company_name = notice.get('company_name', '')
                notice_date = notice.get('notice_date')
                url = notice.get('url', '')

                tickers_processed.add(ticker)

                # Skip if we already have this notice
                cursor.execute(
                    "SELECT COUNT(*) FROM director_trades WHERE url = ?",
                    (url,)
                )
                if cursor.fetchone()[0] > 0:
                    logger.debug(f"Skipping duplicate notice: {url}")
                    continue

                # Determine if this is a PDF or HTML announcement
                is_pdf = url.endswith('.pdf') if url else False

                # Extract trade details
                trades = []
                if is_pdf:
                    trades = extract_trade_details_from_pdf(url)
                elif url:
                    # Fetch HTML content
                    response = safe_request(url)
                    if response:
                        trades = extract_trade_details_from_html(response.text, url)

                # Insert trades into database
                for trade in trades:
                    trade_type = trade.get('trade_type')
                    shares = trade.get('shares')
                    price = trade.get('price')
                    value = trade.get('value')
                    director_name = trade.get('director_name')
                    trade_date = trade.get('trade_date')

                    # Insert into database (using INSERT OR IGNORE for duplicates)
                    cursor.execute("""
                        INSERT OR IGNORE INTO director_trades
                        (ticker, company_name, director_name, trade_type, shares,
                         price, value, trade_date, notice_date, url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker,
                        company_name,
                        director_name,
                        trade_type,
                        shares,
                        price,
                        value,
                        trade_date.strftime('%Y-%m-%d') if trade_date else None,
                        notice_date.strftime('%Y-%m-%d') if notice_date else None,
                        url
                    ))

                    # Update statistics
                    if cursor.rowcount > 0:
                        trades_scraped += 1

                        if trade_type == 'buy':
                            total_buys += 1
                        elif trade_type == 'sell':
                            total_sells += 1

                        if value:
                            total_value += value

                        logger.info(f"Inserted trade: {ticker} - {director_name} - {trade_type} - {shares} shares")

                # Commit after each notice
                conn.commit()

                # Rate limiting
                rate_limit_wait(ASX_RATE_LIMIT)

            except Exception as e:
                logger.error(f"Error processing notice {notice.get('url', 'unknown')}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    logger.info(f"Scraping complete. Scraped {trades_scraped} trades.")

    return {
        'trades_scraped': trades_scraped,
        'total_buys': total_buys,
        'total_sells': total_sells,
        'total_value': total_value,
        'tickers_processed': list(tickers_processed),
    }


def get_director_trades_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary statistics of director trades in the database.

    Args:
        db_path: Path to database (default: from config)

    Returns:
        Dictionary with summary statistics
    """
    if db_path is None:
        db_path = DATABASE_PATH

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Total trades
        cursor.execute("SELECT COUNT(*) FROM director_trades")
        total_trades = cursor.fetchone()[0]

        # Buys vs sells
        cursor.execute("SELECT trade_type, COUNT(*) FROM director_trades GROUP BY trade_type")
        trade_types = dict(cursor.fetchall())

        # Total value
        cursor.execute("SELECT SUM(value) FROM director_trades WHERE value IS NOT NULL")
        total_value = cursor.fetchone()[0] or 0

        # Top directors by trade value
        cursor.execute("""
            SELECT director_name, ticker, SUM(value) as total_value
            FROM director_trades
            WHERE value IS NOT NULL AND director_name IS NOT NULL
            GROUP BY director_name, ticker
            ORDER BY total_value DESC
            LIMIT 10
        """)
        top_directors = cursor.fetchall()

        # Recent trades
        cursor.execute("""
            SELECT ticker, director_name, trade_type, shares, value, notice_date
            FROM director_trades
            ORDER BY notice_date DESC
            LIMIT 10
        """)
        recent_trades = cursor.fetchall()

        return {
            'total_trades': total_trades,
            'total_buys': trade_types.get('buy', 0),
            'total_sells': trade_types.get('sell', 0),
            'total_value': total_value,
            'top_directors': top_directors,
            'recent_trades': recent_trades,
        }
    finally:
        conn.close()


def main():
    """Main function for running the scraper standalone."""
    logger.info("Director Trades Scraper - Standalone Mode")
    logger.info("=" * 60)

    # Scrape last 30 days
    result = scrape_director_trades()

    print("\n" + "=" * 60)
    print("SCRAPING RESULTS")
    print("=" * 60)
    print(f"Trades scraped: {result['trades_scraped']}")
    print(f"Total buys: {result['total_buys']}")
    print(f"Total sells: {result['total_sells']}")
    print(f"Total value: ${result['total_value']:,.2f}")
    print(f"Tickers processed: {len(result['tickers_processed'])}")

    # Show summary
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    summary = get_director_trades_summary()
    print(f"Total trades in database: {summary['total_trades']}")
    print(f"Total buys: {summary['total_buys']}")
    print(f"Total sells: {summary['total_sells']}")
    print(f"Total value: ${summary['total_value']:,.2f}")

    print("\nTop Directors by Trade Value:")
    print("-" * 60)
    for i, (director, ticker, value) in enumerate(summary['top_directors'][:5], 1):
        print(f"{i}. {director} ({ticker}): ${value:,.2f}")

    print("\nRecent Trades:")
    print("-" * 60)
    for ticker, director, trade_type, shares, value, date in summary['recent_trades'][:5]:
        value_str = f"${value:,.2f}" if value else "N/A"
        shares_str = f"{shares:,}" if shares else "N/A"
        print(f"{ticker} - {director} - {trade_type} - {shares_str} shares - {value_str} - {date}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
