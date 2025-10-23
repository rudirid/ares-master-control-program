"""
Live ASX Announcement Monitor

Monitors ASX for real-time company announcements and triggers trading signals.

Features:
- Real-time announcement detection
- Price-sensitive filtering
- Time-stamped data collection
- Database storage
- Event-driven architecture

Author: Claude Code
Date: 2025-10-10
"""

import logging
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3
from bs4 import BeautifulSoup
import pytz

logger = logging.getLogger(__name__)


class ASXAnnouncementMonitor:
    """
    Monitors ASX for real-time company announcements.

    Supports multiple data sources:
    - ASX website scraping (free)
    - API integration (requires credentials)
    """

    def __init__(
        self,
        db_path: str,
        check_interval_seconds: int = 10,  # 10s to capture 30-90s alpha window
        data_source: str = 'asx_web'
    ):
        """
        Initialize announcement monitor.

        Args:
            db_path: Database path
            check_interval_seconds: How often to check for new announcements (default: 10s for 30-90s alpha)
            data_source: 'asx_web', 'api', or 'test'
        """
        self.db_path = db_path
        self.check_interval = check_interval_seconds
        self.data_source = data_source
        self.running = False
        self.tz = pytz.timezone('Australia/Sydney')

        # Track seen announcements to avoid duplicates
        self.seen_announcements = set()

        # Create live announcements table
        self._create_live_table()

    def _create_live_table(self):
        """Create table for live announcements if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                title TEXT NOT NULL,
                announcement_type TEXT,
                price_sensitive INTEGER DEFAULT 0,
                content TEXT,
                asx_timestamp TIMESTAMP NOT NULL,
                detected_timestamp TIMESTAMP NOT NULL,
                url TEXT UNIQUE,
                age_minutes REAL,
                processed INTEGER DEFAULT 0,
                recommendation_generated INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

        logger.info("Live announcements table ready")

    def scrape_asx_announcements(self) -> List[Dict]:
        """
        Fetch latest announcements from ASX API.

        Returns:
            List of announcement dictionaries
        """
        # Use official ASX API endpoint (discovered via network monitoring)
        url = "https://asx.api.markitdigital.com/asx-research/1.0/markets/announcements"

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.asx.com.au/markets/trade-our-cash-market/todays-announcements.html',
                'Origin': 'https://www.asx.com.au'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            announcements = []

            # Extract items from response
            items = data.get('data', {}).get('items', [])

            if not items:
                logger.warning("No announcements found in API response")
                return []

            # Process latest 100 announcements
            for item in items[:100]:
                try:
                    # Extract fields from API response
                    ticker = item.get('symbol', '')
                    title = item.get('headline', '')
                    announcement_types = item.get('announcementTypes', [])
                    announcement_type = announcement_types[0] if announcement_types else 'Other'
                    date_str = item.get('date', '')
                    price_sensitive = 1 if item.get('isPriceSensitive', False) else 0
                    document_key = item.get('documentKey', '')

                    # Parse ISO timestamp from API
                    asx_timestamp = datetime.fromisoformat(date_str.replace('Z', '+00:00'))

                    # Convert to Sydney timezone
                    asx_timestamp = asx_timestamp.astimezone(self.tz)

                    # Create unique URL based on document key
                    ann_url = f"https://www.asx.com.au/asxpdf/{document_key}.pdf" if document_key else None

                    # Skip if missing critical fields
                    if not ticker or not title:
                        continue

                    announcements.append({
                        'ticker': ticker,
                        'title': title,
                        'announcement_type': announcement_type,
                        'price_sensitive': price_sensitive,
                        'asx_timestamp': asx_timestamp,
                        'url': ann_url
                    })

                except Exception as e:
                    logger.warning(f"Error parsing announcement item: {e}")
                    continue

            logger.info(f"Fetched {len(announcements)} announcements from ASX API")
            return announcements

        except requests.RequestException as e:
            logger.error(f"Error fetching ASX announcements: {e}")
            return []
        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing ASX API response: {e}")
            return []

    def _parse_asx_time(self, time_str: str) -> datetime:
        """
        Parse ASX timestamp string to datetime.

        Args:
            time_str: Time string from ASX (e.g., "10:30 AM")

        Returns:
            Datetime object
        """
        try:
            # Handle various time formats
            # ASX typically uses: "10:30 AM" or "DD/MM/YYYY HH:MM AM/PM"

            now = datetime.now(self.tz)

            # If just time (e.g., "10:30 AM"), assume today
            if 'AM' in time_str or 'PM' in time_str:
                if '/' not in time_str:
                    # Just time, use today's date
                    time_parsed = datetime.strptime(time_str.strip(), '%I:%M %p')
                    return now.replace(
                        hour=time_parsed.hour,
                        minute=time_parsed.minute,
                        second=0,
                        microsecond=0
                    )
                else:
                    # Full datetime
                    return datetime.strptime(time_str.strip(), '%d/%m/%Y %I:%M %p')

            # Fallback: return current time
            return now

        except Exception as e:
            logger.warning(f"Could not parse time '{time_str}': {e}")
            return datetime.now(self.tz)

    def get_test_announcements(self) -> List[Dict]:
        """
        Generate test announcements for development.

        Returns:
            List of test announcement dictionaries
        """
        now = datetime.now(self.tz)

        test_announcements = [
            {
                'ticker': 'BHP',
                'title': 'Quarterly Production Report',
                'announcement_type': 'Quarterly Report',
                'price_sensitive': 1,
                'asx_timestamp': now - timedelta(minutes=2),
                'url': 'https://www.asx.com.au/test/bhp-quarterly'
            },
            {
                'ticker': 'CBA',
                'title': 'Trading Update - FY25',
                'announcement_type': 'Trading Update',
                'price_sensitive': 1,
                'asx_timestamp': now - timedelta(minutes=5),
                'url': 'https://www.asx.com.au/test/cba-update'
            },
            {
                'ticker': 'CSL',
                'title': 'Director Interest Notice',
                'announcement_type': 'Director Changes',
                'price_sensitive': 0,
                'asx_timestamp': now - timedelta(minutes=10),
                'url': 'https://www.asx.com.au/test/csl-director'
            }
        ]

        return test_announcements

    def fetch_announcements(self) -> List[Dict]:
        """
        Fetch announcements from configured data source.

        Returns:
            List of announcements
        """
        if self.data_source == 'asx_web':
            return self.scrape_asx_announcements()
        elif self.data_source == 'test':
            return self.get_test_announcements()
        else:
            logger.error(f"Unknown data source: {self.data_source}")
            return []

    def store_announcement(self, announcement: Dict) -> bool:
        """
        Store announcement in database if not already seen.

        Args:
            announcement: Announcement dictionary

        Returns:
            True if stored (new), False if duplicate
        """
        # Check if already seen
        if announcement['url'] in self.seen_announcements:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            detected_timestamp = datetime.now(self.tz)

            # Calculate age in minutes
            age_minutes = (detected_timestamp - announcement['asx_timestamp']).total_seconds() / 60

            cursor.execute("""
                INSERT INTO live_announcements (
                    ticker, title, announcement_type, price_sensitive,
                    asx_timestamp, detected_timestamp, url, age_minutes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                announcement['ticker'],
                announcement['title'],
                announcement['announcement_type'],
                announcement['price_sensitive'],
                announcement['asx_timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                detected_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                announcement['url'],
                age_minutes
            ))

            conn.commit()
            self.seen_announcements.add(announcement['url'])

            logger.info(
                f"NEW ANNOUNCEMENT: {announcement['ticker']} - {announcement['title']} "
                f"(Age: {age_minutes:.1f} min)"
            )

            return True

        except sqlite3.IntegrityError:
            # Duplicate URL
            return False
        finally:
            conn.close()

    def is_market_hours(self) -> bool:
        """
        Check if currently within ASX trading hours.

        Returns:
            True if market is open
        """
        now = datetime.now(self.tz)

        # Check if weekday
        if now.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Check if within 7 AM - 4:30 PM AEST (capture pre-market + trading hours)
        market_start = now.replace(hour=7, minute=0, second=0, microsecond=0)
        market_end = now.replace(hour=16, minute=30, second=0, microsecond=0)

        return market_start <= now <= market_end

    def run_monitoring_loop(self, duration_hours: Optional[int] = None):
        """
        Run continuous monitoring loop.

        Args:
            duration_hours: Run for this many hours (None = run indefinitely)
        """
        self.running = True
        start_time = datetime.now()

        logger.info("=" * 80)
        logger.info("LIVE ASX ANNOUNCEMENT MONITOR STARTED")
        logger.info(f"Data Source: {self.data_source}")
        logger.info(f"Check Interval: {self.check_interval}s")
        logger.info(f"Duration: {'Indefinite' if duration_hours is None else f'{duration_hours} hours'}")
        logger.info("=" * 80)

        check_count = 0
        announcements_found = 0

        try:
            while self.running:
                # Check if duration exceeded
                if duration_hours:
                    elapsed_hours = (datetime.now() - start_time).total_seconds() / 3600
                    if elapsed_hours >= duration_hours:
                        logger.info(f"Duration limit reached ({duration_hours} hours)")
                        break

                # Check if market hours
                if not self.is_market_hours():
                    logger.info("Outside market hours - waiting...")
                    time.sleep(300)  # Check every 5 min when market closed
                    continue

                check_count += 1
                logger.info(f"\n[Check #{check_count}] Fetching announcements...")

                # Fetch announcements
                announcements = self.fetch_announcements()

                if announcements:
                    logger.info(f"Found {len(announcements)} announcements")

                    # Store new announcements
                    new_count = 0
                    for announcement in announcements:
                        if self.store_announcement(announcement):
                            new_count += 1
                            announcements_found += 1

                    logger.info(f"Stored {new_count} new announcements (Total: {announcements_found})")
                else:
                    logger.info("No announcements found")

                # Wait for next check
                logger.info(f"Waiting {self.check_interval}s until next check...")
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("\nMonitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}", exc_info=True)
        finally:
            self.running = False

            logger.info("\n" + "=" * 80)
            logger.info("MONITORING SESSION COMPLETE")
            logger.info(f"Total Checks: {check_count}")
            logger.info(f"Announcements Found: {announcements_found}")
            logger.info("=" * 80)

    def stop(self):
        """Stop the monitoring loop."""
        self.running = False


def main():
    """Run announcement monitor."""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import config

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Use real ASX API data
    monitor = ASXAnnouncementMonitor(
        db_path=config.DATABASE_PATH,
        check_interval_seconds=10,  # Check every 10 seconds (capture 30-90s alpha window)
        data_source='asx_web'  # Real ASX API
    )

    # Run until market close (extended collection)
    monitor.run_monitoring_loop(duration_hours=8)  # Covers until market close


if __name__ == '__main__':
    main()
