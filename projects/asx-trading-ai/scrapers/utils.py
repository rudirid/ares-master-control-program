"""
Common utility functions for web scraping and data collection.
"""

import logging
import time
import requests
from typing import Optional, Dict, Any
import config


def get_logger(name: str) -> logging.Logger:
    """
    Create and configure a logger with the specified name.
    
    Args:
        name: Name of the logger (typically __name__ of the calling module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(getattr(logging, config.LOG_LEVEL))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        import os
        log_file = os.path.join(config.LOG_DIR, f'{name.replace(".", "_")}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            config.LOG_FORMAT,
            datefmt=config.LOG_DATE_FORMAT
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def rate_limit_wait(seconds: float) -> None:
    """
    Sleep for the specified number of seconds to respect rate limits.
    
    Args:
        seconds: Number of seconds to wait
    """
    if seconds > 0:
        time.sleep(seconds)


def safe_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = None,
    max_retries: int = None,
    retry_delay: int = None
) -> Optional[requests.Response]:
    """
    Make an HTTP GET request with error handling and retry logic.
    
    Args:
        url: URL to request
        headers: Optional HTTP headers
        timeout: Request timeout in seconds (default: config.REQUEST_TIMEOUT)
        max_retries: Maximum number of retry attempts (default: config.MAX_RETRIES)
        retry_delay: Seconds to wait between retries (default: config.RETRY_DELAY)
        
    Returns:
        Response object if successful, None if all retries failed
    """
    logger = get_logger(__name__)
    
    # Use config defaults if not specified
    timeout = timeout or config.REQUEST_TIMEOUT
    max_retries = max_retries or config.MAX_RETRIES
    retry_delay = retry_delay or config.RETRY_DELAY
    
    # Set default headers if none provided
    if headers is None:
        headers = {'User-Agent': config.USER_AGENT}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()  # Raise exception for bad status codes
            return response
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            status_code_display = status_code if status_code else 'N/A'
            logger.warning(
                f"HTTP error {status_code_display} on attempt {attempt + 1}/{max_retries} for {url}: {e}"
            )

            # Don't retry on client errors (4xx)
            if status_code and 400 <= status_code < 500:
                logger.error(f"Client error {status_code}, not retrying: {url}")
                return None
                
        except requests.exceptions.ConnectionError as e:
            logger.warning(
                f"Connection error on attempt {attempt + 1}/{max_retries} for {url}: {e}"
            )
            
        except requests.exceptions.Timeout as e:
            logger.warning(
                f"Timeout on attempt {attempt + 1}/{max_retries} for {url}: {e}"
            )
            
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Request error on attempt {attempt + 1}/{max_retries} for {url}: {e}"
            )
        
        # Wait before retrying (except on last attempt)
        if attempt < max_retries - 1:
            logger.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
    
    logger.error(f"All {max_retries} attempts failed for {url}")
    return None


def parse_date(date_string: str, format: str = None) -> Optional[Any]:
    """
    Parse a date string into a datetime object.
    
    Args:
        date_string: Date string to parse
        format: Optional strptime format string
        
    Returns:
        Parsed datetime object or None if parsing fails
    """
    from dateutil import parser
    from datetime import datetime
    
    logger = get_logger(__name__)
    
    try:
        if format:
            return datetime.strptime(date_string, format)
        else:
            # Use dateutil parser for flexible parsing
            return parser.parse(date_string)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None
