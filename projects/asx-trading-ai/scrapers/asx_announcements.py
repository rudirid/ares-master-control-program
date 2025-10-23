"""
Scraper for collecting company announcements from the ASX website.

This module scrapes ASX company announcements from the official ASX announcements page,
extracting information about price sensitive announcements, company updates, and other
market disclosures.
"""

import sqlite3
import logging
import time
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from urllib.parse import urljoin, parse_qs, urlparse

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
ASX_TODAY_ANNOUNCEMENTS = "https://www.asx.com.au/asx/v2/statistics/todayAnns.do"
ASX_ANNOUNCEMENTS_BASE = "https://www.asx.com.au"
ASX_COMPANY_ANNOUNCEMENTS_API = "https://www.asx.com.au/asx/1/company/{ticker}/announcements"


def parse_asx_datetime(datetime_string: str) -> Optional[datetime]:
    """
    Parse ASX date/time format into datetime object.

    ASX typically uses formats like:
    - "09/10/2025 10:30:45 AM"
    - "09-Oct-2025 10:30:45"
    - "09/10/2025"
    - "09/10/20255:40 pm" (missing space between date and time)

    Args:
        datetime_string: Date/time string from ASX

    Returns:
        Datetime object or None if parsing fails
    """
    if not datetime_string or not isinstance(datetime_string, str):
        return None

    datetime_string = datetime_string.strip()

    # Fix common ASX formatting issues
    # Handle missing space between date and time: "09/10/20255:40 pm" -> "09/10/2025 5:40 pm"
    datetime_string = re.sub(r'(\d{4})(\d{1,2}:\d{2})', r'\1 \2', datetime_string)

    # Common ASX date/time formats
    formats = [
        '%d/%m/%Y %I:%M %p',     # 09/10/2025 5:40 pm
        '%d/%m/%Y %I:%M:%S %p',  # 09/10/2025 10:30:45 AM
        '%d/%m/%Y %H:%M:%S',     # 09/10/2025 10:30:45
        '%d/%m/%Y %H:%M',        # 09/10/2025 10:30
        '%d/%m/%Y',              # 09/10/2025
        '%d-%b-%Y %H:%M:%S',     # 09-Oct-2025 10:30:45
        '%d-%b-%Y',              # 09-Oct-2025
        '%Y-%m-%d %H:%M:%S',     # 2025-10-09 10:30:45
        '%Y-%m-%d',              # 2025-10-09
    ]

    for fmt in formats:
        try:
            return datetime.strptime(datetime_string, fmt)
        except (ValueError, AttributeError):
            continue

    # Try using dateutil parser as fallback
    try:
        from dateutil import parser
        return parser.parse(datetime_string, dayfirst=True)
    except (ValueError, TypeError, ImportError) as e:
        logger.warning(f"Failed to parse datetime '{datetime_string}': {e}")
        return None


def is_price_sensitive(element) -> bool:
    """
    Check if an announcement is marked as price sensitive.

    ASX marks price sensitive announcements with a special icon:
    <img src="/asx/v2/markets/image/icon-price-sensitive.svg" alt="price sensitive">

    Args:
        element: BeautifulSoup element containing the announcement row

    Returns:
        True if price sensitive, False otherwise
    """
    if not element:
        return False

    # Look for price sensitive icon
    price_sensitive_img = element.find('img', {'alt': 'price sensitive'})
    if price_sensitive_img:
        return True

    # Alternative: check for specific class or text indicator
    if element.find(class_='price-sensitive') or element.find(class_='priceSensitive'):
        return True

    # Check for asterisk or other text indicators
    text = element.get_text()
    if '*' in text or 'price sensitive' in text.lower():
        return True

    return False


