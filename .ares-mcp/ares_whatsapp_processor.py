"""
Ares WhatsApp Task Processor - Bridge between WhatsApp webhook and Ares

This fetches tasks from the WhatsApp webhook server and processes them
using Ares validation protocols.
"""

import requests
import json
import os
from datetime import datetime
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    format='[%(asctime)s] %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
WHATSAPP_API_URL = "http://localhost:5000"
ARES_DIR = Path.home() / ".ares-mcp"
PROCESSED_IDS_FILE = ARES_DIR / "processed_whatsapp_tasks.json"
PENDING_TASKS_FILE = ARES_DIR / "pending_ares_tasks.txt"


class AresWhatsAppProcessor:
    """Process WhatsApp tasks with Ares"""

    def __init__(self):
        self.processed_ids = self.load_processed_ids()

    def load_processed_ids(self):
        """Load list of already processed task IDs"""
        if PROCESSED_IDS_FILE.exists():
            with open(PROCESSED_IDS_FILE, 'r') as f:
                return set(json.load(f))
        return set()

    def save_processed_ids(self):
        """Save processed IDs"""
        with open(PROCESSED_IDS_FILE, 'w') as f:
            json.dump(list(self.processed_ids), f, indent=2)

    def fetch_tasks(self):
        """Fetch tasks from WhatsApp webhook"""
        try:
            response = requests.get(f"{WHATSAPP_API_URL}/tasks", timeout=5)
            response.raise_for_status()
            data = response.json()
            return data.get('tasks', [])
        except Exception as e:
            logger.error(f"[ERROR] Failed to fetch tasks: {e}")
            return []

    def categorize_task(self, task_content: str) -> str:
        """Categorize task by content"""
        content_lower = task_content.lower()

        # Keywords for categorization
        code_keywords = ['build', 'create', 'implement', 'fix', 'debug', 'refactor', 'code']
        research_keywords = ['research', 'investigate', 'analyze', 'study', 'learn']
        question_keywords = ['what', 'how', 'why', 'when', 'where', 'who', '?']

        if any(kw in content_lower for kw in code_keywords):
            return 'code'
        elif any(kw in content_lower for kw in research_keywords):
            return 'research'
        elif any(kw in content_lower for kw in question_keywords):
            return 'question'
        else:
            return 'general'

    def process_task(self, task):
        """Process a single task"""
        task_id = task['id']

        # Skip if already processed
        if task_id in self.processed_ids:
            return False

        logger.info(f"[NEW TASK] #{task_id}: {task['task']}")

        # Categorize
        category = self.categorize_task(task['task'])
        logger.info(f"[CATEGORY] {category}")

        # Create Ares prompt
        prompt = self.create_ares_prompt(task, category)

        # Save to pending tasks
        with open(PENDING_TASKS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*70}\n")
            f.write(f"Task #{task_id} - {task['timestamp']}\n")
            f.write(f"From: {task['from']}\n")
            f.write(f"Category: {category}\n")
            f.write(f"{'='*70}\n\n")
            f.write(f"{prompt}\n\n")

        # Mark as processed
        self.processed_ids.add(task_id)
        self.save_processed_ids()

        logger.info(f"[OK] Task #{task_id} queued for Ares")

        return True

    def create_ares_prompt(self, task, category):
        """Create Ares-formatted prompt"""
        task_content = task['task']

        if category == 'code':
            return f"""Ares Master Control: Execute Code Task

Task: {task_content}

Execute with Ares v2.1 protocols:
- Internal validation (confidence-based execution)
- Show your work (transparent reasoning)
- Apply proven patterns from ares-mcp/proven-patterns.md
- Check tech-success-matrix.md for recommended approaches
"""
        elif category == 'research':
            return f"""Ares Master Control: Research Task

Research and summarize: {task_content}

Execute with Ares v2.1 protocols:
- Thorough investigation
- Evidence-based findings
- Clear summary with sources
"""
        elif category == 'question':
            return f"""Ares Master Control: Answer Question

Question: {task_content}

Execute with Ares v2.1 protocols:
- Check decision-causality.md for similar past decisions
- Reference proven-patterns.md for context
- Provide clear, direct answer
"""
        else:
            return f"""Ares Master Control: General Task

Task: {task_content}

Execute with Ares v2.1 protocols:
- Determine appropriate action
- Apply relevant patterns
- Execute confidently
"""

    def send_response(self, task_id, message):
        """Send response back via WhatsApp"""
        try:
            response = requests.post(
                f"{WHATSAPP_API_URL}/respond",
                json={'task_id': task_id, 'message': message},
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"[OK] Sent response for task #{task_id}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to send response: {e}")
            return False

    def process_all(self):
        """Fetch and process all new tasks"""
        logger.info("[ARES WHATSAPP PROCESSOR] Starting...")

        tasks = self.fetch_tasks()

        if not tasks:
            logger.info("[INFO] No tasks in queue")
            return 0

        new_tasks = 0
        for task in tasks:
            if self.process_task(task):
                new_tasks += 1

        logger.info(f"[OK] Processed {new_tasks} new tasks")

        if new_tasks > 0:
            logger.info(f"\n📋 Tasks queued in: {PENDING_TASKS_FILE}")
            logger.info("   Copy/paste prompts into Claude Code to execute with Ares\n")

        return new_tasks


def main():
    """Main entry point"""
    print("=" * 70)
    print("ARES WHATSAPP TASK PROCESSOR")
    print("Fetching tasks from WhatsApp bridge...")
    print("=" * 70)
    print()

    processor = AresWhatsAppProcessor()
    new_tasks = processor.process_all()

    if new_tasks > 0:
        print(f"\n✅ {new_tasks} new tasks ready for processing")
        print(f"\nNext step: Review tasks in {PENDING_TASKS_FILE}")
    else:
        print("✅ No new tasks")


if __name__ == "__main__":
    main()
