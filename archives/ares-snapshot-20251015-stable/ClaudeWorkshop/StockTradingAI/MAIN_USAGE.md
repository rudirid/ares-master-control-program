# Main Coordinator Script - Usage Guide

## Overview

The `main.py` script is the central coordinator for the ASX Stock Trading AI data collection system. It orchestrates all scrapers with comprehensive CLI arguments, detailed logging, and robust error handling.

## Features

- **Multi-Scraper Orchestration**: Run individual scrapers or all at once
- **Comprehensive Logging**: File and console logging with color-coded output
- **CLI Arguments**: Flexible command-line interface for customization
- **Error Handling**: Graceful error handling with detailed reporting
- **Database Statistics**: Automatic database size and record count reporting
- **Dry-Run Mode**: Preview what would be scraped without collecting data
- **Progress Tracking**: Real-time execution status and timing
- **Production-Ready**: Exit codes for automation and scheduling

## Installation

1. **Install Dependencies**:
   ```bash
   cd C:\Users\riord\Documents\ClaudeWorkshop\StockTradingAI
   pip install -r requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   python main.py --init-db
   ```

## Command Line Arguments

### Scraper Selection

| Argument | Description |
|----------|-------------|
| `--all` | Run all scrapers |
| `--stock-prices` | Run stock prices scraper (yfinance) |
| `--announcements` | Run ASX announcements scraper |
| `--news` | Run AFR news scraper |
| `--director-trades` | Run director trades scraper |
| `--sentiment` | Run HotCopper sentiment scraper |

### Configuration

| Argument | Default | Description |
|----------|---------|-------------|
| `--days DAYS` | 7 | Number of days to look back |
| `--tickers TICKERS` | ASX200 | Comma-separated list of tickers |
| `--log-level LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `--log-file FILE` | Auto-generated | Custom log file path |

### Special Options

| Argument | Description |
|----------|-------------|
| `--init-db` | Initialize database (create tables) |
| `--dry-run` | Preview what would be scraped (no actual data collection) |
| `-h, --help` | Show help message |

## Usage Examples

### Basic Usage

1. **Run All Scrapers** (default 7 days):
   ```bash
   python main.py --all
   ```

2. **Run Specific Scraper**:
   ```bash
   python main.py --stock-prices
   ```

3. **Run Multiple Scrapers**:
   ```bash
   python main.py --stock-prices --announcements --news
   ```

### Custom Date Ranges

1. **30 Days of Historical Data**:
   ```bash
   python main.py --all --days 30
   ```

2. **90 Days for Specific Tickers**:
   ```bash
   python main.py --stock-prices --days 90 --tickers BHP,CBA,CSL
   ```

### Specific Tickers

1. **Big 4 Banks Only**:
   ```bash
   python main.py --all --tickers CBA,NAB,WBC,ANZ
   ```

2. **Mining Sector**:
   ```bash
   python main.py --stock-prices --tickers BHP,RIO,FMG,MIN
   ```

### Debugging and Testing

1. **Debug Mode** (verbose logging):
   ```bash
   python main.py --all --log-level DEBUG
   ```

2. **Dry Run** (preview without scraping):
   ```bash
   python main.py --all --days 30 --dry-run
   ```

3. **Custom Log File**:
   ```bash
   python main.py --stock-prices --log-file my_custom_log.log
   ```

### Database Management

1. **Initialize Database**:
   ```bash
   python main.py --init-db
   ```

2. **Initialize and Run Scrapers**:
   ```bash
   python main.py --init-db --all
   ```

## Output and Logging

### Console Output

The script provides color-coded console output:
- **Green**: Success messages and INFO logs
- **Yellow**: Warnings and dry-run mode
- **Red**: Errors and failures
- **Blue**: Debug messages (when log-level is DEBUG)

### Log Files

Log files are automatically created in the `logs/` directory with timestamps:
```
logs/trading_scraper_2025-10-09_16-42-54.log
```

Each log file contains:
- Detailed execution steps
- Error tracebacks
- Timing information
- Database operations
- Individual scraper results

### Summary Report

After execution, a comprehensive summary is displayed:

```
======================================================================
EXECUTION SUMMARY
======================================================================

Overall Statistics:
  Total Scrapers Run: 3
  Successful: 3
  Failed: 0
  Total Records Collected: 1,234
  Total Execution Time: 45.32 seconds

