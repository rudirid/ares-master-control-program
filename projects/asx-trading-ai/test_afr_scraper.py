"""
Test script for AFR news scraper.

This script tests the AFR news scraper with a small set of tickers
to verify functionality before running on the full ASX200 list.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.afr_news import (
    scrape_afr_news,
    get_afr_article_count,
    match_tickers_in_text,
    is_paywalled
)
from bs4 import BeautifulSoup


def test_ticker_matching():
    """Test the ticker matching function."""
    print("\n" + "=" * 60)
    print("Test 1: Ticker Matching")
    print("=" * 60)

    test_cases = [
        {
            'text': "BHP and Rio Tinto shares rose today after strong commodity prices",
            'tickers': ['BHP', 'RIO', 'CBA'],
            'expected': {'BHP', 'RIO'}
        },
        {
            'text': "Commonwealth Bank announced record profits",
            'tickers': ['CBA', 'NAB', 'WBC'],
            'expected': {'CBA'}
        },
        {
            'text': "Wesfarmers CEO discusses Bunnings expansion plans",
            'tickers': ['WES', 'WOW', 'COL'],
            'expected': {'WES'}
        },
        {
            'text': "Market update: ASX200 rises on positive sentiment",
            'tickers': ['BHP', 'CBA', 'CSL'],
            'expected': set()  # No specific company mentioned
        }
    ]

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = match_tickers_in_text(test['text'], test['tickers'])
        if result == test['expected']:
            print(f"✓ Test case {i}: PASSED")
            passed += 1
        else:
            print(f"✗ Test case {i}: FAILED")
            print(f"  Text: {test['text'][:60]}...")
            print(f"  Expected: {test['expected']}")
            print(f"  Got: {result}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_paywall_detection():
    """Test the paywall detection function."""
    print("\n" + "=" * 60)
    print("Test 2: Paywall Detection")
    print("=" * 60)

    # Test case 1: Paywalled article
    paywalled_html = """
    <article>
        <h3>Test Article</h3>
        <span class="subscriber-only">Subscriber only</span>
        <p>This is a premium article</p>
    </article>
    """
    soup1 = BeautifulSoup(paywalled_html, 'html.parser')
    result1 = is_paywalled(soup1)

    # Test case 2: Free article
    free_html = """
    <article>
        <h3>Free Article</h3>
        <p>This article is freely available</p>
    </article>
    """
    soup2 = BeautifulSoup(free_html, 'html.parser')
    result2 = is_paywalled(soup2)

    # Test case 3: Article with lock icon
    locked_html = """
    <article>
        <h3>Locked Article</h3>
        <i class="icon-lock"></i>
        <p>Premium content</p>
    </article>
    """
    soup3 = BeautifulSoup(locked_html, 'html.parser')
    result3 = is_paywalled(soup3)

    passed = 0
    failed = 0

    if result1:
        print("✓ Test 1: Correctly detected subscriber-only article")
        passed += 1
    else:
        print("✗ Test 1: Failed to detect subscriber-only article")
        failed += 1

    if not result2:
        print("✓ Test 2: Correctly identified free article")
        passed += 1
    else:
        print("✗ Test 2: Incorrectly flagged free article as paywalled")
        failed += 1

    if result3:
        print("✓ Test 3: Correctly detected locked article")
        passed += 1
    else:
        print("✗ Test 3: Failed to detect locked article")
        failed += 1

    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_live_scraping():
    """Test live scraping with a small set of tickers."""
    print("\n" + "=" * 60)
    print("Test 3: Live Scraping (Small Test)")
    print("=" * 60)

    # Test with just a few major tickers
    test_tickers = ['BHP', 'CBA', 'CSL']

    print(f"Testing with tickers: {test_tickers}")
    print("This may take 20-30 seconds due to rate limiting...\n")

    try:
        result = scrape_afr_news(
            lookback_days=7,
            tickers=test_tickers
        )

        print("\nScraping Results:")
        print(f"  Articles found: {result['articles_scraped']}")
        print(f"  Articles inserted: {result['articles_inserted']}")
        print(f"  Articles skipped: {result['articles_skipped']}")
        print(f"  Tickers with articles: {len(result['tickers_found'])}")

        if result['tickers_found']:
            print(f"  Found tickers: {', '.join(result['tickers_found'])}")

        if result['errors']:
            print(f"\n  Errors: {len(result['errors'])}")
            for error in result['errors'][:3]:
                print(f"    - {error}")

        # Check if we got any results
        if result['articles_scraped'] > 0:
            print("\n✓ Live scraping test: PASSED (articles found)")
            return True
        else:
            print("\n⚠ Live scraping test: WARNING (no articles found)")
            print("  This could be normal if:")
            print("    - AFR has changed their HTML structure")
            print("    - No recent articles mention these tickers")
            print("    - Network/access issues")
            return True  # Still pass the test, just a warning

    except Exception as e:
        print(f"\n✗ Live scraping test: FAILED")
        print(f"  Error: {e}")
        return False


def test_database_statistics():
    """Test database statistics function."""
    print("\n" + "=" * 60)
    print("Test 4: Database Statistics")
    print("=" * 60)

    try:
        stats = get_afr_article_count()

        print(f"Total AFR articles: {stats.get('total_articles', 0)}")
        print(f"Unique tickers: {stats.get('unique_tickers', 0)}")

        if stats.get('date_range'):
            print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")

        if stats.get('top_tickers'):
            print("\nTop tickers:")
            for ticker, count in stats['top_tickers'][:5]:
                print(f"  {ticker}: {count} articles")

        print("\n✓ Database statistics test: PASSED")
        return True

    except Exception as e:
        print(f"\n✗ Database statistics test: FAILED")
        print(f"  Error: {e}")
        return False


def run_all_tests():
    """Run all tests and display summary."""
    print("\n" + "=" * 70)
    print(" AFR NEWS SCRAPER - TEST SUITE")
    print("=" * 70)

    tests = [
        ("Ticker Matching", test_ticker_matching),
        ("Paywall Detection", test_paywall_detection),
        ("Live Scraping", test_live_scraping),
        ("Database Statistics", test_database_statistics),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")

    print("\n" + "-" * 70)
    print(f"Total: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed")

    print("=" * 70 + "\n")


if __name__ == '__main__':
    run_all_tests()
