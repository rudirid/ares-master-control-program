# ASX Trading AI - Quantitative Analysis Summary

## Current State: System is Mathematically Unprofitable

```
Current Performance: -5.87% return, 34.0% win rate
Break-even Needed:   45.3% win rate
Profitable Target:   55%+ win rate
```

---

## The Core Problem (Math)

### Expected Value Analysis

```
Current System EV per Trade:
  (0.34 × $51.51) - (0.66 × $42.64) = -$10.63

This is NEGATIVE expected value.
Kelly Criterion says: DO NOT TRADE at 34% win rate.
```

### Why Technical Analysis Made It Worse

```
Before Technical Filter:
  - Potential trades: 73
  - Executed trades: 58
  - Return: -4.63%

After Technical Filter (Hard Reject):
  - Potential trades: 73
  - REJECTED: 26 trades (36% rejected!)
  - Executed trades: 47
  - Return: -5.87% (WORSE)

Problem: Over-filtering reduced edge instead of improving it.
```

---

## Critique of Recommendations

### ✅ EXCELLENT Recommendations (Implement Immediately)

1. **Change Technical Analysis to Soft Modifier**
   - Current: Hard reject → loses trades
   - Better: Confidence adjustment → keeps trades with adjusted risk
   - Impact: +3-5% win rate

2. **Integrate Dynamic Exits**
   - Current: Fixed 7-day hold
   - Better: Adaptive exits (take profit, trailing stops, momentum)
   - Impact: +3-5% return

3. **Reduce Min Data Requirement**
   - Current: 50 days → early period has no data
   - Better: 20-30 days → more coverage
   - Impact: +2% win rate

### ⚠️ NEEDS WORK (Too Vague)

4. **"Improve Sentiment Analysis - 37% accuracy"**
   - Missing: What's the baseline? (37% is worse than random 50%)
   - Missing: Current IC (Information Coefficient)
   - Missing: Confusion matrix analysis
   - **Fix**: Measure IC first, then improve if IC < 0.05

5. **"Fix News Scrapers"**
   - Missing: Cost-benefit analysis
   - Missing: Will more data help if signals are weak?
   - **Fix**: First improve signal quality, then add volume

6. **"Machine Learning Optimization"**
   - Missing: Specific approach (what features? what model?)
   - Missing: Overfitting prevention strategy
   - **Fix**: Use walk-forward validation, limit parameters

### ❌ CRITICAL MISSING ELEMENTS

**Not Mentioned but Essential**:

1. **Information Coefficient (IC)** - Must measure signal-to-price correlation
2. **Regime Detection** - Different strategies for bull/bear markets
3. **Parameter Stability Testing** - Prevent overfitting
4. **Walk-Forward Validation** - Proper out-of-sample testing
5. **Earnings Surprise Quantification** - Not just detection, but magnitude
6. **Position Sizing Optimization** - Kelly Criterion, not fixed 2%

---

## Mathematical Improvements Added

### 1. Information Coefficient (IC)

**What It Measures**: Correlation between signal and future returns

```python
IC = correlation(sentiment_score, next_day_return)

Interpretation:
  IC > 0.10 = EXCELLENT (strong predictive power)
  IC > 0.05 = GOOD (tradeable edge)
  IC > 0.02 = FAIR (marginal edge)
  IC < 0.02 = POOR (no edge, don't trade!)

Action: Measure this FIRST before any optimization.
```

### 2. Signal Decay Analysis

**Find Optimal Holding Period Empirically**:

```python
# Measure correlation over time
1 hour:  correlation = ?
4 hours: correlation = ?
1 day:   correlation = ?
3 days:  correlation = ?
7 days:  correlation = ?

Find when correlation drops below 0.02 → that's max hold time
```

### 3. Win Rate by Confidence Bucket

**Validation Check** (should be monotonically increasing):

```
Confidence 0.6-0.7: Win Rate = ?%
Confidence 0.7-0.8: Win Rate = ?%
Confidence 0.8-0.9: Win Rate = ?%
Confidence 0.9-1.0: Win Rate = ?%

If NOT increasing → confidence calculation is broken
```

### 4. Kelly Position Sizing

**Current**: Fixed 2% risk (ignores win rate)

