# Business Brain - Quick Start Guide

Get the demo running in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- A web browser

## Step-by-Step Setup

### 1. Install Dependencies

Open terminal/command prompt in the `business-brain` folder:

```bash
pip install -r requirements.txt
```

This installs all required Python packages.

### 2. (Optional) Add Anthropic API Key

For AI-powered features, get a free API key:
- Visit https://console.anthropic.com/
- Create account and get API key
- Add to environment:

**Windows:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Mac/Linux:**
```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Note**: Basic demo works WITHOUT API key using rule-based detection.

### 3. Run the Demo

```bash
python demo.py
```

You'll see:
- Workflow discovery in action
- Automation suggestions with ROI
- AI agents processing invoices and emails
- Results saved to database

### 4. View in Web Dashboard

**Option A - Quick Demo:**
1. Open `src/dashboard/index.html` in your browser
2. Click "Analyze Sample Business Data"
3. See interactive results

**Option B - Full System:**

**Terminal 1:**
```bash
cd src/api
python main.py
```

**Terminal 2:**
Open `src/dashboard/index.html` in browser

The dashboard connects to the API and shows live data.

## What You'll See

### Console Demo Output

```
🧠 BUSINESS BRAIN - Proof of Concept Demo

STEP 1: DISCOVERING WORKFLOW PATTERNS
✓ Discovered 3 workflow patterns

STEP 2: GENERATING AUTOMATION SUGGESTIONS
ROI: 11.9 hours/week = $46,410/year saved

STEP 3: INVOICE PROCESSING AGENT DEMO
✓ Invoice detected and processed!

STEP 4: EMAIL RESPONSE AGENT DEMO
✓ Draft created!

STEP 5: STORING RESULTS IN DATABASE
✓ All data stored
```

### Web Dashboard

- 📊 Statistics cards showing discovered workflows
- 🔍 Detailed workflow patterns found
- 💡 Automation suggestions with ROI calculations
- 📈 Total potential savings

## Troubleshooting

**Error: "No module named 'fastapi'"**
- Run: `pip install -r requirements.txt`

**Error: "Port 8000 already in use"**
- Kill other process using port 8000
- Or change port in `src/api/main.py`

**Dashboard shows no data**
- Make sure API server is running (`python src/api/main.py`)
- Check browser console for errors
- Run `python demo.py` first to populate database

**API key errors**
- Basic features work without API key
- For full AI features, add `ANTHROPIC_API_KEY` to environment
- Or create `.env` file (copy from `.env.example`)

## Next Steps

1. **Customize the demo data** in `demo.py` to match your business
2. **Adjust ROI parameters** in automation suggestions
3. **Test the agents** with your actual emails (copy/paste into demo)
4. **Review the code** to understand how it works
5. **Plan real integrations** (Gmail, Xero, etc.)

## File Structure Quick Reference

```
business-brain/
├── demo.py              ← Start here - run the demo
├── requirements.txt     ← Dependencies to install
├── README.md           ← Full documentation
├── QUICKSTART.md       ← This file
│
├── src/
│   ├── database.py           ← Database layer
│   ├── discovery/            ← Workflow discovery engine
│   ├── agents/               ← AI agents (invoice, email)
│   ├── api/main.py           ← FastAPI backend
│   └── dashboard/index.html  ← Web UI
│
└── data/                ← Database files (created on first run)
```

## Support

If you encounter issues:
1. Check Python version: `python --version` (need 3.11+)
2. Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`
3. Check logs in console output
4. Verify file paths are correct

## What This Demo Proves

✅ **Automatic workflow discovery** - No manual setup required
✅ **AI agents work** - Invoice processing & email drafting functional
✅ **ROI is calculable** - Real savings projections
✅ **System is extensible** - Easy to add more agents
✅ **Database tracks everything** - Learning improves over time

Ready to validate with real businesses!
