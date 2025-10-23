# Machine Learning Parallel Strategy
## A/B Testing: Rule-Based vs ML Engine

**Author**: Claude Code
**Date**: 2025-10-16
**Budget**: $5K AUD total
**Goal**: Scientific comparison to find best approach

---

## Executive Summary

Run TWO recommendation engines **in parallel** on the SAME announcements:

1. **REAL Engine** (Rule-based + Bayesian) - Stable baseline
2. **ML Engine** (FinBERT + XGBoost) - Learning system

After 30-60 days (500-1000 trades each), compare IC scores and pick the winner.

---

## Architecture Comparison

### SAME Structure (8 Steps):
Both engines use identical pipeline:

```
1. TIME FILTER          → Same (< 30 min rule)
2. MATERIALITY FILTER   → Same (price-sensitive keywords)
3. TIME-OF-DAY FILTER   → Same (10 AM - 2 PM)
4. SENTIMENT ANALYSIS   → DIFFERENT (see below)
5. PRICE DATA           → Same (yfinance)
6. TECHNICAL ANALYSIS   → Same (RSI, MACD, MA)
7. CONTRARIAN SIGNALS   → Same (5-day price change)
8. CONFIDENCE SCORING   → DIFFERENT (see below)
```

### KEY DIFFERENCES:

| Component | REAL Engine (Rule-Based) | ML Engine (Machine Learning) |
|-----------|--------------------------|------------------------------|
| **Sentiment** | 300+ keyword dictionary | FinBERT (pre-trained transformer) |
| **Confidence** | Bayesian probability formula | XGBoost gradient boosting |
| **Training** | No training needed | Retrains weekly on outcomes |
| **Explainability** | 100% transparent | Feature importance only |
| **Data required** | 0 (works day 1) | Improves with 500+ trades |

---

## ML Model Selection

### 1. Sentiment Analysis: FinBERT

**Why FinBERT?**
- Pre-trained on financial news (130M parameters)
- Understands context better than keywords
- Free, open-source (Hugging Face)
- Runs locally on CPU ($0 cost)

**Example**:
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Load FinBERT
tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

# Analyze title
inputs = tokenizer("Guidance Upgraded 15% Above Forecast", return_tensors="pt")
outputs = model(**inputs)

# Get sentiment
sentiment_probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
# Returns: [negative: 0.05, neutral: 0.12, positive: 0.83]
```

**Advantages over keywords**:
- Understands negation ("not bad" = positive)
- Context-aware ("beat expectations" vs "beat down")
- Handles sarcasm better
- No manual keyword list maintenance

**Cost**: $0 (runs locally, 1-2 seconds per title)

---

### 2. Confidence Scoring: XGBoost

**Why XGBoost?**
- Industry standard for tabular data
- Learns optimal feature combinations
- Fast inference (milliseconds)
- Built-in feature importance

**Features (input variables)**:
```python
features = [
    # Sentiment
    'sentiment_score',          # FinBERT output
    'sentiment_confidence',     # FinBERT confidence

    # Time factors
    'announcement_age_minutes', # Freshness
    'hour_of_day',             # Time-of-day effect

    # Technical
    'rsi',                     # RSI value
    'macd',                    # MACD signal
    'ma_trend',                # Above/below MA

    # Materiality
    'price_sensitive',         # 0 or 1
    'has_numeric_signal',      # % or $ amounts

    # Contrarian
    'price_change_5d',         # Recent move
    'price_change_20d',        # Medium-term trend

    # Stock characteristics
    'market_cap',              # Size
    'avg_volume',              # Liquidity
]
```

**Target variable**: 7-day forward return (%)

**Training process**:
1. Week 1: Use default model (untrained baseline)
2. Week 2: Retrain on Week 1 outcomes
3. Week 3: Retrain on Weeks 1-2 outcomes
4. **ML gets smarter over time**, REAL stays static

**Cost**: $0 (runs locally, < 10ms per prediction)

---

## The Training Data Problem (SOLVED)

**Problem**: ML needs labeled data, but we don't have any yet.

**Solution**: Bootstrap approach
1. **Day 1-30**: Run ML with pre-trained FinBERT + untrained XGBoost
   - FinBERT works immediately (pre-trained on 130M financial texts)
   - XGBoost uses default hyperparameters (baseline)
2. **Day 7**: First retrain on 50-100 outcomes
3. **Day 14**: Second retrain on 100-200 outcomes
4. **Day 30**: Major retrain on 500+ outcomes
5. **Monthly**: Continue retraining as data grows

**Key insight**: ML starts weak but **improves**, REAL stays constant.

This creates a fair race:
- REAL has advantage early (proven rules)
- ML has advantage later (learns patterns)
- Best overall IC wins

---

## Parallel Execution Design

### Database Schema:

```sql
-- Add engine_type to recommendations
ALTER TABLE live_recommendations ADD COLUMN engine_type TEXT;
-- Values: 'REAL' or 'ML'