**Better**: Fractional Kelly

```python
Kelly % = (win_rate × win/loss_ratio - (1-win_rate)) / win/loss_ratio

Current system (34% win rate):
Kelly = (0.34 × 1.21 - 0.66) / 1.21 = -0.21 → NEGATIVE!

Target system (50% win rate):
Kelly = (0.50 × 1.21 - 0.50) / 1.21 = 0.087 = 8.7% position

Use 25% of Kelly for safety → 2.2% position size
```

### 5. Advanced Risk Metrics

**Add These**:

```
Sharpe Ratio = (return - risk_free) / std_dev
  Target: > 1.0

Sortino Ratio = (return - risk_free) / downside_dev
  Target: > 1.5

Max Consecutive Losses
  Important for psychology

Time Underwater (% in drawdown)
  Target: < 30%
```

---

## Better Signal Combination Methods

### Current Approach (WRONG)

```python
if technical_disagrees:
    reject_trade()  # Loses edge
```

### Recommended: Ensemble Scoring

```python
# Weighted combination
score = (
    0.40 × sentiment_signal +
    0.25 × technical_signal +
    0.20 × fundamental_signal +
    0.15 × flow_signal
)

# Diversity bonus (signals should disagree slightly)
diversity = 1.0 + (0.1 × (1 - correlation_between_signals))

final_score = score × diversity
```

### Alternative: Bayesian Update

```python
# Start with sentiment confidence
prior = sentiment_confidence

# Update with technical signal
if technical_agrees:
    posterior = bayesian_update(prior, likelihood=0.70)
else:
    posterior = bayesian_update(prior, likelihood=0.30)

# Posterior is new confidence
```

---

## Validation Methods (Prevent Overfitting)

### 1. Walk-Forward Analysis (ESSENTIAL)

```
Train Period: 252 days (1 year)
Test Period:  63 days (3 months)

Optimize on train → Test on out-of-sample → Roll forward

If test performance < 80% of train performance → Overfitting
```

### 2. Monte Carlo Simulation

```python
# Resample trades 10,000 times
# Calculate 95% confidence interval
# Check: P(return > 0) > 70% needed for confidence
```

### 3. Parameter Stability Test

```python
# Test RSI threshold: 25, 27, 30, 33, 35
# If performance varies wildly → Overfitting

Good strategy: Performance is smooth curve
Bad strategy: Performance has sharp peaks
```

### 4. Statistical Significance

```python
# Compare strategy vs benchmark
# t-test: p < 0.05 needed
# Cohen's d > 0.5 for meaningful effect
```

---

## Priority Fixes (Ranked by Impact)

### TIER 1: Critical (Week 1) → +10-15% Win Rate

1. **Fix Sentiment Analysis** (+8-12% win rate)
   - Measure current IC
   - Add earnings detection
   - Implement context awareness
   - Target IC > 0.05

2. **Technical → Soft Filter** (+3-5% win rate)
   - Stop hard rejecting trades
   - Adjust confidence instead
   - Accept borderline trades

3. **Integrate Dynamic Exits** (+3-5% return)
   - Replace fixed 7-day hold
   - Add trailing stops
   - Take profit targets

### TIER 2: Important (Week 2) → +5-8% Win Rate

4. **Regime Detection** (+4-6% win rate)
   - Bull/bear/sideways classification
   - Different thresholds per regime
   - Adapt strategy to market

5. **Earnings Surprise** (+3-5% win rate)
   - Extract metrics from text
   - Calculate % surprise
   - Boost signal on beats

### TIER 3: Optimization (Week 3) → +2-4% Win Rate

6. **ML Meta-Model** (+2-3% win rate)
   - Only after base signals improved
   - Use walk-forward validation
   - Gradient boosting with max_depth=3

7. **Multi-Timeframe** (+1-2% win rate)
   - Short/medium/long term analysis
   - All must agree or neutral

---

## Implementation Timeline

### Week 1: Critical Fixes
- **Day 1**: Technical soft filter + min data reduction
- **Day 2**: IC measurement + earnings detection
- **Day 3**: Dynamic exits integration
- **Day 4**: Test all fixes on 300 samples
- **Day 5**: Debug and iterate

