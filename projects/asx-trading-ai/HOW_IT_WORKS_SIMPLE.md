# How the Trading AI Works - Simple Explanation

**For**: Non-technical users who want to understand what the system does

**Last Updated**: 2025-10-10

---

## The Big Picture

Imagine you have a smart assistant that:
1. **Watches** the ASX stock exchange for company news (like a hawk)
2. **Reads** each announcement and figures out if it's good news or bad news
3. **Decides** whether that news is worth trading on
4. **Recommends** whether to BUY or SELL that stock
5. **Learns** from its mistakes to get better over time

That's exactly what this system does, except it does it in seconds, not hours.

---

## Step-by-Step: How a Trading Recommendation is Made

### Step 1: Watching for News (The Monitor)

**What happens:**
- Every 60 seconds, the system checks the ASX website for new company announcements
- It's like constantly refreshing a news feed

**Example:**
```
10:15 AM - BHP announces "Quarterly Production Report"
10:16 AM - System detects it (1 minute old)
```

**Why 1 minute matters:**
- Fresh news = trading opportunity
- Old news (>30 minutes) = already priced in, no edge

---

### Step 2: Reading the News (Sentiment Analysis)

**What happens:**
- The system reads the announcement title and content
- It looks for positive words ("growth", "profit", "exceed") vs negative words ("decline", "loss", "below")
- It calculates a "sentiment score" from -1.0 (very negative) to +1.0 (very positive)

**Example:**
```
Announcement: "BHP Quarterly Production Report - Iron Ore output exceeds expectations"

Analysis:
- Positive words detected: "exceeds", "expectations"
- Negative words: None
- Sentiment: POSITIVE
- Score: 0.75 (strong positive)
- Confidence: 0.68 (fairly confident)
```

**Real-world translation:**
- Sentiment 0.75 = "This is good news, the company is doing better than expected"

---

### Step 3: Filtering Out Noise (The Filters)

**Not all news is worth trading on.** The system applies multiple filters:

#### Filter 1: TIME - Is this news fresh?
- **PASS**: Announcement is <5 minutes old (ultra-fresh, maximum edge)
- **PASS**: Announcement is <30 minutes old (fresh, strong edge)
- **FAIL**: Announcement is >30 minutes old (already priced in)

**Why:** Stock prices react to news within minutes. If you're late, the opportunity is gone.

#### Filter 2: MATERIALITY - Is this news important?
- **PASS**: Earnings reports, trading updates, dividends, capital raising
- **FAIL**: Director changed his address, administrative paperwork

**Why:** 80% of company announcements are just routine admin. We only care about news that moves stock prices.

**Example of NOISE:**
```
"Notice of Annual General Meeting" - FILTERED OUT
```

**Example of MATERIAL:**
```
"Trading Update - FY25 profit guidance raised 15%" - PASSED
```

#### Filter 3: TIME-OF-DAY - Is this a good time to trade?
- **PASS**: 10:00 AM - 2:00 PM (high liquidity, tight spreads)
- **FAIL**: 9:00-10:00 AM (volatile opening), 3:00-4:00 PM (thin volume)

**Why:** Trading at 10 AM = lots of buyers and sellers, fair prices
Trading at 3:45 PM = fewer traders, wider spreads, worse execution

#### Filter 4: TECHNICAL ANALYSIS - What do the charts say?
- Checks if the stock is trending up or down
- Checks if it's overbought or oversold
- **Doesn't reject trades**, just adjusts confidence up or down

**Example:**
```
BHP sentiment = POSITIVE (score 0.75)
Technical analysis = Stock trending up, RSI healthy
Result: Confidence BOOSTED +0.10 → Final confidence = 0.85
```

#### Filter 5: CONTRARIAN - Is everyone too excited?
- If sentiment is EXTREME (>0.85), it might be "priced in"
- System applies skepticism: "Everyone loves this stock, is it too late?"

**Example:**
```
CSL sentiment = 0.92 (extremely positive)
Stock up 15% this week already
Contrarian signal: FADE (reduce confidence by -0.15)
```

---

### Step 4: Making the Decision

**After all filters, the system asks:**

1. **Did this announcement pass all filters?**
   - If NO → Reject, don't trade

2. **Is the final confidence ≥ 60%?**
   - If NO → Too uncertain, don't trade
   - If YES → Generate recommendation

**Example of a PASS:**
```
Company: BHP
Announcement: "Quarterly Production Report - Iron ore exceeds expectations"
Age: 2 minutes (PASS - fresh)
Materiality: High (PASS - material news)
Time: 10:15 AM (PASS - optimal time)
Sentiment: POSITIVE, score 0.75
Technical: Bullish (+0.10 boost)
Final Confidence: 0.85

RECOMMENDATION: BUY BHP at $43.21 (Confidence: 85%)
```

**Example of a FAIL:**
```
Company: CBA
Announcement: "Director Interest Notice"
Age: 5 minutes (PASS)
Materiality: Low (FAIL - administrative)

FILTERED OUT - Not material enough to trade
```

---

## Step 5: Learning from Results (Self-Improvement)

**The Critical Question: Does this system actually work?**

We measure this using **Information Coefficient (IC)**:

### What is IC? (Simple Version)

**IC = How well do our predictions match reality?**