def extract_announcement_from_row(row, base_url: str = ASX_ANNOUNCEMENTS_BASE) -> Optional[Dict[str, Any]]:
    """
    Extract announcement details from a table row element.

    Args:
        row: BeautifulSoup element representing an announcement row
        base_url: Base URL for constructing absolute URLs

    Returns:
        Dictionary with announcement details or None if extraction fails
    """
    try:
        # Find all cells in the row
        cells = row.find_all('td')
        if len(cells) < 3:
            return None

        # Extract ticker (usually first cell)
        ticker_cell = cells[0]
        ticker = ticker_cell.get_text(strip=True)

        # Extract datetime (usually second cell)
        datetime_cell = cells[1]
        datetime_str = datetime_cell.get_text(strip=True)
        announcement_datetime = parse_asx_datetime(datetime_str)

        # Extract title and URL (usually third or fourth cell)
        # The structure varies, so we need to be flexible
        title = None
        url = None
        price_sensitive = False

        # Check for price sensitive indicator in the row
        price_sensitive = is_price_sensitive(row)

        # Find the title cell (look for a link)
        for cell in cells[2:]:
            link = cell.find('a')
            if link:
                title = link.get_text(strip=True)
                href = link.get('href', '')
                if href:
                    # Construct absolute URL
                    if href.startswith('http'):
                        url = href
                    else:
                        url = urljoin(base_url, href)
                break

        # If no link found, try to get title from cell text
        if not title:
            for cell in cells[2:]:
                text = cell.get_text(strip=True)
                if text and text != ticker and text != datetime_str:
                    title = text
                    break

        # Extract company name if available (sometimes in a separate cell)
        company_name = None
        for cell in cells:
            if 'company' in str(cell.get('class', [])).lower():
                company_name = cell.get_text(strip=True)
                break

        # Determine announcement type from title
        announcement_type = categorize_announcement(title) if title else None

        return {
            'ticker': ticker,
            'company_name': company_name,
            'announcement_type': announcement_type,
            'title': title,
            'datetime': announcement_datetime,
            'price_sensitive': price_sensitive,
            'url': url,
        }

    except Exception as e:
        logger.warning(f"Error extracting announcement from row: {e}")
        return None


def categorize_announcement(title: str) -> Optional[str]:
    """
    Categorize announcement based on title keywords.

    Args:
        title: Announcement title

    Returns:
        Category string or None
    """
    if not title:
        return None

    title_lower = title.lower()

    # Define category keywords
    categories = {
        'Quarterly Report': ['quarterly', 'appendix 4c', 'appendix 5b', 'quarterly activities', 'quarterly cash flow'],
        'Half Year Results': ['half year', 'half-year', 'interim results', '1h', 'h1 '],
        'Full Year Results': ['full year', 'full-year', 'annual results', 'fy20', 'fy 20'],
        'Annual Report': ['annual report', 'annual general meeting notice'],
        'Trading Update': ['trading update', 'trading halt', 'operational update', 'production report'],
        'Takeover/Scheme': ['takeover', 'scheme', 'merger', 'acquisition', 'offer'],
        'Capital Raising': ['capital raising', 'placement', 'rights issue', 'spp', 'share purchase plan', 'equity raising'],
        'Director Changes': ['director', 'change of director', 'appendix 3y', 'appendix 3x', 'resignation', 'appointment'],
        'Substantial Holder': ['substantial holder', 'change in substantial', 'becoming substantial'],
        'ASX Query': ['asx query', 'price query', 'aware query', 'response to asx'],
        'Dividend': ['dividend', 'distribution', 'appendix 3a.1'],
        'Progress Report': ['progress', 'exploration', 'drilling', 'results'],
        'Change in Interest': ['change of interest', 'appendix 3z'],
        'General Announcement': ['announcement', 'letter', 'update', 'clarification'],
    }

    # Check each category
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title_lower:
                return category

    return 'Other'


