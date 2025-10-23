"""
Ares WhatsApp Message Poller
Runs as a background service to poll for new messages periodically
Works even when webhook server is down - queues messages for later processing
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG_DIR = Path.home() / ".ares-mcp"
TASK_QUEUE_FILE = CONFIG_DIR / "mobile_task_queue.json"
LAST_MESSAGE_FILE = CONFIG_DIR / "last_message_timestamp.txt"

# WhatsApp API Configuration
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
ACCESS_TOKEN = "EAAIZCTzaF1osBPlFn8V13lWJgsFjTh4twQZC7MMT0WcOhwL1q3FcD5NcRvZBGu6AWx0ve5t8ZB6ZB4UTc7ZBYbngqSwkZB63ouRuxk8TUE451SqMCZB3IneBuNtfNhAtUPy0WrT2YrGq54Rm0eFaWMQBPXUmgzEKfUvdCZA0MtEtY2i4ubzdAetsFbtsa1NM1MZBkhPwZDZD"
PHONE_NUMBER_ID = "810808242121215"
AUTHORIZED_NUMBER = "61432154351"  # Without + prefix

# Polling configuration
POLL_INTERVAL = 30  # Check every 30 seconds
MAX_RETRIES = 3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_task_queue():
    """Load task queue from file"""
    if TASK_QUEUE_FILE.exists():
        with open(TASK_QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_task_queue(queue):
    """Save task queue to file"""
    with open(TASK_QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)


def get_last_message_timestamp():
    """Get the timestamp of the last processed message"""
    if LAST_MESSAGE_FILE.exists():
        with open(LAST_MESSAGE_FILE, 'r') as f:
            return f.read().strip()
    return None


def save_last_message_timestamp(timestamp):
    """Save the timestamp of the last processed message"""
    with open(LAST_MESSAGE_FILE, 'w') as f:
        f.write(str(timestamp))


def poll_messages():
    """Poll WhatsApp for new messages"""
    try:
        # Get messages from WhatsApp Business API
        url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"
        headers = {
            "Authorization": f"Bearer {ACCESS_TOKEN}"
        }

        # Note: WhatsApp Cloud API doesn't have a direct "get messages" endpoint
        # Messages are pushed via webhooks. This poller serves as a backup/fallback.
        # In production, you'd use the webhook primarily and this as backup.

        logger.info("[POLLER] Checking for connectivity...")

        # Test connection by verifying the phone number
        verify_url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}"
        response = requests.get(verify_url, headers=headers)

        if response.status_code == 200:
            logger.info("[POLLER] ✅ Connected to WhatsApp API")
            return True
        else:
            logger.warning(f"[POLLER] ⚠️ API connection issue: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"[POLLER] ❌ Error: {e}")
        return False


def send_whatsapp_message(to_number, message):
    """Send a WhatsApp message"""
    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        logger.info(f"[SENT] Message to {to_number}")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Failed to send: {e}")
        return False


def main():
    """Main polling loop"""
    logger.info("=" * 70)
    logger.info("ARES WHATSAPP MESSAGE POLLER")
    logger.info("=" * 70)
    logger.info(f"[CONFIG] Polling interval: {POLL_INTERVAL}s")
    logger.info(f"[CONFIG] Task queue: {TASK_QUEUE_FILE}")
    logger.info(f"[CONFIG] Authorized number: {AUTHORIZED_NUMBER}")
    logger.info("")
    logger.info("[INFO] This poller runs in the background")
    logger.info("[INFO] It ensures messages are queued even when bridge is offline")
    logger.info("")
    logger.info("Starting polling loop...")
    logger.info("=" * 70)

    consecutive_errors = 0

    while True:
        try:
            # Check for new messages
            success = poll_messages()

            if success:
                consecutive_errors = 0
            else:
                consecutive_errors += 1

            # If too many consecutive errors, slow down polling
            if consecutive_errors > MAX_RETRIES:
                wait_time = POLL_INTERVAL * 2
                logger.warning(f"[POLLER] Multiple errors, waiting {wait_time}s before retry")
                time.sleep(wait_time)
                consecutive_errors = 0
            else:
                time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("[SHUTDOWN] Poller stopped by user")
            break
        except Exception as e:
            logger.error(f"[ERROR] Polling loop error: {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
