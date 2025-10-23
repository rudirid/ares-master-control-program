"""
Australian Financial Review (AFR) News Scraper

This module scrapes business news articles from the Australian Financial Review (AFR)
website, focusing on articles mentioning ASX200 companies. It respects the website's
robots.txt, implements rate limiting, and only collects freely available content.

Key Features:
- Searches for articles mentioning ASX200 company tickers
- Identifies and skips paywalled content
- Extracts article metadata (title, date, URL, preview text)
- Stores articles in SQLite database
- Implements ethical scraping practices (rate limiting, user agent, robots.txt compliance)

Database Schema:
- source: 'AFR'
- ticker: ASX ticker symbol found in article
- title: Article headline
- datetime: Publication date/time
- content: Article preview/snippet (publicly available text)
- url: Article URL (unique constraint)
- sentiment: NULL initially (to be analyzed later)

Usage:
    from scrapers.afr_news import scrape_afr_news

    # Scrape last 7 days
    result = scrape_afr_news(lookback_days=7)

    # Scrape specific tickers
    result = scrape_afr_news(tickers=['BHP', 'CBA', 'NAB'])

Author: Claude Code
Date: 2025-10-09
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import re
import logging
from typing import List, Dict, Optional, Set, Tuple
from urllib.parse import urljoin, quote_plus

# Import from config
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from scrapers.utils import get_logger, rate_limit_wait, safe_request, parse_date

# Initialize logger
logger = get_logger(__name__)


# Company name to ticker mapping for major ASX200 companies
# This helps match articles that mention company names instead of ticker symbols
COMPANY_NAME_TO_TICKER = {
    'BHP': ['BHP', 'BHP Group', 'BHP Billiton'],
    'CBA': ['Commonwealth Bank', 'CommBank', 'CBA'],
    'CSL': ['CSL', 'CSL Limited'],
    'NAB': ['National Australia Bank', 'NAB'],
    'WBC': ['Westpac', 'Westpac Banking Corporation'],
    'ANZ': ['ANZ', 'Australia and New Zealand Banking'],
    'WES': ['Wesfarmers'],
    'MQG': ['Macquarie Group', 'Macquarie Bank'],
    'WOW': ['Woolworths', 'Woolworths Group'],
    'FMG': ['Fortescue Metals', 'Fortescue', 'FMG'],
    'RIO': ['Rio Tinto'],
    'TLS': ['Telstra', 'Telstra Corporation'],
    'WDS': ['Woodside', 'Woodside Energy'],
    'GMG': ['Goodman Group'],
    'TCL': ['Transurban', 'Transurban Group'],
    'COL': ['Coles', 'Coles Group'],
    'QBE': ['QBE Insurance'],
    'SCG': ['Scentre Group'],
    'STO': ['Santos'],
    'AMC': ['Amcor'],
}


def build_company_name_mapping(tickers: List[str]) -> Dict[str, str]:
    """
    Build a mapping of company names to ticker symbols.

    Args:
        tickers: List of ticker symbols

    Returns:
        Dictionary mapping company names (lowercase) to tickers
    """
    mapping = {}

    for ticker in tickers:
        if ticker in COMPANY_NAME_TO_TICKER:
            for name in COMPANY_NAME_TO_TICKER[ticker]:
                mapping[name.lower()] = ticker
        # Also add the ticker itself
        mapping[ticker.lower()] = ticker

    return mapping


def match_tickers_in_text(text: str, ticker_list: List[str]) -> Set[str]:
    """
    Find ticker mentions in article text.

    Searches for both ticker symbols and company names in the text.
    Uses word boundaries to avoid false matches.

    Args:
        text: Article text to search
        ticker_list: List of ticker symbols to search for

    Returns:
        Set of matched ticker symbols
    """
    if not text:
        return set()

    text_lower = text.lower()
    matched_tickers = set()

    # Build company name mapping
    name_mapping = build_company_name_mapping(ticker_list)

    # Search for each company name/ticker
    for name, ticker in name_mapping.items():
        # Use word boundaries to avoid false matches
        pattern = r'\b' + re.escape(name) + r'\b'
        if re.search(pattern, text_lower):
            matched_tickers.add(ticker)

    return matched_tickers


def is_paywalled(article_soup: BeautifulSoup, article_url: str = None) -> bool:
    """
    Check if an article is behind a paywall.

    Common indicators:
    - "Subscriber only" badge or label
    - Lock icon or paywall indicator
    - Limited content preview
    - Subscription prompt in HTML

    Args:
        article_soup: BeautifulSoup object of article HTML
        article_url: Optional article URL for additional checks

    Returns:
        True if article is paywalled, False otherwise
    """
    # Check for common paywall indicators in the HTML
    paywall_indicators = [
        'subscriber-only',
        'subscribers-only',
        'premium-content',
        'locked-article',
        'paywall',
        'subscription-required',
        'data-subscriber-only="true"',
    ]

    html_str = str(article_soup).lower()

    for indicator in paywall_indicators:
        if indicator in html_str:
            logger.debug(f"Paywall indicator found: {indicator}")
            return True

    # Check for subscriber badge/label
    subscriber_elements = article_soup.find_all(['span', 'div', 'p'],
                                                 class_=lambda x: x and 'subscriber' in x.lower())
    if subscriber_elements:
        logger.debug(f"Subscriber element found: {subscriber_elements[0].get('class')}")
        return True

    # Check for lock icons
    lock_elements = article_soup.find_all(['i', 'svg', 'span'],
                                          class_=lambda x: x and 'lock' in str(x).lower())
    if lock_elements:
        logger.debug("Lock icon found")
        return True

    return False


def extract_article_data(article_element: BeautifulSoup, base_url: str = 'https://www.afr.com') -> Optional[Dict]:
    """
    Parse article HTML element and extract relevant data.

    Attempts to extract:
    - title: Article headline
    - url: Full article URL
    - datetime: Publication date/time
    - content: Article preview/teaser text

    Args:
        article_element: BeautifulSoup element containing article data
        base_url: Base URL for constructing absolute URLs

    Returns:
        Dictionary with article data or None if extraction fails
    """
    try:
        article_data = {}

        # Extract title - try multiple selectors
        title_elem = (
            article_element.find('h3') or
            article_element.find('h2') or
            article_element.find(['a'], class_=lambda x: x and 'headline' in str(x).lower()) or
            article_element.find('a', attrs={'data-testid': lambda x: x and 'headline' in str(x).lower()})
        )

        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)
        else:
            # Try to find any anchor tag with substantial text
            for link in article_element.find_all('a'):
                text = link.get_text(strip=True)
                if len(text) > 20:  # Likely a headline
                    article_data['title'] = text
                    break

        if not article_data.get('title'):
            logger.debug("No title found in article element")
            return None

        # Extract URL - look for article link
        url_elem = article_element.find('a', href=True)
        if url_elem:
            href = url_elem['href']
            # Make absolute URL
            article_data['url'] = urljoin(base_url, href)
        else:
            logger.debug("No URL found in article element")
            return None

        # Extract datetime - try multiple formats
        date_elem = (
            article_element.find('time') or
            article_element.find(['span', 'div'], class_=lambda x: x and 'date' in str(x).lower()) or
            article_element.find(['span', 'div'], class_=lambda x: x and 'time' in str(x).lower())
        )

        if date_elem:
            # Try datetime attribute first
            date_str = date_elem.get('datetime') or date_elem.get_text(strip=True)
            parsed_date = parse_date(date_str)
            if parsed_date:
                article_data['datetime'] = parsed_date

        # Extract content preview
        content_elem = (
            article_element.find(['p'], class_=lambda x: x and any(term in str(x).lower()
                                 for term in ['summary', 'excerpt', 'description', 'standfirst'])) or
            article_element.find('p')
        )

        if content_elem:
            article_data['content'] = content_elem.get_text(strip=True)
        else:
            # Fall back to using title as content if no preview available
            article_data['content'] = article_data['title']

        return article_data

    except Exception as e:
        logger.error(f"Error extracting article data: {e}")
        return None


def search_afr_for_ticker(ticker: str, days_back: int = 7, max_articles: int = 10) -> List[Dict]:
    """
    Search AFR for articles mentioning a specific ticker.

    Implements multiple search strategies:
    1. Use AFR's search functionality with ticker symbol
    2. Search for company name
    3. Parse business section and filter by ticker

    Args:
        ticker: Ticker symbol to search for
        days_back: Number of days to look back
        max_articles: Maximum number of articles to return per ticker

    Returns:
        List of article dictionaries
    """
    articles = []

    try:
        # Strategy 1: Try AFR search
        # AFR search URLs typically look like: /search?query=TICKER
        search_url = f"https://www.afr.com/search?query={quote_plus(ticker)}"

        logger.info(f"Searching AFR for ticker: {ticker}")
        logger.debug(f"Search URL: {search_url}")

        response = safe_request(search_url)

        if not response:
            logger.warning(f"Failed to fetch search results for {ticker}")
            return articles

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find article elements - AFR typically uses article tags or specific div classes
        # We need to be flexible as the exact structure may vary
        article_elements = (
            soup.find_all('article') or
            soup.find_all(['div'], class_=lambda x: x and any(term in str(x).lower()
                          for term in ['article', 'story', 'search-result'])) or
            soup.find_all(['li'], class_=lambda x: x and 'search' in str(x).lower())
        )

        logger.debug(f"Found {len(article_elements)} potential article elements")

        cutoff_date = datetime.now() - timedelta(days=days_back)

        for idx, article_elem in enumerate(article_elements[:max_articles * 2]):  # Check extra in case some are filtered
            if len(articles) >= max_articles:
                break

            # Check if paywalled
            if is_paywalled(article_elem):
                logger.debug(f"Skipping paywalled article {idx + 1}")
                continue

            # Extract article data
            article_data = extract_article_data(article_elem)

            if not article_data:
                continue

            # Check date if available
            if 'datetime' in article_data:
                if article_data['datetime'] < cutoff_date:
                    logger.debug(f"Article too old: {article_data['datetime']}")
                    continue

            # Add ticker to article data
            article_data['ticker'] = ticker
            article_data['source'] = 'AFR'

            articles.append(article_data)
            logger.debug(f"Added article: {article_data['title'][:50]}...")

        logger.info(f"Found {len(articles)} articles for {ticker}")

    except Exception as e:
        logger.error(f"Error searching AFR for {ticker}: {e}")

    return articles


def scrape_afr_business_section(lookback_days: int = 7, ticker_list: List[str] = None) -> List[Dict]:
    """
    Scrape AFR business section and match articles to tickers.

    This is an alternative strategy that browses the main business section
    and matches articles to tickers based on content.

    Args:
        lookback_days: Number of days to look back
        ticker_list: List of tickers to match against

    Returns:
        List of article dictionaries
    """
    articles = []

    try:
        # AFR business section URLs to try
        business_urls = [
            'https://www.afr.com/companies',
            'https://www.afr.com/markets',
            'https://www.afr.com/street-talk',
        ]

        for business_url in business_urls:
            logger.info(f"Scraping AFR section: {business_url}")

            response = safe_request(business_url)

            if not response:
                logger.warning(f"Failed to fetch {business_url}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find article elements
            article_elements = (
                soup.find_all('article') or
                soup.find_all(['div'], class_=lambda x: x and 'article' in str(x).lower())
            )

            logger.debug(f"Found {len(article_elements)} articles in {business_url}")

            for article_elem in article_elements:
                # Check if paywalled
                if is_paywalled(article_elem):
                    continue

                # Extract article data
                article_data = extract_article_data(article_elem)

                if not article_data:
                    continue

                # Match tickers in title and content
                search_text = f"{article_data.get('title', '')} {article_data.get('content', '')}"
                matched_tickers = match_tickers_in_text(search_text, ticker_list)

                if matched_tickers:
                    # Create article entry for each matched ticker
                    for ticker in matched_tickers:
                        article_copy = article_data.copy()
                        article_copy['ticker'] = ticker
                        article_copy['source'] = 'AFR'
                        articles.append(article_copy)
                        logger.debug(f"Matched {ticker} in article: {article_data['title'][:50]}...")

            # Rate limit between sections
            rate_limit_wait(config.AFR_RATE_LIMIT)

        logger.info(f"Found {len(articles)} articles from business sections")

    except Exception as e:
        logger.error(f"Error scraping AFR business section: {e}")

    return articles


def save_articles_to_db(articles: List[Dict], db_path: str) -> Tuple[int, int]:
    """
    Save articles to the news_articles database table.

    Uses INSERT OR IGNORE to avoid duplicate URLs.

    Args:
        articles: List of article dictionaries
        db_path: Path to SQLite database

    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    inserted = 0
    skipped = 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for article in articles:
            try:
                # Convert datetime to string if it's a datetime object
                article_datetime = article.get('datetime')
                if isinstance(article_datetime, datetime):
                    article_datetime = article_datetime.strftime('%Y-%m-%d %H:%M:%S')

                # Insert article (will be ignored if URL already exists)
                cursor.execute("""
                    INSERT OR IGNORE INTO news_articles
                    (source, ticker, title, datetime, content, url, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get('source', 'AFR'),
                    article.get('ticker'),
                    article.get('title'),
                    article_datetime,
                    article.get('content'),
                    article.get('url'),
                    None  # sentiment to be analyzed later
                ))

                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1

            except sqlite3.IntegrityError as e:
                logger.debug(f"Duplicate article skipped: {article.get('url')}")
                skipped += 1
            except Exception as e:
                logger.error(f"Error inserting article: {e}")
                skipped += 1

        conn.commit()
        conn.close()

        logger.info(f"Database save complete: {inserted} inserted, {skipped} skipped")

    except Exception as e:
        logger.error(f"Error saving articles to database: {e}")

    return inserted, skipped


def scrape_afr_news(lookback_days: int = 7, tickers: List[str] = None, db_path: str = None) -> Dict:
    """
    Main function to scrape AFR news articles for ASX companies.

    Implements a hybrid approach:
    1. Search for specific tickers
    2. Scrape business sections and match tickers
    3. Deduplicate and save to database

    Args:
        lookback_days: Number of days to look back (default: 7)
        tickers: List of ticker symbols to search for (default: ASX200_TICKERS or test list)
        db_path: Path to database (default: from config)

    Returns:
        Dictionary with:
            - articles_scraped: Total number of articles found
            - articles_inserted: Number of new articles inserted
            - articles_skipped: Number of duplicate articles
            - tickers_found: Set of tickers found in articles
            - errors: List of errors encountered
    """
    logger.info("=" * 60)
    logger.info("Starting AFR News Scraper")
    logger.info("=" * 60)
    logger.info(f"Lookback days: {lookback_days}")

    # Set defaults
    if db_path is None:
        db_path = config.DATABASE_PATH

    if tickers is None:
        if config.ASX200_TICKERS:
            tickers = config.ASX200_TICKERS
        else:
            # Use test list if ASX200_TICKERS is empty
            logger.info("ASX200_TICKERS is empty, using test ticker list")
            tickers = ['BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'WOW', 'FMG']

    logger.info(f"Searching for {len(tickers)} tickers")
    logger.info(f"Database: {db_path}")
    logger.info(f"Rate limit: {config.AFR_RATE_LIMIT} seconds")

    all_articles = []
    tickers_found = set()
    errors = []

    # Strategy 1: Search for specific tickers
    logger.info("\n--- Strategy 1: Searching for specific tickers ---")
    for idx, ticker in enumerate(tickers):
        try:
            logger.info(f"[{idx + 1}/{len(tickers)}] Searching for {ticker}...")

            articles = search_afr_for_ticker(ticker, days_back=lookback_days, max_articles=5)

            if articles:
                all_articles.extend(articles)
                tickers_found.add(ticker)
                logger.info(f"  Found {len(articles)} articles for {ticker}")

            # Rate limiting
            if idx < len(tickers) - 1:  # Don't wait after last ticker
                rate_limit_wait(config.AFR_RATE_LIMIT)

        except Exception as e:
            error_msg = f"Error searching for {ticker}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

    # Strategy 2: Scrape business sections
    logger.info("\n--- Strategy 2: Scraping business sections ---")
    try:
        section_articles = scrape_afr_business_section(lookback_days, tickers)
        if section_articles:
            all_articles.extend(section_articles)
            for article in section_articles:
                if article.get('ticker'):
                    tickers_found.add(article['ticker'])
    except Exception as e:
        error_msg = f"Error scraping business sections: {e}"
        logger.error(error_msg)
        errors.append(error_msg)

    # Deduplicate articles by URL
    logger.info("\n--- Deduplicating articles ---")
    unique_articles = {}
    for article in all_articles:
        url = article.get('url')
        if url and url not in unique_articles:
            unique_articles[url] = article

    articles_list = list(unique_articles.values())
    logger.info(f"Total unique articles: {len(articles_list)}")

    # Save to database
    logger.info("\n--- Saving to database ---")
    inserted, skipped = save_articles_to_db(articles_list, db_path)

    # Prepare summary
    result = {
        'articles_scraped': len(articles_list),
        'articles_inserted': inserted,
        'articles_skipped': skipped,
        'tickers_found': sorted(list(tickers_found)),
        'tickers_searched': len(tickers),
        'errors': errors,
        'lookback_days': lookback_days,
    }

    # Print summary
    logger.info("=" * 60)
    logger.info("AFR Scraper Summary")
    logger.info("=" * 60)
    logger.info(f"Articles scraped: {result['articles_scraped']}")
    logger.info(f"Articles inserted: {result['articles_inserted']}")
    logger.info(f"Articles skipped (duplicates): {result['articles_skipped']}")
    logger.info(f"Tickers searched: {result['tickers_searched']}")
    logger.info(f"Tickers found: {len(result['tickers_found'])}")
    logger.info(f"Errors: {len(result['errors'])}")

    if result['tickers_found']:
        logger.info(f"\nTickers with articles: {', '.join(result['tickers_found'][:10])}")
        if len(result['tickers_found']) > 10:
            logger.info(f"  ... and {len(result['tickers_found']) - 10} more")

    logger.info("=" * 60)

    return result


def get_afr_article_count(db_path: str = None) -> Dict:
    """
    Get statistics about AFR articles in the database.

    Args:
        db_path: Path to database (default: from config)

    Returns:
        Dictionary with article statistics
    """
    if db_path is None:
        db_path = config.DATABASE_PATH

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Total AFR articles
        cursor.execute("SELECT COUNT(*) FROM news_articles WHERE source = 'AFR'")
        total_articles = cursor.fetchone()[0]

        # Unique tickers
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM news_articles WHERE source = 'AFR'")
        unique_tickers = cursor.fetchone()[0]

        # Date range
        cursor.execute("""
            SELECT MIN(datetime), MAX(datetime)
            FROM news_articles
            WHERE source = 'AFR' AND datetime IS NOT NULL
        """)
        date_range = cursor.fetchone()

        # Articles by ticker (top 10)
        cursor.execute("""
            SELECT ticker, COUNT(*) as count
            FROM news_articles
            WHERE source = 'AFR' AND ticker IS NOT NULL
            GROUP BY ticker
            ORDER BY count DESC
            LIMIT 10
        """)
        top_tickers = cursor.fetchall()

        conn.close()

        return {
            'total_articles': total_articles,
            'unique_tickers': unique_tickers,
            'date_range': date_range,
            'top_tickers': top_tickers,
        }

    except Exception as e:
        logger.error(f"Error getting article statistics: {e}")
        return {}


if __name__ == '__main__':
    """
    Main execution block for standalone script execution.

    Scrapes last 7 days of AFR news and displays summary statistics.
    """
    print("\n" + "=" * 60)
    print("AFR News Scraper - Standalone Execution")
    print("=" * 60 + "\n")

    # Run scraper
    result = scrape_afr_news(lookback_days=7)

    # Show detailed summary
    print("\n" + "=" * 60)
    print("SCRAPING RESULTS")
    print("=" * 60)
    print(f"Articles scraped: {result['articles_scraped']}")
    print(f"Articles inserted: {result['articles_inserted']}")
    print(f"Articles skipped: {result['articles_skipped']}")
    print(f"Tickers searched: {result['tickers_searched']}")
    print(f"Tickers found in articles: {len(result['tickers_found'])}")

    if result['tickers_found']:
        print(f"\nTickers with articles:")
        for ticker in result['tickers_found'][:20]:
            print(f"  - {ticker}")
        if len(result['tickers_found']) > 20:
            print(f"  ... and {len(result['tickers_found']) - 20} more")

    if result['errors']:
        print(f"\nErrors encountered: {len(result['errors'])}")
        for error in result['errors'][:5]:
            print(f"  - {error}")
        if len(result['errors']) > 5:
            print(f"  ... and {len(result['errors']) - 5} more")

    # Show database statistics
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    stats = get_afr_article_count()
    if stats:
        print(f"Total AFR articles in database: {stats['total_articles']}")
        print(f"Unique tickers covered: {stats['unique_tickers']}")

        if stats['date_range'][0] and stats['date_range'][1]:
            print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")

        if stats['top_tickers']:
            print("\nTop 10 tickers by article count:")
            for ticker, count in stats['top_tickers']:
                print(f"  {ticker}: {count} articles")

    print("\n" + "=" * 60)
    print("Scraping complete!")
    print("=" * 60 + "\n")
