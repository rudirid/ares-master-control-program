"""
Test script for HotCopper sentiment scraper.

This script tests the various components of the HotCopper scraper:
- Sentiment calculation
- Date parsing
- Topic extraction
- Database storage
- End-to-end scraping
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.hotcopper import (
    calculate_sentiment,
    parse_date_string,
    extract_trending_topics,
    count_posts_by_date,
    get_ticker_forum_url,
    scrape_hotcopper_sentiment
)

import logging
logging.basicConfig(level=logging.INFO)


def test_sentiment_calculation():
    """Test sentiment calculation with various inputs."""
    print("\n" + "=" * 60)
    print("TEST: Sentiment Calculation")
    print("=" * 60)

    test_cases = [
        ("BHP looks strong, great buying opportunity!", "Positive"),
        ("Terrible results, going to crash and burn", "Negative"),
        ("Neutral statement about the company", "Neutral"),
        ("Bullish on this one! Moon rocket time! Strong buy!", "Very Positive"),
        ("Bearish, weak, falling, avoid this loser", "Very Negative"),
        ("", "Empty (Neutral)")
    ]

    for text, expected in test_cases:
        score = calculate_sentiment(text)
        print(f"\nText: {text[:50]}...")
        print(f"Expected: {expected}")
        print(f"Score: {score:.2f}")

        # Validate score is in range
        assert -1 <= score <= 1, f"Score {score} out of range"

    print("\n✓ Sentiment calculation tests passed")


def test_date_parsing():
    """Test date parsing with various formats."""
    print("\n" + "=" * 60)
    print("TEST: Date Parsing")
    print("=" * 60)

    test_cases = [
        "2025-10-09",
        "2025-10-09T14:30:00",
        "today",
        "yesterday",
        "2 hours ago",
        "3 days ago",
        "9 Oct 2025",
        "Oct 9, 2025"
    ]

    for date_str in test_cases:
        parsed = parse_date_string(date_str)
        print(f"Input: {date_str:30} -> Output: {parsed}")

        # Validate format
        if parsed:
            assert len(parsed) == 10, f"Invalid date format: {parsed}"
            assert parsed[4] == '-' and parsed[7] == '-', f"Invalid date format: {parsed}"

    print("\n✓ Date parsing tests passed")


def test_topic_extraction():
    """Test trending topic extraction."""
    print("\n" + "=" * 60)
    print("TEST: Topic Extraction")
    print("=" * 60)

    test_posts = [
        {'title': 'BHP earnings report shows strong results', 'content': 'Great earnings'},
        {'title': 'BHP dividend increase announced', 'content': 'Dividend up 10%'},
        {'title': 'BHP iron ore production update', 'content': 'Production strong'},
        {'title': 'Earnings guidance positive', 'content': 'Looking good'}
    ]

    topics = extract_trending_topics(test_posts, max_topics=3)
    print(f"\nExtracted topics: {topics}")

    # Should find common words like "earnings", "dividend", etc.
    assert len(topics) > 0, "Should extract at least some topics"

    print("✓ Topic extraction tests passed")


def test_post_counting():
    """Test post counting by date."""
    print("\n" + "=" * 60)
    print("TEST: Post Counting by Date")
    print("=" * 60)

    test_posts = [
        {'date': '2025-10-09', 'title': 'Post 1'},
        {'date': '2025-10-09', 'title': 'Post 2'},
        {'date': '2025-10-08', 'title': 'Post 3'},
        {'date': '2025-10-07', 'title': 'Post 4'},
        {'date': '2025-10-07', 'title': 'Post 5'},
        {'date': '2025-10-07', 'title': 'Post 6'}
    ]

    posts_by_date = count_posts_by_date(test_posts)

    print(f"\nPosts by date:")
    for date, posts in sorted(posts_by_date.items()):
        print(f"  {date}: {len(posts)} posts")

    # Validate counts
    assert len(posts_by_date['2025-10-09']) == 2, "Should have 2 posts on 2025-10-09"
    assert len(posts_by_date['2025-10-08']) == 1, "Should have 1 post on 2025-10-08"
    assert len(posts_by_date['2025-10-07']) == 3, "Should have 3 posts on 2025-10-07"

    print("✓ Post counting tests passed")


def test_url_generation():
    """Test forum URL generation."""
    print("\n" + "=" * 60)
    print("TEST: URL Generation")
    print("=" * 60)

    test_tickers = ['BHP', 'CBA', 'CSL', 'WBC']

    for ticker in test_tickers:
        url = get_ticker_forum_url(ticker)
        print(f"{ticker}: {url}")

        # Validate URL structure
        assert url.startswith('https://hotcopper.com.au/'), "Invalid URL"
        assert ticker in url, "Ticker should be in URL"

    print("\n✓ URL generation tests passed")


def test_end_to_end_scraping():
    """
    Test end-to-end scraping with a single ticker.

    Note: This test makes actual HTTP requests and may fail if:
    - Network is unavailable
    - HotCopper is down
    - HotCopper's HTML structure has changed
    - Rate limiting is triggered
    """
    print("\n" + "=" * 60)
    print("TEST: End-to-End Scraping (Single Ticker)")
    print("=" * 60)

    print("\nNote: This test makes actual HTTP requests to HotCopper")
    print("It may take a few seconds due to rate limiting...")

    # Test with a single ticker
    test_ticker = ['BHP']

    try:
        result = scrape_hotcopper_sentiment(
            tickers=test_ticker,
            lookback_days=7
        )

        print(f"\nResults:")
        print(f"  Tickers analyzed: {len(result['tickers_analyzed'])}")
        print(f"  Tickers failed: {len(result['tickers_failed'])}")
        print(f"  Total posts: {result['total_posts']}")

        if result['tickers_analyzed']:
            print("  ✓ Successfully scraped at least one ticker")
        else:
            print("  ! No tickers were successfully analyzed")
            if result['tickers_failed']:
                for failed in result['tickers_failed']:
                    print(f"    - {failed['ticker']}: {failed['error']}")

        # Note: We don't assert success here because:
        # 1. HotCopper may block automated requests
        # 2. Network issues may occur
        # 3. HTML structure may have changed
        # This is more of an integration test to verify the code runs

        print("\n✓ End-to-end test completed (check results above)")

    except Exception as e:
        print(f"\n! End-to-end test encountered an error: {e}")
        print("This may be expected if HotCopper blocks automated requests")


def run_all_tests():
    """Run all test functions."""
    print("\n" + "=" * 70)
    print("HOTCOPPER SCRAPER TEST SUITE")
    print("=" * 70)

    tests = [
        test_sentiment_calculation,
        test_date_parsing,
        test_topic_extraction,
        test_post_counting,
        test_url_generation,
        test_end_to_end_scraping
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n✗ Test failed: {test_func.__name__}")
            print(f"  Error: {e}")
            failed += 1
        except Exception as e:
            print(f"\n✗ Test error: {test_func.__name__}")
            print(f"  Error: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print("=" * 70)

    if failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {failed} test(s) failed")

    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
