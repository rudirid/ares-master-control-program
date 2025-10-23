# ASX Trading AI - Financial Dashboard User Guide

## 🎯 Overview

The Financial Dashboard is a professional-grade GUI designed for financial advisers to monitor and analyze the ASX Trading AI system's performance in real-time.

## 🚀 Getting Started

### Quick Launch

**Option 1: Double-click the batch file**
```
LAUNCH_DASHBOARD.bat
```

**Option 2: Run from command line**
```bash
cd asx-trading-ai
python financial_dashboard.py
```

The dashboard will automatically connect to your database and begin loading data.

---

## 📊 Dashboard Features

### 1. **Overview Tab** - Executive Summary

The Overview tab provides at-a-glance metrics that matter most to financial advisers:

#### Key Metrics Cards

**Collection Performance**
- **Total Announcements**: Total number of announcements collected since start
- **Price Sensitive**: Count and percentage of high-priority announcements
- **Unique Companies**: Market coverage breadth

**Alpha Window Performance** (Critical for Trading Edge)
- **Ultra-Fresh (< 5 min)**: Announcements captured within maximum alpha window
  - Target: 30%+ is excellent
  - Color-coded: Green = 30%+, Yellow = 20-30%, Blue = <20%

- **Fresh (5-15 min)**: Good alpha window
  - Still valuable for trading decisions

- **Stale (> 30 min)**: No alpha remaining
  - Information already priced in
  - Should be filtered out

**Recommendation Metrics**
- **Recommendations**: Total trading signals generated
- **Filter Pass Rate**: Percentage of announcements passing all filters
  - Target: 5-15% (highly selective = quality signals)
  - <5% = System correctly filtering noise
  - >15% = May be too permissive

- **Optimal Hours**: Announcements during 10 AM - 2 PM window
  - Best liquidity and spreads
  - Most predictable price action

#### Collection Timeline

Visual timeline showing:
- First and last announcement timestamps
- Collection duration in hours
- Announcement rate (per hour)
- Today vs yesterday comparison
- Weekly totals

---

### 2. **Live Announcements Tab** - Real-Time Monitoring

Real-time table of all collected announcements with sophisticated filtering.

#### Filter Options

- **All**: Show all announcements
- **Price Sensitive Only**: High-priority signals flagged by ASX
- **Fresh (< 5 min)**: Ultra-fresh announcements in alpha window
- **Today Only**: Focus on current trading day

#### Table Columns

| Column | Description |
|--------|-------------|
| **Ticker** | Company stock symbol |
| **Title** | Announcement headline |
| **Type** | ASX announcement category |
| **PS** | Price Sensitive flag (YES/blank) |
| **Age (min)** | Minutes since ASX published |
| **Time** | When system detected announcement |
| **Status** | Processing status |

#### Color Coding

- **Dark Green**: Price-sensitive announcements
- **Dark Blue**: Ultra-fresh (< 5 min)
- **Dark Purple**: Fresh (5-15 min)
- **Default**: Standard announcements

#### Key Insights for Financial Advisers

**What to Look For:**
1. **Price Sensitive + Ultra-Fresh** = Highest quality signals
2. **Age < 5 minutes** = Within alpha window
3. **Time 10:00-14:00** = Optimal trading hours
4. **Status: Processed** = Already analyzed by recommendation engine

**Red Flags:**
- High percentage of stale announcements (> 30 min)
- Most announcements outside optimal hours
- Low price-sensitive percentage

---

### 3. **Recommendations Tab** - Trading Signals

Track all generated trading recommendations with full transparency.

#### Summary Metrics

- **Total**: Total recommendations generated
- **BUY**: Long positions recommended
- **SELL**: Short positions or exits
- **Avg Confidence**: Mean confidence score across all recommendations

#### Recommendations Table

| Column | Description |
|--------|-------------|
| **Ticker** | Stock symbol |
| **Action** | BUY or SELL |
| **Confidence** | System confidence (0.0-1.0) |
| **Entry Price** | Recommended entry point |
| **Sentiment** | Detected sentiment (Positive/Negative) |
| **Generated** | Timestamp of recommendation |
| **Filters Passed** | Which filters approved this signal |

#### Color Coding

- **Green rows**: BUY recommendations
- **Red rows**: SELL recommendations

#### Interpreting Confidence Scores

| Score | Quality | Action |
|-------|---------|--------|
| 0.80+ | **Excellent** | High-conviction trade |
| 0.70-0.79 | **Good** | Strong signal |
| 0.60-0.69 | **Moderate** | Consider position sizing |
| <0.60 | **Weak** | Should be filtered out |

#### Why Zero Recommendations?

