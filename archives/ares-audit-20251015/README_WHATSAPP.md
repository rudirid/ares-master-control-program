# Ares WhatsApp Integration

**Status:** WORKING ✅
**Last Updated:** 2025-10-14
**Version:** 1.0

---

## What This Is

Direct WhatsApp → Ares → Claude Code pipeline for sending tasks from your phone to your development machine.

## Architecture

```
WhatsApp Message
    ↓
Meta Cloud API (webhook)
    ↓
whatsapp_bridge.py (Flask server on localhost:5000)
    ↓
mobile_task_queue.json (task storage)
    ↓
ares_whatsapp_processor.py (fetches & formats tasks)
    ↓
Claude Code (executes with Ares v2.1 protocols)
```

---

## Core Files

### 1. `whatsapp_bridge.py` (243 lines)
**Purpose:** Receives WhatsApp messages via Meta webhook, stores tasks

**Endpoints:**
- `GET /webhook` - Webhook verification
- `POST /webhook` - Receive messages from WhatsApp
- `POST /send` - Send messages back to WhatsApp
- `GET /tasks` - List all queued tasks
- `DELETE /tasks/<id>` - Remove task from queue

**Special Commands:**
- Send "status" → Get bridge status and task count
- Send "list" → List all queued tasks
- Any other message → Added to task queue

### 2. `ares_whatsapp_processor.py` (214 lines)
**Purpose:** Fetches tasks from bridge, formats for Ares execution

**Features:**
- Categorizes tasks (code, research, question, general)
- Formats with Ares v2.1 protocols
- Tracks processed task IDs (no duplicates)
- Outputs formatted prompts to `pending_ares_tasks.txt`

### 3. `start_whatsapp_bridge.bat`
**Purpose:** Launch WhatsApp bridge server

```batch
python C:\Users\riord\.ares-mcp\whatsapp_bridge.py
```

---

## Quick Start

### 1. Start the Bridge
```bash
# Option A: Direct
python .ares-mcp/whatsapp_bridge.py

# Option B: Batch file
.ares-mcp/start_whatsapp_bridge.bat
```

### 2. Send a WhatsApp Message
Send any message to your WhatsApp Business number

### 3. Fetch and Process Tasks
```bash
python .ares-mcp/ares_whatsapp_processor.py
```

### 4. Execute with Ares
Copy/paste prompts from `.ares-mcp/pending_ares_tasks.txt` into Claude Code

---

## Configuration

Located in `whatsapp_bridge.py`:

```python
ACCESS_TOKEN = "EAAIZCTzaF1osBPs..." # Meta access token
PHONE_NUMBER_ID = "810808242121215"   # WhatsApp Business phone ID
VERIFY_TOKEN = "ares_webhook_verify_2024"
AUTHORIZED_NUMBER = "+61432154351"    # Your phone (only this number can send tasks)
```

---

## Task Categories

**Code Tasks** (build, create, implement, fix, debug, refactor)
- Formatted with full Ares development protocols
- References proven-patterns.md
- Checks tech-success-matrix.md

**Research Tasks** (research, investigate, analyze, study)
- Deep investigation mode
- Evidence-based findings
- Clear summary with sources

**Questions** (what, how, why, where, when, ?)
- Context-aware answers
- References decision-causality.md
- Quick, direct responses

**General** (everything else)
- Ares determines best approach
- Applies relevant patterns
- Executes confidently

---

## Files & Directories

```
.ares-mcp/
├── whatsapp_bridge.py              # Flask webhook server
├── ares_whatsapp_processor.py      # Task processor
├── start_whatsapp_bridge.bat       # Launch script
├── mobile_task_queue.json          # Task storage (auto-created)
├── processed_whatsapp_tasks.json   # Processed IDs (auto-created)
├── pending_ares_tasks.txt          # Formatted prompts (auto-created)
└── README_WHATSAPP.md              # This file
```

---

## Workflow Example

1. **You (WhatsApp):** "Build a price alert system for ASX stocks"
2. **Bridge:** Receives message, stores task #4
3. **Processor:** Categorizes as "code", formats with Ares protocols
4. **Claude Code:** Executes with internal validation, applies proven patterns
5. **Result:** System built following your coding DNA

---

## Meta Webhook Configuration

**Webhook URL:** `https://your-ngrok-url.ngrok-free.app/webhook`
**Verify Token:** `ares_webhook_verify_2024`
**Subscribe to:** `messages` field

---

## API Endpoints

### Send Message to WhatsApp
```bash
curl -X POST http://localhost:5000/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Task completed!", "to": "+61432154351"}'
```

### List Tasks
```bash
curl http://localhost:5000/tasks
```

### Delete Task
```bash
curl -X DELETE http://localhost:5000/tasks/1
```

---

## Next Steps

1. ✅ **Working:** WhatsApp → Bridge → Task Queue
2. ✅ **Working:** Processor → Ares-formatted prompts
3. ⏳ **Next:** Automated Ares loop (continuous processing)
4. ⏳ **Next:** Send responses back to WhatsApp automatically
5. ⏳ **Next:** Voice message transcription support

---

## Removed (Bloat Cleanup 2025-10-14)

**Signal Integration:**
- `signal_bridge.py`
- `SIGNAL_SETUP_GUIDE.md`
- `QUICK_FIX_SIGNAL.md`
- `setup_signal_windows.bat`
- `complete_signal_setup.bat`
- `install_signal_cli.ps1`
- `install_signal_desktop.ps1`
- `check_signal.py`
- `link_signal.py`
- `signal_qr.png`
- `transfer_signal_credentials.py`

**Telegram Integration:**
- `mobile_bridge.py`
- `MOBILE_SETUP_GUIDE.md`
- `mobile_task_queue.json` (old version)

**Session Logs:**
- All `*_SETUP.md`, `*_LOG.md`, `*_SUMMARY.md` bloat
- 15+ temporary documentation files

**Test Scripts:**
- `make_qr_simple.py`
- `generate_qr.py`
- `test_send_direct.py`
- `check_webhook_status.py`
- `meta_webhook_automation.py`
- Various temp scripts

**WhatsApp Duplicates:**
- `whatsapp_bridge_working.py` (consolidated into whatsapp_bridge.py)
- `whatsapp_web_bridge.py` (unused Playwright version)
- `ares_task_processor.py` (Telegram version, replaced by ares_whatsapp_processor.py)

---

## Philosophy

**Single Channel:** WhatsApp only (proven, working)
**Minimal Files:** 3 core files + this README
**Zero Bloat:** No Signal, no Telegram, no session logs
**Maximum Efficiency:** Direct pipeline, no intermediate steps

---

**Ares Master Control Program - WhatsApp Integration v1.0**
🤖 Generated with [Claude Code](https://claude.com/claude-code)