Scraper Results:
  ✓ Stock Prices Scraper
      Records: 500
      Duration: 15.23s
  ✓ ASX Announcements Scraper
      Records: 634
      Duration: 20.45s
  ✓ AFR News Scraper
      Records: 100
      Duration: 9.64s

Database Statistics:
  Location: C:\...\StockTradingAI\data\trading.db
  Size: 5.67 MB (5,947,392 bytes)
  Total Records: 1,234

  Records per table:
    - stock_prices: 500
    - asx_announcements: 634
    - news_articles: 100
    - director_trades: 0
    - hotcopper_sentiment: 0

Log File:
  C:\...\StockTradingAI\logs\trading_scraper_2025-10-09_16-42-54.log

======================================================================
```

## Exit Codes

The script returns standard exit codes for automation:

| Exit Code | Meaning |
|-----------|---------|
| 0 | All scrapers successful |
| 1 | Some scrapers failed |
| 2 | All scrapers failed |
| 130 | Interrupted by user (Ctrl+C) |

Use exit codes in shell scripts:
```bash
python main.py --all
if [ $? -eq 0 ]; then
    echo "Success!"
else
    echo "Some scrapers failed"
fi
```

## Scheduling for Daily Execution

### Windows Task Scheduler

1. **Open Task Scheduler**:
   - Press `Win + R`, type `taskschd.msc`, press Enter

2. **Create Basic Task**:
   - Click "Create Basic Task" in the right panel
   - Name: "ASX Stock Data Collection"
   - Description: "Daily ASX stock market data scraping"

3. **Set Trigger**:
   - Choose "Daily"
   - Set time: 18:30 (6:30 PM - after market close at 4:00 PM AEDT)
   - Recur every: 1 days

4. **Set Action**:
   - Action: "Start a program"
   - Program/script: `python.exe`
   - Add arguments: `C:\Users\riord\Documents\ClaudeWorkshop\StockTradingAI\main.py --all`
   - Start in: `C:\Users\riord\Documents\ClaudeWorkshop\StockTradingAI`

5. **Advanced Settings**:
   - Check "Run whether user is logged on or not"
   - Check "Run with highest privileges"
   - Configure for: Windows 10

6. **Optional - Email Notifications**:
   - Use PowerShell script to send email on failure
   - Check exit code and send email if non-zero

### Linux/Mac Cron

1. **Edit Crontab**:
   ```bash
   crontab -e
   ```

2. **Add Daily Job** (6:30 PM daily):
   ```bash
   30 18 * * * cd /path/to/StockTradingAI && python main.py --all >> /path/to/logs/cron.log 2>&1
   ```

3. **Alternative - Run at Market Close** (4:05 PM AEDT):
   ```bash
   5 16 * * 1-5 cd /path/to/StockTradingAI && python main.py --all
   ```
   (Monday-Friday only)

4. **With Error Handling**:
   ```bash
   30 18 * * * cd /path/to/StockTradingAI && python main.py --all || echo "Scraping failed" | mail -s "Stock Scraper Error" your@email.com
   ```

### Best Practices for Scheduling

1. **Timing**:
   - Run after ASX market close (4:00 PM AEDT)
   - Allow time for data to be published (suggest 6:00-7:00 PM)
   - Avoid weekends (market closed) - use `1-5` in cron

2. **Error Notifications**:
   - Configure email alerts for failures
   - Monitor log files regularly
   - Set up disk space monitoring

3. **Resource Management**:
   - Ensure adequate disk space for database growth
   - Rotate log files periodically
   - Monitor CPU/memory usage during execution

4. **Data Validation**:
   - Check database after each run
   - Validate record counts
   - Monitor for data gaps or anomalies

## Advanced Usage

### Custom Scraper Configuration

Edit `config.py` to customize:
```python
# Rate limiting (seconds between requests)
ASX_RATE_LIMIT = 2
AFR_RATE_LIMIT = 3
HOTCOPPER_RATE_LIMIT = 2

# Date ranges
DEFAULT_LOOKBACK_DAYS = 7
STOCK_PRICE_YEARS = 2

# Request settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 5
```

### Error Recovery

If a scraper fails:
1. Check the log file for detailed error messages
2. Verify internet connection
3. Check if the target website is accessible
4. Re-run with `--log-level DEBUG` for more details
5. Re-run only the failed scraper

Example:
```bash
# First attempt - some scrapers fail
python main.py --all

