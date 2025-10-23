# 📊 Financial Adviser Dashboard - Quick Start

## 🚀 Launch the Dashboard

**Simply double-click:**
```
LAUNCH_DASHBOARD.bat
```

Or run from command line:
```bash
cd asx-trading-ai
python financial_dashboard.py
```

---

## 📈 What You'll See

### 4 Professional Tabs:

#### 1. 📊 **Overview** - Executive Dashboard
At-a-glance metrics for quick assessment:
- Total announcements collected
- Price-sensitive percentage
- Alpha window capture rate (< 5 min = best)
- Filter pass rate (5-15% = ideal)
- Collection timeline and statistics

#### 2. 📢 **Live Announcements** - Real-Time Feed
Monitor ASX announcements as they arrive:
- Sortable table with 200 most recent
- Filter by: All, Price Sensitive, Fresh, Today
- Color-coded by priority and freshness
- Shows age, type, and processing status

#### 3. 💡 **Recommendations** - Trading Signals
Track all generated recommendations:
- BUY/SELL actions with confidence scores
- Entry prices and sentiment analysis
- Filters that approved each signal
- Summary statistics (total, BUY/SELL count, avg confidence)

#### 4. 📈 **Analytics** - Performance Intelligence
Deep-dive analysis for strategic decisions:
- Time-of-day performance breakdown
- Announcement type distribution
- Filter effectiveness analysis
- System status assessment

---

## 🎯 Key Metrics Explained

### Alpha Window Capture (< 5 min)
**What:** Percentage of announcements caught within 5 minutes
**Target:** 30%+ is excellent
**Why:** Research shows information is priced in within 15-30 minutes

### Filter Pass Rate
**What:** Percentage passing all filters
**Target:** 5-15% (highly selective)
**Why:** Most announcements are noise - selectivity = quality

### Price-Sensitive %
**What:** Announcements flagged by ASX as market-moving
**Target:** 10-20% is normal
**Why:** Indicates data quality and signal potential

---

## 🔄 Auto-Refresh

The dashboard updates every **30 seconds** automatically.

**Toggle:** Checkbox in bottom-right corner
**Manual Refresh:** Click "↻ Refresh" button (top-right)
**Status:** Shows last update timestamp

---

## 📊 Understanding the Data

### Why Zero Recommendations?

**This is NORMAL and EXPECTED:**

✅ **80% of ASX announcements are administrative noise**
- AGM notices
- Appendix filings
- Director interest changes

✅ **Only 10 AM - 2 PM is optimal for trading**
- After-hours = filtered out
- Low liquidity = avoided

✅ **System is highly selective (by design)**
- Waiting for genuine market-moving news
- Prevents overtrading
- Focuses on quality signals

### When to Expect Recommendations:

🎯 **Quarterly earnings reports**
🎯 **Major contract wins**
🎯 **Takeover announcements**
🎯 **Profit guidance updates**
🎯 **During 10 AM - 2 PM window**
🎯 **Price-sensitive flagged by ASX**

---

## 🎨 Color Coding

### Live Announcements Tab:
- **Dark Green** = Price-sensitive announcements
- **Dark Blue** = Ultra-fresh (< 5 min)
- **Dark Purple** = Fresh (5-15 min)
- **Default** = Standard announcements

### Recommendations Tab:
- **Green rows** = BUY signals
- **Red rows** = SELL signals

### Metric Cards:
- **Green** = Excellent performance
- **Yellow** = Warning/moderate
- **Blue** = Standard value
- **Red** = Alert/poor performance

---

## 💼 For Financial Advisers

### Daily Workflow

**Before Market (9:30 AM):**
1. Launch dashboard
2. Review overnight collection
3. Check system is running

**During Market (10 AM - 4 PM):**
1. Monitor Live Announcements tab
2. Watch for price-sensitive + ultra-fresh
3. Review recommendations as generated
4. Check confidence scores (0.7+ = strong signal)

**After Market (4:30 PM):**
1. Review Analytics tab
2. Check filter performance
3. Note any recommendations for follow-up

### Weekly Review

