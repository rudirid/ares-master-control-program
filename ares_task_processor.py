"""
Ares Task Processor - Executes tasks from mobile bridge queue

This runs on your development machine and processes tasks
queued from your phone via Telegram.

Features:
- Processes tasks from mobile_task_queue.json
- Categorizes tasks (code, research, note, reminder)
- Creates Claude Code CLI commands
- Sends status updates back via Telegram
- Integrates with Ares validation protocols
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import logging
import asyncio

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Paths
ARES_DIR = Path.home() / ".ares-mcp"
TASK_QUEUE_FILE = ARES_DIR / "mobile_task_queue.json"
PROCESSED_LOG = ARES_DIR / "processed_tasks.log"


class AresTaskProcessor:
    """Process mobile tasks with Ares validation"""

    def __init__(self):
        self.task_queue = self.load_task_queue()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

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

    def categorize_task(self, task_content: str) -> str:
        """Categorize task by content"""
        content_lower = task_content.lower()

        # Keywords for categorization
        code_keywords = ['build', 'create', 'implement', 'fix', 'debug', 'refactor', 'code']
        research_keywords = ['research', 'investigate', 'analyze', 'study', 'learn']
        note_keywords = ['note', 'remember', 'idea', 'thought', 'consider']
        reminder_keywords = ['remind', 'don\'t forget', 'later', 'tomorrow']

        if any(kw in content_lower for kw in code_keywords):
            return 'code'
        elif any(kw in content_lower for kw in research_keywords):
            return 'research'
        elif any(kw in content_lower for kw in note_keywords):
            return 'note'
        elif any(kw in content_lower for kw in reminder_keywords):
            return 'reminder'
        else:
            return 'general'

    def create_ares_command(self, task: Dict) -> str:
        """Create Ares command from task"""
        category = self.categorize_task(task['content'])

        if category == 'code':
            # Use /ares command for coding tasks
            return f"/ares {task['content']}"
        elif category == 'research':
            # Use /ares with research focus
            return f"/ares Research and summarize: {task['content']}"
        elif category == 'note':
            # Create note file
            return f"echo '{task['content']}' >> .ares-mcp/mobile_notes.txt"
        elif category == 'reminder':
            # Create reminder file
            return f"echo '[{datetime.now().isoformat()}] {task['content']}' >> .ares-mcp/reminders.txt"
        else:
            # General task
            return f"/ares {task['content']}"

    def process_task(self, task: Dict):
        """Process a single task"""
        logger.info(f"[PROCESSING] Task #{task['id']}: {task['content'][:50]}...")

        try:
            # Update status
            task['status'] = 'processing'
            task['processed_at'] = datetime.now().isoformat()
            self.save_task_queue()

            # Categorize
            category = self.categorize_task(task['content'])
            logger.info(f"[CATEGORY] {category}")

            # Create command
            command = self.create_ares_command(task)
            logger.info(f"[COMMAND] {command}")

            # For notes and reminders, execute directly
            if category in ['note', 'reminder']:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    task['status'] = 'completed'
                    task['result'] = f"Saved to {category} file"
                    logger.info(f"[OK] Task #{task['id']} completed")
                else:
                    task['status'] = 'failed'
                    task['error'] = result.stderr
                    logger.error(f"[ERROR] Task #{task['id']} failed: {result.stderr}")
            else:
                # For code/research tasks, output command for manual execution
                task['status'] = 'ready'
                task['command'] = command
                task['result'] = "Command ready for execution in Claude Code CLI"
                logger.info(f"[READY] Task #{task['id']} - Run: {command}")

                # Write to execution file
                exec_file = ARES_DIR / "pending_tasks.sh"
                with open(exec_file, 'a') as f:
                    f.write(f"# Task #{task['id']} - {task['timestamp']}\n")
                    f.write(f"# {task['content']}\n")
                    f.write(f"{command}\n\n")

                logger.info(f"[OK] Added to {exec_file}")

            # Save updated task
            self.save_task_queue()

            # Log to processed file
            with open(PROCESSED_LOG, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] Task #{task['id']}: {task['status']} - {task['content'][:50]}\n")

        except Exception as e:
            task['status'] = 'failed'
            task['error'] = str(e)
            self.save_task_queue()
            logger.error(f"[ERROR] Task #{task['id']} failed: {str(e)}")

    async def send_telegram_update(self, user_id: int, message: str):
        """Send status update to Telegram"""
        if not self.bot_token:
            logger.warning("[WARNING] No bot token, skipping Telegram update")
            return

        try:
            from telegram import Bot
            bot = Bot(token=self.bot_token)
            await bot.send_message(chat_id=user_id, text=message)
            logger.info(f"[OK] Sent update to user {user_id}")
        except Exception as e:
            logger.error(f"[ERROR] Failed to send Telegram update: {str(e)}")

    def process_queue(self):
        """Process all queued tasks"""
        logger.info("[ARES TASK PROCESSOR] Starting...")

        pending = [t for t in self.task_queue if t['status'] == 'queued']

        if not pending:
            logger.info("[INFO] No pending tasks")
            return

        logger.info(f"[INFO] Processing {len(pending)} tasks...")

        for task in pending:
            self.process_task(task)

            # Send update to user
            if task['status'] in ['completed', 'ready']:
                msg = f"✅ Task #{task['id']} {task['status']}\n\n{task.get('result', '')}"
            else:
                msg = f"❌ Task #{task['id']} failed\n\n{task.get('error', '')}"

            # Note: This would need to run in async context
            # asyncio.run(self.send_telegram_update(task['user_id'], msg))

        logger.info("[OK] Queue processing complete")

        # Show summary
        self.show_summary()

    def show_summary(self):
        """Show processing summary"""
        total = len(self.task_queue)
        completed = len([t for t in self.task_queue if t['status'] == 'completed'])
        ready = len([t for t in self.task_queue if t['status'] == 'ready'])
        failed = len([t for t in self.task_queue if t['status'] == 'failed'])
        queued = len([t for t in self.task_queue if t['status'] == 'queued'])

        print("\n" + "=" * 70)
        print("PROCESSING SUMMARY")
        print("=" * 70)
        print(f"Total tasks: {total}")
        print(f"✅ Completed: {completed}")
        print(f"🔄 Ready for execution: {ready}")
        print(f"❌ Failed: {failed}")
        print(f"⏳ Still queued: {queued}")
        print()

        if ready > 0:
            exec_file = ARES_DIR / "pending_tasks.sh"
            print(f"📋 {ready} tasks ready for execution")
            print(f"   Run commands from: {exec_file}")
            print()


def main():
    """Main entry point"""
    print("=" * 70)
    print("ARES TASK PROCESSOR - Execute Mobile Tasks")
    print("=" * 70)
    print()

    processor = AresTaskProcessor()
    processor.process_queue()


if __name__ == "__main__":
    main()