# Re-run only failed scraper with debug logging
python main.py --announcements --log-level DEBUG
```

### Database Maintenance

1. **Check Database Size**:
   ```bash
   python main.py --stock-prices --tickers BHP  # Quick test
   # Check database statistics in output
   ```

2. **Backup Database**:
   ```bash
   # Windows
   copy data\trading.db data\trading_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db

   # Linux/Mac
   cp data/trading.db data/trading_backup_$(date +%Y%m%d).db
   ```

3. **Compact Database**:
   ```python
   import sqlite3
   conn = sqlite3.connect('data/trading.db')
   conn.execute('VACUUM')
   conn.close()
   ```

## Troubleshooting

### Common Issues

1. **Module Not Found Error**:
   ```
   ModuleNotFoundError: No module named 'yfinance'
   ```
   **Solution**: Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Locked Error**:
   ```
   sqlite3.OperationalError: database is locked
   ```
   **Solution**: Close any programs accessing the database
   - Close DB Browser for SQLite
   - Kill any running scraper processes

3. **Unicode Encoding Error** (Windows):
   ```
   UnicodeEncodeError: 'charmap' codec can't encode character
   ```
   **Solution**: Already handled in main.py. If persists, set environment variable:
   ```bash
   set PYTHONIOENCODING=utf-8
   python main.py --all
   ```

4. **Timeout Error**:
   ```
   requests.exceptions.Timeout: Request timeout
   ```
   **Solution**: Increase timeout in config.py or check internet connection

5. **No Data Returned**:
   - Verify ticker symbols are correct (use ASX codes without .AX suffix)
   - Check date range is valid
   - Ensure market was open during requested period

## Integration with Analysis Tools

### Jupyter Notebooks

```python
import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect('data/trading.db')

# Load stock prices
df = pd.read_sql_query("SELECT * FROM stock_prices WHERE ticker='BHP'", conn)

# Analysis
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)
df['close'].plot(figsize=(12, 6), title='BHP Stock Price')
```

### Python Scripts

```python
from scrapers.stock_prices import get_price_statistics
import config

# Get database statistics
stats = get_price_statistics(config.DATABASE_PATH)
print(f"Total records: {stats['total_records']}")
print(f"Date range: {stats['date_range']}")
```

## Performance Considerations

### Execution Time Estimates

| Scrapers | Tickers | Timeframe | Estimated Duration |
|----------|---------|-----------|-------------------|
| Stock Prices | 10 | 7 days | 5-10 seconds |
| Stock Prices | 200 (ASX200) | 7 days | 2-3 minutes |
| All Scrapers | 200 | 7 days | 15-30 minutes |
| All Scrapers | 200 | 30 days | 45-90 minutes |

### Optimization Tips

1. **Parallel Execution**: Future enhancement - run independent scrapers in parallel
2. **Rate Limiting**: Respect website rate limits to avoid being blocked
3. **Batch Size**: Adjust batch size in scrapers for optimal performance
4. **Database Indexing**: Indexes already created for common queries
5. **Selective Scraping**: Only run scrapers you need for your analysis

## Contributing

### Adding New Scrapers

1. Create scraper module in `scrapers/` directory
2. Implement scraper function with standard signature:
   ```python
   def scrape_new_data(tickers: List[str], days: int, db_path: str) -> Dict[str, Any]:
       # Implementation
       return {
           'total_records': count,
           'successful_tickers': [...],
           'failed_tickers': [...]
       }
   ```

3. Import in main.py:
   ```python
   from scrapers.new_scraper import scrape_new_data
   ```

4. Add CLI argument and execution logic in main.py

### Testing New Features

1. Always test with `--dry-run` first
2. Test with small ticker list: `--tickers BHP,CBA`
3. Test with short timeframe: `--days 7`
4. Check log files for errors
5. Validate database records after execution

## Support and Documentation

- **Main Documentation**: README.md
- **Scraper Setup**: SCRAPER_SETUP.md
- **Database Schema**: database/init_db.py
- **Configuration**: config.py
- **Log Files**: logs/ directory

## Version History

- **v1.0.0** (2025-10-09): Initial release
  - Multi-scraper orchestration
  - CLI argument parsing
  - Comprehensive logging
  - Database statistics
  - Dry-run mode
  - Scheduling documentation

## License

Copyright 2025 - ASX Stock Trading AI System
For educational and personal use only.