1. Compare total announcements week-over-week
2. Analyze time-of-day patterns
3. Review recommendation quality
4. Assess filter pass rate trends

---

## 📋 Quick Reference

| Metric | Good | Warning | Poor |
|--------|------|---------|------|
| Alpha Window (< 5 min) | 30%+ | 20-30% | <20% |
| Filter Pass Rate | 5-15% | 0-5% or 15-30% | >30% |
| Price-Sensitive % | 15-25% | 10-15% | <10% |
| Optimal Hours % | 40%+ | 30-40% | <30% |

---

## 🔧 Troubleshooting

**Dashboard won't start?**
- Check Python is installed
- Verify database file exists (data/trading.db)
- Try running from command line to see errors

**No data showing?**
- Click manual refresh button
- Check if data collection is running
- Verify date range filters

**Dashboard slow?**
- Turn off auto-refresh temporarily
- Use filters to reduce data load
- Close other resource-intensive applications

---

## 📖 Full Documentation

For detailed information, see:
- **DASHBOARD_USER_GUIDE.md** - Complete feature documentation
- **OCT_14_TEST_RESULTS.md** - Performance results from testing
- **CURRENT_STATUS.md** - System status and workflow

---

## 🎓 Understanding the System

### The 30-90 Second Alpha Window

**Academic research shows:**
- Stock prices react to news within 15-30 minutes
- Most movement happens in first 90 seconds
- Early information = potential trading edge

**System implementation:**
- Detects announcements within seconds
- Processes instantly (< 1 second)
- Generates recommendations < 3 seconds total
- Well within alpha window

### Why High Selectivity?

**Quality over quantity:**
- 80% of announcements = administrative noise
- Only 5-15% should pass filters (by design)
- Reduces false signals
- Prevents overtrading
- Focuses capital on best opportunities

### Information Coefficient (IC)

**After 7-day holding period:**
- Calculate correlation: confidence scores vs actual returns
- IC > 0.05 = Real predictive edge
- IC < 0.05 = No edge (filtering more needed)

**This validates if the system has genuine predictive power**

---

## 🎯 What Makes a Good Signal?

A recommendation is generated when ALL of these align:

✅ **Fresh announcement** (< 30 min old)
✅ **Optimal hours** (10 AM - 2 PM)
✅ **Material news** (high materiality score)
✅ **Strong sentiment** (clearly positive or negative)
✅ **Technical confirmation** (RSI, MACD, MA align)
✅ **Price-sensitive** (bonus points, not required)

**This multi-filter approach ensures only high-quality signals.**

---

## 📊 Current System Status

As of October 15, 2025:

- ✅ **Collection System**: OPERATIONAL
- ✅ **Immediate Processing**: < 1 second
- ✅ **Alpha Window Capture**: 39.3% (EXCELLENT)
- ✅ **Filter System**: WORKING
- ✅ **Live Paper Trader**: RUNNING
- ⏳ **Recommendations**: Waiting for quality signals
- ⏳ **IC Calculation**: After 7-day holding period

**246 announcements collected**
**90 ultra-fresh (< 5 min)**
**36 price-sensitive**
**All processed immediately**

---

## 💡 Pro Tips

1. **Keep dashboard open during market hours** for real-time monitoring
2. **Focus on 10 AM - 2 PM period** for highest quality signals
3. **Don't worry about zero recommendations** - it's normal during quiet periods
4. **Watch for clusters** of price-sensitive + ultra-fresh announcements
5. **Review Analytics tab weekly** to spot patterns
6. **Use filters strategically** to focus on relevant data

---

## 🚀 You're Ready!

The dashboard is designed to be intuitive for financial advisers. Key features:

✅ Professional dark theme (easy on the eyes)
✅ Auto-refresh (stay current without clicking)
✅ Color-coded priorities (spot important signals fast)
✅ Multiple views (overview to deep analysis)
✅ Real-time updates (30-second refresh)

**Just double-click `LAUNCH_DASHBOARD.bat` and you're monitoring the ASX!**

---

**Questions? See DASHBOARD_USER_GUIDE.md for complete documentation.**

**System developed by Claude Code for professional trading analysis.**
