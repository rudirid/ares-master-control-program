#!/usr/bin/env python3
"""
News Sentiment & Price Impact Analysis Tool

This script:
1. Fetches all news articles from the database
2. Analyzes sentiment using Claude API
3. Calculates stock price changes at 1, 3, and 7 days after publication
4. Exports results to CSV for further analysis

The output CSV contains:
- Article metadata (title, date, ticker, source)
- Sentiment analysis (sentiment, score, confidence, themes)
- Price impacts (1-day, 3-day, 7-day percentage changes)
- Baseline volatility for comparison

Usage:
    python analyze_news_impact.py

    # Analyze specific tickers only
    python analyze_news_impact.py --tickers BHP,CBA,NAB

    # Limit number of articles
    python analyze_news_impact.py --limit 10

Author: Claude Code
Date: 2025-10-09
"""

import sqlite3
import csv
import argparse
import time
import os
import sys
from datetime import datetime
from typing import List, Dict

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from analysis.local_sentiment_analyzer import LocalSentimentAnalyzer
from analysis.price_analyzer import PriceAnalyzer
from scrapers.utils import get_logger

# Initialize logger
logger = get_logger(__name__)


def get_articles_from_db(db_path: str, tickers: List[str] = None, limit: int = None) -> List[Dict]:
    """
    Fetch articles from database.

    Args:
        db_path: Path to SQLite database
        tickers: Optional list of tickers to filter by
        limit: Optional limit on number of articles

    Returns:
        List of article dictionaries
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build query
        query = """
            SELECT
                id, source, ticker, title,
                COALESCE(datetime, created_at) as article_date,
                content, url
            FROM news_articles
            WHERE COALESCE(datetime, created_at) IS NOT NULL
        """

        params = []

        if tickers:
            placeholders = ','.join('?' * len(tickers))
            query += f" AND ticker IN ({placeholders})"
            params.extend(tickers)

        query += " ORDER BY article_date DESC"

        if limit:
            query += f" LIMIT {limit}"

        cursor.execute(query, params)
        articles = [dict(row) for row in cursor.fetchall()]

        conn.close()

        logger.info(f"Fetched {len(articles)} articles from database")
        return articles

    except Exception as e:
        logger.error(f"Error fetching articles from database: {e}")
        return []


def analyze_article(article: Dict, sentiment_analyzer: LocalSentimentAnalyzer,
                   price_analyzer: PriceAnalyzer) -> Dict:
    """
    Analyze a single article for sentiment and price impact.

    Args:
        article: Article dictionary
        sentiment_analyzer: SentimentAnalyzer instance
        price_analyzer: PriceAnalyzer instance

    Returns:
        Dictionary with combined analysis results
    """
    result = {
        'article_id': article['id'],
        'ticker': article['ticker'],
        'source': article['source'],
        'title': article['title'],
        'article_date': article['article_date'],
        'url': article.get('url', ''),
    }

    try:
        # Sentiment analysis
        logger.debug(f"Analyzing sentiment for article {article['id']}: {article['ticker']}")
        sentiment = sentiment_analyzer.analyze_article(
            title=article['title'],
            content=article.get('content', ''),
            ticker=article['ticker']
        )

        result['sentiment'] = sentiment['sentiment']
        result['sentiment_score'] = sentiment['sentiment_score']
        result['confidence'] = sentiment['confidence']
        result['themes'] = '|'.join(sentiment['themes'])  # Join themes with pipe separator
        result['summary'] = sentiment['summary']
        result['impact_assessment'] = sentiment['impact_assessment']

        # Extract date for price analysis
        article_date = article['article_date']
        if ' ' in article_date:
            article_date = article_date.split(' ')[0]  # Take date part only

        # Price impact analysis
        logger.debug(f"Analyzing price impact for {article['ticker']} on {article_date}")
        price_impact = price_analyzer.analyze_article_impact(
            ticker=article['ticker'],
            article_date=article_date
        )

        # Extract price changes
        for days in [1, 3, 7]:
            key = f'day_{days}'
            if price_impact.get(key):
                data = price_impact[key]
                result[f'price_change_{days}d'] = data['price_change']
                result[f'price_change_pct_{days}d'] = data['price_change_pct']
                result[f'start_price_{days}d'] = data['start_price']
                result[f'end_price_{days}d'] = data['end_price']
            else:
                result[f'price_change_{days}d'] = None
                result[f'price_change_pct_{days}d'] = None
                result[f'start_price_{days}d'] = None
                result[f'end_price_{days}d'] = None

        # Get baseline volatility
        volatility = price_analyzer.get_baseline_volatility(article['ticker'], article_date, days=30)
        result['baseline_volatility_30d'] = volatility

        result['status'] = 'success'

    except Exception as e:
        logger.error(f"Error analyzing article {article['id']}: {e}")
        result['status'] = 'error'
        result['error'] = str(e)

    return result


def export_to_csv(results: List[Dict], output_file: str):
    """
    Export analysis results to CSV.

    Args:
        results: List of analysis result dictionaries
        output_file: Output CSV file path
    """
    if not results:
        logger.warning("No results to export")
        return

    try:
        # Define CSV columns
        columns = [
            'article_id', 'ticker', 'source', 'article_date', 'title',
            'sentiment', 'sentiment_score', 'confidence',
            'themes', 'summary', 'impact_assessment',
            'price_change_1d', 'price_change_pct_1d', 'start_price_1d', 'end_price_1d',
            'price_change_3d', 'price_change_pct_3d', 'start_price_3d', 'end_price_3d',
            'price_change_7d', 'price_change_pct_7d', 'start_price_7d', 'end_price_7d',
            'baseline_volatility_30d',
            'url', 'status', 'error'
        ]

        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Results exported to {output_file}")
        print(f"\nResults exported to: {output_file}")

    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        print(f"\nError exporting to CSV: {e}")


def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description='Analyze news sentiment and price impact')
    parser.add_argument('--tickers', type=str, help='Comma-separated list of tickers to analyze')
    parser.add_argument('--limit', type=int, help='Limit number of articles to analyze')
    parser.add_argument('--output', type=str, default='results/news_impact_analysis.csv',
                       help='Output CSV file path')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("NEWS SENTIMENT & PRICE IMPACT ANALYSIS")
    print("=" * 70 + "\n")

    # Parse tickers
    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(',')]
        print(f"Filtering for tickers: {', '.join(tickers)}")

    if args.limit:
        print(f"Limiting to {args.limit} articles")

    print(f"Output file: {args.output}")
    print(f"Analysis method: Local rule-based (no API required)")
    print()

    # Initialize analyzers
    print("Initializing analyzers...")
    sentiment_analyzer = LocalSentimentAnalyzer()
    price_analyzer = PriceAnalyzer(config.DATABASE_PATH)

    # Fetch articles
    print("Fetching articles from database...")
    articles = get_articles_from_db(config.DATABASE_PATH, tickers=tickers, limit=args.limit)

    if not articles:
        print("No articles found in database")
        return

    print(f"Found {len(articles)} articles to analyze\n")

    # Confirm before proceeding
    estimated_time = len(articles) * 0.1  # Much faster now - ~0.1 seconds per article
    print(f"Estimated time: ~{estimated_time:.1f} seconds")
    print()

    response = input("Proceed with analysis? (y/n): ")
    if response.lower() != 'y':
        print("Analysis cancelled")
        return

    # Analyze articles
    print("\n" + "=" * 70)
    print("ANALYZING ARTICLES")
    print("=" * 70 + "\n")

    results = []
    start_time = time.time()

    for idx, article in enumerate(articles, 1):
        print(f"[{idx}/{len(articles)}] {article['ticker']}: {article['title'][:50]}...")

        result = analyze_article(article, sentiment_analyzer, price_analyzer)
        results.append(result)

        # Show progress
        if result['status'] == 'success':
            sentiment_display = f"{result['sentiment']} ({result['sentiment_score']:+.2f})"
            price_1d = result.get('price_change_pct_1d')
            price_display = f"{price_1d:+.2f}%" if price_1d is not None else "N/A"
            print(f"  Sentiment: {sentiment_display}, Price (1d): {price_display}")
        else:
            print(f"  ERROR: {result.get('error', 'Unknown error')}")

    elapsed_time = time.time() - start_time

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Export results
    print("\n" + "=" * 70)
    print("EXPORTING RESULTS")
    print("=" * 70)
    export_to_csv(results, args.output)

    # Summary statistics
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"Total articles analyzed: {len(results)}")
    successful = sum(1 for r in results if r['status'] == 'success')
    print(f"Successful: {successful}")
    print(f"Errors: {len(results) - successful}")
    print(f"Time elapsed: {elapsed_time:.1f} seconds")

    # Sentiment distribution
    sentiments = [r.get('sentiment') for r in results if r.get('sentiment')]
    if sentiments:
        print(f"\nSentiment distribution:")
        print(f"  Positive: {sentiments.count('positive')}")
        print(f"  Neutral: {sentiments.count('neutral')}")
        print(f"  Negative: {sentiments.count('negative')}")

    # Price impact summary
    price_changes_1d = [r.get('price_change_pct_1d') for r in results
                       if r.get('price_change_pct_1d') is not None]
    if price_changes_1d:
        avg_change = sum(price_changes_1d) / len(price_changes_1d)
        print(f"\nAverage 1-day price change: {avg_change:+.2f}%")

    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