-- Track both engines' outputs
CREATE TABLE recommendation_comparison (
    id INTEGER PRIMARY KEY,
    announcement_id INTEGER,
    ticker TEXT,

    -- REAL engine output
    real_recommendation TEXT,
    real_confidence REAL,
    real_decision_log TEXT,

    -- ML engine output
    ml_recommendation TEXT,
    ml_confidence REAL,
    ml_feature_importance TEXT,

    -- Outcome (same for both)
    entry_price REAL,
    exit_price REAL,
    return_pct REAL,

    -- Winner tracking
    real_correct BOOLEAN,
    ml_correct BOOLEAN,

    timestamp TIMESTAMP
);
```

### Execution Flow:

```
NEW ANNOUNCEMENT ARRIVES
    ↓
┌─────────────────────────────────────────┐
│  Run BOTH engines in parallel           │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ REAL Engine  │    │  ML Engine   │  │
│  │ (Rule-based) │    │ (FinBERT +   │  │
│  │              │    │  XGBoost)    │  │
│  └──────┬───────┘    └──────┬───────┘  │
│         │                   │          │
│         ▼                   ▼          │
│   BUY @ 65%           BUY @ 58%       │
│   [8-step log]        [Features]      │
└─────────────────────────────────────────┘
    ↓
Store BOTH recommendations
    ↓
Create TWO separate trades
    ↓
Track performance independently
```

**Implementation**:
```python
def process_announcement(announcement_id):
    """Run BOTH engines on same announcement."""

    # Run REAL engine
    real_rec = real_engine.process_announcement(announcement_id)

    # Run ML engine
    ml_rec = ml_engine.process_announcement(announcement_id)

    # Store both
    comparison_id = store_comparison(
        announcement_id=announcement_id,
        real_rec=real_rec,
        ml_rec=ml_rec
    )

    # Create trades for BOTH (if recommendations generated)
    if real_rec:
        create_trade(real_rec, engine='REAL')

    if ml_rec:
        create_trade(ml_rec, engine='ML')

    return comparison_id
```

---

## Fair Comparison Metrics

### Primary Metric: Information Coefficient (IC)

```python
# After 30 days (500+ trades per engine):

real_ic = correlation(
    real_engine.confidence_scores,
    actual_7day_returns
)

ml_ic = correlation(
    ml_engine.confidence_scores,
    actual_7day_returns
)

# Winner = higher IC
winner = 'REAL' if real_ic > ml_ic else 'ML'
```

**Statistical significance test**:
```python
from scipy.stats import ttest_ind

# Need p-value < 0.05 to declare winner
p_value = ttest_ind(real_returns, ml_returns).pvalue

if p_value < 0.05:
    print(f"Statistically significant winner: {winner}")
else:
    print("No significant difference - keep running")
```

### Secondary Metrics:

| Metric | Formula | Target |
|--------|---------|--------|
| **Sharpe Ratio** | (Avg Return - Risk Free) / Std Dev | > 1.5 |
| **Win Rate** | Wins / Total Trades | > 55% |
| **Avg Win/Loss** | Avg Win / Avg Loss | > 2.0 |
| **Max Drawdown** | Largest peak-to-trough decline | < 15% |
| **Pass Rate** | Recommendations / Announcements | 10-20% |

### Agreement Analysis:

```python
# When do they agree/disagree?
agreement_rate = (both_buy + both_pass) / total_announcements

