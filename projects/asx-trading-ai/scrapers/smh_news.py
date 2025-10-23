"""
Sydney Morning Herald (SMH) Business News Scraper

Scrapes business news from SMH, one of Australia's major newspapers.
Part of Nine Entertainment, high credibility for business news.

Author: Claude Code
Date: 2025-10-10
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time

logger = logging.getLogger(__name__)


def scrape_smh_news(
    lookback_days: int = 7,
    tickers: Optional[List[str]] = None,
    db_path: str = 'data/trading.db',
    rate_limit: float = 2.0
) -> Dict:
    """
    Scrape SMH for Australian business news.

    Args:
        lookback_days: Days to look back
        tickers: List of ticker symbols
        db_path: Database path
        rate_limit: Seconds between requests

    Returns:
        Dictionary with scraping results
    """
    logger.info("=" * 60)
    logger.info("Starting SMH News Scraper")
    logger.info("=" * 60)

    articles = []
    errors = 0

    # SMH business sections
    sections = [
        'https://www.smh.com.au/business',
        'https://www.smh.com.au/business/markets',
        'https://www.smh.com.au/business/banking-and-finance',
        'https://www.smh.com.au/business/companies'
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for section_url in sections:
        try:
            logger.info(f"Scraping SMH section: {section_url}")

            response = requests.get(section_url, headers=headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # SMH uses article elements with data attributes
            article_elements = soup.find_all('article', {'data-testid': True})

            for article in article_elements[:15]:
                try:
                    # Extract link
                    link_tag = article.find('a', href=True)
                    if not link_tag:
                        continue

                    article_url = link_tag['href']
                    if not article_url.startswith('http'):
                        article_url = 'https://www.smh.com.au' + article_url

                    # Extract title
                    title_tag = article.find('h3') or article.find('h2') or link_tag
                    title = title_tag.get_text(strip=True) if title_tag else ''

                    if not title:
                        continue

                    # Extract snippet
                    snippet_tag = article.find('p')
                    content = snippet_tag.get_text(strip=True) if snippet_tag else ''

                    # Match tickers
                    matched_ticker = None
                    search_text = f"{title} {content}".upper()

                    if tickers:
                        for ticker in tickers:
                            if ticker.upper() in search_text:
                                matched_ticker = ticker
                                break

                    if matched_ticker or not tickers:
                        articles.append({
                            'source': 'SMH',
                            'ticker': matched_ticker,
                            'title': title,
                            'content': content,
                            'url': article_url,
                            'datetime': datetime.now().isoformat()
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
    logger.info("SMH Scraper Summary")
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
            continue
        except Exception as e:
            logger.error(f"Error inserting: {e}")
            continue

    conn.commit()
    conn.close()

    return inserted


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    test_tickers = ['BHP', 'CBA', 'CSL', 'NAB', 'WBC']

    result = scrape_smh_news(
        lookback_days=7,
        tickers=test_tickers,
        db_path='data/trading.db'
    )

    print(f"\nScraping complete: {result}")
