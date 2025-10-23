"""
Quick test script to verify the stock prices scraper is working.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapers.stock_prices import download_stock_prices, get_price_statistics

def test_scraper():
    """Test the scraper with a single ticker."""
    print("Testing stock prices scraper...")
    print("-" * 60)
    
    # Test with just one ticker
    test_ticker = ['BHP']
    
    print(f"Downloading data for: {test_ticker}")
    result = download_stock_prices(test_ticker)
    
    print("\nResults:")
    print(f"  Successful: {result['successful_tickers']}")
    print(f"  Failed: {result['failed_tickers']}")
    print(f"  Total rows: {result['total_rows_inserted']}")
    print(f"  Date range: {result['date_range']}")
    
    # Show stats
    print("\nDatabase Statistics:")
    stats = get_price_statistics()
    print(f"  Total records: {stats['total_records']}")
    print(f"  Unique tickers: {stats['unique_tickers']}")
    
    print("\n" + "-" * 60)
    print("Test complete!")

if __name__ == '__main__':
    test_scraper()