# When they disagree, who's right?
real_correct_when_disagree = sum(real_wins_when_ml_passes)
ml_correct_when_disagree = sum(ml_wins_when_real_passes)

# This reveals complementary strengths
```

---

## Budget Breakdown ($5K Total)

### Phase 1: Setup ($500)
- $200: OpenAI API for initial data labeling (optional)
- $150: AWS Lambda for serverless execution
- $150: Historical data (3 years ASX announcements)

### Phase 2: Parallel Testing ($1,500)
- $500: Real-time data feeds (ASX + yfinance premium)
- $500: GPU hours for FinBERT inference (AWS EC2 spot)
- $500: Monitoring/logging infrastructure

### Phase 3: Trading Capital ($2,000)
- $1,000: Trade winning engine only
- $1,000: Reserved for scaling winner

### Reserve: $1,000 (buffer)

**Free alternatives** (if budget constrained):
- FinBERT: Run locally on CPU (slower but free)
- XGBoost: Trains locally (free)
- Data: Scrape ASX website (free but slow)
- Execution: Run on personal computer (free)

**Optimized budget** (free tier): $0 for testing, $2K for trading only

---

## Timeline

### Week 1: Setup
- [x] Replace DEMO → REAL engine
- [ ] Build ML engine (FinBERT + XGBoost)
- [ ] Set up parallel execution framework
- [ ] Create comparison dashboard

### Week 2-5: Data Collection
- Run BOTH engines on every announcement
- Collect 500-1000 recommendations per engine
- Retrain ML weekly on growing dataset

### Week 6: Interim Analysis
- Calculate IC for both engines
- Statistical significance test
- Adjust if needed

### Week 8-12: Extended Test
- Continue parallel execution
- Build confidence in winner
- Prepare for live trading

### Week 13+: Deploy Winner
- Switch off losing engine
- Deploy $2K capital to winning engine
- Monitor and iterate

---

## Implementation Plan

### Step 1: Modify `live_full_system.py`

```python
# OLD (DEMO mode):
rec_id = generate_demo_recommendation(...)

# NEW (Parallel mode):
real_rec = real_engine.process_announcement(ann_id)
ml_rec = ml_engine.process_announcement(ann_id)

# Store both
store_parallel_recommendations(real_rec, ml_rec)
```

### Step 2: Build ML Engine

Create `live_trading/ml_recommendation_engine.py`:

```python
class MLRecommendationEngine:
    """
    ML-based recommendation engine using:
    - FinBERT for sentiment
    - XGBoost for confidence scoring
    """

    def __init__(self, db_path):
        self.db_path = db_path
        self.finbert = self._load_finbert()
        self.xgboost = self._load_xgboost()
        # Same filters as REAL engine
        self.time_filter = TimeFilter(max_age_minutes=30)
        self.materiality_filter = MaterialityFilter()
        # ... same 8-step structure

    def analyze_sentiment(self, title):
        """Use FinBERT instead of keyword dictionary."""
        inputs = self.tokenizer(title, return_tensors="pt")
        outputs = self.finbert(**inputs)
        probs = softmax(outputs.logits)
        return {
            'sentiment': ['negative', 'neutral', 'positive'][probs.argmax()],
            'confidence': probs.max(),
            'scores': probs
        }

    def compute_confidence(self, features):
        """Use XGBoost instead of Bayesian formula."""
        if not self.xgboost.is_trained:
            # Bootstrap: use simple logistic regression
            return self._bootstrap_confidence(features)

        # Predict probability of positive return
        return self.xgboost.predict_proba(features)[1]

    def retrain(self):
        """Weekly retraining on new outcomes."""
        # Fetch outcomes from past week
        data = self._fetch_training_data()

        # Retrain XGBoost
        self.xgboost.fit(data.X, data.y)

        # Log feature importance
        self._log_feature_importance()