- **IC = 0.15**: Strong predictive power (we're good at this!)
- **IC = 0.05**: Weak edge (barely better than random)
- **IC = 0.00**: No edge (we're just guessing)
- **IC = -0.10**: Inverse relationship (we're predicting BACKWARDS!)

**Real Example from Historical Testing:**
```
Sentiment Score IC: 0.000
Translation: Our sentiment analysis has ZERO predictive power on old news
Conclusion: Disable sentiment on historical data

Recommendation Confidence IC: -0.117
Translation: When we're confident, we're WRONG. When we're uncertain, we're RIGHT!
Conclusion: Use CONTRARIAN logic (flip our recommendations)
```

**This is why we built the live trading system:**
- Historical data showed IC = 0.000 (no edge)
- But we believe FRESH news (live data) will have edge
- That's what we're testing Oct 13-17

---

## Real-World Example: Full Trade Flow

**Monday 10:15 AM:**

```
[MONITOR] Checking ASX for new announcements...
[MONITOR] FOUND: BHP - "Quarterly Production Report"

[FILTER - TIME] Age: 2.3 minutes → PASS (fresh, +0.15 confidence boost)
[FILTER - MATERIALITY] Type: "Quarterly Report" → PASS (material)
[FILTER - TIME-OF-DAY] Time: 10:15 AM → PASS (optimal, +0.05 confidence boost)

[SENTIMENT] Analyzing announcement...
[SENTIMENT] Title: "Iron ore production exceeds market expectations"
[SENTIMENT] Detected keywords: "exceeds", "expectations" (positive)
[SENTIMENT] Score: 0.75 (positive)
[SENTIMENT] Confidence: 0.68

[PRICE] Fetching current market price...
[PRICE] BHP.AX current price: $43.21

[TECHNICAL] Analyzing charts...
[TECHNICAL] RSI: 58 (neutral)
[TECHNICAL] MACD: Bullish crossover
[TECHNICAL] 50-day MA: Price above (bullish)
[TECHNICAL] Verdict: Bullish alignment (+0.10 confidence boost)

[CONTRARIAN] Checking for extremes...
[CONTRARIAN] Sentiment 0.75 is not extreme (threshold: 0.85)
[CONTRARIAN] No adjustment needed

[DECISION] Calculating final confidence...
[DECISION] Base confidence: 0.68
[DECISION] + TIME boost: +0.15
[DECISION] + TIME-OF-DAY boost: +0.05
[DECISION] + Technical boost: +0.10
[DECISION] = Final confidence: 0.98

[DECISION] Confidence 0.98 ≥ 0.60 → RECOMMEND

✓ RECOMMENDATION: BUY BHP @ $43.21 (Confidence: 98%)
```

**What you'd see:**
```
[10:15:27] ✓ RECOMMENDATION: BUY BHP @ $43.21 (Confidence: 0.98)
```

---

## How We Measure Success

After the 5-day live trading test (Oct 13-17), we'll analyze:

### 1. Win Rate
- **What it is**: How many trades made money?
- **Target**: 48-52% (anything above 50% is profitable with proper sizing)
- **Example**: 100 trades, 55 winners = 55% win rate (GOOD)

### 2. Information Coefficient (IC)
- **What it is**: Does our sentiment actually predict price movement?
- **Target**: IC > 0.05 (we have an edge)
- **Example**: IC = 0.087 means our signals are 8.7% better than random (PROFITABLE)

### 3. Sharpe Ratio
- **What it is**: Return vs risk (higher is better)
- **Target**: Sharpe > 0 (positive risk-adjusted returns)
- **Example**: Sharpe = 0.75 means we make decent returns for the risk taken

### 4. Average Return
- **What it is**: Average profit per trade
- **Target**: +0.5% to +1.5% per trade
- **Example**: Average +0.8% per trade over 300 trades = 240% total return (amazing!)

---

## The Go-Live Decision

**After 5 days, we'll ask:**

### Minimum Viable (We can go live with real money):
- ✅ IC > 0.05 (we have edge)
- ✅ Win Rate > 48% (more wins than losses)
- ✅ Sharpe > 0 (positive risk-adjusted return)
- ✅ Sample Size > 50 trades (enough data)

### Ideal (High confidence):
- 🎯 IC > 0.10 (strong edge)
- 🎯 Win Rate > 52% (comfortable margin)
- 🎯 Sharpe > 0.5 (good risk-adjusted return)
- 🎯 Sample Size > 100 trades (very confident)

**If we pass:** Start trading with real money (small amounts like $100-500 per trade)

**If we fail:** Back to the drawing board, improve the models

---

## Summary: The Trading AI in 3 Sentences

1. **We monitor ASX announcements in real-time, catching news within minutes of release**

2. **We analyze sentiment, apply smart filters (time, materiality, technical), and only recommend trades with >60% confidence**

3. **We measure our accuracy using Information Coefficient (IC), and only go live with real money if we prove we have an edge (IC > 0.05)**

---

## Why This Matters

**Traditional investing:** Buy and hold, hope stocks go up

**Our approach:** Find news FAST, trade the initial reaction, get out within a week

**The edge:** Speed + smart filtering + learning from results

**Risk management:** Never risk more than 2% per trade, 5% stop loss, 5% daily limit

---

## What's Next?

**Monday Oct 13, 7:00 AM:**
- Start monitoring ASX for live announcements
- Generate recommendations for 5 days
- Target: 300 recommendations

**Friday Oct 17, 5:00 PM:**
- Run performance analysis
- Calculate IC (do we have edge?)
- Make go-live decision

**If successful:**
- Start trading with $500-1000 capital
- $50-100 per trade
- Monitor for 2 weeks
- Scale up if edge persists

---

## Questions?

**Q: Is this guaranteed to make money?**
A: NO. Past performance doesn't guarantee future results. That's why we test with paper trading first.

**Q: What's the biggest risk?**
A: Signal decay - what works today might not work tomorrow. Markets adapt.

**Q: How much can I make?**
A: If IC = 0.08 and we make 300 trades/year with 0.8% avg return = 240% annual return (before costs). But this is OPTIMISTIC.

**Q: What if it doesn't work?**
A: We don't go live. We improve the models and test again.

---

**This is NOT financial advice. Always do your own research. Only invest what you can afford to lose.**