def fetch_announcement_content(url: str) -> Optional[str]:
    """
    Fetch the full content of an announcement from its detail page.

    Note: This is a basic implementation. Some announcements may be PDFs
    or require additional parsing.

    Args:
        url: URL of the announcement detail page

    Returns:
        Text content or None if fetching fails
    """
    if not url:
        return None

    # Skip PDF files for now (would require PDF parsing)
    if url.lower().endswith('.pdf'):
        logger.debug(f"Skipping PDF content extraction: {url}")
        return None

    try:
        response = safe_request(url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        # Try to find the main content area
        # Different pages may have different structures
        content_areas = [
            soup.find('div', class_='announcement-content'),
            soup.find('div', class_='content'),
            soup.find('div', {'id': 'content'}),
            soup.find('article'),
            soup.find('main'),
        ]

        for area in content_areas:
            if area:
                # Get text content, cleaning up whitespace
                text = area.get_text(separator='\n', strip=True)
                return text

        # Fallback: get all text from body
        body = soup.find('body')
        if body:
            text = body.get_text(separator='\n', strip=True)
            # Limit length to avoid storing too much
            return text[:10000] if len(text) > 10000 else text

        return None

    except Exception as e:
        logger.warning(f"Error fetching announcement content from {url}: {e}")
        return None


def scrape_today_announcements() -> List[Dict[str, Any]]:
    """
    Scrape today's announcements from the ASX website.

    Returns:
        List of announcement dictionaries
    """
    announcements = []

    logger.info(f"Fetching today's announcements from {ASX_TODAY_ANNOUNCEMENTS}")

    response = safe_request(ASX_TODAY_ANNOUNCEMENTS)
    if not response:
        logger.error("Failed to fetch today's announcements page")
        return announcements

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the announcements table
    # The exact structure may vary, so we try multiple approaches
    table = soup.find('table', {'id': 'announcements'}) or \
            soup.find('table', class_='announcements') or \
            soup.find('table')

    if not table:
        logger.warning("Could not find announcements table")
        return announcements

    # Find all data rows (skip header rows)
    rows = table.find_all('tr')

    for row in rows:
        # Skip header rows
        if row.find('th'):
            continue

        # Extract announcement details
        announcement = extract_announcement_from_row(row)
        if announcement and announcement.get('ticker'):
            announcements.append(announcement)

    logger.info(f"Extracted {len(announcements)} announcements from today's page")
    return announcements


def scrape_company_announcements(ticker: str, max_count: int = 20) -> List[Dict[str, Any]]:
    """
    Scrape announcements for a specific company using the ASX API.

    Args:
        ticker: ASX stock code
        max_count: Maximum number of announcements to retrieve

    Returns:
        List of announcement dictionaries
    """
    announcements = []

    api_url = ASX_COMPANY_ANNOUNCEMENTS_API.format(ticker=ticker.upper())
    logger.info(f"Fetching announcements for {ticker} from API")

    response = safe_request(api_url)
    if not response:
        logger.warning(f"Failed to fetch announcements for {ticker}")
        return announcements

    try:
        data = response.json()

        # Parse API response
        if 'data' in data:
            for item in data['data'][:max_count]:
                # Extract fields from API response
                announcement_datetime = parse_asx_datetime(item.get('document_release_date', ''))

                # Check for price sensitive flag
                price_sensitive = item.get('price_sensitive', False) or \
                                item.get('priceSensitive', False) or \
                                item.get('market_sensitive', False)

                # Extract URL
                url = item.get('url', '')
                if url and not url.startswith('http'):
                    url = urljoin(ASX_ANNOUNCEMENTS_BASE, url)

                announcement = {
                    'ticker': ticker.upper(),
                    'company_name': item.get('issuer_name', ''),
                    'announcement_type': categorize_announcement(item.get('header', '')),
                    'title': item.get('header', ''),
                    'datetime': announcement_datetime,
                    'price_sensitive': price_sensitive,
                    'url': url,
                }

                announcements.append(announcement)

        logger.info(f"Extracted {len(announcements)} announcements for {ticker}")

    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing API response for {ticker}: {e}")

    return announcements


def store_announcement(cursor, announcement: Dict[str, Any], fetch_content: bool = False) -> bool:
    """
    Store an announcement in the database.

    Args:
        cursor: Database cursor
        announcement: Announcement dictionary
        fetch_content: Whether to fetch full content from detail page

    Returns:
        True if inserted, False if skipped (duplicate)
    """
    # Fetch content if requested and URL is available
    content = None
    if fetch_content and announcement.get('url'):
        content = fetch_announcement_content(announcement['url'])
        rate_limit_wait(ASX_RATE_LIMIT)  # Rate limit content fetching

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO asx_announcements
            (ticker, company_name, announcement_type, title, datetime,
             price_sensitive, url, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            announcement.get('ticker'),
            announcement.get('company_name'),
            announcement.get('announcement_type'),
            announcement.get('title'),
            announcement['datetime'].strftime('%Y-%m-%d %H:%M:%S') if announcement.get('datetime') else None,
            1 if announcement.get('price_sensitive') else 0,
            announcement.get('url'),
            content
        ))

        return cursor.rowcount > 0

    except sqlite3.Error as e:
        logger.error(f"Database error storing announcement: {e}")
        return False


