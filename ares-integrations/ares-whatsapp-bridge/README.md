# Ares WhatsApp Bridge

**Two-way WhatsApp integration with Claude Code AI assistant**

Send tasks from your phone via WhatsApp, get AI-powered responses and status updates back.

---

## Features

- **Send tasks via WhatsApp** - Text from your phone to queue AI tasks
- **Automatic categorization** - Code, research, notes, reminders
- **Status updates** - Get responses back in WhatsApp
- **Permanent token** - Never-expiring Meta API access
- **Development mode ready** - Works with personal number
- **Production scalable** - Upgrade to 1K-unlimited messages/day

---

## Quick Start

### 1. Prerequisites

```bash
pip install flask requests
```

### 2. Configuration

Edit `whatsapp_bridge.py` with your credentials:

```python
ACCESS_TOKEN = "your_meta_access_token"
PHONE_NUMBER_ID = "your_phone_number_id"
AUTHORIZED_NUMBER = "+your_phone_number"
```

### 3. Start the Bridge

```bash
python whatsapp_bridge.py
```

### 4. Expose with ngrok (for webhook)

```bash
ngrok http 5000
```

Configure webhook in Meta Developer Console with ngrok URL.

### 5. Process Tasks

```bash
python ares_task_processor.py
```

---

## Architecture

```
WhatsApp Message
    ↓
Meta Servers
    ↓
Webhook (ngrok → Flask)
    ↓
Task Queue (mobile_task_queue.json)
    ↓
Ares Task Processor
    ↓
Categorize & Execute
    ↓
Status Response → WhatsApp
```

---

## Files

| File | Purpose |
|------|---------|
| `whatsapp_bridge.py` | Flask webhook server, receives WhatsApp messages |
| `ares_task_processor.py` | Processes queued tasks, sends responses |
| `test_whatsapp_send.py` | Test sending messages |
| `send_test_template.py` | Test template messages |
| `WHATSAPP_INTEGRATION_COMPLETE.md` | Full setup documentation |

---

## Setup Guide

### Get Meta WhatsApp API Access

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create app → Business → WhatsApp
3. Get Phone Number ID and Access Token

### Create Permanent Token

1. Go to Business Settings → System Users
2. Create System User (Admin role)
3. Assign app with Full Control
4. Generate Token → Set to **Never Expire**
5. Copy token immediately

### Configure Webhook

1. In Meta Developer Console → WhatsApp → Configuration
2. Edit webhook URL: `https://your-ngrok-url.ngrok.io/webhook`
3. Verify token: `ares_webhook_verify_2024`
4. Subscribe to `messages` events

---

## Usage

### Send from WhatsApp

Text anything to your WhatsApp Business number:

```
Create a hello.txt file with "Hello World"
```

### Special Commands

- `status` - Get bridge status
- `list` - Show queued tasks

### Task Categories

**Code tasks:**
```
Build a login page
Fix the authentication bug
Create a REST API
```

**Research tasks:**
```
Research Next.js vs React
Investigate database options
```

**Notes:**
```
Note: Remember to update docs
Idea: Add dark mode
```

**Reminders:**
```
Remind me to deploy tomorrow
Don't forget to backup database
```

---

## Development vs Production

### Development Mode (Current)

- ✅ Free messages
- ✅ Personal number works
- ✅ 5 test recipients
- ❌ Template messages only
- ❌ Limited features

### Production Mode (After Business Verification)

- ✅ Custom messages
- ✅ 1,000+ messages/day
- ✅ Scales to unlimited
- ✅ All message types
- ✅ Rich media support

---

## API Endpoints

### `/webhook` (GET)
Webhook verification from Meta

### `/webhook` (POST)
Receive incoming WhatsApp messages

### `/send` (POST)
Send message to WhatsApp
```json
{
  "message": "Task completed!",
  "to": "+61432154351"
}
```

### `/tasks` (GET)
Get all queued tasks

### `/tasks/<id>` (DELETE)
Remove task from queue

---

## Task Processor

Processes tasks automatically:

```bash
python ares_task_processor.py
```

Output:
```
[PROCESSING] Task #1: Create hello.txt file
[CATEGORY] code
[COMMAND] /ares Create hello.txt file
[READY] Task #1 - Command ready
[OK] Added to pending_tasks.sh
```

Commands saved to `.ares-mcp/pending_tasks.sh` for execution.

---

## Configuration Options

### Environment Variables

```bash
export WHATSAPP_BRIDGE_URL="http://localhost:5000"
```

### Custom Queue Location

```python
TASK_QUEUE_FILE = Path("/custom/path/mobile_task_queue.json")
```

---

## Troubleshooting

### Token Expired
Use permanent System User token (see setup guide)

### Webhook Not Receiving
- Check ngrok tunnel is active
- Verify webhook URL in Meta console
- Check verify token matches

### Messages Not Sending
- Verify access token is valid
- Check phone number ID is correct
- Ensure recipient is in test numbers (dev mode)

### Status 403 Forbidden
- Add recipient to test phone numbers in Meta console

---

## Security

- **Never commit tokens** - Add to `.gitignore`
- **Use environment variables** for production
- **Verify webhook requests** from Meta servers
- **Authorize only specific numbers**

### Example .env

```bash
WHATSAPP_ACCESS_TOKEN=your_token_here
WHATSAPP_PHONE_ID=your_phone_id
AUTHORIZED_NUMBER=+61432154351
VERIFY_TOKEN=ares_webhook_verify_2024
```

---

## Roadmap

- [ ] Automatic task processing (continuous mode)
- [ ] Rich media support (images, documents)
- [ ] Multiple user support
- [ ] Task scheduling
- [ ] Response templates
- [ ] Error retry logic
- [ ] Logging dashboard

---

## Requirements

```txt
flask>=2.3.0
requests>=2.31.0
```

---

## License

MIT License - Use freely for personal or commercial projects

---

## Support

For issues or questions:
- Check `WHATSAPP_INTEGRATION_COMPLETE.md` for detailed setup
- Review Meta's [WhatsApp Business API documentation](https://developers.facebook.com/docs/whatsapp/)

---

## Credits

Built with:
- Meta WhatsApp Business Cloud API
- Flask web framework
- Claude Code AI assistant

---

**Status:** Operational ✅
**Last Updated:** October 14, 2025
**Version:** 1.0.0
