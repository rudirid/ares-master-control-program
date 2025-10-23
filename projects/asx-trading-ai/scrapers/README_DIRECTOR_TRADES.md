# Director Trades Scraper Documentation

## Overview

The Director Trades Scraper (`director_trades.py`) collects Change of Director's Interest Notices (Appendix 3Y forms) from the Australian Securities Exchange (ASX). These notices are filed whenever a company director buys or sells shares in their own company and are important signals for market analysis.

**File Location:** `C:\Users\riord\Documents\ClaudeWorkshop\StockTradingAI\scrapers\director_trades.py`

## Features

### Core Functionality

1. **Scrapes Appendix 3Y Notices** - Automatically finds and processes director trading notices
2. **Multi-source Support** - Can scrape specific tickers or search across all companies
3. **Intelligent Parsing** - Extracts structured data from unstructured notices
4. **Trade Type Detection** - Automatically determines if a transaction is a buy or sell
5. **Rate Limiting** - Respects ASX servers with configurable delays
6. **Duplicate Prevention** - Uses URL-based deduplication
7. **Robust Error Handling** - Continues processing even if individual notices fail

### Data Extraction

The scraper extracts the following fields from each notice:

- **ticker**: ASX stock code (e.g., BHP, CBA)
- **company_name**: Full company name
- **director_name**: Name of the director
- **trade_type**: 'buy' or 'sell' (automatically determined)
- **shares**: Number of shares traded
- **price**: Price per share (if available)
- **value**: Total transaction value (calculated if shares and price available)
- **trade_date**: Date the transaction occurred
- **notice_date**: Date the notice was filed with ASX
- **url**: Link to the original notice

## Installation Requirements

```bash
pip install requests beautifulsoup4 python-dateutil
```

### Optional Requirements

For full PDF parsing support (currently a placeholder):
```bash
pip install pdfplumber
```

## Usage

### Basic Usage - Standalone Script

Run the scraper as a standalone script to scrape the last 30 days:

```bash
cd C:\Users\riord\Documents\ClaudeWorkshop\StockTradingAI
python scrapers\director_trades.py
```

### Programmatic Usage

```python
from scrapers.director_trades import scrape_director_trades, get_director_trades_summary
from datetime import datetime, timedelta

# Scrape last 7 days
result = scrape_director_trades(
    date_from=datetime.now() - timedelta(days=7),
    date_to=datetime.now()
)

print(f"Scraped {result['trades_scraped']} trades")
print(f"Buys: {result['total_buys']}, Sells: {result['total_sells']}")
print(f"Total value: ${result['total_value']:,.2f}")

# Get database summary
summary = get_director_trades_summary()
print(f"Total trades in database: {summary['total_trades']}")
```

### Scrape Specific Tickers

```python
from scrapers.director_trades import scrape_director_trades

# Scrape director trades for specific companies
result = scrape_director_trades(
    tickers=['BHP', 'CBA', 'WBC', 'NAB'],
    date_from='2023-01-01',
    date_to='2023-12-31'
)
```

### Custom Database Path

```python
from scrapers.director_trades import scrape_director_trades

result = scrape_director_trades(
    db_path='path/to/custom/database.db'
)
```

## API Reference

### Main Functions

#### `scrape_director_trades(date_from, date_to, db_path, tickers)`

Scrape ASX director trading notices for the specified date range.

**Parameters:**
- `date_from` (datetime or str, optional): Start date (default: 30 days ago)
- `date_to` (datetime or str, optional): End date (default: today)
- `db_path` (str, optional): Path to database (default: from config)
- `tickers` (List[str], optional): Specific tickers to scrape (default: search all)

**Returns:**
Dictionary with:
- `trades_scraped`: Number of trades successfully scraped
- `total_buys`: Number of buy transactions
- `total_sells`: Number of sell transactions
- `total_value`: Total value of all trades
- `tickers_processed`: List of tickers processed

**Example:**
```python
result = scrape_director_trades(
    date_from='2023-10-01',
    date_to='2023-10-31',
    tickers=['BHP', 'RIO']
)
```

#### `get_director_trades_summary(db_path)`

Get summary statistics of director trades stored in the database.

**Parameters:**
- `db_path` (str, optional): Path to database (default: from config)

**Returns:**
Dictionary with:
- `total_trades`: Total number of trades
- `total_buys`: Number of buy transactions
- `total_sells`: Number of sell transactions
- `total_value`: Total value of all trades
- `top_directors`: List of top directors by trade value
- `recent_trades`: List of most recent trades

