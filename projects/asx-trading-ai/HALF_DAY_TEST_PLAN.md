# Half-Day Live Trading Test Plan

**Date:** Tomorrow (Tuesday, October 14, 2025)
**Time:** 10:00 AM - 2:30 PM AEST (4.5 hours)
**Goal:** Collect 40-80 announcements, generate 10-20 recommendations

---

## Why Half-Day Test?

✅ **Optimal trading window** (11AM-3PM = highest liquidity)
✅ **No overnight computer requirement**
✅ **Peak announcement volume**
✅ **Can repeat Wed/Thu/Fri if needed**

---

## Schedule

### 9:45 AM - Setup (15 minutes)

1. Open folder: `C:\Users\riord\asx-trading-ai`
2. Double-click: `start_halfday_test.bat`
3. Watch for "Starting live collection..." message

### 10:00 AM - System Running

**What you'll see:**
```
CYCLE #1 - 2025-10-14 10:00:15
Found 2 announcements
- BHP: Quarterly Production Report (Age: 2.3 min)
- CBA: Trading Update (Age: 1.1 min)

Processing: BHP - Quarterly Production Report
✓ TIME FILTER: Fresh (2.3 min) - strong edge
✓ MATERIALITY: Material (score: 0.85)
✓ TIME-OF-DAY: Optimal window (10:15 AEST)
SENTIMENT: positive (0.68)
CONFIDENCE: 0.72
✓ RECOMMENDATION: BUY BHP @ $43.21
```

**Leave this terminal open!**

### 11:00 AM - First Check (optional)

1. Open NEW terminal/window
2. Navigate to: `C:\Users\riord\asx-trading-ai`
3. Double-click: `check_progress.bat`

Expected:
```
[LIVE STATS] 15-25 announcements | 2-5 recommendations | 15-20% pass rate
```

### 12:30 PM - Mid-Session Check

Run `check_progress.bat` again

Expected:
```
[LIVE STATS] 30-50 announcements | 5-12 recommendations | 15-25% pass rate
```

### 2:30 PM - STOP Collection

1. Go to the ORIGINAL terminal (where system is running)
2. Press `Ctrl + C`
3. Wait for "Session complete" message

### 2:35 PM - Final Results

Run `check_progress.bat` one more time

Expected:
```
[LIVE STATS] 40-80 announcements | 8-20 recommendations | 10-25% pass rate
```

---

## What Happens Next?

### If you get 15+ recommendations:
✅ **Good!** You have enough data to see trends
➡️ **Next:** Repeat test Wed/Thu to get 30-50 total recs
➡️ **Friday:** Run IC analysis

### If you get 5-15 recommendations:
⚠️ **Okay** - Need more sessions
➡️ **Next:** Run 2-3 more half-day sessions this week
➡️ **Target:** 30-50 total recommendations for analysis

### If you get <5 recommendations:
❌ **Too few** - Filters may be too strict
➡️ **Action:** Review filter settings
➡️ **Consider:** Lower confidence threshold from 0.6 to 0.5

---

## Multi-Day Strategy (Recommended)

| Day | Time | Announcements (cumulative) | Recs (cumulative) |
|-----|------|----------------------------|-------------------|
| **Tue** | 10:00-14:30 | 40-80 | 8-20 |
| **Wed** | 10:00-14:30 | 80-160 | 16-40 |
| **Thu** | 10:00-14:30 | 120-240 | 24-60 |
| **Fri** | Analysis | - | 30-60 (target reached!) |

**Advantage:** Data accumulates in database, no need to run continuously

---

## Troubleshooting

### "No announcements detected"
- Check internet connection
- Verify ASX website accessible: https://www.asx.com.au/markets/company-announcements
- ASX may be having technical issues

### "System crashes"
- Check error in terminal
- Restart with same command (data is preserved)
- If repeated crashes, run in test mode: `--test-mode` flag

### "0 recommendations generated"
- This is normal if announcements are low-quality or neutral sentiment
- Check `check_progress.bat` to see how many announcements detected
- If many announcements but 0 recs, filters may be too strict

---

## Files Created for You

✅ `start_halfday_test.bat` - Run this at 10:00 AM tomorrow
✅ `check_progress.bat` - Run anytime to see progress
✅ `HALF_DAY_TEST_PLAN.md` - This file (your guide)

---

## Analysis After Test

After collecting 30+ recommendations across multiple sessions:

```bash
# Calculate returns and IC
python analysis/performance_attribution_live.py

# Generate go-live readiness report
python live_trading/readiness_report.py
```

This tells you:
- **IC (Information Coefficient):** Do signals predict price movements?
- **Win Rate:** What % of recommendations are profitable?
- **Sharpe Ratio:** Risk-adjusted returns
- **GO/NO-GO Decision:** Ready for live trading?

---

## Success Criteria

**Minimum for analysis:**
- 30+ recommendations
- 3+ days of data
- Mix of positive/negative sentiments

**Good performance:**
- IC > 0.05 (clear edge)
- Win Rate > 52%
- Sharpe > 0.5

**Strong performance:**
- IC > 0.10 (strong edge)
- Win Rate > 55%
- Sharpe > 1.0

---

## Tomorrow Morning Checklist

- [ ] 9:45 AM: Open `asx-trading-ai` folder
- [ ] 9:50 AM: Double-click `start_halfday_test.bat`
- [ ] 10:00 AM: Confirm system running
- [ ] 12:30 PM: Check progress
- [ ] 2:30 PM: Press Ctrl+C to stop
- [ ] 2:35 PM: Review results

---

**Good luck! 🚀**

**Questions?** All scripts are ready. Just double-click `start_halfday_test.bat` at 10 AM tomorrow.
