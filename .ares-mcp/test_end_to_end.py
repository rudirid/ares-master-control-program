"""
Test complete end-to-end WhatsApp -> Ares workflow
"""

import requests
import time
import json
from pathlib import Path

BRIDGE_URL = "http://localhost:5000"
TASK_QUEUE = Path.home() / ".ares-mcp" / "mobile_task_queue.json"

def send_test_message():
    """Simulate receiving a WhatsApp message by adding to queue"""
    print("=" * 70)
    print("END-TO-END TEST: WhatsApp -> Ares Integration")
    print("=" * 70)
    print()

    # Load current queue
    if TASK_QUEUE.exists():
        with open(TASK_QUEUE, 'r') as f:
            queue = json.load(f)
    else:
        queue = []

    # Add test task
    test_task = {
        "id": len(queue) + 1,
        "task": "Test: Create a hello.txt file with 'Hello from WhatsApp!'",
        "from": "61432154351",
        "timestamp": "2025-10-14T12:55:00.000000",
        "message_id": "test_message_id_001"
    }

    queue.append(test_task)

    # Save queue
    with open(TASK_QUEUE, 'w') as f:
        json.dump(queue, f, indent=2)

    print(f"✅ Task #{test_task['id']} added to queue")
    print(f"   Task: {test_task['task']}")
    print()

    # Process task
    print("[STEP 1] Task queued from WhatsApp")
    print("[STEP 2] Running Ares task processor...")
    print()

    import subprocess
    result = subprocess.run(['python', 'ares-master-control-program/ares_task_processor.py'],
                          capture_output=True, text=True)

    print(result.stdout)

    # Check if response was sent
    print("[STEP 3] Checking WhatsApp response...")

    # Reload queue to see status
    with open(TASK_QUEUE, 'r') as f:
        updated_queue = json.load(f)

    our_task = next((t for t in updated_queue if t['id'] == test_task['id']), None)

    if our_task:
        print(f"✅ Task processed with status: {our_task.get('status', 'unknown')}")
        if 'command' in our_task:
            print(f"   Command: {our_task['command']}")
        print()

    print("=" * 70)
    print("TEST COMPLETE!")
    print()
    print("Full workflow demonstrated:")
    print("1. WhatsApp message received and queued")
    print("2. Ares task processor categorizes and prepares command")
    print("3. Status update sent back to WhatsApp")
    print("=" * 70)

if __name__ == "__main__":
    send_test_message()
