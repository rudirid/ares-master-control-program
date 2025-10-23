# Ares Signal Bridge - FREE Encrypted Mobile Setup

Send tasks from your phone to Ares via Signal (100% free, military-grade encryption).

## Why Signal?

✅ **Completely FREE** (no API costs, no message limits)
✅ **End-to-end encrypted** (military-grade, open-source)
✅ **More secure than WhatsApp** (audited by security researchers)
✅ **No Meta/Facebook involvement** (independent nonprofit)
✅ **Open-source protocol** (Signal Protocol)
✅ **Voice messages supported**

**Cost:** $0 forever (no hidden fees, no usage limits)

---

## How It Works

```
Phone (Signal) → signal-cli on your computer → Ares Task Queue → Claude Code CLI
```

**Simple Flow:**
1. Send Signal message from phone: "Build a Python web scraper"
2. Message received by signal-cli on computer
3. Task queued in `.ares-mcp/mobile_task_queue.json`
4. Run `python ares_task_processor.py` to process
5. Ares executes with full validation

---

## Setup (15 minutes)

### Step 1: Install Signal on Phone

1. Download Signal from app store (if not already installed)
2. Register your phone number
3. That's it for phone setup!

### Step 2: Install Java (if not installed)

**Windows:**
```bash
# Download from: https://adoptium.net
# Choose: Latest LTS version
# Install with default settings
```

**Linux:**
```bash
sudo apt update
sudo apt install default-jre
```

**Mac:**
```bash
brew install openjdk
```

Verify:
```bash
java -version
# Should show Java 11 or later
```

### Step 3: Install signal-cli

**Windows:**
1. Download latest release: https://github.com/AsamK/signal-cli/releases
2. Extract to `C:\signal-cli`
3. Add to PATH:
   ```cmd
   setx PATH "%PATH%;C:\signal-cli\bin"
   ```
4. Or use full path: `C:\signal-cli\bin\signal-cli.bat`

**Linux (Ubuntu/Debian):**
```bash
# Official repository
wget -O- https://github.com/AsamK/signal-cli/releases/download/v0.12.8/signal-cli-0.12.8-Linux.tar.gz | tar xz -C /opt
sudo ln -sf /opt/signal-cli-0.12.8/bin/signal-cli /usr/local/bin/
```

**Mac:**
```bash
brew install signal-cli
```

Verify:
```bash
signal-cli --version
# Should show: signal-cli 0.12.x
```

### Step 4: Link Signal Account

```bash
# Start linking process
python .ares-mcp/signal_bridge.py
```

**What happens:**
1. Script asks for your phone number (format: +1234567890)
2. QR code appears in terminal
3. Open Signal on phone → Settings → Linked Devices → Link New Device
4. Scan QR code with phone
5. Done! Bridge is linked

**Your phone number format:**
- Correct: `+12345678901` (+ country code, no spaces)
- Wrong: `+1 234-567-8901` (no spaces or dashes)
- Wrong: `12345678901` (must have +)

### Step 5: Start the Bridge

```bash
python .ares-mcp/signal_bridge.py
```

Output:
```
[OK] Signal Bridge initialized
[OK] Linked phone: +12345678901
[OK] Task queue: C:\Users\riord\.ares-mcp\mobile_task_queue.json

💬 Send messages from Signal on your phone
📱 Commands: 'status', 'list'

Press Ctrl+C to stop
```

---

## Usage

### Send Tasks from Phone

Open Signal, send to yourself:

**Text Message:**
```
Build a Python function to calculate prime numbers
```

**Quick Note:**
```
Note: Try FastAPI instead of Flask for next project
```

**Reminder:**
```
Remind me to update documentation tomorrow
```

**Check Status:**
```
status
```

**List Tasks:**
```
list
```

### Receive Confirmation

You'll get instant reply:
```
✅ Task #1 queued!

Will be executed when terminal comes online.

Reply 'status' or 'list' to check queue.
```

### Process Tasks on Computer

When terminal is online:

```bash
# Process all queued tasks
python .ares-mcp/ares_task_processor.py
```

Output:
```
[PROCESSING] Task #1: Build a Python function to calculate prime numbers...
[CATEGORY] code
[COMMAND] /ares Build a Python function to calculate prime numbers
[READY] Task #1 - Run: /ares Build a Python function to calculate prime numbers

PROCESSING SUMMARY
==================
✅ Completed: 0
🔄 Ready for execution: 1
📋 1 tasks ready for execution
   Run commands from: C:\Users\riord\.ares-mcp\pending_tasks.sh
```

### Execute in Claude Code CLI

```bash
# View pending commands
cat .ares-mcp/pending_tasks.sh

# Or just copy the command shown
/ares Build a Python function to calculate prime numbers
```

---

## Task Categories

Signal bridge uses the same smart categorization:

**Code Tasks:**
- Keywords: build, create, implement, fix, debug, refactor
- Example: "Build a REST API with Express"
- Action: Creates `/ares` command for execution

**Research Tasks:**
- Keywords: research, investigate, analyze, study
- Example: "Research best Node.js testing frameworks"
- Action: Creates `/ares Research:` command

**Notes:**
- Keywords: note, remember, idea, thought
- Example: "Note: Consider using PostgreSQL instead of SQLite"
- Action: Auto-saved to `mobile_notes.txt`

**Reminders:**
- Keywords: remind, don't forget, later
- Example: "Remind me to push changes to GitHub"
- Action: Timestamped in `reminders.txt`

---

## Security Features

