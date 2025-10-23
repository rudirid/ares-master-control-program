"""
Configuration settings for ASX Stock Trading Analysis System.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Database configuration
DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'trading.db')

# Logging configuration
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Log format configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'

# User agent for web requests (realistic browser user agent)
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Rate limiting settings (seconds between requests)
ASX_RATE_LIMIT = 2  # Seconds between ASX requests
AFR_RATE_LIMIT = 3  # Seconds between Australian Financial Review requests
HOTCOPPER_RATE_LIMIT = 2  # Seconds between Hot Copper requests

# Date range settings
DEFAULT_LOOKBACK_DAYS = 7  # Default number of days to look back for announcements
STOCK_PRICE_YEARS = 2  # Number of years of historical stock price data to fetch

# ASX200 tickers configuration
# This list will be populated dynamically by scraping the ASX website
# or can be manually updated with the current ASX200 constituents
ASX200_TICKERS = []

# Request timeout settings
REQUEST_TIMEOUT = 30  # Seconds before request timeout

# Retry settings
MAX_RETRIES = 3  # Maximum number of retry attempts for failed requests
RETRY_DELAY = 5  # Seconds to wait between retry attempts
