# Ares Mobile Bridge - Setup Guide

Send tasks from your phone to Ares via WhatsApp (end-to-end encrypted).

## How It Works

```
Phone (WhatsApp) → Meta Cloud API → Your Computer (Bridge) → Ares Task Queue → Claude Code CLI
```

**Flow:**
1. Send WhatsApp message/voice note from phone
2. Message queued in `.ares-mcp/mobile_task_queue.json`
3. When terminal online, run `python ares_task_processor.py`
4. Tasks auto-categorized and executed by Ares

---

## Setup (20 minutes)

### Step 1: Create WhatsApp Business App

1. Go to https://developers.facebook.com
2. Click "My Apps" → "Create App"
3. Select "Business" type
4. Fill in app details:
   - App Name: "Ares Mobile Bridge"
   - Contact Email: your@email.com
5. Click "Create App"

### Step 2: Add WhatsApp Product

1. In app dashboard, click "Add Product"
2. Find "WhatsApp" → Click "Set Up"
3. You'll see "API Setup" page

### Step 3: Get Your Credentials

On the "API Setup" page, you'll see:

**Temporary Access Token** (valid 24 hours - we'll extend this):
- Copy the token shown
- This is your `WHATSAPP_ACCESS_TOKEN`

**Phone Number ID:**
- Look for "Phone number ID"
- Copy the number
- This is your `WHATSAPP_PHONE_NUMBER_ID`

**Test Number:**
- Meta provides a test number
- You'll send messages FROM your phone TO this number

### Step 4: Generate Permanent Access Token

1. Go to "System Users" in Business Settings
2. Create new system user: "Ares Bridge"
3. Assign WhatsApp permissions
4. Generate token → Select "Never Expire"
5. Copy the permanent token
6. Replace temporary token with this

### Step 5: Add Your Phone Number

1. In WhatsApp API Setup, find "To" field
2. Click "Manage phone number list"
3. Add your phone number (format: +1234567890)
4. You'll receive verification code on WhatsApp
5. Enter code to verify

### Step 6: Configure Webhook

1. On WhatsApp API Setup page, find "Webhook" section
2. Click "Configure"
3. You need a public URL - use **ngrok**:

   ```bash
   # Install ngrok: https://ngrok.com/download
   ngrok http 5000
   ```

4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
5. In Meta dashboard:
   - Callback URL: `https://abc123.ngrok.io/webhook`
   - Verify Token: `ares_webhook_token` (or create your own)
   - Subscribe to: `messages`

### Step 7: Set Environment Variables

**Windows:**
```cmd
setx WHATSAPP_PHONE_NUMBER_ID "your_phone_number_id_here"
setx WHATSAPP_ACCESS_TOKEN "your_permanent_token_here"
setx YOUR_PHONE_NUMBER "1234567890"
setx WEBHOOK_VERIFY_TOKEN "ares_webhook_token"
setx OPENAI_API_KEY "your_openai_key_here"
```

**Linux/Mac:**
```bash
export WHATSAPP_PHONE_NUMBER_ID="your_phone_number_id_here"
export WHATSAPP_ACCESS_TOKEN="your_permanent_token_here"
export YOUR_PHONE_NUMBER="1234567890"
export WEBHOOK_VERIFY_TOKEN="ares_webhook_token"
export OPENAI_API_KEY="your_openai_key_here"
```

Or create `.env` file in `.ares-mcp/`:
```
WHATSAPP_PHONE_NUMBER_ID=your_id
WHATSAPP_ACCESS_TOKEN=your_token
YOUR_PHONE_NUMBER=1234567890
WEBHOOK_VERIFY_TOKEN=ares_webhook_token
OPENAI_API_KEY=your_key
```

### Step 8: Install Dependencies

```bash
pip install flask requests openai python-dotenv
```

### Step 9: Start the Bridge

**Terminal 1 - Start ngrok:**
```bash
ngrok http 5000
```

**Terminal 2 - Start WhatsApp bridge:**
```bash
python .ares-mcp/whatsapp_bridge.py
```

---

## Usage

### Send Tasks from Phone

**Text Message:**
```
Build a Python function to calculate Fibonacci numbers
```

**Voice Message:**
- Record voice note in WhatsApp
- Automatically transcribed and queued

**Check Status:**
```
status
```

### Process Tasks on Computer

When terminal comes online:

```bash
# Process queued tasks
python .ares-mcp/ares_task_processor.py
```

This will:
1. Categorize each task (code/research/note/reminder)
2. Auto-execute notes and reminders
3. Create Ares commands for code/research tasks
4. Save commands to `pending_tasks.sh`

### Execute Ares Commands

```bash
# View pending commands
cat .ares-mcp/pending_tasks.sh

# Execute in Claude Code CLI
# Copy/paste commands or source the file
```

---

## Task Categories

**Code Tasks:**
- Keywords: build, create, implement, fix, debug, refactor
- Action: Creates `/ares` command
- Example: "Build a REST API with Express"

**Research Tasks:**
- Keywords: research, investigate, analyze, study
- Action: Creates `/ares Research:` command
- Example: "Research best practices for async Python"

**Notes:**
- Keywords: note, remember, idea, thought
- Action: Appends to `mobile_notes.txt`
- Example: "Note: Try Redis for caching"

**Reminders:**
- Keywords: remind, don't forget, later, tomorrow
- Action: Appends to `reminders.txt` with timestamp
- Example: "Remind me to update documentation"

---

## Security

**WhatsApp Encryption:**
- End-to-end encrypted messages
- Meta Cloud API (official)
- Your phone number is the only authorized sender

**Best Practices:**
1. Use permanent access token (not temporary)
2. Keep tokens in environment variables (not code)
3. Only authorize your phone number
4. Use ngrok for local development only
5. Deploy to proper server for production

---

## Troubleshooting

### "Webhook verification failed"
- Check `WEBHOOK_VERIFY_TOKEN` matches in code and Meta dashboard
- Ensure ngrok URL is correct and accessible

### "Unauthorized number"
- Verify `YOUR_PHONE_NUMBER` format: 1234567890 (no + or spaces)
- Check number is added and verified in Meta dashboard

### "Failed to download audio"
- Ensure `OPENAI_API_KEY` is set for transcription
- Check audio file size (Meta limits apply)

### "No messages received"
- Verify webhook is subscribed to "messages"
- Check ngrok is running
- Look at Flask logs for errors

---

## Production Deployment

For 24/7 operation:

1. **Deploy to Cloud Server:**
   - AWS EC2, DigitalOcean, or similar
   - Install Python and dependencies
   - Use systemd or PM2 to keep running

2. **Configure Firewall:**
   - Allow inbound on port 5000 (or your choice)
   - Use HTTPS (Let's Encrypt)

3. **Update Webhook URL:**
   - Point to your server: `https://your-server.com/webhook`

4. **Monitor:**
   - Check logs regularly
   - Set up alerts for failures

---

## Cost

**Free Tier (Meta WhatsApp Cloud API):**
- 1,000 messages/month free
- Additional: $0.005-0.015 per message (varies by country)

**OpenAI Whisper API (Voice Transcription):**
- $0.006 per minute of audio

**Total:** ~$0-5/month for normal usage

---

## Example Workflow

**Morning:**
1. Open WhatsApp on phone
2. Send: "Build a task manager CLI tool with Python"
3. Send voice note: "Research best database for small projects"

**At Computer:**
1. Open terminal
2. Run: `python .ares-mcp/ares_task_processor.py`
3. Check: `cat .ares-mcp/pending_tasks.sh`
4. Execute: Copy Ares commands into Claude Code CLI

**Result:**
- Ares builds task manager
- Ares researches databases
- Both with full validation and evidence

---

## Files Created

```
.ares-mcp/
├── whatsapp_bridge.py          # WhatsApp webhook receiver
├── ares_task_processor.py      # Task processor with Ares integration
├── mobile_task_queue.json      # Task queue (auto-created)
├── pending_tasks.sh            # Ready-to-execute Ares commands
├── mobile_notes.txt            # Quick notes from phone
├── reminders.txt               # Timestamped reminders
├── processed_tasks.log         # Processing history
└── voice_*.ogg                 # Downloaded voice messages
```

---

## Next Steps

1. Complete setup (Steps 1-9 above)
2. Send test message from phone
3. Process queue on computer
4. Integrate with daily workflow

**Ares Mobile Bridge v1.0 - Phone to Terminal, Encrypted** 🔐
