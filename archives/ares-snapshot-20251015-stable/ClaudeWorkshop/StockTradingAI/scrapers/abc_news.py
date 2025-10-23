"""
ABC News (Australian Broadcasting Corporation) Scraper

Scrapes business and finance news from ABC News Australia.
ABC is Australia's national public broadcaster with high credibility.

Author: Claude Code
Date: 2025-10-10
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import time
import re

logger = logging.getLogger(__name__)


def scrape_abc_news(
    lookback_days: int = 7,
    tickers: Optional[List[str]] = None,
    db_path: str = 'data/trading.db',
    rate_limit: float = 2.0
) -> Dict:
    """
    Scrape ABC News for Australian business and finance stories.

    Args:
        lookback_days: Days to look back
        tickers: List of ticker symbols to search for
        db_path: Database path
        rate_limit: Seconds between requests

    Returns:
        Dictionary with scraping results
    """
    logger.info("=" * 60)
    logger.info("Starting ABC News Scraper")
    logger.info("=" * 60)
    logger.info(f"Lookback days: {lookback_days}")
    logger.info(f"Database: {db_path}")

    articles = []
    errors = 0

    # ABC News business sections
    sections = [
        'https://www.abc.net.au/news/business/',
        'https://www.abc.net.au/news/economy/',
        'https://www.abc.net.au/news/finance/'
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for section_url in sections:
        try:
            logger.info(f"Scraping ABC section: {section_url}")

            response = requests.get(section_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # ABC uses article tags with specific classes
            article_links = soup.find_all('article', class_='_3FGt-')

            for article in article_links[:20]:  # Limit per section
                try:
                    # Extract article link
                    link_tag = article.find('a', href=True)
                    if not link_tag:
                        continue

                    article_url = link_tag['href']
                    if not article_url.startswith('http'):
                        article_url = 'https://www.abc.net.au' + article_url

                    # Extract title
                    title_tag = article.find('h3') or article.find('h2')
                    if not title_tag:
                        continue

                    title = title_tag.get_text(strip=True)

                    # Extract description
                    desc_tag = article.find('p')
                    description = desc_tag.get_text(strip=True) if desc_tag else ''

                    # Extract date
                    time_tag = article.find('time')
                    pub_date = None
                    if time_tag and time_tag.get('datetime'):
                        pub_date = time_tag['datetime']

                    # Match against tickers
                    matched_ticker = None
                    text_to_search = f"{title} {description}".upper()

                    if tickers:
                        for ticker in tickers:
                            if ticker.upper() in text_to_search:
                                matched_ticker = ticker
                                break

                    if matched_ticker or not tickers:
                        articles.append({
                            'source': 'ABC News',
                            'ticker': matched_ticker,
                            'title': title,
                            'content': description,
                            'url': article_url,
                            'datetime': pub_date or datetime.now().isoformat()
                        })

                except Exception as e:
                    logger.debug(f"Error parsing article: {e}")
                    continue

            time.sleep(rate_limit)

        except Exception as e:
            logger.error(f"Error scraping {section_url}: {e}")
            errors += 1

    # Save to database
    inserted = save_to_database(articles, db_path)

    logger.info("=" * 60)
    logger.info("ABC News Scraper Summary")
    logger.info("=" * 60)
    logger.info(f"Articles found: {len(articles)}")
    logger.info(f"Articles inserted: {inserted}")
    logger.info(f"Errors: {errors}")
    logger.info("=" * 60)

    return {
        'articles_scraped': len(articles),
        'articles_inserted': inserted,
        'errors': errors
    }


def save_to_database(articles: List[Dict], db_path: str) -> int:
    """Save articles to database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0

    for article in articles:
        try:
            cursor.execute("""
                INSERT INTO news_articles (source, ticker, title, content, url, datetime, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                article['source'],
                article['ticker'],
                article['title'],
                article['content'],
                article['url'],
                article['datetime'],
                datetime.now().isoformat()
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            # Duplicate URL
            continue
        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            continue

    conn.commit()
    conn.close()

    return inserted


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Test with ASX200 tickers
    test_tickers = ['BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'TLS', 'WOW']

    result = scrape_abc_news(
        lookback_days=7,
        tickers=test_tickers,
        db_path='data/trading.db'
    )

    print(f"\nScraping complete: {result}")
