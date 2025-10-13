"""
Ares WhatsApp Bridge - End-to-end encrypted mobile communication

Uses WhatsApp Cloud API (official, free tier):
- End-to-end encrypted messages
- Voice message support with transcription
- Works with your existing WhatsApp number
- Free tier: 1000 messages/month

Setup:
1. Create Meta Developer account: https://developers.facebook.com
2. Create app → Add WhatsApp product
3. Get Phone Number ID and Access Token
4. Add environment variables:
   - WHATSAPP_PHONE_NUMBER_ID
   - WHATSAPP_ACCESS_TOKEN
   - YOUR_PHONE_NUMBER (format: 1234567890, no +)
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from flask import Flask, request, jsonify
import logging

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Paths
ARES_DIR = Path.home() / ".ares-mcp"
TASK_QUEUE_FILE = ARES_DIR / "mobile_task_queue.json"
CONFIG_FILE = ARES_DIR / "whatsapp_config.json"

# WhatsApp API
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"

# Flask app for webhook
app = Flask(__name__)


class AresWhatsAppBridge:
    """Bridge between WhatsApp and Ares Master Control Program"""

    def __init__(self):
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.your_phone = os.getenv("YOUR_PHONE_NUMBER")
        self.task_queue = self.load_task_queue()
        self.config = self.load_config()

        if not all([self.phone_number_id, self.access_token, self.your_phone]):
            logger.error("[ERROR] Missing WhatsApp credentials")
            raise ValueError("Missing WhatsApp credentials. Check environment variables.")

    def load_task_queue(self):
        """Load task queue"""
        if TASK_QUEUE_FILE.exists():
            with open(TASK_QUEUE_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_task_queue(self):
        """Save task queue"""
        with open(TASK_QUEUE_FILE, 'w') as f:
            json.dump(self.task_queue, f, indent=2)

    def load_config(self):
        """Load configuration"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self):
        """Save configuration"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)

    def send_message(self, to: str, message: str) -> bool:
        """Send WhatsApp message"""
        url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            logger.info(f"[OK] Sent message to {to}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Failed to send message: {str(e)}")
            return False

    def download_audio(self, media_id: str) -> Optional[Path]:
        """Download voice message from WhatsApp"""
        # Get media URL
        url = f"{WHATSAPP_API_URL}/{media_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            media_url = response.json()['url']

            # Download file
            audio_response = requests.get(media_url, headers=headers)
            audio_response.raise_for_status()

            # Save to file
            audio_path = ARES_DIR / f"voice_{media_id}.ogg"
            with open(audio_path, 'wb') as f:
                f.write(audio_response.content)

            logger.info(f"[OK] Downloaded audio: {audio_path}")
            return audio_path

        except Exception as e:
            logger.error(f"[ERROR] Failed to download audio: {str(e)}")
            return None

    def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio using OpenAI Whisper API"""
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")

            with open(audio_path, 'rb') as f:
                transcript = openai.Audio.transcribe("whisper-1", f)
                return transcript['text']
        except Exception as e:
            logger.error(f"[ERROR] Transcription failed: {str(e)}")
            return "[Voice message - transcription failed]"

    def add_task(self, task: Dict):
        """Add task to queue"""
        task['id'] = len(self.task_queue) + 1
        task['timestamp'] = datetime.now().isoformat()
        task['status'] = 'queued'
        self.task_queue.append(task)
        self.save_task_queue()
        logger.info(f"[TASK QUEUED] #{task['id']}: {task['content'][:50]}...")

    def handle_text_message(self, from_number: str, message_body: str):
        """Handle text message"""
        logger.info(f"[MESSAGE] From {from_number}: {message_body[:50]}...")

        # Check if it's from authorized number
        if from_number != self.your_phone:
            logger.warning(f"[WARNING] Unauthorized number: {from_number}")
            self.send_message(from_number, "🚫 Unauthorized")
            return

        # Add to task queue
        task = {
            'content': message_body,
            'type': 'text',
            'from': from_number,
            'priority': False
        }
        self.add_task(task)

        # Send confirmation
        self.send_message(
            from_number,
            f"✅ Task #{task['id']} queued!\n\n"
            f"Will be executed when terminal comes online.\n\n"
            f"Reply 'status' to check queue."
        )

    def handle_audio_message(self, from_number: str, media_id: str):
        """Handle voice message"""
        logger.info(f"[VOICE] From {from_number}: {media_id}")

        if from_number != self.your_phone:
            logger.warning(f"[WARNING] Unauthorized number: {from_number}")
            return

        # Download audio
        audio_path = self.download_audio(media_id)
        if not audio_path:
            self.send_message(from_number, "❌ Failed to download voice message")
            return

        # Transcribe
        self.send_message(from_number, "🎤 Transcribing voice message...")
        transcription = self.transcribe_audio(audio_path)

        # Add to task queue
        task = {
            'content': transcription,
            'type': 'voice',
            'voice_file': str(audio_path),
            'from': from_number,
            'priority': False
        }
        self.add_task(task)

        # Send confirmation with transcription
        self.send_message(
            from_number,
            f"✅ Voice message queued as Task #{task['id']}!\n\n"
            f"Transcription:\n{transcription}"
        )

    def handle_status_request(self, from_number: str):
        """Handle status request"""
        total = len(self.task_queue)
        queued = len([t for t in self.task_queue if t['status'] == 'queued'])
        completed = len([t for t in self.task_queue if t['status'] == 'completed'])

        status_msg = f"""
📊 *Ares System Status*

Total tasks: {total}
⏳ Queued: {queued}
✅ Completed: {completed}

🔗 Connection: Online
"""
        self.send_message(from_number, status_msg)


