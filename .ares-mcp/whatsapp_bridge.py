"""
Ares WhatsApp Cloud API Bridge
Uses official WhatsApp Business Cloud API to receive and send messages
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# Configuration
CONFIG_DIR = Path.home() / ".ares-mcp"
CONFIG_FILE = CONFIG_DIR / "whatsapp_config.json"
TASK_QUEUE_FILE = CONFIG_DIR / "mobile_task_queue.json"

# WhatsApp API Configuration (loaded from environment variables)
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
AUTHORIZED_NUMBER = os.getenv('AUTHORIZED_NUMBER', '+61432154351')

# Validate required environment variables
if not ACCESS_TOKEN:
    raise ValueError("WHATSAPP_ACCESS_TOKEN not set in .env file")
if not PHONE_NUMBER_ID:
    raise ValueError("WHATSAPP_PHONE_NUMBER_ID not set in .env file")
if not VERIFY_TOKEN:
    raise ValueError("WHATSAPP_VERIFY_TOKEN not set in .env file")

# Setup logging
import sys
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Flask app for webhook
app = Flask(__name__)

# Ensure directories exist
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Initialize encryption for task queue
try:
    from cryptography.fernet import Fernet
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    if ENCRYPTION_KEY:
        cipher = Fernet(ENCRYPTION_KEY.encode())
        ENCRYPTION_ENABLED = True
        logger.info("[SECURITY] Task queue encryption enabled")
    else:
        ENCRYPTION_ENABLED = False
        logger.warning("[SECURITY] ENCRYPTION_KEY not set - task queue will not be encrypted")
except ImportError:
    ENCRYPTION_ENABLED = False
    logger.warning("[SECURITY] cryptography not installed - task queue will not be encrypted")


def load_task_queue():
    """Load task queue from file (with optional encryption)"""
    if not TASK_QUEUE_FILE.exists():
        return []

    try:
        content = TASK_QUEUE_FILE.read_text()

        if ENCRYPTION_ENABLED and content.startswith('gAAAAA'):  # Fernet token signature
            # Decrypt
            decrypted = cipher.decrypt(content.encode()).decode()
            return json.loads(decrypted)
        else:
            # Plain JSON (for backwards compatibility)
            return json.loads(content)
    except Exception as e:
        logger.error(f"[ERROR] Failed to load task queue: {e}")
        return []


def save_task_queue(queue):
    """Save task queue to file (with optional encryption)"""
    try:
        json_data = json.dumps(queue, indent=2)

        if ENCRYPTION_ENABLED:
            # Encrypt before saving
            encrypted = cipher.encrypt(json_data.encode()).decode()
            TASK_QUEUE_FILE.write_text(encrypted)
            logger.debug(f"[SECURITY] Task queue encrypted and saved ({len(queue)} tasks)")
        else:
            # Plain JSON
            TASK_QUEUE_FILE.write_text(json_data)
            logger.debug(f"[SECURITY] Task queue saved (unencrypted, {len(queue)} tasks)")
    except Exception as e:
        logger.error(f"[ERROR] Failed to save task queue: {e}")


def send_whatsapp_message(to_number, message):
    """Send a WhatsApp message using Cloud API"""
    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": to_number.replace("+", ""),
        "type": "text",
        "text": {"body": message}
    }

    try:
        logger.info(f"[SENDING] Attempting to send to {to_number}")
        logger.info(f"[API URL] {url}")
        response = requests.post(url, headers=headers, json=data)
        logger.info(f"[API RESPONSE] Status: {response.status_code}")
        logger.info(f"[API RESPONSE] Body: {response.text}")
        response.raise_for_status()
        logger.info(f"[SENT] Message to {to_number}")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Failed to send message: {e}")
        logger.error(f"[ERROR] Response: {response.text if 'response' in locals() else 'No response'}")
        return False


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """Handle WhatsApp webhook"""

    if request.method == 'GET':
        # Webhook verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            logger.info("[OK] Webhook verified")
            return challenge, 200
        else:
            logger.warning("[WARNING] Webhook verification failed")
            return 'Forbidden', 403

    elif request.method == 'POST':
        # Process incoming message
        try:
            data = request.get_json()
            logger.info(f"[RECEIVED] Webhook data: {json.dumps(data, indent=2)}")

            # Extract message
            if 'entry' in data:
                for entry in data['entry']:
                    for change in entry.get('changes', []):
                        value = change.get('value', {})

                        # Get messages
                        messages = value.get('messages', [])
                        for message in messages:
                            from_number = message.get('from')
                            message_body = message.get('text', {}).get('body', '')
                            message_id = message.get('id')

                            # Only process messages from authorized number
                            if f"+{from_number}" == AUTHORIZED_NUMBER:
                                logger.info(f"[MESSAGE] From {from_number}: {message_body}")

                                # Handle special commands
                                if message_body.lower() == 'status':
                                    queue = load_task_queue()
                                    status_msg = f"Ares Status:\n✅ Bridge Active\n📋 Tasks in queue: {len(queue)}"
                                    send_whatsapp_message(f"+{from_number}", status_msg)

                                elif message_body.lower() == 'list':
                                    queue = load_task_queue()
                                    if queue:
                                        list_msg = "Task Queue:\n" + "\n".join([f"{i+1}. {t['task']}" for i, t in enumerate(queue)])
                                    else:
                                        list_msg = "Task queue is empty"
                                    send_whatsapp_message(f"+{from_number}", list_msg)

                                else:
                                    # Add to task queue
                                    queue = load_task_queue()
                                    task = {
                                        "id": len(queue) + 1,
                                        "task": message_body,
                                        "from": from_number,
                                        "timestamp": datetime.now().isoformat(),
                                        "message_id": message_id
                                    }
                                    queue.append(task)
                                    save_task_queue(queue)

                                    logger.info(f"[TASK QUEUED] #{task['id']}: {message_body}")

                                    # Send confirmation
                                    confirmation = f"✅ Task #{task['id']} queued:\n{message_body}"
                                    send_whatsapp_message(f"+{from_number}", confirmation)

                            else:
                                logger.warning(f"[UNAUTHORIZED] Message from {from_number} ignored")

            return jsonify({"status": "ok"}), 200

        except Exception as e:
            logger.error(f"[ERROR] Processing webhook: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500


def require_api_key(f):
    """Decorator to require API key authentication"""
    from functools import wraps
    import hmac

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')

        if not api_key:
            logger.warning("[AUTH] Missing API key")
            return jsonify({'error': 'API key required', 'code': 'AUTH_001'}), 401

        valid_key = os.getenv('ARES_API_KEY')
        if not valid_key:
            logger.error("[AUTH] ARES_API_KEY not set in environment")
            return jsonify({'error': 'Server configuration error', 'code': 'AUTH_002'}), 500

        # Use constant-time comparison to prevent timing attacks
        if not hmac.compare_digest(api_key, valid_key):
            logger.warning(f"[AUTH] Invalid API key from {request.remote_addr}")
            return jsonify({'error': 'Invalid API key', 'code': 'AUTH_003'}), 401

        logger.info(f"[AUTH] Valid API key from {request.remote_addr}")
        return f(*args, **kwargs)
    return decorated_function


@app.route('/send', methods=['POST'])
@require_api_key
def send_message():
    """Endpoint to send messages from Ares (requires API key)"""
    try:
        logger.info("[SEND ENDPOINT] Request received")
        data = request.get_json(force=True)
        logger.info(f"[SEND ENDPOINT] Data: {data}")
        message = data.get('message')
        to_number = data.get('to', AUTHORIZED_NUMBER)
        logger.info(f"[SEND ENDPOINT] Sending to {to_number}: {message}")

        result = send_whatsapp_message(to_number, message)
        logger.info(f"[SEND ENDPOINT] Result: {result}")

        if result:
            return jsonify({"status": "sent"}), 200
        else:
            return jsonify({"status": "failed"}), 500

    except Exception as e:
        logger.error(f"[ERROR] Send endpoint exception: {e}")
        import traceback
        logger.error(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all queued tasks"""
    queue = load_task_queue()
    return jsonify({"tasks": queue}), 200


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task from queue"""
    queue = load_task_queue()
    queue = [t for t in queue if t['id'] != task_id]
    save_task_queue(queue)
    return jsonify({"status": "deleted"}), 200


if __name__ == "__main__":
    logger.info("=" * 70)
    logger.info("ARES WHATSAPP CLOUD API BRIDGE")
    logger.info("=" * 70)
    logger.info(f"[CONFIG] Phone Number ID: {PHONE_NUMBER_ID}")
    logger.info(f"[CONFIG] Authorized Number: {AUTHORIZED_NUMBER}")
    logger.info(f"[CONFIG] Task Queue: {TASK_QUEUE_FILE}")
    logger.info("")
    logger.info("[INFO] Starting webhook server on http://localhost:5000")
    logger.info("[INFO] Webhook URL: http://localhost:5000/webhook")
    logger.info("")
    logger.info("[NEXT STEP] Configure Meta webhook with this URL")
    logger.info("[NEXT STEP] For public access, use ngrok or similar")
    logger.info("")
    logger.info("Send yourself a WhatsApp message to test!")
    logger.info("=" * 70)

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