def scrape_asx_announcements(
    date_from: Optional[Any] = None,
    date_to: Optional[Any] = None,
    db_path: Optional[str] = None,
    tickers: Optional[List[str]] = None,
    fetch_content: bool = False
) -> Dict[str, Any]:
    """
    Scrape ASX company announcements.

    Args:
        date_from: Start date (datetime or string, default: 7 days ago)
        date_to: End date (datetime or string, default: today)
        db_path: Path to database (default: from config)
        tickers: Optional list of specific tickers to scrape (default: scrape all from today's page)
        fetch_content: Whether to fetch full announcement content (slower, default: False)

    Returns:
        Dictionary with:
            - announcements_scraped: Number of announcements scraped
            - price_sensitive_count: Number of price sensitive announcements
            - tickers_processed: List of tickers processed
            - date_range: Tuple of (date_from, date_to)
    """
    logger.info("Starting ASX announcements scraper")

    # Handle date parameters
    if date_to is None:
        date_to = datetime.now()
    elif isinstance(date_to, str):
        date_to = parse_asx_datetime(date_to)

    if date_from is None:
        date_from = date_to - timedelta(days=7)
    elif isinstance(date_from, str):
        date_from = parse_asx_datetime(date_from)

    # Use default database path if not provided
    if db_path is None:
        db_path = DATABASE_PATH

    logger.info(f"Scraping announcements from {date_from.date()} to {date_to.date()}")
    if fetch_content:
        logger.info("Content fetching enabled (this will be slower)")

    # Initialize statistics
    announcements_scraped = 0
    price_sensitive_count = 0
    tickers_processed = set()
    failed_count = 0

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Collect all announcements
        all_announcements = []

        if tickers:
            # Scrape specific tickers using API
            logger.info(f"Scraping {len(tickers)} specific tickers")
            for ticker in tickers:
                logger.info(f"Fetching announcements for {ticker}")
                ticker_announcements = scrape_company_announcements(ticker)

                # Filter by date range
                for ann in ticker_announcements:
                    if ann.get('datetime') and date_from <= ann['datetime'] <= date_to:
                        all_announcements.append(ann)

                rate_limit_wait(ASX_RATE_LIMIT)
        else:
            # Scrape today's announcements page
            logger.info("Scraping today's announcements page")
            all_announcements = scrape_today_announcements()

        logger.info(f"Processing {len(all_announcements)} announcements")

        # Process and store each announcement
        for announcement in all_announcements:
            try:
                ticker = announcement.get('ticker', '')
                if ticker:
                    tickers_processed.add(ticker)

                # Store in database
                inserted = store_announcement(cursor, announcement, fetch_content=fetch_content)

                if inserted:
                    announcements_scraped += 1
                    if announcement.get('price_sensitive'):
                        price_sensitive_count += 1

                    logger.info(
                        f"Inserted: {ticker} - {announcement.get('title', 'N/A')[:50]} "
                        f"{'[PRICE SENSITIVE]' if announcement.get('price_sensitive') else ''}"
                    )
                else:
                    logger.debug(f"Skipped duplicate: {announcement.get('url', 'N/A')}")

            except Exception as e:
                logger.error(f"Error processing announcement: {e}")
                failed_count += 1
                continue

        # Commit all changes
        conn.commit()

        logger.info(f"Successfully scraped {announcements_scraped} announcements")
        logger.info(f"Failed: {failed_count}")

    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    return {
        'announcements_scraped': announcements_scraped,
        'price_sensitive_count': price_sensitive_count,
        'tickers_processed': sorted(list(tickers_processed)),
        'failed_count': failed_count,
        'date_range': (date_from.strftime('%Y-%m-%d'), date_to.strftime('%Y-%m-%d')),
    }


