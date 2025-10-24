# Sales Coach Extension - Quick Start (5 Minutes)

Get started with real-time sales coaching in 5 minutes.

## Prerequisites

- Chrome browser
- Python 3.8+
- Sales coach repo cloned

## Installation (2 minutes)

### 1. Create Icons

```bash
cd ~/.ares/applications/sales-coach/extension
pip install Pillow
python create_placeholder_icons.py
```

**Output**:
```
Created: icons/icon16.png
Created: icons/icon48.png
Created: icons/icon128.png
Placeholder icons created successfully!
```

### 2. Load Extension

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable **Developer mode** (toggle top-right)
4. Click **Load unpacked**
5. Select: `~/.ares/applications/sales-coach/extension`

**Verify**: Extension icon appears in toolbar

## First Run (3 minutes)

### 1. Start Backend (Terminal)

```bash
cd ~/.ares/applications/sales-coach
python extension_server.py
```

**Expected output**:
```
================================================================================
SALES COACH EXTENSION SERVER
================================================================================

Server starting on localhost:5001
Waiting for extension connections...
```

Leave this running.

### 2. Join Google Meet

1. Go to https://meet.google.com
2. Start a test meeting (or join existing)
3. Look for **green overlay** in top-right corner

### 3. Start Coaching

1. Click **extension icon** in Chrome toolbar
2. Status should show: "Ready | Backend connected"
3. Click **"Start Coaching"** button

**Expected**:
- Status changes to: "Coaching Active | Listening to call..."
- Overlay shows: "Listening for conversation..."

### 4. Test It

**Speak into microphone**:
- "How much does this cost?"

**Expected** (within 1 second):
- Transcript appears in overlay
- Suggestion appears: "Don't answer yet - qualify: 'What budget range are you working with?'"
- Terminal shows: `[Server] Transcript: How much does this cost?`

### 5. Try More

**Test phrases**:
- "We're already using Gong" → Competitive objection handler
- "I need to think about it" → Timing stall reframe
- "That sounds interesting" → Buying signal prompt
- "How long does implementation take?" → Closing opportunity

Each should generate instant suggestions!

## Success Checklist

- [ ] Extension loaded in Chrome
- [ ] Backend server running (Terminal shows "Waiting...")
- [ ] Green overlay visible in Google Meet
- [ ] Extension popup shows "Ready"
- [ ] Clicking "Start Coaching" works
- [ ] Speaking generates transcripts
- [ ] Suggestions appear in overlay

## Common Issues

### "Not Connected" in Extension Popup

**Fix**: Start backend server
```bash
python extension_server.py
```

### No Overlay in Google Meet

**Fix**: Reload Meet tab (Ctrl+R)

### No Transcripts Appearing

**Fix**:
1. Grant microphone permission (Chrome will ask)
2. Check you're using Chrome (not Firefox/Safari)
3. Speak clearly and loudly

### Extension Not Loading

**Fix**:
1. Go to `chrome://extensions/`
2. Check for errors
3. Click reload icon (circular arrow)

## Next Steps

**Working? Great!** Now:

1. **Create real context**:
   ```bash
   cp templates/pre_call_context_template.yaml calls/my_prospect.yaml
   # Edit with real prospect info
   ```

2. **Use on real call**:
   - Fill out pre-call context (5 min)
   - Join sales call
   - Start coaching
   - Glance at suggestions during call

3. **Customize**:
   - Edit `config/sales_frameworks.yaml` for custom objection handlers
   - Add your playbook patterns

## Tips

- **Latency**: Suggestions appear in ~700ms (instant patterns) to 2s (Claude analysis)
- **Cost**: $0 per call (uses Chrome's free Web Speech API)
- **Privacy**: Runs locally, but Web Speech uses Google servers
- **Accuracy**: Works best with clear audio, quiet environment

## Full Documentation

See `README.md` for:
- Detailed architecture
- Advanced configuration
- ARES agent integration
- Troubleshooting guide
- Roadmap

---

**Ready to coach!** 🚀
