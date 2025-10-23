"""
HotCopper Forum Sentiment Scraper for ASX stocks.

This module collects and analyzes sentiment from HotCopper stock forums,
a popular Australian retail investor discussion platform. The scraper:
- Collects forum posts for specified ASX tickers
- Analyzes sentiment using keyword-based scoring
- Calculates daily post counts and sentiment metrics
- Stores results in the hotcopper_sentiment database table

Note: HotCopper sentiment represents retail investor sentiment, which can be
volatile and may serve as a contrarian indicator during extremes.
"""

import sqlite3
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
import config
from scrapers.utils import get_logger, rate_limit_wait, safe_request

# Configure logging
logger = get_logger(__name__)


# Sentiment word lists for basic sentiment analysis
POSITIVE_WORDS = {
    'bullish', 'buy', 'moon', 'rocket', 'strong', 'profit', 'growth',
    'uptrend', 'breakout', 'support', 'green', 'gains', 'winner',
    'bullish', 'rally', 'surge', 'soar', 'boom', 'stellar', 'excellent',
    'positive', 'opportunity', 'undervalued', 'accumulate', 'bounce',
    'recovery', 'breakthrough', 'success', 'upgrade', 'outperform'
}

NEGATIVE_WORDS = {
    'bearish', 'sell', 'crash', 'dump', 'weak', 'loss', 'decline',
    'downtrend', 'resistance', 'red', 'falling', 'loser', 'avoid',
    'plunge', 'tank', 'collapse', 'disaster', 'terrible', 'negative',
    'overvalued', 'exit', 'drop', 'downturn', 'failure', 'concern',
    'downgrade', 'underperform', 'disappointing', 'warning', 'risk'
}


def get_ticker_forum_url(ticker: str) -> str:
    """
    Build the HotCopper forum URL for a given ticker.

    HotCopper forum URLs typically follow the pattern:
    https://hotcopper.com.au/threads/[company-name-ticker]

    For searching/accessing threads, we use the search functionality:
    https://hotcopper.com.au/search?q=[ticker]&type=threads

    Args:
        ticker: ASX ticker symbol (e.g., 'BHP', 'CBA')

    Returns:
        URL string for the ticker's forum search page
    """
    # Use search URL as it's more reliable for finding ticker discussions
    return f"https://hotcopper.com.au/search?q={ticker}&type=threads"


def calculate_sentiment(text: str) -> float:
    """
    Calculate sentiment score from text using keyword analysis.

    This is a basic sentiment analysis approach that counts positive and
    negative words. For production use, consider:
    - Machine learning models (e.g., BERT, RoBERTa)
    - Financial sentiment lexicons (e.g., Loughran-McDonald)
    - Context-aware sentiment analysis
    - Sarcasm detection

    Args:
        text: Text content to analyze (post title or content)

    Returns:
        Sentiment score between -1 (most negative) and 1 (most positive)
        Returns 0 for neutral or empty text

    Example:
        >>> calculate_sentiment("BHP looks strong, great buying opportunity!")
        0.67
        >>> calculate_sentiment("Terrible results, going to crash")
        -0.67
    """
    if not text:
        return 0.0

    # Convert to lowercase for case-insensitive matching
    text_lower = text.lower()

    # Count positive and negative words
    positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)

    # Calculate sentiment score
    # Formula: (positive - negative) / (positive + negative + 1)
    # The +1 prevents division by zero and dampens extreme scores
    total_words = positive_count + negative_count + 1
    sentiment_score = (positive_count - negative_count) / total_words

    # Clamp to [-1, 1] range
    sentiment_score = max(-1.0, min(1.0, sentiment_score))

    # Round to 2 decimal places
    return round(sentiment_score, 2)