```

### Step 3: Parallel Dashboard

Add comparison view to `dashboard.html`:

```html
<div class="comparison-panel">
    <h2>Engine Comparison</h2>

    <div class="metrics">
        <div class="real-engine">
            <h3>REAL Engine (Rule-Based)</h3>
            <p>IC: <span id="real-ic">0.042</span></p>
            <p>Win Rate: <span id="real-win">54%</span></p>
            <p>Sharpe: <span id="real-sharpe">1.3</span></p>
        </div>

        <div class="ml-engine">
            <h3>ML Engine (FinBERT + XGBoost)</h3>
            <p>IC: <span id="ml-ic">0.038</span></p>
            <p>Win Rate: <span id="ml-win">52%</span></p>
            <p>Sharpe: <span id="ml-sharpe">1.1</span></p>
        </div>
    </div>

    <div class="agreement">
        <h3>Agreement Analysis</h3>
        <p>Both BUY: 45% | Both PASS: 30% | Disagree: 25%</p>
        <p>When disagree, REAL correct: 60% | ML correct: 40%</p>
    </div>
</div>
```

---

## Risks and Mitigations

### Risk 1: ML overfits to noise
**Mitigation**:
- Use train/validation/test split
- Cross-validation
- Early stopping
- Monitor out-of-sample IC

### Risk 2: Not enough training data
**Mitigation**:
- Start with pre-trained FinBERT
- Use transfer learning
- Bootstrap with simple model
- Retrain incrementally

### Risk 3: Both engines fail (IC < 0.05)
**Mitigation**:
- Run historical backtest FIRST
- If backtest IC < 0.05, don't go live
- Pivot to different strategy

### Risk 4: Budget overrun
**Mitigation**:
- Use free tier where possible
- Run locally on CPU (slower but free)
- Only pay for real-time data when proven

---

## Decision Criteria (After 30 Days)

### Scenario A: REAL wins (IC_real > IC_ml + 0.02)
**Action**: Deploy $2K to REAL engine, archive ML

### Scenario B: ML wins (IC_ml > IC_real + 0.02)
**Action**: Deploy $2K to ML engine, archive REAL

### Scenario C: Tie (|IC_real - IC_ml| < 0.02)
**Action**:
- Run 30 more days
- OR use ensemble (average both confidences)
- OR use REAL (simpler = better if equal performance)

### Scenario D: Both fail (IC < 0.05)
**Action**:
- Stop trading
- Analyze why
- Pivot to different strategy (micro-caps, longer holds, etc.)

---

## Next Steps (Today)

1. **Switch DEMO → REAL** (30 minutes)
2. **Install ML dependencies** (15 minutes)
   ```bash
   pip install transformers torch xgboost scikit-learn
   ```
3. **Build ML engine skeleton** (2 hours)
4. **Set up parallel execution** (1 hour)
5. **Update dashboard** (1 hour)

**Total**: ~5 hours of work to get both engines running

---

## Expected Outcome

**My prediction**:
- **Week 1-2**: REAL engine leads (proven rules)
- **Week 3-4**: ML catches up (learns patterns)
- **Week 5-8**: ML pulls ahead (adapts to market)
- **Week 12**: ML wins with IC = 0.06 vs REAL IC = 0.04

**Why?** ML can learn:
- Subtle keyword combinations rules miss
- Non-linear feature interactions
- Time-varying patterns (seasonality)
- Stock-specific behavior

**BUT**: If REAL wins, that's valuable too! Means simple rules > complex ML (Occam's razor).

Either way, you get the BEST system backed by empirical evidence.

---

## Questions to Answer

1. **Start both today?** Or run REAL for 1 week first?
2. **Budget allocation?** Free tier or pay for speed?
3. **Trade both?** Or just track recommendations?
4. **Real money?** Or paper trade both until winner clear?

**My recommendation**:
- Start both TODAY (maximize data collection)
- Use FREE tier (run locally)
- PAPER TRADE both (no risk)
- Deploy $2K to winner after 30 days + IC > 0.05

---

**Ready to build this?** 🚀
