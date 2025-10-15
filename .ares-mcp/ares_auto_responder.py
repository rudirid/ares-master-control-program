"""
Ares Auto-Responder - Sends responses back to WhatsApp

This module handles sending Ares responses back to the user via WhatsApp.
"""

import requests
import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
WHATSAPP_API_URL = "http://localhost:5000"
ARES_DIR = Path.home() / ".ares-mcp"
RESPONSE_LOG = ARES_DIR / "response_log.json"


def send_response(task_id, message, to_number=None):
    """Send response back to WhatsApp"""
    try:
        # Prepare request
        url = f"{WHATSAPP_API_URL}/send"
        data = {"message": message}

        if to_number:
            data["to"] = to_number

        logger.info(f"[SENDING] Response for task #{task_id}")

        # Send via bridge
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()

        logger.info(f"[OK] Response sent for task #{task_id}")

        # Log response
        log_response(task_id, message, success=True)

        return True

    except Exception as e:
        logger.error(f"[ERROR] Failed to send response: {e}")
        log_response(task_id, message, success=False, error=str(e))
        return False


def log_response(task_id, message, success=True, error=None):
    """Log sent responses"""
    log_entry = {
        "task_id": task_id,
        "timestamp": datetime.now().isoformat(),
        "message": message[:100] + "..." if len(message) > 100 else message,
        "success": success,
        "error": error
    }

    # Load existing log
    if RESPONSE_LOG.exists():
        with open(RESPONSE_LOG, 'r') as f:
            log = json.load(f)
    else:
        log = []

    # Append new entry
    log.append(log_entry)

    # Keep only last 100 responses
    log = log[-100:]

    # Save
    with open(RESPONSE_LOG, 'w') as f:
        json.dump(log, f, indent=2)


def send_status_update(task_id, status, details=None):
    """Send status update for a task"""
    status_emojis = {
        "processing": "🔄",
        "completed": "✅",
        "failed": "❌",
        "warning": "⚠️"
    }

    emoji = status_emojis.get(status, "ℹ️")
    message = f"{emoji} Task #{task_id}: {status.capitalize()}"

    if details:
        message += f"\n\n{details}"

    return send_response(task_id, message)


def send_result(task_id, result_text):
    """Send execution result"""
    message = f"✅ Task #{task_id} Complete\n\n{result_text}"
    return send_response(task_id, message)


def send_error(task_id, error_text):
    """Send error notification"""
    message = f"❌ Task #{task_id} Failed\n\n{error_text}"
    return send_response(task_id, message)


# Example usage
if __name__ == "__main__":
    # Test sending a response
    print("=" * 70)
    print("ARES AUTO-RESPONDER - Test Mode")
    print("=" * 70)

    test_message = "Test response from Ares. This is a proof-of-concept."

    print(f"Sending test message: {test_message}")
    result = send_response(task_id=999, message=test_message)

    if result:
        print("✅ Test message sent successfully")
    else:
        print("❌ Test message failed")
