# Sales Coach Chrome Extension

Real-time AI sales coaching during Google Meet calls. Get tactical suggestions powered by Chris Voss tactical empathy and MEDDIC framework - instantly, as the call happens.

## Features

- **Real-Time Transcription**: Uses Chrome's Web Speech API (free, built-in)
- **Instant Suggestions**: Pattern matching responds in <1 second
- **Context-Aware Coaching**: Loads pre-call context (MEDDIC, objections, strategy)
- **Overlay UI**: Non-intrusive panel injected into Google Meet
- **MEDDIC Tracking**: Visual progress tracking during call
- **Zero Cost**: No transcription APIs needed (uses Chrome's built-in recognition)

## Installation

### 1. Create Placeholder Icons

**Option A - Use Python script**:
```bash
cd ~/.ares/applications/sales-coach/extension
pip install Pillow
python create_placeholder_icons.py
```

**Option B - Manual** (if no Python/Pillow):
See `ICON_INSTRUCTIONS.txt` for manual icon creation.

### 2. Load Extension in Chrome

1. Open Chrome
2. Go to `chrome://extensions/`
3. Enable "Developer mode" (toggle in top right)
4. Click "Load unpacked"
5. Select folder: `~/.ares/applications/sales-coach/extension`
6. Extension should appear with green "SC" icon

### 3. Verify Installation

- Extension icon should appear in Chrome toolbar
- Click icon → Popup should open
- Status should show "Not Connected" (backend not running yet)

## Usage

### Step 1: Start Backend Server

**Terminal 1**:
```bash
cd ~/.ares/applications/sales-coach
python extension_server.py
```

You should see:
```
================================================================================
SALES COACH EXTENSION SERVER
================================================================================

Server starting on localhost:5001
Extension should connect to: ws://localhost:5001/extension

Waiting for extension connections...
```

### Step 2: Prepare Pre-Call Context

Fill out context file for your call:

```bash
cp templates/pre_call_context_template.yaml calls/my_call.yaml
# Edit my_call.yaml with prospect info
```

**Quick version** (use sample):
- Extension defaults to `sample_call_context.yaml`
- Fine for testing

### Step 3: Join Google Meet

1. Go to https://meet.google.com
2. Join or start a meeting
3. Wait for Meet to fully load

The extension will:
- Auto-detect Google Meet
- Inject overlay (top-right corner)
- Show "Ready" status

### Step 4: Start Coaching

**Option A - Via Extension Popup**:
1. Click extension icon in toolbar
2. Status should show "Ready" (backend connected)
3. Select context file (or use default)
4. Click "Start Coaching"

**Option B - Auto-start** (future):
- Extension can auto-start when call begins
- Configure in settings (coming soon)

### Step 5: During Call

**What happens**:
- You/prospect speaks
- Web Speech API transcribes (<500ms)
- Pattern matcher generates instant suggestions
- Suggestions appear in overlay (color-coded by urgency)

**Overlay shows**:
- **Suggestions** (top) - Tactical prompts, color-coded
- **Live Transcript** (middle) - Real-time transcript
- **MEDDIC Progress** (bottom) - Framework completion

**Interacting with overlay**:
- Drag header to reposition
- Click "_" to minimize
- Click "×" to hide (doesn't stop coaching)
- Expand/collapse sections

### Step 6: After Call

1. Click extension icon → "Stop Coaching"
2. Or auto-stops when call ends
3. Backend shows summary in terminal

## Overlay UI

```
┌─────────────────────────────┐
│ SALES COACH            _ × │
├─────────────────────────────┤
│ ● Coaching Active           │
│   Listening to call...      │
├─────────────────────────────┤
│ TACTICAL SUGGESTIONS    3   │
│                             │
│ ┌─────────────────────────┐ │
│ │ [HIGH] question 90%     │ │
│ │ Don't answer yet -      │ │
│ │ qualify: "What budget..." │
│ │                          │ │
│ │ Chris Voss | pattern    │ │
│ └─────────────────────────┘ │
│                             │
│ ┌─────────────────────────┐ │
│ │ [MEDIUM] reframe 85%    │ │
│ │ It sounds like budget is │ │
│ │ a key concern...        │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ LIVE TRANSCRIPT          ▼  │
│ How much does this cost?    │
│ We're already using Gong... │
├─────────────────────────────┤
│ MEDDIC PROGRESS       67%   │
│ [X] Metrics                 │
│ [X] Economic Buyer          │
│ [X] Decision Criteria       │
│ [X] Decision Process        │
│ [ ] Pain                    │
│ [ ] Champion                │
│ ████████░░░░                │
└─────────────────────────────┘
```

## Configuration

### Context Files

Located in: `~/.ares/applications/sales-coach/calls/`

**Sample contexts**:
- `sample_call_context.yaml` - Demo call (TechCorp)
- `pre_call_context_template.yaml` - Blank template

**Create custom**:
```bash
cp templates/pre_call_context_template.yaml calls/prospect_name.yaml
# Edit with:
# - Prospect info
# - MEDDIC data
# - Anticipated objections
# - Call strategy
```

### Extension Settings (Future)

Coming soon:
- Auto-start on call begin
- Custom context file selection
- Suggestion urgency filters
- UI theme/position preferences

## How It Works

### Architecture

```
[Google Meet Audio]
        ↓
[Web Speech API] (Chrome built-in)
        ↓ (~500ms)
[content.js] (extension content script)
        ↓
[background.js] (service worker)
        ↓ (WebSocket)
[extension_server.py] (Python backend)
        ↓
[RealtimeCoach]
   ├→ PatternMatcher (<100ms)
   └→ Claude (optional, ~1s)
        ↓
[Suggestion]
        ↓ (WebSocket)
[Extension Overlay] (in Meet tab)
```

**Total Latency**: 600ms - 2s (under 3 second target ✅)

### Component Roles

**content.js**:
- Injected into Google Meet page
- Captures audio via Web Speech API
- Creates overlay UI
- Displays suggestions

**background.js**:
- Service worker (runs persistently)
- Manages WebSocket to Python backend
- Coordinates messaging

**extension_server.py**:
- Python WebSocket server
- Loads pre-call context
- Generates suggestions (pattern matching + Claude)
- Broadcasts to extension

**popup.html/js**:
- Extension popup UI
- Start/stop controls
- Status display

## Troubleshooting

### Extension Not Loading

**Check**:
1. `chrome://extensions/` → Extension appears?
2. Developer mode enabled?
3. No errors shown?

**Fix**:
- Reload extension (circular arrow icon)
- Check browser console (F12)
- Verify manifest.json is valid

### Status Shows "Not Connected"

**Problem**: Backend server not running or not reachable

**Check**:
1. Terminal shows "Server starting on localhost:5001"?
2. Firewall blocking port 5001?
3. Another process using port 5001?

**Fix**:
```bash
# Start server
python extension_server.py

# Or use different port
python extension_server.py --port 5002
# Then update extension code to match
```

### No Suggestions Appearing

**Check**:
1. Coaching active? (extension popup shows "Coaching Active")
2. Backend server receiving transcripts? (terminal shows "Transcript: ...")
3. Speaking clearly? (Web Speech API requires clear audio)

**Fix**:
- Click extension → "Stop" → "Start" (restart)
- Check browser console for errors (F12)
- Verify Web Speech API is working:
  - Try dictation in Google Docs
  - If that doesn't work, Web Speech API isn't available

### Transcription Not Working

**Problem**: Web Speech API not capturing audio

**Check**:
1. Microphone permissions granted? (Chrome should ask)
2. Chrome browser (not Firefox/Safari - they don't have Web Speech API)
3. Internet connection? (Web Speech uses Google servers)

**Fix**:
- Grant microphone permission: `chrome://settings/content/microphone`
- Reload Meet tab
- Restart browser

### Suggestions Too Slow

**Check**:
1. Latency shown in terminal?
2. Claude API enabled? (optional, adds 1-2s)

**Optimize**:
- Disable Claude (pattern matching only): Remove `ANTHROPIC_API_KEY`
- Use faster internet connection
- Close resource-intensive apps

### Overlay Not Appearing

**Check**:
1. On Google Meet page? (only injects on meet.google.com)
2. Extension loaded?
3. Browser console shows errors?

**Fix**:
- Reload Meet tab
- Reload extension
- Check `content.js` console errors

## Advanced

### Using ARES Agent Orchestration

Enable context-aware strategic suggestions:

**Set API key**:
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

**Restart server**:
```bash
python extension_server.py
```

Now complex questions trigger ARES agent routing:
- Simple objections → Pattern matching (instant)
- Complex strategy → ARES agent (2s, but higher quality)

### Custom Frameworks

Edit: `~/.ares/applications/sales-coach/config/sales_frameworks.yaml`

Add your own:
- Objection handlers
- Buying signal patterns
- Discovery questions
- Closing techniques

### Integration with ARES Master Control

Extension runs as ARES-managed application:

```bash
# From ARES
python ares_app_manager.py start sales-coach

# Or standalone
python extension_server.py
```

## Limitations

1. **Chrome Only**: Web Speech API is Chrome/Edge only (not Firefox/Safari)
2. **Requires Internet**: Web Speech uses Google servers
3. **No Speaker Diarization**: Can't distinguish you vs prospect automatically (assumes all speech is prospect)
4. **Meet Only**: Currently only Google Meet (Zoom/Teams coming later)
5. **English Only**: Web Speech API configured for en-US (can change in code)

## Roadmap

**v1.1** (Next):
- Auto-start on call begin
- Settings page (UI theme, shortcuts)
- Custom context file picker
- Offline mode (using Whisper instead of Web Speech)

**v1.2**:
- Speaker diarization (you vs prospect)
- Zoom/Teams support
- Post-call summary export
- CRM integration (HubSpot)

**v1.3**:
- Team version (shared playbooks)
- Analytics dashboard
- Mobile companion app
- Voice commands ("show objection handlers")

## Support

**Issues**: Document in `~/.ares/applications/sales-coach/extension/issues.txt`

**Logs**:
- Extension: Chrome DevTools Console (F12)
- Backend: Terminal output

**Community**: (Future - Discord/Slack)

## License

Private - Rio's personal project

---

**Built with ARES Master Control Program**
**Speed: <3 seconds | Cost: $0 per call | Privacy: Local-first**