def get_announcements_summary(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get summary statistics of announcements in the database.

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
        # Total announcements
        cursor.execute("SELECT COUNT(*) FROM asx_announcements")
        total_announcements = cursor.fetchone()[0]

        # Price sensitive count
        cursor.execute("SELECT COUNT(*) FROM asx_announcements WHERE price_sensitive = 1")
        price_sensitive_count = cursor.fetchone()[0]

        # Announcements by type
        cursor.execute("""
            SELECT announcement_type, COUNT(*)
            FROM asx_announcements
            WHERE announcement_type IS NOT NULL
            GROUP BY announcement_type
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        by_type = cursor.fetchall()

        # Most active companies
        cursor.execute("""
            SELECT ticker, company_name, COUNT(*) as count
            FROM asx_announcements
            GROUP BY ticker, company_name
            ORDER BY count DESC
            LIMIT 10
        """)
        most_active = cursor.fetchall()

        # Recent announcements
        cursor.execute("""
            SELECT ticker, title, datetime, price_sensitive
            FROM asx_announcements
            ORDER BY datetime DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()

        # Date range
        cursor.execute("""
            SELECT MIN(datetime), MAX(datetime)
            FROM asx_announcements
            WHERE datetime IS NOT NULL
        """)
        date_range = cursor.fetchone()

        return {
            'total_announcements': total_announcements,
            'price_sensitive_count': price_sensitive_count,
            'price_sensitive_percentage': (price_sensitive_count / total_announcements * 100) if total_announcements > 0 else 0,
            'by_type': by_type,
            'most_active_companies': most_active,
            'recent_announcements': recent,
            'date_range': date_range,
        }
    finally:
        conn.close()


def main():
    """Main function for running the scraper standalone."""
    logger.info("ASX Announcements Scraper - Standalone Mode")
    logger.info("=" * 60)

    # Scrape last 7 days of announcements
    result = scrape_asx_announcements(fetch_content=False)

    print("\n" + "=" * 60)
    print("SCRAPING RESULTS")
    print("=" * 60)
    print(f"Announcements scraped: {result['announcements_scraped']}")
    print(f"Price sensitive: {result['price_sensitive_count']}")
    print(f"Failed: {result['failed_count']}")
    print(f"Tickers processed: {len(result['tickers_processed'])}")
    print(f"Date range: {result['date_range'][0]} to {result['date_range'][1]}")

    if result['tickers_processed']:
        print(f"\nSample tickers: {', '.join(result['tickers_processed'][:10])}")

    # Show summary
    print("\n" + "=" * 60)
    print("DATABASE SUMMARY")
    print("=" * 60)

    summary = get_announcements_summary()
    print(f"Total announcements in database: {summary['total_announcements']}")
    print(f"Price sensitive: {summary['price_sensitive_count']} ({summary['price_sensitive_percentage']:.1f}%)")

    if summary['date_range'][0] and summary['date_range'][1]:
        print(f"Date range: {summary['date_range'][0]} to {summary['date_range'][1]}")

    print("\nTop Announcement Types:")
    print("-" * 60)
    for i, (ann_type, count) in enumerate(summary['by_type'][:5], 1):
        print(f"{i}. {ann_type}: {count}")

    print("\nMost Active Companies:")
    print("-" * 60)
    for i, (ticker, company, count) in enumerate(summary['most_active_companies'][:5], 1):
        company_str = f" - {company}" if company else ""
        print(f"{i}. {ticker}{company_str}: {count} announcements")

    print("\nRecent Announcements:")
    print("-" * 60)
    for ticker, title, dt, price_sens in summary['recent_announcements'][:5]:
        ps_flag = " [PS]" if price_sens else ""
        title_short = title[:60] + "..." if title and len(title) > 60 else title
        print(f"{ticker} - {title_short}{ps_flag}")
        print(f"  {dt}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