def extract_trending_topics(posts: List[Dict[str, Any]], max_topics: int = 3) -> str:
    """
    Extract the most common/trending discussion topics from posts.

    This function identifies frequently mentioned words and phrases to
    determine what topics are trending in the forum discussions.

    Args:
        posts: List of post dictionaries with 'title' and 'content' keys
        max_topics: Maximum number of topics to return

    Returns:
        Comma-separated string of trending topics/keywords

    Example:
        >>> posts = [
        ...     {'title': 'BHP earnings update', 'content': '...'},
        ...     {'title': 'BHP dividend increase', 'content': '...'}
        ... ]
        >>> extract_trending_topics(posts)
        'earnings, dividend, update'
    """
    if not posts:
        return ""

    # Combine all post titles (titles are more indicative of topics)
    all_titles = ' '.join(post.get('title', '') for post in posts)

    # Extract words (remove common stop words)
    stop_words = {
        'the', 'is', 'at', 'which', 'on', 'a', 'an', 'as', 'are', 'was',
        'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can',
        'to', 'of', 'in', 'for', 'with', 'by', 'from', 'up', 'about', 'into',
        'through', 'during', 'before', 'after', 'above', 'below', 'between',
        'thread', 'post', 'discussion', 'asx', 'stock', 'share'
    }

    # Tokenize and count words (minimum 3 characters, not in stop words)
    words = re.findall(r'\b[a-z]{3,}\b', all_titles.lower())
    word_counts = defaultdict(int)

    for word in words:
        if word not in stop_words:
            word_counts[word] += 1

    # Get top N most common words
    top_topics = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    top_topics = [topic for topic, count in top_topics[:max_topics]]

    return ', '.join(top_topics) if top_topics else "general discussion"