**Success Criteria**:
- Win Rate: 34% → 40%+
- IC: Unknown → > 0.05
- Return: -5.87% → -2% to +2%

### Week 2: Regime & Earnings
- **Day 1-2**: Regime detection
- **Day 3-4**: Earnings surprise
- **Day 5**: Integration test

**Success Criteria**:
- Win Rate: 40% → 45%+
- Return: -2% → +2% to +5%

### Week 3: Validation & ML
- **Day 1-2**: Walk-forward validation
- **Day 3-4**: ML meta-model (if previous successful)
- **Day 5**: Final test

**Success Criteria**:
- Win Rate: 45% → 48%+
- Return: +2% → +5% to +8%
- Sharpe > 1.0

---

## Key Insights (Mathematical)

### 1. Current System Has Negative EV
```
EV = (0.34 × $51) - (0.66 × $43) = -$10.63 per trade

Cannot be fixed by filtering alone.
Must improve base signal quality.
```

### 2. Kelly Criterion Confirms: Don't Trade at 34%
```
Kelly = (p×b - q)/b where b = avg_win/avg_loss
Kelly = (0.34×1.21 - 0.66)/1.21 = -0.21

Negative Kelly = Guaranteed long-term losses
```

### 3. Technical Filter Removed Edge
```
Rejected 26/73 trades (36%)
Made return worse: -4.63% → -5.87%

Lesson: Over-filtering hurts when base win rate is low
```

### 4. Need 45%+ Win Rate for Profitability
```
Break-even: 45.3%
Good strategy: 50%+
Excellent strategy: 55%+

Current gap: +11-21 percentage points needed
```

### 5. IC is the Key Metric
```
IC < 0.02: No edge (don't trade)
IC 0.02-0.05: Weak edge (marginal)
IC 0.05-0.10: Good edge (tradeable)
IC > 0.10: Strong edge (excellent)

Must measure this BEFORE any optimization.
```

---

## What Will Work vs Won't Work

### ✅ WILL WORK

1. Measuring IC and improving signals with IC < 0.05
2. Soft confidence adjustment instead of hard filters
3. Dynamic exits capturing momentum
4. Regime-aware strategy adjustments
5. Proper walk-forward validation

### ❌ WON'T WORK

1. Adding more filters without improving base signals
2. Over-optimizing on historical data
3. Using hard reject filters (proven to hurt)
4. Ignoring transaction costs
5. ML without proper feature engineering and validation

---

## Final Recommendation

### Implement in This Order:

1. **Measure IC first** (if < 0.05, fix sentiment before anything else)
2. **Change technical to soft filter** (stop rejecting trades)
3. **Integrate dynamic exits** (better risk management)
4. **Add regime detection** (adapt to market conditions)
5. **Implement walk-forward validation** (prevent overfitting)
6. **Only then consider ML** (if previous steps successful)

### Do NOT Proceed to Live Trading Until:

- ✅ Win rate > 48% on out-of-sample data
- ✅ IC > 0.05 (significant correlation)
- ✅ Sharpe ratio > 1.0
- ✅ 500+ historical trades validated
- ✅ Walk-forward shows consistent performance
- ✅ Monte Carlo: >70% probability of profitability

---

## Bottom Line

**The current recommendations are on the right track but missing critical mathematical foundations.**

**Key Additions from This Analysis**:
1. IC measurement (must be done first)
2. Proper ensemble methods (not just filtering)
3. Walk-forward validation (prevent overfitting)
4. Kelly position sizing (optimize risk)
5. Statistical significance testing (avoid luck)

**Expected Outcome**: Following this quantitative approach can improve win rate from 34% to 48-52%, making the system profitable with positive expected value.

**Confidence Level**: 70% - Good infrastructure exists, signals need improvement, but with proper methodology success is achievable.

---

**Files Created**:
1. `QUANTITATIVE_ANALYSIS.md` - Full detailed analysis (70+ pages)
2. `IMMEDIATE_FIXES.md` - Step-by-step implementation guide
3. `ANALYSIS_SUMMARY.md` - This executive summary

**Next Steps**: Start with Week 1 critical fixes, measure IC, and iterate based on results.