**Signal Protocol (Military-Grade):**
- End-to-end encryption (messages encrypted on your phone, decrypted on your computer)
- Forward secrecy (past messages safe even if keys compromised)
- Metadata minimization (Signal doesn't know who you're messaging)
- Open-source (audited by security researchers globally)

**Bridge Security:**
- Only your linked account can send tasks
- Auto-authorizes first sender (you)
- All data stored locally (no cloud)
- signal-cli runs locally (no third-party servers)

**Used by:**
- Edward Snowden (security expert)
- EU Commission
- US Senate staff
- Security researchers worldwide

---

## Comparison

| Feature | Signal | WhatsApp | Telegram |
|---------|--------|----------|----------|
| Cost | FREE | $0.005/msg after 1,000 | FREE (bot only) |
| Encryption | E2E (open-source) | E2E (closed-source) | Not E2E by default |
| Message limits | Unlimited | 1,000/month free | Unlimited |
| Voice messages | ✓ | ✓ | ✓ |
| Setup complexity | Medium | Medium | Easy |
| Privacy | Best | Good | Fair |
| API costs | $0 | ~$5/month | $0 |
| Open-source | ✓ | ✗ | ✗ |

**Recommendation:** Signal for best security + zero cost

---

## Example Workflow

**Morning (on phone):**
1. Open Signal
2. Text yourself: "Build a task manager CLI with priority sorting"
3. Voice: "Research best practices for async Python"
4. Text: "Note: Consider adding Docker support"

**At computer (when online):**
1. `python signal_bridge.py` (if not already running)
2. `python ares_task_processor.py`
3. Check `cat .ares-mcp/pending_tasks.sh`
4. Execute Ares commands in Claude Code CLI

**Result:**
- Task manager built with Ares validation
- Research completed with evidence
- Note saved for reference
- All with zero API costs

---

## Troubleshooting

### "signal-cli not found"
**Solution:**
```bash
# Verify installation
signal-cli --version

# If not found, check PATH
echo $PATH  # Linux/Mac
echo %PATH%  # Windows

# Or use full path
/usr/local/bin/signal-cli --version  # Linux/Mac
C:\signal-cli\bin\signal-cli.bat --version  # Windows
```

### "Failed to link account"
**Solution:**
- Ensure phone number format: `+1234567890` (no spaces)
- Check internet connection on both devices
- Make sure Signal is updated on phone
- Try scanning QR code again

### "No messages received"
**Solution:**
- Check if signal-cli is running: `python signal_bridge.py`
- Verify you're sending from linked phone
- Check phone number matches authorized number
- Look at logs for errors

### "Java not found"
**Solution:**
```bash
# Install Java
# Windows: https://adoptium.net
# Linux: sudo apt install default-jre
# Mac: brew install openjdk

# Verify
java -version
```

---

## Running 24/7 (Optional)

To keep bridge always running:

**Windows (Task Scheduler):**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: At startup
4. Action: Start program
   - Program: `python`
   - Arguments: `C:\Users\riord\.ares-mcp\signal_bridge.py`
   - Start in: `C:\Users\riord\.ares-mcp`

**Linux (systemd):**
```bash
# Create service file
sudo nano /etc/systemd/system/ares-signal.service

# Add:
[Unit]
Description=Ares Signal Bridge
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/your_username/.ares-mcp
ExecStart=/usr/bin/python3 signal_bridge.py
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ares-signal
sudo systemctl start ares-signal
```

**Mac (launchd):**
```bash
# Create plist file
nano ~/Library/LaunchAgents/com.ares.signal.plist

# Add configuration (similar to Linux systemd)
# Load: launchctl load ~/Library/LaunchAgents/com.ares.signal.plist
```

---

## Files Structure

```
.ares-mcp/
├── signal_bridge.py            # Main bridge (polls Signal)
├── ares_task_processor.py      # Task processor
├── signal_config.json          # Phone number and auth (auto-created)
├── mobile_task_queue.json      # Task queue (auto-created)
├── pending_tasks.sh            # Ready-to-execute Ares commands
├── mobile_notes.txt            # Quick notes
├── reminders.txt               # Timestamped reminders
└── processed_tasks.log         # Processing history
```

---

## Advanced: Voice Transcription

For voice message transcription, install OpenAI Whisper:

```bash
pip install openai-whisper

# Or use OpenAI API
pip install openai
export OPENAI_API_KEY="your_key"
```

Update `signal_bridge.py` to add transcription support.

---

## Quick Start Summary

```bash
# 1. Install Java
java -version

# 2. Install signal-cli
# (platform-specific, see Step 3 above)

# 3. Link account
python .ares-mcp/signal_bridge.py
# Scan QR code with phone

# 4. Start bridge
python .ares-mcp/signal_bridge.py

# 5. Send test message from phone

# 6. Process tasks
python .ares-mcp/ares_task_processor.py
```

---

## Why Signal Over Alternatives?

**Security:**
- Used by Edward Snowden, EU Commission, security experts
- Fully open-source (code audited by researchers)
- Zero metadata collection
- Perfect forward secrecy

**Privacy:**
- Nonprofit foundation (no ads, no data selling)
- No phone number visible to Signal
- Minimal data retention
- Sealed sender (hides sender from Signal servers)

**Cost:**
- $0 forever
- No usage limits
- No subscription fees
- No API costs

**Recommended by:**
- Electronic Frontier Foundation (EFF)
- Bruce Schneier (cryptographer)
- Edward Snowden (whistleblower)
- Privacy International

---

**Ares Signal Bridge - FREE • Secure • Unlimited** 🔐

Zero cost, maximum security, unlimited messages.