def count_posts_by_date(posts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Aggregate posts by date for daily metrics calculation.

    Args:
        posts: List of post dictionaries with 'date' key

    Returns:
        Dictionary mapping date strings (YYYY-MM-DD) to lists of posts

    Example:
        >>> posts = [
        ...     {'date': '2025-10-09', 'title': 'Post 1'},
        ...     {'date': '2025-10-09', 'title': 'Post 2'},
        ...     {'date': '2025-10-08', 'title': 'Post 3'}
        ... ]
        >>> result = count_posts_by_date(posts)
        >>> len(result['2025-10-09'])
        2
    """
    posts_by_date = defaultdict(list)

    for post in posts:
        date_str = post.get('date', '')
        if date_str:
            posts_by_date[date_str].append(post)

    return dict(posts_by_date)


def parse_hotcopper_page(html_content: str, ticker: str) -> List[Dict[str, Any]]:
    """
    Parse HotCopper HTML page to extract post information.

    This function handles the specific HTML structure of HotCopper pages.
    Note: HotCopper's HTML structure may change, requiring updates to selectors.

    Args:
        html_content: Raw HTML content from HotCopper page
        ticker: Ticker symbol being scraped (for context)

    Returns:
        List of post dictionaries with keys: title, date, content, url

    Note:
        This implementation uses generic selectors that should work with
        typical forum structures. In production, you may need to update
        selectors based on HotCopper's actual HTML structure.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    posts = []

    try:
        # Find thread/post containers
        # Note: These selectors are generic and may need adjustment
        # based on actual HotCopper HTML structure

        # Common forum patterns: look for article, post, thread containers
        post_containers = (
            soup.find_all('article', class_=re.compile(r'post|thread|message')) or
            soup.find_all('div', class_=re.compile(r'post|thread|message')) or
            soup.find_all('li', class_=re.compile(r'post|thread|message'))
        )

        for container in post_containers:
            try:
                post_data = {}

                # Extract title (look for common title patterns)
                title_elem = (
                    container.find('h2') or
                    container.find('h3') or
                    container.find(class_=re.compile(r'title|subject|heading'))
                )
                post_data['title'] = title_elem.get_text(strip=True) if title_elem else ""

                # Extract date (look for time/date elements)
                date_elem = (
                    container.find('time') or
                    container.find(class_=re.compile(r'date|time|timestamp'))
                )

                if date_elem:
                    # Try to get datetime attribute first, then text
                    date_str = (
                        date_elem.get('datetime') or
                        date_elem.get('title') or
                        date_elem.get_text(strip=True)
                    )
                    post_data['date'] = parse_date_string(date_str)
                else:
                    post_data['date'] = ""

                # Extract content (look for content/body elements)
                content_elem = (
                    container.find(class_=re.compile(r'content|body|text|message')) or
                    container.find('p')
                )
                post_data['content'] = content_elem.get_text(strip=True) if content_elem else ""

                # Extract URL (look for links)
                link_elem = container.find('a', href=True)
                if link_elem:
                    url = link_elem['href']
                    # Make absolute URL if relative
                    if url.startswith('/'):
                        url = f"https://hotcopper.com.au{url}"
                    post_data['url'] = url
                else:
                    post_data['url'] = ""

                # Only add if we have at least a title or content
                if post_data['title'] or post_data['content']:
                    posts.append(post_data)

            except Exception as e:
                logger.debug(f"Error parsing individual post container: {e}")
                continue

        logger.debug(f"Parsed {len(posts)} posts for {ticker}")

    except Exception as e:
        logger.error(f"Error parsing HotCopper page for {ticker}: {e}")

    return posts


def parse_date_string(date_str: str) -> str:
    """
    Parse various date string formats to standard YYYY-MM-DD format.

    Handles common date formats found on forums:
    - ISO format: 2025-10-09T14:30:00
    - Relative: "2 hours ago", "yesterday"
    - Various formats: "9 Oct 2025", "Oct 9, 2025"

    Args:
        date_str: Date string in various formats

    Returns:
        Date string in YYYY-MM-DD format, or empty string if parsing fails
    """
    if not date_str:
        return ""

    try:
        # Handle ISO format with timezone
        if 'T' in date_str:
            # Extract just the date part
            date_str = date_str.split('T')[0]
            return date_str

        # Handle relative dates
        today = datetime.now()

        if 'today' in date_str.lower():
            return today.strftime('%Y-%m-%d')

        if 'yesterday' in date_str.lower():
            yesterday = today - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d')

        # Handle "X hours/days ago"
        hours_match = re.search(r'(\d+)\s*hour', date_str.lower())
        if hours_match:
            return today.strftime('%Y-%m-%d')

        days_match = re.search(r'(\d+)\s*day', date_str.lower())
        if days_match:
            days_ago = int(days_match.group(1))
            date = today - timedelta(days=days_ago)
            return date.strftime('%Y-%m-%d')

        # Try common date formats
        for fmt in ['%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d',
                    '%d %b %Y', '%b %d, %Y', '%d %B %Y', '%B %d, %Y']:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        # If all else fails, use today's date for recent posts
        logger.debug(f"Could not parse date string: {date_str}, using today's date")
        return today.strftime('%Y-%m-%d')

    except Exception as e:
        logger.debug(f"Error parsing date string '{date_str}': {e}")
        return ""


def scrape_ticker_forum(
    ticker: str,
    lookback_days: int = 7
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Scrape HotCopper forum for a specific ticker.

    This function handles the actual HTTP request and parsing for a single ticker.
    It respects rate limits and handles errors gracefully.

    Args:
        ticker: ASX ticker symbol
        lookback_days: Number of days to look back for posts

    Returns:
        Tuple of (posts_list, forum_url)
        posts_list: List of post dictionaries
        forum_url: URL of the forum page scraped

    Note:
        This function implements polite scraping practices:
        - Respects robots.txt
        - Uses rate limiting
        - Uses realistic User-Agent
        - Handles errors gracefully
    """
    url = get_ticker_forum_url(ticker)
    logger.info(f"Scraping HotCopper forum for {ticker}: {url}")

    # Make request with rate limiting
    headers = {
        'User-Agent': config.USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-AU,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    response = safe_request(url, headers=headers)

    if response is None:
        logger.warning(f"Failed to fetch HotCopper forum for {ticker}")
        return [], url

    # Parse the page
    posts = parse_hotcopper_page(response.text, ticker)

    # Filter posts by date range
    cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
    filtered_posts = [
        post for post in posts
        if post.get('date', '') >= cutoff_date
    ]

    logger.info(f"Found {len(filtered_posts)} posts for {ticker} in last {lookback_days} days")

    # Apply rate limiting before next request
    rate_limit_wait(config.HOTCOPPER_RATE_LIMIT)

    return filtered_posts, url


def store_sentiment_data(
    conn: sqlite3.Connection,
    ticker: str,
    date: str,
    post_count: int,
    sentiment_score: float,
    post_title: str,
    url: str
) -> None:
    """
    Store sentiment data in the database.

    Uses INSERT OR REPLACE to update existing records for the same ticker/date.

    Args:
        conn: Database connection
        ticker: ASX ticker symbol
        date: Date in YYYY-MM-DD format
        post_count: Number of posts for this date
        sentiment_score: Calculated sentiment score (-1 to 1)
        post_title: Trending topics/titles
        url: Forum URL
    """
    cursor = conn.cursor()

    query = """
    INSERT OR REPLACE INTO hotcopper_sentiment
    (ticker, date, post_count, sentiment_score, post_title, url)
    VALUES (?, ?, ?, ?, ?, ?)
    """

    cursor.execute(query, (
        ticker,
        date,
        post_count,
        sentiment_score,
        post_title,
        url
    ))

    logger.debug(f"Stored sentiment data for {ticker} on {date}: "
                f"count={post_count}, sentiment={sentiment_score:.2f}")


def scrape_hotcopper_sentiment(
    tickers: List[str],
    lookback_days: int = 7,
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Scrape HotCopper forum sentiment for multiple tickers.

    This is the main entry point for the HotCopper scraper. It:
    1. Scrapes forum posts for each ticker
    2. Calculates daily sentiment metrics
    3. Stores results in the database
    4. Returns a summary of the operation

    Args:
        tickers: List of ASX ticker symbols to analyze
        lookback_days: How many days back to analyze (default: 7)
        db_path: Path to SQLite database (default: from config)

    Returns:
        Dictionary with summary information:
            - tickers_analyzed: List of tickers that were analyzed
            - tickers_failed: List of tickers that failed
            - total_posts: Total number of posts collected
            - date_range: Tuple of (start_date, end_date)
            - sentiment_summary: Dict with highest/lowest sentiment tickers

    Example:
        >>> result = scrape_hotcopper_sentiment(['BHP', 'CBA', 'CSL'], lookback_days=7)
        >>> print(f"Analyzed {len(result['tickers_analyzed'])} tickers")
        >>> print(f"Total posts: {result['total_posts']}")

    Important Notes:
        - HotCopper sentiment represents retail investor sentiment
        - High activity can be a contrarian indicator (extreme optimism at tops)
        - Sentiment should be used as one of many indicators
        - Basic keyword sentiment analysis has limitations (sarcasm, context)
        - Respects rate limits to avoid overwhelming the server
        - Some tickers may not have active HotCopper forums
    """
    # Set defaults
    if db_path is None:
        db_path = config.DATABASE_PATH

    logger.info(f"Starting HotCopper sentiment analysis for {len(tickers)} tickers")
    logger.info(f"Lookback period: {lookback_days} days")

    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Connect to database
    conn = sqlite3.connect(db_path)

    # Track results
    tickers_analyzed = []
    tickers_failed = []
    total_posts = 0
    sentiment_by_ticker = {}

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)

    # Process each ticker
    for ticker in tickers:
        try:
            logger.info(f"Processing {ticker}...")

            # Scrape forum posts
            posts, forum_url = scrape_ticker_forum(ticker, lookback_days)

            if not posts:
                logger.warning(f"No posts found for {ticker} in last {lookback_days} days")
                tickers_failed.append({
                    'ticker': ticker,
                    'error': 'No posts found'
                })
                continue

            # Group posts by date
            posts_by_date = count_posts_by_date(posts)

            # Process each date
            ticker_total_posts = 0
            ticker_sentiments = []

            for date_str, date_posts in posts_by_date.items():
                # Calculate metrics for this date
                post_count = len(date_posts)
                ticker_total_posts += post_count

                # Calculate sentiment from all posts on this date
                all_text = ' '.join(
                    f"{post.get('title', '')} {post.get('content', '')}"
                    for post in date_posts
                )
                sentiment_score = calculate_sentiment(all_text)
                ticker_sentiments.append(sentiment_score)

                # Extract trending topics
                trending_topics = extract_trending_topics(date_posts)

                # Store in database
                store_sentiment_data(
                    conn=conn,
                    ticker=ticker,
                    date=date_str,
                    post_count=post_count,
                    sentiment_score=sentiment_score,
                    post_title=trending_topics,
                    url=forum_url
                )

            # Commit after each ticker
            conn.commit()

            # Track overall sentiment for this ticker
            avg_sentiment = sum(ticker_sentiments) / len(ticker_sentiments) if ticker_sentiments else 0
            sentiment_by_ticker[ticker] = {
                'avg_sentiment': avg_sentiment,
                'post_count': ticker_total_posts,
                'days_active': len(posts_by_date)
            }

            total_posts += ticker_total_posts
            tickers_analyzed.append(ticker)

            logger.info(f"Successfully analyzed {ticker}: {ticker_total_posts} posts, "
                       f"avg sentiment: {avg_sentiment:.2f}")

        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            tickers_failed.append({
                'ticker': ticker,
                'error': str(e)
            })
            continue

    # Close database connection
    conn.close()

    # Find highest and lowest sentiment tickers
    if sentiment_by_ticker:
        highest_sentiment = max(
            sentiment_by_ticker.items(),
            key=lambda x: x[1]['avg_sentiment']
        )
        lowest_sentiment = min(
            sentiment_by_ticker.items(),
            key=lambda x: x[1]['avg_sentiment']
        )
        most_active = max(
            sentiment_by_ticker.items(),
            key=lambda x: x[1]['post_count']
        )

        sentiment_summary = {
            'highest_sentiment': {
                'ticker': highest_sentiment[0],
                'score': highest_sentiment[1]['avg_sentiment'],
                'posts': highest_sentiment[1]['post_count']
            },
            'lowest_sentiment': {
                'ticker': lowest_sentiment[0],
                'score': lowest_sentiment[1]['avg_sentiment'],
                'posts': lowest_sentiment[1]['post_count']
            },
            'most_active': {
                'ticker': most_active[0],
                'posts': most_active[1]['post_count'],
                'sentiment': most_active[1]['avg_sentiment']
            }
        }
    else:
        sentiment_summary = {}

    # Prepare summary
    summary = {
        'tickers_analyzed': tickers_analyzed,
        'tickers_failed': tickers_failed,
        'total_posts': total_posts,
        'date_range': (start_date.date(), end_date.date()),
        'sentiment_summary': sentiment_summary,
        'sentiment_by_ticker': sentiment_by_ticker
    }

    logger.info(f"HotCopper analysis complete: {len(tickers_analyzed)} successful, "
               f"{len(tickers_failed)} failed, {total_posts} total posts")

    return summary


def get_sentiment_statistics(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get statistics about stored HotCopper sentiment data.

    Args:
        db_path: Path to SQLite database (default: from config)

    Returns:
        Dictionary with statistics including:
            - total_records: Total number of sentiment records
            - unique_tickers: Number of unique tickers tracked
            - date_range: Earliest and latest dates
            - avg_sentiment: Overall average sentiment score
            - records_per_ticker: Count of records per ticker
    """
    if db_path is None:
        db_path = config.DATABASE_PATH

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Total records
        cursor.execute("SELECT COUNT(*) FROM hotcopper_sentiment")
        total_records = cursor.fetchone()[0]

        # Unique tickers
        cursor.execute("SELECT COUNT(DISTINCT ticker) FROM hotcopper_sentiment")
        unique_tickers = cursor.fetchone()[0]

        # Date range
        cursor.execute("SELECT MIN(date), MAX(date) FROM hotcopper_sentiment")
        date_range = cursor.fetchone()

        # Average sentiment
        cursor.execute("SELECT AVG(sentiment_score) FROM hotcopper_sentiment")
        avg_sentiment = cursor.fetchone()[0] or 0

        # Records per ticker
        cursor.execute("""
            SELECT ticker, COUNT(*) as count, AVG(sentiment_score) as avg_sentiment
            FROM hotcopper_sentiment
            GROUP BY ticker
            ORDER BY count DESC
        """)
        records_per_ticker = {
            row[0]: {'count': row[1], 'avg_sentiment': row[2]}
            for row in cursor.fetchall()
        }

        return {
            'total_records': total_records,
            'unique_tickers': unique_tickers,
            'date_range': date_range,
            'avg_sentiment': round(avg_sentiment, 2),
            'records_per_ticker': records_per_ticker
        }

    finally:
        conn.close()


if __name__ == '__main__':
    """
    Main execution block for testing the HotCopper scraper.
    Analyzes test tickers and displays sentiment summary.
    """
    logger.info("=" * 60)
    logger.info("HotCopper Forum Sentiment Scraper - Test Run")
    logger.info("=" * 60)

    # Test with a few major ASX stocks
    test_tickers = ['BHP', 'CBA', 'CSL', 'WBC', 'ANZ']

    logger.info(f"\nTest tickers: {', '.join(test_tickers)}")
    logger.info(f"Lookback period: {config.DEFAULT_LOOKBACK_DAYS} days")
    logger.info(f"Rate limit: {config.HOTCOPPER_RATE_LIMIT} seconds between requests\n")

    # Run scraper
    result = scrape_hotcopper_sentiment(
        tickers=test_tickers,
        lookback_days=config.DEFAULT_LOOKBACK_DAYS
    )

    # Display results
    print("\n" + "=" * 60)
    print("HOTCOPPER SENTIMENT ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Date Range: {result['date_range'][0]} to {result['date_range'][1]}")
    print(f"Tickers Analyzed: {len(result['tickers_analyzed'])}")
    print(f"Tickers Failed: {len(result['tickers_failed'])}")
    print(f"Total Posts Collected: {result['total_posts']}")

    if result['tickers_analyzed']:
        print(f"\nSuccessfully analyzed: {', '.join(result['tickers_analyzed'])}")

    if result['tickers_failed']:
        print("\nFailed tickers:")
        for failed in result['tickers_failed']:
            print(f"  - {failed['ticker']}: {failed['error']}")

    # Display sentiment summary
    if result['sentiment_summary']:
        print("\n" + "=" * 60)
        print("SENTIMENT HIGHLIGHTS")
        print("=" * 60)

        highest = result['sentiment_summary']['highest_sentiment']
        print(f"\nMost Bullish: {highest['ticker']}")
        print(f"  Sentiment Score: {highest['score']:.2f}")
        print(f"  Post Count: {highest['posts']}")

        lowest = result['sentiment_summary']['lowest_sentiment']
        print(f"\nMost Bearish: {lowest['ticker']}")
        print(f"  Sentiment Score: {lowest['score']:.2f}")
        print(f"  Post Count: {lowest['posts']}")

        active = result['sentiment_summary']['most_active']
        print(f"\nMost Active Discussion: {active['ticker']}")
        print(f"  Post Count: {active['posts']}")
        print(f"  Sentiment: {active['sentiment']:.2f}")

    # Display per-ticker breakdown
    if result['sentiment_by_ticker']:
        print("\n" + "=" * 60)
        print("TICKER BREAKDOWN")
        print("=" * 60)

        for ticker, data in result['sentiment_by_ticker'].items():
            print(f"\n{ticker}:")
            print(f"  Posts: {data['post_count']}")
            print(f"  Days Active: {data['days_active']}")
            print(f"  Avg Sentiment: {data['avg_sentiment']:.2f}")

    # Display database statistics
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)

    stats = get_sentiment_statistics()
    print(f"Total Records: {stats['total_records']}")
    print(f"Unique Tickers: {stats['unique_tickers']}")
    print(f"Date Range: {stats['date_range'][0]} to {stats['date_range'][1]}")
    print(f"Overall Avg Sentiment: {stats['avg_sentiment']:.2f}")

    print("\n" + "=" * 60)
    print("IMPORTANT NOTES")
    print("=" * 60)
    print("- HotCopper sentiment represents retail investor sentiment")
    print("- High activity can be a contrarian indicator")
    print("- Sentiment should be used with other technical/fundamental analysis")
    print("- Basic keyword analysis has limitations (sarcasm, context)")
    print("- Some tickers may have limited forum activity")
    print("=" * 60)

    print(f"\nDatabase location: {config.DATABASE_PATH}")
    print("=" * 60)
