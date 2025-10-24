# Sales Coach - Real-Time AI Sales Assistant

A real-time AI sales coach that listens to live sales calls, absorbs pre-call context, and delivers tactical suggestions during the conversation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: PRE-CALL INTELLIGENCE                             │
│ - CRM data, emails, LinkedIn research, company intel       │
│ - MEDDIC framework tracking                                │
│ - Anticipated objections and strategies                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: REAL-TIME TRANSCRIPTION                           │
│ - Deepgram WebSocket (300ms latency)                       │
│ - Speaker diarization ("You" vs "Prospect")                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: TACTICAL INTELLIGENCE (3-Tier System)             │
│ - Tier 1: Pattern Matching (<100ms) - Instant suggestions  │
│ - Tier 2: Claude Streaming (~800ms) - Complex analysis     │
│ - Tier 3: Deep Context (~2s) - Strategic suggestions       │
└─────────────────────────────────────────────────────────────┘
```

## Current Status: REAL-TIME SYSTEM READY

**Phases 0-2 Complete** - Full real-time system operational

### What Works Now:
- ✅ Pre-call context template system
- ✅ Pattern matcher (instant suggestions <100ms)
- ✅ Claude-powered suggestion generator
- ✅ Sales frameworks (Chris Voss, MEDDIC)
- ✅ **Real-time transcription (Deepgram WebSocket)**
- ✅ **Audio capture (microphone + virtual cable support)**
- ✅ **Web UI for second screen display**
- ✅ **Full system orchestration**

### Ready For:
- ✅ **Live testing with microphone (NOW)**
- ✅ **Google Meet integration (with virtual audio cable)**
- ⏳ Production testing on real sales calls
- ⏳ CRM integration (HubSpot) - Phase 3

## Quick Start (Real-Time System)

### 1. Install Dependencies

```bash
cd ~/.ares/applications/sales-coach
pip install -r requirements.txt
```

### 2. Get API Keys

**Deepgram** (Required): https://deepgram.com (Free tier: $200 credit)
**Anthropic** (Optional): https://console.anthropic.com

```bash
export DEEPGRAM_API_KEY="your_deepgram_key"
export ANTHROPIC_API_KEY="your_anthropic_key"  # Optional
```

### 3. Test Audio Devices

```bash
python run_sales_coach.py --list-devices
```

### 4. Run Live System

```bash
python run_sales_coach.py calls/sample_call_context.yaml
```

### 5. Open UI

Open browser: **http://localhost:5000**

Display on second screen for real-time coaching.

### 6. Speak into Microphone

System will:
- Transcribe in real-time
- Show suggestions as you/prospect speaks
- Track MEDDIC progress
- Display live transcript

**See SETUP.md for detailed instructions including Google Meet integration.**

## File Structure

```
~/.ares/applications/sales-coach/
├── README.md                     # This file
├── SETUP.md                      # Detailed setup guide (Google Meet, APIs, etc.)
├── requirements.txt              # Python dependencies
├── run_sales_coach.py            # Main orchestrator (START HERE)
├── ui_server.py                  # Flask + SocketIO server for UI
├── demo_sales_coach.py           # PoC demo simulation (offline)
├── config/
│   └── sales_frameworks.yaml     # Chris Voss, MEDDIC frameworks
├── templates/
│   ├── pre_call_context_template.yaml  # Template for pre-call prep
│   └── coach_ui.html             # Web UI for second screen
├── calls/
│   └── sample_call_context.yaml  # Sample context (TechCorp call)
└── core/
    ├── pattern_matcher.py        # Tier 1: Instant suggestions (<100ms)
    ├── suggestion_generator.py   # Tier 2/3: Claude-powered suggestions
    ├── realtime_transcriber.py   # Deepgram WebSocket integration
    ├── audio_capture.py          # Audio input (mic/virtual cable)
    └── realtime_coach.py         # Live suggestion engine
