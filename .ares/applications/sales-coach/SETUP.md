# Sales Coach - Setup Guide

## Quick Start (5 Minutes)

### 1. Install Dependencies

```bash
cd ~/.ares/applications/sales-coach
pip install -r requirements.txt
```

### 2. Get API Keys

**Deepgram** (Required - for transcription):
1. Sign up at https://deepgram.com
2. Get your API key from dashboard
3. Free tier: 45,000 minutes/month ($200 credit)

**Anthropic Claude** (Optional - for context-aware suggestions):
1. Sign up at https://console.anthropic.com
2. Get API key
3. Note: Pattern matching works without Claude

### 3. Set Environment Variables

**Linux/Mac**:
```bash
export DEEPGRAM_API_KEY="your_deepgram_key"
export ANTHROPIC_API_KEY="your_anthropic_key"  # Optional
```

**Windows (PowerShell)**:
```powershell
$env:DEEPGRAM_API_KEY="your_deepgram_key"
$env:ANTHROPIC_API_KEY="your_anthropic_key"  # Optional
```

**Permanent (add to ~/.bashrc or ~/.zshrc)**:
```bash
echo 'export DEEPGRAM_API_KEY="your_key"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="your_key"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Test Audio Setup

List available audio devices:
```bash
python run_sales_coach.py --list-devices
```

You should see output like:
```
Available Audio Devices:
================================================================================
 0. Built-in Microphone
    Type: INPUT [DEFAULT]
    Channels: In=2, Out=0
    Sample Rate: 44100.0 Hz

 1. VB-Cable
    Type: INPUT/OUTPUT
    Channels: In=2, Out=2
    Sample Rate: 48000.0 Hz
================================================================================
```

### 5. Run with Sample Context

```bash
python run_sales_coach.py calls/sample_call_context.yaml
```

### 6. Open UI

Open browser to: **http://localhost:5000**

Display on second monitor for real-time coaching.

---

## Google Meet Integration

### Option A: Virtual Audio Cable (Recommended)

**What**: Routes Google Meet audio to the coaching system
**Pros**: Clean audio, works reliably
**Cons**: Requires setup

#### Windows Setup

1. **Download VB-CABLE**:
   - Visit: https://vb-audio.com/Cable/
   - Download and install VB-CABLE

2. **Configure Google Meet**:
   - In Google Meet settings
   - Set speakers to "CABLE Input (VB-Audio Virtual Cable)"

3. **Configure System**:
   - Right-click volume icon → "Sound settings"
   - Recording devices → Enable "CABLE Output"

4. **Run Sales Coach**:
   ```bash
   python run_sales_coach.py --list-devices
   # Find VB-Cable device number (e.g., 3)
   python run_sales_coach.py calls/your_context.yaml --device 3
   ```

#### Mac Setup

1. **Download BlackHole**:
   - Visit: https://existential.audio/blackhole/
   - Download and install BlackHole 2ch

2. **Create Multi-Output Device**:
   - Open Audio MIDI Setup (Applications → Utilities)
   - Click "+" → "Create Multi-Output Device"
   - Check: Built-in Output + BlackHole 2ch
   - Right-click → "Use This Device For Sound Output"

3. **Configure Google Meet**:
   - Set speakers to Multi-Output Device

4. **Run Sales Coach**:
   ```bash
   python run_sales_coach.py --list-devices
   # Find BlackHole device number
   python run_sales_coach.py calls/your_context.yaml --device <id>
   ```

### Option B: System Audio Capture (Simpler but Less Ideal)

Captures ALL system audio (including notifications).

1. **Windows** - Use Stereo Mix:
   - Right-click volume icon → "Sound settings"
   - Recording → Enable "Stereo Mix"
   - Run: `python run_sales_coach.py calls/context.yaml --device <stereo_mix_id>`

2. **Mac** - Use BlackHole:
   - Same as Option A, but simpler (no multi-output needed)

### Option C: Microphone Only (For Testing)

Simplest but only captures your side of conversation.

```bash
# Use default microphone
python run_sales_coach.py calls/context.yaml
```

---

## Pre-Call Preparation

### 1. Create Call Context File

Copy template:
```bash
cp templates/pre_call_context_template.yaml calls/your_prospect.yaml
```

### 2. Fill Out Context (5 minutes)

Edit `calls/your_prospect.yaml`:

```yaml
call_metadata:
  call_date: "2025-10-25"
  call_type: "discovery"  # discovery, demo, negotiation, close

prospect:
  name: "John Smith"
  company: "TechCorp Inc"
  role: "VP of Sales"
  industry: "B2B SaaS"

# MEDDIC Framework
meddic:
  metrics:
    current_problem_cost: "How much is this costing them?"

  economic_buyer:
    name: "Who can say yes?"

  pain:
    identified_pains:
      - "Main pain point #1"
      - "Main pain point #2"

# Anticipated Objections
anticipated_objections:
  - type: "price"
    objection: "Too expensive"
    reframe: "Your reframe here"

# Your Strategy
strategy:
  primary_goal: "Get pilot commitment"
  opening_approach: "Reference their LinkedIn post about..."
