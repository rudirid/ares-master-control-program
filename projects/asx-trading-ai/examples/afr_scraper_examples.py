"""
AFR News Scraper - Usage Examples

This file demonstrates various ways to use the AFR news scraper
for different scenarios and requirements.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.afr_news import scrape_afr_news, get_afr_article_count


def example_1_basic_scraping():
    """
    Example 1: Basic scraping with default settings.

    Scrapes last 7 days for default ticker list.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Basic Scraping")
    print("=" * 60)

    result = scrape_afr_news(lookback_days=7)

    print(f"\nResults:")
    print(f"  Articles scraped: {result['articles_scraped']}")
    print(f"  Articles inserted: {result['articles_inserted']}")
    print(f"  Tickers found: {len(result['tickers_found'])}")

    if result['tickers_found']:
        print(f"  Example tickers: {', '.join(result['tickers_found'][:5])}")


def example_2_specific_tickers():
    """
    Example 2: Scrape specific tickers only.

    Useful when you're only interested in certain companies.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Specific Tickers")
    print("=" * 60)

    # Major banks and miners
    my_tickers = ['BHP', 'RIO', 'FMG', 'CBA', 'NAB', 'WBC', 'ANZ']

    print(f"Scraping for: {', '.join(my_tickers)}")

    result = scrape_afr_news(
        lookback_days=14,  # Last 2 weeks
        tickers=my_tickers
    )

    print(f"\nResults:")
    print(f"  Articles scraped: {result['articles_scraped']}")
    print(f"  Articles inserted: {result['articles_inserted']}")

    # Show which tickers had articles
    found = set(result['tickers_found'])
    not_found = set(my_tickers) - found

    print(f"\n  Tickers with articles: {', '.join(sorted(found))}")
    if not_found:
        print(f"  Tickers without articles: {', '.join(sorted(not_found))}")


def example_3_daily_update():
    """
    Example 3: Daily update (just last 24 hours).

    Perfect for scheduled daily runs.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Daily Update")
    print("=" * 60)

    print("Scraping articles from last 24 hours...")

    result = scrape_afr_news(lookback_days=1)

    print(f"\nToday's Results:")
    print(f"  New articles: {result['articles_inserted']}")
    print(f"  Duplicate articles: {result['articles_skipped']}")
    print(f"  Active tickers: {len(result['tickers_found'])}")

    if result['errors']:
        print(f"\n  ⚠️  Errors encountered: {len(result['errors'])}")


def example_4_view_statistics():
    """
    Example 4: View database statistics.

    Check what's in the database without scraping.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Database Statistics")
    print("=" * 60)

    stats = get_afr_article_count()

    print(f"\nDatabase Contents:")
    print(f"  Total AFR articles: {stats['total_articles']}")
    print(f"  Unique tickers covered: {stats['unique_tickers']}")

    if stats['date_range'][0]:
        print(f"  Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")

    if stats['top_tickers']:
        print(f"\n  Most covered tickers:")
        for ticker, count in stats['top_tickers'][:10]:
            print(f"    {ticker}: {count} articles")


def example_5_error_handling():
    """
    Example 5: Proper error handling.

    Shows how to handle errors gracefully.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)

    try:
        result = scrape_afr_news(
            lookback_days=7,
            tickers=['BHP', 'CBA']
        )

        # Check for errors
        if result['errors']:
            print(f"⚠️  Scraping completed with {len(result['errors'])} errors:")
            for error in result['errors']:
                print(f"    - {error}")
        else:
            print("✅ Scraping completed successfully with no errors")

        # Check if we got useful data
        if result['articles_scraped'] == 0:
            print("\n⚠️  Warning: No articles found")
            print("   This could mean:")
            print("   - No recent articles mention these tickers")
            print("   - AFR's HTML structure may have changed")
            print("   - Network/access issues")
        else:
            print(f"\n✅ Found {result['articles_scraped']} articles")

    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        print("   Check logs for details: logs/scrapers_afr_news.log")


def example_6_selective_scraping():
    """
    Example 6: Scrape only top ASX companies.

    Focuses on the most liquid/traded companies.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 6: Top ASX Companies Only")
    print("=" * 60)

    # Top 20 ASX companies by market cap (approximate)
    top_20_asx = [
        'BHP', 'CBA', 'CSL', 'NAB', 'WBC', 'ANZ', 'WES', 'MQG', 'WOW', 'FMG',
        'RIO', 'TLS', 'WDS', 'GMG', 'TCL', 'COL', 'QBE', 'SCG', 'STO', 'AMC'
    ]

    print(f"Scraping top 20 ASX companies...")
    print(f"This will take approximately 60-90 seconds...\n")

    result = scrape_afr_news(
        lookback_days=7,
        tickers=top_20_asx
    )

    print(f"\nResults:")
    print(f"  Articles found: {result['articles_scraped']}")
    print(f"  Companies with coverage: {len(result['tickers_found'])} / {len(top_20_asx)}")

    # Calculate coverage percentage
    coverage = (len(result['tickers_found']) / len(top_20_asx)) * 100
    print(f"  Coverage: {coverage:.1f}%")


def example_7_integration_workflow():
    """
    Example 7: Complete integration workflow.

    Shows how AFR scraper fits into a larger trading system.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 7: Integration Workflow")
    print("=" * 60)

    # Step 1: Scrape news
    print("\nStep 1: Scraping AFR news...")
    news_result = scrape_afr_news(lookback_days=1)
    print(f"  ✓ Found {news_result['articles_scraped']} articles")

    # Step 2: Get statistics
    print("\nStep 2: Analyzing database...")
    stats = get_afr_article_count()
    print(f"  ✓ Database contains {stats['total_articles']} total articles")

    # Step 3: Identify tickers with news
    print("\nStep 3: Identifying tickers with recent news...")
    tickers_with_news = news_result['tickers_found']
    print(f"  ✓ {len(tickers_with_news)} tickers have recent news")

    # Step 4: Next steps (placeholder)
    print("\nStep 4: Next steps in pipeline:")
    print("  → Analyze sentiment of articles")
    print("  → Fetch price data for relevant tickers")
    print("  → Correlate news sentiment with price movements")
    print("  → Generate trading signals")

    print("\n✅ Workflow example complete!")


def run_all_examples():
    """Run all examples in sequence."""
    print("\n" + "=" * 70)
    print(" AFR NEWS SCRAPER - USAGE EXAMPLES")
    print("=" * 70)

    examples = [
        ("Basic Scraping", example_1_basic_scraping),
        ("Specific Tickers", example_2_specific_tickers),
        ("Daily Update", example_3_daily_update),
        ("Database Statistics", example_4_view_statistics),
        ("Error Handling", example_5_error_handling),
        ("Top Companies", example_6_selective_scraping),
        ("Integration Workflow", example_7_integration_workflow),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    print("\nNote: Running all examples will take several minutes due to rate limiting.")
    print("You can also run individual examples by calling their functions directly.\n")

    # Uncomment below to run all examples automatically
    # for name, func in examples:
    #     try:
    #         func()
    #     except Exception as e:
    #         print(f"\n❌ Example '{name}' failed: {e}\n")


if __name__ == '__main__':
    # Run example selector
    run_all_examples()

    # To run a specific example, uncomment one of these:
    # example_1_basic_scraping()
    # example_2_specific_tickers()
    # example_3_daily_update()
    # example_4_view_statistics()
    # example_5_error_handling()
    # example_6_selective_scraping()
    # example_7_integration_workflow()