# Global bridge instance
bridge = None


@app.route('/webhook', methods=['GET'])
def webhook_verify():
    """Verify webhook (Meta requirement)"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    # Verify token should match your configured token
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN", "ares_webhook_token")

    if mode == 'subscribe' and token == verify_token:
        logger.info("[OK] Webhook verified")
        return challenge, 200
    else:
        logger.error("[ERROR] Webhook verification failed")
        return 'Forbidden', 403


@app.route('/webhook', methods=['POST'])
def webhook_receive():
    """Receive webhook from WhatsApp"""
    global bridge

    try:
        data = request.get_json()
        logger.info(f"[WEBHOOK] Received: {json.dumps(data, indent=2)}")

        # Extract message data
        entry = data['entry'][0]
        changes = entry['changes'][0]
        value = changes['value']

        if 'messages' not in value:
            return jsonify({"status": "ok"}), 200

        message = value['messages'][0]
        from_number = message['from']

        # Handle different message types
        if message['type'] == 'text':
            message_body = message['text']['body']

            # Check for commands
            if message_body.lower() == 'status':
                bridge.handle_status_request(from_number)
            else:
                bridge.handle_text_message(from_number, message_body)

        elif message['type'] == 'audio':
            media_id = message['audio']['id']
            bridge.handle_audio_message(from_number, media_id)

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"[ERROR] Webhook processing failed: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


def main():
    """Main entry point"""
    global bridge

    print("=" * 70)
    print("ARES WHATSAPP BRIDGE - End-to-End Encrypted Mobile Communication")
    print("=" * 70)
    print()

    # Check for credentials
    if not all([
        os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
        os.getenv("WHATSAPP_ACCESS_TOKEN"),
        os.getenv("YOUR_PHONE_NUMBER")
    ]):
        print("[ERROR] Missing WhatsApp credentials")
        print()
        print("Setup instructions:")
        print("1. Go to https://developers.facebook.com")
        print("2. Create app → Add WhatsApp product")
        print("3. Get your credentials:")
        print("   - Phone Number ID (from WhatsApp → API Setup)")
        print("   - Access Token (from WhatsApp → API Setup)")
        print("   - Your phone number (format: 1234567890, no +)")
        print()
        print("4. Set environment variables:")
        print("   setx WHATSAPP_PHONE_NUMBER_ID \"your_id\"")
        print("   setx WHATSAPP_ACCESS_TOKEN \"your_token\"")
        print("   setx YOUR_PHONE_NUMBER \"1234567890\"")
        print("   setx OPENAI_API_KEY \"your_key\" (for voice transcription)")
        print()
        return

    # Initialize bridge
    try:
        bridge = AresWhatsAppBridge()
    except ValueError as e:
        print(f"[ERROR] {str(e)}")
        return

    print("[OK] WhatsApp Bridge initialized")
    print(f"[OK] Authorized number: {bridge.your_phone}")
    print(f"[OK] Task queue: {TASK_QUEUE_FILE}")
    print()
    print("Starting webhook server...")
    print("Listening on http://localhost:5000/webhook")
    print()
    print("⚠️  IMPORTANT: You need to expose this to the internet")
    print("   Use ngrok: ngrok http 5000")
    print("   Then configure webhook URL in Meta dashboard")
    print()

    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == "__main__":
    main()