**Example:**
```python
summary = get_director_trades_summary()
for director, ticker, value in summary['top_directors'][:5]:
    print(f"{director} ({ticker}): ${value:,.2f}")
```

### Helper Functions

#### `determine_trade_type(text)`

Determine if a transaction is a buy or sell based on text content.

**Parameters:**
- `text` (str): Text content from notice

**Returns:**
- `'buy'`, `'sell'`, or `None`

**Buy indicators:** acquisition, purchase, on-market purchase, issue, allotment, grant, exercise of options

**Sell indicators:** disposal, sale, on-market sale, transfer

#### `extract_shares_from_text(text)`

Extract number of shares from text using pattern matching.

**Parameters:**
- `text` (str): Text containing share quantity

**Returns:**
- `int` or `None`

#### `extract_price_from_text(text)`

Extract price per share from text.

**Parameters:**
- `text` (str): Text containing price information

**Returns:**
- `float` or `None`

#### `clean_numeric_value(value_string)`

Clean and convert currency/number strings to float.

**Parameters:**
- `value_string` (str): String with numeric value (may contain $, commas, etc.)

**Returns:**
- `float` or `None`

#### `parse_date_flexible(date_string)`

Parse date string in various formats.

**Parameters:**
- `date_string` (str): Date string to parse

**Returns:**
- `datetime` or `None`

**Supported formats:**
- DD/MM/YYYY
- DD-MM-YYYY
- YYYY-MM-DD
- DD Month YYYY
- Month DD, YYYY

## Database Schema

The scraper stores data in the `director_trades` table:

```sql
CREATE TABLE director_trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    company_name TEXT,
    director_name TEXT,
    trade_type TEXT CHECK(trade_type IN ('buy', 'sell')),
    shares INTEGER,
    price REAL,
    value REAL,
    trade_date DATE,
    notice_date DATE,
    url TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Implementation Details

### Scraping Strategy

The scraper uses a two-tier approach:

1. **Company-Specific Scraping** (when tickers provided):
   - Queries ASX API endpoint for each ticker
   - More reliable and faster for specific companies
   - URL: `https://www.asx.com.au/asx/1/company/{ticker}/announcements`

2. **General Search** (when no tickers specified):
   - Searches ASX announcements page
   - Filters for Appendix 3Y notices
   - URL: `https://www.asx.com.au/asx/statistics/announcements.do`

### Parsing Logic

The scraper handles both HTML and PDF announcements:

- **HTML Announcements**: Directly parses with BeautifulSoup
- **PDF Announcements**: Placeholder for future PDF parsing (requires pdfplumber)

### Trade Type Detection

Trade type is determined by keyword matching:

```python
Buy indicators:  acquisition, purchase, issue, grant, allotment
Sell indicators: disposal, sale, transfer, sold
```

The function counts occurrences and returns the type with more matches.

### Rate Limiting

- Default: 2 seconds between requests (configurable via `ASX_RATE_LIMIT`)
- Applied after each announcement fetch
- Respects ASX servers and prevents blocking

### Error Handling

- **Network errors**: Retried with exponential backoff
- **Parsing errors**: Logged and skipped, processing continues
- **Missing data**: Gracefully handled with NULL values
- **Duplicate URLs**: Silently skipped using INSERT OR IGNORE

## Configuration

Configuration is managed through `config.py`:

```python
# Rate limiting (seconds between requests)
ASX_RATE_LIMIT = 2

# Database path
DATABASE_PATH = 'data/trading.db'

# User agent for web requests
USER_AGENT = 'Mozilla/5.0 ...'

# Request timeout
REQUEST_TIMEOUT = 30

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 5
```

## Known Limitations

### 1. PDF Parsing Not Fully Implemented

Currently, PDF notices are logged but not parsed. Most Appendix 3Y forms are PDFs.

**Workaround**: The scraper creates database entries with available metadata (ticker, company, notice date, URL), but detailed trade information may be missing.

**Future Enhancement**: Implement full PDF parsing using pdfplumber:

```python
import pdfplumber
import io

def extract_trade_details_from_pdf(pdf_url: str) -> List[Dict[str, Any]]:
    response = safe_request(pdf_url)
    if response:
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            # Parse text using existing extraction functions
            return parse_trade_details(text)
```

### 2. No Official ASX API