**This is EXPECTED during most trading periods:**

1. **Materiality Filter**: 80% of ASX announcements are administrative noise
   - AGM notices
   - Appendix filings
   - Director interest changes

2. **Time-of-Day Filter**: Only 10 AM - 2 PM is optimal
   - After-hours announcements filtered out
   - Low liquidity periods avoided

3. **Sentiment Filter**: Need strong positive/negative signals
   - Neutral announcements don't generate trades

4. **Technical Filter**: Must align with price action
   - RSI, MACD, Moving Averages must confirm

**When to Expect Recommendations:**
- Quarterly earnings reports
- Major contract wins
- Takeover announcements
- Profit guidance updates
- During 10 AM - 2 PM window
- Price-sensitive flagged by ASX

---

### 4. **Analytics Tab** - Performance Intelligence

Comprehensive breakdown of system performance for strategic analysis.

#### Time-of-Day Performance

Visual bar chart showing:
- Announcement distribution by hour
- Price-sensitive count per hour
- Optimal hours highlighted (10 AM - 2 PM)

**Strategic Use:**
- Identify peak activity hours
- Schedule monitoring during high-quality periods
- Avoid low-liquidity hours

#### Top Announcement Types

Ranking of most common announcement categories:
- Identify administrative noise patterns
- Spot high-value announcement types
- Understand market composition

#### Filter Analysis

Detailed breakdown of filter performance:
- Total announcements processed
- Recommendations generated
- Pass rate percentage
- Reject rate percentage
- Status assessment

**Interpreting Status:**
- "Correctly rejecting noise" = System working as designed
- "Good selectivity" = Quality signals being generated
- "Too permissive" = May need filter tightening

---

## 🔄 Auto-Refresh Feature

The dashboard automatically refreshes every **30 seconds** to show live data.

**Controls:**
- ✅ **Auto-refresh checkbox** (bottom right): Toggle on/off
- 🔄 **Refresh button** (top right): Manual refresh
- **Last updated**: Timestamp of most recent data load

**Best Practices:**
- Keep auto-refresh ON during active trading hours
- Turn OFF when analyzing historical data
- Manual refresh after system changes

---

## 📈 Key Metrics for Financial Advisers

### Alpha Window Capture Rate

**What it means:**
The percentage of announcements captured within 0-5 minutes of ASX publication.

**Why it matters:**
Research shows information is priced into markets within 15-30 minutes. The faster we capture and analyze announcements, the greater the potential edge.

**Benchmarks:**
- 40%+ = **Excellent** - System catching announcements very quickly
- 30-40% = **Good** - Solid alpha window capture
- 20-30% = **Fair** - May need infrastructure improvements
- <20% = **Poor** - Delayed data collection

### Filter Pass Rate

**What it means:**
Percentage of announcements that pass all filters and generate recommendations.

**Why it matters:**
A highly selective system (5-15% pass rate) focuses on quality over quantity, reducing false signals and overtrading.

**Benchmarks:**
- 0-5% = **Very Selective** - Waiting for high-quality signals
- 5-15% = **Selective** - Good balance
- 15-30% = **Permissive** - May generate too many signals
- >30% = **Too Permissive** - Likely generating noise

### Price-Sensitive Percentage

**What it means:**
Percentage of collected announcements flagged as price-sensitive by ASX.

**Why it matters:**
Price-sensitive announcements have higher probability of moving stock prices. This metric shows data quality.

**Benchmarks:**
- 20%+ = **High Quality** - Capturing important announcements
- 10-20% = **Normal** - Typical ASX distribution
- <10% = **Low Quality** - May be missing key announcements

---

## 🎯 Using the Dashboard for Client Analysis

### Morning Routine (Market Open)

1. **Launch dashboard** before market opens
2. **Check Overview tab** for overnight activity
3. **Monitor Live Announcements** for fresh signals during 10 AM - 2 PM
4. **Review Recommendations** for potential trades

### Intraday Monitoring

1. Keep dashboard open during trading hours
2. Watch for **price-sensitive + ultra-fresh** announcements
3. Review recommendations as they're generated
4. Check confidence scores before executing

### End-of-Day Analysis

1. **Overview tab**: Review daily capture metrics
2. **Analytics tab**: Study time-of-day patterns
3. **Recommendations**: Assess signal quality
4. Export data for reporting (future feature)

### Weekly Review

1. Compare weekly totals vs previous weeks
2. Analyze filter pass rate trends
3. Review recommendation performance
4. Identify system optimization opportunities

---

## 🔧 Troubleshooting

### Dashboard Won't Start

**Error: "No module named 'tkinter'"**
- Solution: Reinstall Python with Tcl/Tk support
- Windows: Download from python.org with default options

