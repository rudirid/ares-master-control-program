"""
Test script for director trades scraper functions.
"""

from scrapers.director_trades import (
    determine_trade_type,
    clean_numeric_value,
    extract_shares_from_text,
    extract_price_from_text,
    extract_director_name_from_text,
    parse_date_flexible
)

def test_all_functions():
    """Test all extraction functions."""
    print("=" * 60)
    print("Testing Director Trades Scraper Functions")
    print("=" * 60)

    # Test trade type detection
    print("\n1. Testing trade_type detection:")
    print("-" * 60)
    test_cases = [
        ("The director acquired 10,000 shares", "buy"),
        ("On-market purchase of 5,000 ordinary shares", "buy"),
        ("The director disposed of 3,000 shares", "sell"),
        ("On-market sale of securities", "sell"),
        ("Issue of 1,000 shares to director", "buy"),
    ]

    for text, expected in test_cases:
        result = determine_trade_type(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] '{text[:40]}...' => {result} (expected: {expected})")

    # Test numeric value cleaning
    print("\n2. Testing clean_numeric_value:")
    print("-" * 60)
    test_cases = [
        ("$1,234.56", 1234.56),
        ("1234", 1234.0),
        ("$50,000", 50000.0),
        ("(100)", -100.0),
    ]

    for text, expected in test_cases:
        result = clean_numeric_value(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] '{text}' => {result} (expected: {expected})")

    # Test shares extraction
    print("\n3. Testing extract_shares_from_text:")
    print("-" * 60)
    test_cases = [
        ("10,000 ordinary shares", 10000),
        ("5000 shares", 5000),
        ("Number: 25,000", 25000),
        ("Quantity of 1,500 securities", 1500),
    ]

    for text, expected in test_cases:
        result = extract_shares_from_text(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] '{text}' => {result} (expected: {expected})")

    # Test price extraction
    print("\n4. Testing extract_price_from_text:")
    print("-" * 60)
    test_cases = [
        ("at $1.50 per share", 1.50),
        ("price: $10.25 per share", 10.25),
        ("consideration $2.50", 2.50),
        ("acquired at $3.00 per share", 3.00),
    ]

    for text, expected in test_cases:
        result = extract_price_from_text(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] '{text}' => {result} (expected: {expected})")

    # Test director name extraction
    print("\n5. Testing extract_director_name_from_text:")
    print("-" * 60)
    test_cases = [
        ("Name of Director: John Smith", "John Smith"),
        ("Director: Jane Doe", "Jane Doe"),
    ]

    for text, expected in test_cases:
        result = extract_director_name_from_text(text)
        status = "PASS" if result == expected else "FAIL"
        print(f"  [{status}] '{text}' => {result} (expected: {expected})")

    # Test date parsing
    print("\n6. Testing parse_date_flexible:")
    print("-" * 60)
    test_cases = [
        "01/12/2023",
        "2023-12-01",
        "1 December 2023",
        "Dec 1, 2023",
    ]

    for date_str in test_cases:
        result = parse_date_flexible(date_str)
        status = "PASS" if result is not None else "FAIL"
        print(f"  [{status}] '{date_str}' => {result}")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_all_functions()