The ASX does not provide an official public JSON API for announcements. The scraper uses:
- Undocumented API endpoints (may change without notice)
- Web scraping (subject to page structure changes)

**Recommendation**: For production use, consider:
- ASX Online Information Services (paid subscription)
- Third-party data providers with official ASX feeds

### 3. Price Information Often Missing

Many director trading notices don't include price information, especially for:
- Off-market transfers
- Share issues/allotments
- Option exercises

The `value` field will be NULL in these cases.

### 4. Date Range Limitations

When searching all notices (no specific tickers), the scraper may only find recent announcements due to ASX website pagination limits.

**Workaround**: Provide specific tickers for historical scraping:

```python
# Get list of ASX200 tickers
tickers = ['BHP', 'CBA', 'WBC', ...]  # Full ASX200 list

# Scrape historical data
result = scrape_director_trades(
    tickers=tickers,
    date_from='2022-01-01',
    date_to='2023-12-31'
)
```

### 5. Multiple Transactions Per Notice

Some notices contain multiple transactions (e.g., buy and sell on same day). Current implementation creates separate records for each transaction.

## Testing

Run the test suite:

```bash
cd C:\Users\riord\Documents\ClaudeWorkshop\StockTradingAI
python test_director_scraper.py
```

The test suite validates:
- Trade type detection
- Numeric value cleaning
- Share quantity extraction
- Price extraction
- Director name extraction
- Date parsing

All tests should pass with output showing:
```
[PASS] Test case => result (expected: expected)
```

## Logging

The scraper uses comprehensive logging:

**Log file location**: `logs/scrapers_director_trades.log`

**Log levels:**
- INFO: Normal operations (scraping progress, records inserted)
- WARNING: Non-critical issues (PDF skipped, parsing failures)
- ERROR: Critical failures (network errors, database errors)
- DEBUG: Detailed debugging information

**Enable debug logging:**

```python
import logging
logging.getLogger('scrapers.director_trades').setLevel(logging.DEBUG)
```

## Performance

### Speed

- Approximately 2-5 seconds per ticker (due to rate limiting)
- 100 tickers takes 3-8 minutes
- Full ASX200 takes 7-15 minutes

### Database Growth

- Approximately 1-3 director trades per ticker per month
- ASX200 companies: ~200-600 trades/month
- Database size: ~10-20 MB per year (including all tables)

## Use Cases

### 1. Insider Trading Analysis

Track director buying/selling patterns:

```python
import sqlite3

conn = sqlite3.connect('data/trading.db')
cursor = conn.cursor()

# Find directors who are buying heavily
cursor.execute("""
    SELECT ticker, director_name, COUNT(*) as num_buys, SUM(shares) as total_shares
    FROM director_trades
    WHERE trade_type = 'buy' AND notice_date > date('now', '-30 days')
    GROUP BY ticker, director_name
    HAVING num_buys >= 2
    ORDER BY total_shares DESC
""")

heavy_buyers = cursor.fetchall()
for ticker, director, num_buys, total_shares in heavy_buyers:
    print(f"{ticker}: {director} bought {total_shares:,} shares in {num_buys} transactions")
```

### 2. Sentiment Indicator

Calculate buy/sell ratios:

```python
# Get recent buy/sell ratio for a stock
cursor.execute("""
    SELECT
        SUM(CASE WHEN trade_type = 'buy' THEN 1 ELSE 0 END) as buys,
        SUM(CASE WHEN trade_type = 'sell' THEN 1 ELSE 0 END) as sells
    FROM director_trades
    WHERE ticker = ? AND notice_date > date('now', '-90 days')
""", ('BHP',))

buys, sells = cursor.fetchone()
ratio = buys / (buys + sells) if (buys + sells) > 0 else 0
print(f"Director sentiment: {ratio:.1%} bullish")
```

### 3. Alert System

Monitor for significant director activity:

```python
# Find large transactions (>$1M)
cursor.execute("""
    SELECT ticker, director_name, trade_type, shares, value, notice_date
    FROM director_trades
    WHERE value > 1000000 AND notice_date > date('now', '-7 days')
    ORDER BY value DESC
""")

large_trades = cursor.fetchall()
for ticker, director, trade_type, shares, value, date in large_trades:
    print(f"ALERT: {ticker} - {director} {trade_type} ${value:,.0f} on {date}")
```

### 4. Integration with Price Data

Correlate director trades with stock performance:

