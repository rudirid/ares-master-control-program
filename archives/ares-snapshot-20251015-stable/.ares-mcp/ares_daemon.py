"""
Ares Daemon - Continuous Task Monitoring and Processing

This runs in the background and automatically:
1. Monitors for new WhatsApp tasks
2. Processes them with Ares protocols
3. Sends updates back to WhatsApp

Run this once and it handles everything automatically.
"""

import time
import logging
from datetime import datetime
from pathlib import Path
from ares_whatsapp_processor import AresWhatsAppProcessor
from ares_auto_responder import send_status_update, send_result

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
POLL_INTERVAL = 30  # Check for new tasks every 30 seconds
ARES_DIR = Path.home() / ".ares-mcp"
DAEMON_LOG = ARES_DIR / "ares_daemon.log"


class AresDaemon:
    """Automated Ares task processor"""

    def __init__(self, poll_interval=POLL_INTERVAL):
        self.poll_interval = poll_interval
        self.processor = AresWhatsAppProcessor()
        self.running = False
        self.task_count = 0

    def start(self):
        """Start the daemon"""
        self.running = True
        logger.info("[ARES DAEMON] Starting...")
        logger.info(f"[CONFIG] Poll interval: {self.poll_interval}s")
        logger.info(f"[CONFIG] Pending tasks file: {ARES_DIR / 'pending_ares_tasks.txt'}")
        logger.info("")

        try:
            while self.running:
                self.check_and_process()
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("\n[SHUTDOWN] Daemon stopped by user")
            self.stop()

        except Exception as e:
            logger.error(f"[ERROR] Daemon crashed: {e}")
            self.stop()

    def stop(self):
        """Stop the daemon"""
        self.running = False
        logger.info("[SHUTDOWN] Ares daemon stopped")

    def check_and_process(self):
        """Check for new tasks and process them"""
        try:
            logger.info(f"[POLLING] Checking for new tasks...")

            # Fetch new tasks
            new_task_count = self.processor.process_all()

            if new_task_count > 0:
                self.task_count += new_task_count
                logger.info(f"[OK] {new_task_count} new tasks processed")
                logger.info(f"[STATS] Total tasks processed: {self.task_count}")

                # Get the latest tasks
                tasks = self.processor.fetch_tasks()
                if tasks:
                    # Send notification for each new task
                    for task in tasks[-new_task_count:]:
                        task_id = task['id']
                        send_status_update(
                            task_id,
                            "processing",
                            "Task received and queued for Ares execution"
                        )

            else:
                logger.info(f"[INFO] No new tasks (Total processed: {self.task_count})")

        except Exception as e:
            logger.error(f"[ERROR] Processing error: {e}")

    def get_stats(self):
        """Get daemon statistics"""
        return {
            "running": self.running,
            "total_processed": self.task_count,
            "poll_interval": self.poll_interval,
            "uptime": "N/A"  # Could add uptime tracking
        }


def main():
    """Main entry point"""
    print("=" * 70)
    print("ARES DAEMON - Automated Task Processor")
    print("=" * 70)
    print()
    print("This daemon will:")
    print("  1. Monitor WhatsApp for new messages")
    print("  2. Process them with Ares protocols")
    print("  3. Send updates back to WhatsApp")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()

    # Create and start daemon
    daemon = AresDaemon()
    daemon.start()


if __name__ == "__main__":
    main()