```

## Pre-Call Context System

Before each call, fill out the pre-call context template:

```bash
cp templates/pre_call_context_template.yaml calls/my_call_context.yaml
# Edit my_call_context.yaml with prospect info
```

The context includes:
- **Prospect Info**: Name, company, role, recent activity
- **MEDDIC Framework**: Metrics, Economic Buyer, Decision Criteria, etc.
- **Anticipated Objections**: Pre-loaded reframes
- **Strategy**: Primary goal, discovery focus, close plan

## Suggestion Types

### Tier 1: INSTANT (<100ms) - Pattern Matching
- Pricing objections → Qualification questions
- Competitive mentions → Discovery questions
- Buying signals → Closing prompts
- Stalls → Urgency builders

### Tier 2: FAST (~800ms) - Claude Streaming
- Context-aware reframes
- Strategic questions based on MEDDIC gaps
- Chris Voss tactical empathy prompts

### Tier 3: DEEP (~2s) - Complex Analysis
- Multi-turn conversation analysis
- Framework-guided strategy
- Closing orchestration

## Sales Frameworks

### Chris Voss Tactical Empathy (FBI Negotiation)
- **Mirroring**: Repeat last 3 words
- **Labeling**: Name the emotion ("It sounds like...")
- **Calibrated Questions**: "How would...", "What would..."
- **That's Right**: Confirm understanding
- **No-Oriented Questions**: Lower resistance

### MEDDIC Qualification (Enterprise Sales)
- **Metrics**: Quantify the pain/value
- **Economic Buyer**: Find who can say yes
- **Decision Criteria**: How they'll decide
- **Decision Process**: Map the buying steps
- **Identify Pain**: Confirm urgency
- **Champion**: Internal advocate

## Testing Pattern Matcher

```bash
cd core
python pattern_matcher.py
```

Shows instant suggestions for common sales scenarios.

## Testing Suggestion Generator

```bash
cd core
export ANTHROPIC_API_KEY="your_key_here"
python suggestion_generator.py
```

Generates context-aware suggestions using Claude API.

## Example: Pre-Call to Real-Time Flow

**Before Call**:
1. Research prospect (LinkedIn, CRM, emails)
2. Fill out pre-call context (5 minutes)
3. Review anticipated objections
4. Load into system

**During Call**:
- Prospect: "How much does this cost?"
- System (Instant): "Don't answer yet - qualify: 'Great question. To give you accurate pricing, what budget range are you working with?'"
- System (Context-Aware): "Reference their pain: '$X investment vs $750k at risk from slow ramp time - let's discuss ROI...'"

**After Call**:
- Auto-generated summary
- MEDDIC progress updated
- Next steps identified
- CRM auto-update (future)

## Configuration

Edit `config/sales_frameworks.yaml` to:
- Add custom objection handlers
- Define new buying signal patterns
- Customize framework questions
- Add your own playbooks

## Performance Targets

- **Latency**: <2 seconds (prospect stops talking → suggestion appears)
- **Accuracy**: >90% relevant suggestions
- **Usage**: 30%+ suggestions used during call
- **Impact**: 10%+ win rate improvement (measured over 20+ calls)

## Roadmap

### Phase 0: PoC (✅ COMPLETE)
- Pre-call context system
- Pattern matcher (instant suggestions)
- Claude integration (context-aware suggestions)
- Demo simulation

### Phase 1: Real-Time Transcription (Week 2-3)
- Deepgram WebSocket integration
- Speaker diarization
- Live transcript viewer
- Audio capture setup (virtual cable)

### Phase 2: Live Testing (Week 4-5)
- Google Meet audio capture
- Second screen UI
- Real call testing
- Latency optimization

### Phase 3: Context Integration (Week 6-7)
- CRM integration (HubSpot)
- Knowledge base (RAG)
- Playbook library
- Framework tracking

### Phase 4: Production (Week 8-10)
- Desktop app (Electron)
- Mobile responsive
- Usage analytics
- Performance optimization

### Phase 5: Post-Call (Week 11-12)
- Auto-generated summaries
- CRM auto-update
- Action items extraction
- Win/loss analytics

## License

Private - Rio's personal project

## Author

Built with ARES Master Control Program v2.5
