"""
Ares Signal Bridge - FREE End-to-End Encrypted Mobile Communication

Uses Signal Messenger (100% free, open-source, military-grade encryption):
- End-to-end encrypted messages
- Voice message support
- No API costs (completely free)
- Open-source protocol
- More secure than WhatsApp

Setup:
1. Install signal-cli on your computer
2. Link your Signal account
3. Run this bridge
4. Send messages from Signal on your phone

Requirements:
- Signal installed on phone
- Java installed on computer
- signal-cli installed
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging
import time
import re

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Paths
ARES_DIR = Path.home() / ".ares-mcp"
TASK_QUEUE_FILE = ARES_DIR / "mobile_task_queue.json"
CONFIG_FILE = ARES_DIR / "signal_config.json"


class AresSignalBridge:
    """Bridge between Signal and Ares Master Control Program"""

    def __init__(self):
        self.signal_cli = self.find_signal_cli()
        self.phone_number = self.load_config().get("phone_number")
        self.authorized_number = self.load_config().get("authorized_number")
        self.task_queue = self.load_task_queue()

        if not self.signal_cli:
            raise FileNotFoundError("signal-cli not found. Please install it first.")

    def find_signal_cli(self) -> str:
        """Find signal-cli executable"""
        # Try common locations
        locations = [
            "signal-cli",  # In PATH
            "/usr/local/bin/signal-cli",
            "/usr/bin/signal-cli",
            str(Path.home() / "signal-cli" / "bin" / "signal-cli"),
            "C:\\signal-cli\\bin\\signal-cli.bat"
        ]

        for loc in locations:
            try:
                result = subprocess.run([loc, "--version"],
                                       capture_output=True,
                                       text=True,
                                       timeout=5)
                if result.returncode == 0:
                    logger.info(f"[OK] Found signal-cli: {loc}")
                    return loc
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        return None

    def load_task_queue(self) -> List[Dict]:
        """Load task queue"""
        if TASK_QUEUE_FILE.exists():
            with open(TASK_QUEUE_FILE, 'r') as f:
                return json.load(f)
        return []

    def save_task_queue(self):
        """Save task queue"""
        with open(TASK_QUEUE_FILE, 'w') as f:
            json.dump(self.task_queue, f, indent=2)

    def load_config(self) -> Dict:
        """Load configuration"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}

    def save_config(self, config: Dict):
        """Save configuration"""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

    def register_phone(self, phone_number: str):
        """Register phone number with Signal"""
        logger.info(f"[REGISTERING] {phone_number}")

        # Link mode (easier - scan QR code)
        logger.info("[INFO] Starting linking mode...")
        logger.info("[INFO] Open Signal on your phone and scan the QR code")

        cmd = [self.signal_cli, "-a", phone_number, "link", "-n", "Ares-Bridge"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            logger.info("[OK] Successfully linked!")
            config = self.load_config()
            config['phone_number'] = phone_number
            self.save_config(config)
            self.phone_number = phone_number
            return True
        else:
            logger.error(f"[ERROR] Linking failed: {result.stderr}")
            return False

    def send_message(self, to: str, message: str) -> bool:
        """Send Signal message"""
        if not self.phone_number:
            logger.error("[ERROR] Not registered")
            return False

        cmd = [
            self.signal_cli,
            "-a", self.phone_number,
            "send",
            "-m", message,
            to
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"[OK] Sent message to {to}")
                return True
            else:
                logger.error(f"[ERROR] Failed to send: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            logger.error("[ERROR] Send timeout")
            return False

    def receive_messages(self) -> List[Dict]:
        """Receive new messages"""
        if not self.phone_number:
            return []

        cmd = [
            self.signal_cli,
            "-a", self.phone_number,
            "receive",
            "--json"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return []

            # Parse JSON messages
            messages = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if msg.get('envelope', {}).get('dataMessage'):
                        messages.append(msg)
                except json.JSONDecodeError:
                    continue

            return messages

        except subprocess.TimeoutExpired:
            logger.error("[ERROR] Receive timeout")
            return []

    def add_task(self, task: Dict):
        """Add task to queue"""
        task['id'] = len(self.task_queue) + 1
        task['timestamp'] = datetime.now().isoformat()
        task['status'] = 'queued'
        self.task_queue.append(task)
        self.save_task_queue()
        logger.info(f"[TASK QUEUED] #{task['id']}: {task['content'][:50]}...")

    def handle_message(self, message_data: Dict):
        """Handle incoming message"""
        envelope = message_data.get('envelope', {})
        data_message = envelope.get('dataMessage', {})
        source = envelope.get('sourceNumber') or envelope.get('source')

        if not source:
            return

        # Check authorization
        if self.authorized_number and source != self.authorized_number:
            logger.warning(f"[WARNING] Unauthorized: {source}")
            self.send_message(source, "🚫 Unauthorized")
            return

        # Auto-authorize first sender
        if not self.authorized_number:
            config = self.load_config()
            config['authorized_number'] = source
            self.save_config(config)
            self.authorized_number = source
            logger.info(f"[OK] Authorized: {source}")

        # Get message text
        message_text = data_message.get('message', '')

        if not message_text:
            return

        logger.info(f"[MESSAGE] From {source}: {message_text[:50]}...")

        # Handle commands
        if message_text.lower() == 'status':
            self.handle_status_request(source)
            return
        elif message_text.lower() == 'list':
            self.handle_list_request(source)
            return

        # Add to task queue
        task = {
            'content': message_text,
            'type': 'text',
            'from': source,
            'priority': False
        }

        self.add_task(task)

        # Send confirmation
        self.send_message(
            source,
            f"✅ Task #{task['id']} queued!\n\n"
            f"Will be executed when terminal comes online.\n\n"
            f"Reply 'status' or 'list' to check queue."
        )

    def handle_status_request(self, from_number: str):
        """Handle status request"""
        total = len(self.task_queue)
        queued = len([t for t in self.task_queue if t['status'] == 'queued'])
        completed = len([t for t in self.task_queue if t['status'] == 'completed'])

        status_msg = (
            f"📊 Ares System Status\n\n"
            f"Total tasks: {total}\n"
            f"⏳ Queued: {queued}\n"
            f"✅ Completed: {completed}\n\n"
            f"🔗 Connection: Online"
        )

        self.send_message(from_number, status_msg)

    def handle_list_request(self, from_number: str):
        """Handle list request"""
        pending = [t for t in self.task_queue if t['status'] == 'queued']

        if not pending:
            self.send_message(from_number, "📋 Task queue is empty.")
            return

        msg = f"📋 Task Queue ({len(pending)} pending)\n\n"
        for task in pending[:5]:  # Show first 5
            priority_icon = "⚡" if task.get('priority') else "•"
            msg += f"{priority_icon} #{task['id']}: {task['content'][:40]}...\n"

        if len(pending) > 5:
            msg += f"\n...and {len(pending) - 5} more"

        self.send_message(from_number, msg)

    def run(self, poll_interval: int = 10):
        """Start receiving messages"""
        logger.info("[ARES SIGNAL BRIDGE] Starting...")
        logger.info(f"[INFO] Phone: {self.phone_number}")
        logger.info(f"[INFO] Authorized: {self.authorized_number or 'None (will auto-authorize first sender)'}")
        logger.info(f"[INFO] Poll interval: {poll_interval}s")
        logger.info("[OK] Listening for messages...")

        try:
            while True:
                # Receive messages
                messages = self.receive_messages()

                # Process each message
                for msg in messages:
                    self.handle_message(msg)

                # Wait before next poll
                time.sleep(poll_interval)

        except KeyboardInterrupt:
            logger.info("\n[INFO] Shutting down...")


def setup_signal_cli():
    """Guide user through signal-cli setup"""
    print("=" * 70)
    print("SIGNAL-CLI SETUP REQUIRED")
    print("=" * 70)
    print()
    print("signal-cli is required but not found. Here's how to install:")
    print()
    print("### Windows:")
    print("1. Install Java: https://adoptium.net")
    print("2. Download signal-cli:")
    print("   https://github.com/AsamK/signal-cli/releases")
    print("3. Extract to C:\\signal-cli")
    print("4. Add to PATH or use full path")
    print()
    print("### Linux:")
    print("sudo apt install signal-cli  # Ubuntu/Debian")
    print("or")
    print("brew install signal-cli  # with Homebrew")
    print()
    print("### Mac:")
    print("brew install signal-cli")
    print()
    print("After installation, run this script again.")
    print()


def main():
    """Main entry point"""
    print("=" * 70)
    print("ARES SIGNAL BRIDGE - FREE End-to-End Encrypted Communication")
    print("=" * 70)
    print()

    try:
        bridge = AresSignalBridge()
    except FileNotFoundError:
        setup_signal_cli()
        return

    # Check if registered
    if not bridge.phone_number:
        print("[SETUP] First time setup - Link your Signal account")
        print()
        phone = input("Enter your phone number (format: +1234567890): ").strip()

        if not phone.startswith('+'):
            print("[ERROR] Phone must start with + and country code")
            return

        print()
        print("[INFO] A QR code will appear...")
        print("[INFO] Open Signal on your phone → Settings → Linked Devices → Link New Device")
        print("[INFO] Scan the QR code that appears")
        print()
        input("Press Enter when ready...")

        if not bridge.register_phone(phone):
            print("[ERROR] Registration failed")
            return

    print("[OK] Signal Bridge initialized")
    print(f"[OK] Linked phone: {bridge.phone_number}")
    print(f"[OK] Task queue: {TASK_QUEUE_FILE}")
    print()
    print("💬 Send messages from Signal on your phone")
    print("📱 Commands: 'status', 'list'")
    print()
    print("Press Ctrl+C to stop")
    print()

    # Run bridge
    bridge.run(poll_interval=10)


if __name__ == "__main__":
    main()