**Error: "Database locked"**
- Solution: Close other applications accessing the database
- Check if live_paper_trader.py is running

### No Data Showing

**All metrics show zero:**
- Check database path is correct (data/trading.db)
- Verify data collection has started
- Click manual refresh button

### Dashboard Freezes

**Not responding:**
- Turn off auto-refresh temporarily
- Reduce data load (use filters)
- Check system resources

---

## 📊 Understanding System Architecture

### Data Flow

```
ASX API (10s polling)
    ↓
Announcement Monitor
    ↓
Database Storage (live_announcements table)
    ↓
Recommendation Engine (< 1 second processing)
    ↓
Multiple Filters (Time, Materiality, Sentiment, Technical)
    ↓
Database Storage (live_recommendations table)
    ↓
Dashboard GUI (30s refresh)
```

### Critical Timing

- **10 seconds**: ASX API polling interval
- **< 1 second**: Announcement processing time
- **< 3 seconds**: Total detection-to-recommendation time
- **30-90 seconds**: Alpha window (research-backed edge)
- **30 seconds**: Dashboard auto-refresh interval

---

## 💡 Advanced Tips

### Identifying High-Quality Periods

Watch for clusters of:
- Multiple price-sensitive announcements
- High ultra-fresh percentage
- Time-of-day 10 AM - 2 PM
- Recommendation generation activity

### Filter Performance Analysis

**If pass rate is 0%:**
1. Check if it's outside optimal hours (normal)
2. Review announcement types (mostly administrative?)
3. Wait for earnings season or major news
4. System is correctly selective (expected)

**If pass rate is >20%:**
1. Review filter settings
2. Check for data quality issues
3. Verify recommendation confidence scores
4. May indicate market event period

### Optimizing for Different Market Conditions

**Earnings Season:**
- Expect higher pass rates (10-15%)
- More recommendations generated
- Higher average confidence scores

**Quiet Periods:**
- Pass rates near 0% (normal)
- Focus on data quality metrics
- System waiting for good signals

**Market Volatility:**
- More price-sensitive flags
- Technical filters may be more restrictive
- Watch for false signals

---

## 📋 Checklist for Financial Advisers

### Daily Tasks
- [ ] Launch dashboard before market open
- [ ] Verify data collection is active
- [ ] Monitor ultra-fresh announcements
- [ ] Review any recommendations generated
- [ ] Check filter pass rate is appropriate

### Weekly Tasks
- [ ] Review total announcements collected
- [ ] Analyze time-of-day patterns
- [ ] Compare week-over-week metrics
- [ ] Assess recommendation quality
- [ ] Plan for following week

### Monthly Tasks
- [ ] Calculate Information Coefficient (IC)
- [ ] Review long-term performance trends
- [ ] Analyze filter effectiveness
- [ ] Optimize system parameters
- [ ] Generate client reports

---

## 🎓 Key Concepts Explained

### 30-90 Second Alpha Window

**Definition:** The critical time window after announcement publication when information has not yet been fully priced into the market.

**Research Basis:** Academic studies show stock prices react to news within 15-30 minutes, with most movement in first 90 seconds.

**System Implementation:**
- Detect announcements within seconds
- Process instantly (< 1 second)
- Generate recommendations within 3 seconds
- Total response time under alpha window

### Information Coefficient (IC)

**Definition:** Correlation between predicted returns (confidence scores) and actual returns.

**Interpretation:**
- IC > 0.05 = Real predictive edge
- IC 0.02-0.05 = Weak edge
- IC < 0.02 = No edge (random)

**Calculation:** After 7-day holding period, correlate confidence scores with actual stock returns.

### Bayesian Confidence Scoring

**Definition:** Probabilistic framework combining multiple signals with different reliability weights.

**Components:**
- Base probability (prior)
- Sentiment signal (high weight)
- Time-of-day factor (medium weight)
- Technical indicators (medium weight)
- Materiality score (high weight)

**Result:** Single confidence score (0-1) representing probability of successful trade.

---

## 📞 Support & Next Steps

### Getting Help

If you encounter issues:
1. Check this user guide first
2. Review log files in asx-trading-ai directory
3. Check system requirements
4. Verify database integrity

### Future Enhancements

Planned features:
- Export to Excel/CSV for client reporting
- Email alerts for high-confidence recommendations
- Historical performance charts
- Custom filter configuration
- Real-time price tracking
- Position management interface

---

**Dashboard Version:** 1.0
**Last Updated:** October 15, 2025
**Author:** ASX Trading AI System

For financial adviser use only. This dashboard displays algorithmic trading signals and should be used in conjunction with professional judgment and risk management practices.