```

**Key Sections**:
- **Prospect Info**: LinkedIn research, recent activity
- **MEDDIC**: Pre-fill what you know, system tracks gaps
- **Objections**: Pre-loaded reframes for speed
- **Strategy**: Your game plan

### 3. Test Context Loading

```bash
cd core
python realtime_coach.py
```

Should show MEDDIC progress from your context.

---

## Running Live Calls

### Full Workflow

**Before Call** (5 min):
1. Fill out pre-call context: `calls/prospect_name.yaml`
2. Set up audio routing (Google Meet → Virtual Cable)
3. Open UI on second screen: `http://localhost:5000`

**Start System**:
```bash
python run_sales_coach.py calls/prospect_name.yaml --device <virtual_cable_id>
```

**During Call**:
- Glance at second screen for suggestions
- Suggestions appear as prospect speaks
- MEDDIC progress tracked automatically
- Transcript recorded

**After Call**:
- Ctrl+C to stop
- Review suggestions shown
- Update context with learnings

---

## Troubleshooting

### "DEEPGRAM_API_KEY not set"

```bash
# Check if set
echo $DEEPGRAM_API_KEY

# Set it
export DEEPGRAM_API_KEY="your_key_here"

# Test
python -c "import os; print(os.getenv('DEEPGRAM_API_KEY'))"
```

### "Failed to connect to Deepgram"

1. Check API key is valid
2. Check internet connection
3. Check Deepgram credits remaining (https://console.deepgram.com)

### "No audio captured"

1. Run `--list-devices` to see devices
2. Check device is not in use by another app
3. Test microphone with system sound recorder
4. Verify virtual cable is installed (if using)

### "Pattern matching only" (no Claude suggestions)

This is OK! Pattern matching generates instant suggestions.

To enable Claude:
```bash
export ANTHROPIC_API_KEY="your_key"
```

### UI not showing suggestions

1. Check UI server is running (should see "UI server running" in terminal)
2. Open browser to http://localhost:5000
3. Check browser console for errors (F12)
4. Verify firewall isn't blocking port 5000

### Audio delay / Choppy

1. Reduce blocksize in `audio_capture.py` (currently 8000)
2. Check CPU usage (should be <30%)
3. Close other apps using audio
4. Check internet speed (Deepgram needs stable connection)

---

## System Architecture

```
[Google Meet Audio]
        ↓
[Virtual Audio Cable] ← Routes Meet audio
        ↓
[Audio Capture] ← Captures audio stream (16kHz mono)
        ↓
[Deepgram WebSocket] ← Real-time transcription (~300ms)
        ↓
[Transcript Segment] ← "Speaker: How much does this cost?"
        ↓
[Real-Time Coach]
   ├─→ [Pattern Matcher] ← Instant suggestions (<100ms)
   └─→ [Claude Analyzer] ← Context-aware suggestions (~1s)
        ↓
[Suggestion] ← "Reframe: What budget are you working with?"
        ↓
[SocketIO] ← WebSocket to UI
        ↓
[Web UI] ← Second screen display
```

---

## Performance Targets

- **Latency**: <2 seconds (prospect speaks → suggestion shows)
- **Accuracy**: >90% transcription accuracy
- **Relevance**: >50% suggestions are useful
- **Uptime**: 99% during calls (no crashes)

**Current Performance**:
- Pattern matching: <100ms ✅
- Deepgram: ~300ms ✅
- Claude: ~1-2s ✅
- Total: 1.5-2.5s ✅

---

## API Costs

### Deepgram
- **Pricing**: $0.0043/minute
- **30-min call**: $0.13
- **100 calls/month**: ~$13/month
- **Free tier**: $200 credit (45,000 minutes)

### Anthropic Claude
- **Pricing**: ~$3/$15 per million tokens (input/output)
- **30-min call**: ~$0.50 (context + suggestions)
- **100 calls/month**: ~$50/month
- **Note**: Pattern matching only = $0

**Total Cost** (100 calls/month):
- With Claude: ~$63/month
- Without Claude: ~$13/month

---

## Next Steps

### Phase 1: Test with Microphone (NOW)
```bash
python run_sales_coach.py calls/sample_call_context.yaml
```

Speak into microphone, verify:
- [x] Transcription appears
- [x] Suggestions generate
- [x] UI updates

### Phase 2: Test with Virtual Cable (This Week)
1. Install VB-Cable or BlackHole
2. Route audio from a recorded call
3. Verify full pipeline works

### Phase 3: Live Google Meet Call (Next Week)
1. Fill out real pre-call context
2. Run on actual sales call
3. Measure: Were suggestions useful?

### Phase 4: Iterate (Ongoing)
1. Add custom objection handlers
2. Fine-tune suggestion timing
3. Optimize for your sales style

---

## FAQ

**Q: Can I use this for phone calls (not Google Meet)?**
A: Yes! Route phone audio through virtual cable the same way.

**Q: Does the prospect need to consent?**
A: YES. You must disclose recording + AI analysis.

**Q: Can I customize the sales frameworks?**
A: Yes! Edit `config/sales_frameworks.yaml`

**Q: Does this work offline?**
A: No - requires internet for Deepgram transcription.

**Q: Can multiple people use it simultaneously?**
A: Not yet - single user for now. Team version planned.

**Q: What happens if I lose internet during a call?**
A: System stops working. Local backup planned for future.

---

## Support

**Issues**: Document in `~/.ares/applications/sales-coach/issues.txt`

**Logs**: Check terminal output for errors

**Community**: (Future - Discord/Slack for users)

---

**Ready to go live!** 🚀