```python
# Get director trades and subsequent price movement
cursor.execute("""
    SELECT
        dt.ticker,
        dt.trade_type,
        dt.notice_date,
        dt.value,
        sp1.close as price_at_notice,
        sp2.close as price_30d_later,
        ((sp2.close - sp1.close) / sp1.close) * 100 as return_pct
    FROM director_trades dt
    LEFT JOIN stock_prices sp1 ON dt.ticker = sp1.ticker
        AND dt.notice_date = sp1.date
    LEFT JOIN stock_prices sp2 ON dt.ticker = sp2.ticker
        AND date(dt.notice_date, '+30 days') = sp2.date
    WHERE dt.value > 100000
    ORDER BY dt.notice_date DESC
""")
```

## Troubleshooting

### Problem: No trades scraped

**Possible causes:**
1. ASX website structure changed
2. Network connectivity issues
3. Rate limiting/blocking by ASX

**Solutions:**
- Check logs for error messages
- Test with a single recent ticker: `scrape_director_trades(tickers=['BHP'])`
- Verify ASX website is accessible: visit https://www.asx.com.au in browser

### Problem: Many trades have NULL values

**Possible causes:**
1. PDF parsing not implemented (expected)
2. Announcement format doesn't match parsing patterns
3. Information not disclosed in notice

**Solutions:**
- Check individual notice URLs to see what data is available
- Many notices legitimately lack price information
- Consider implementing PDF parsing for better extraction

### Problem: Duplicate key errors

**Possible causes:**
1. URL uniqueness constraint violated
2. Running scraper multiple times on same data

**Solutions:**
- The scraper uses INSERT OR IGNORE, so duplicates should be silently skipped
- If seeing errors, check database schema: `url TEXT UNIQUE`

### Problem: Scraper is slow

**Possible causes:**
1. Rate limiting (intentional, 2 seconds per request)
2. Network latency
3. Large date range

**Solutions:**
- Rate limiting is necessary to respect ASX servers (don't reduce)
- Scrape specific tickers instead of searching all
- Break large date ranges into smaller chunks

## Future Enhancements

### Priority Enhancements

1. **PDF Parsing**
   - Implement pdfplumber integration
   - Extract data from Appendix 3Y PDF forms
   - Handle various PDF formats and layouts

2. **Better API Integration**
   - Reverse engineer more ASX API endpoints
   - Implement proper pagination handling
   - Add support for bulk queries

3. **Enhanced Data Extraction**
   - Extract more granular trade types (on-market, off-market, options, etc.)
   - Parse transaction reasons (if disclosed)
   - Extract holdings before/after trade

### Secondary Enhancements

4. **Notification System**
   - Email/SMS alerts for large trades
   - Webhooks for real-time integration
   - Customizable alert rules

5. **Data Quality**
   - Validate extracted data against rules
   - Flag suspicious or unusual patterns
   - Confidence scores for extractions

6. **Performance**
   - Async scraping with concurrent requests
   - Caching layer for frequently accessed data
   - Database indexing optimization

## Legal and Ethical Considerations

### Terms of Service

- ASX announcements are publicly available information
- Director trading notices are regulatory filings (public records)
- Respect ASX's robots.txt and rate limits

### Best Practices

1. **Rate Limiting**: Always maintain 2+ second delays between requests
2. **User Agent**: Use descriptive User-Agent string identifying your application
3. **Error Handling**: Don't hammer servers on errors; implement exponential backoff
4. **Caching**: Cache responses to minimize redundant requests
5. **Attribution**: Keep original notice URLs for proper attribution

### Data Usage

- Director trading data is public information
- Can be used for investment research and analysis
- Cannot be used to manipulate markets or engage in illegal trading
- Consult with legal counsel for commercial applications

## Support and Contribution

For issues, questions, or contributions:

1. Check logs for error messages
2. Test with a small dataset first
3. Review this documentation
4. Submit issues with detailed error logs and reproduction steps

## Changelog

### Version 1.0 (2025-10-09)
- Initial implementation
- Support for HTML announcement parsing
- Trade type detection
- Numeric value extraction
- Database storage with deduplication
- Comprehensive logging
- Test suite
- Documentation

## License

This scraper is part of the StockTradingAI project. Use responsibly and in compliance with ASX terms of service.

---

**Last Updated**: October 9, 2025
**Author**: Claude (Web Scraping Expert)
**Tested On**: Python 3.8+, Windows 11
