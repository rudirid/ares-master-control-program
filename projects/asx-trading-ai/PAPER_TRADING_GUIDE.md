# Paper Trading System Guide

## Overview

The paper trading system monitors news in real-time (or via daily scrapes), analyzes articles using validated patterns, generates trade recommendations, and tracks their performance without executing real trades.

## Features

- **Automated News Monitoring**: Continuously checks for new articles
- **Pattern-Based Analysis**: Uses validated patterns to score recommendations
- **Confidence Scoring**: Multi-factor confidence calculation
- **Position Tracking**: Monitors active recommendations and auto-closes after holding period
- **Daily Summaries**: Automated daily performance reports
- **Live Dashboard**: Real-time performance visualization
- **Backtest Comparison**: Compare live performance vs backtest expectations

## Quick Start

### 1. Initial Setup

Ensure you have:
- Historical price data downloaded
- Pattern analysis completed (provides better recommendations)

```bash
# Download price data
python download_asx_top100.py

# Analyze patterns (optional but recommended)
python analyze_news_impact.py
python analysis/pattern_analyzer.py
```

### 2. Start the Scheduler

The scheduler monitors for new articles and generates recommendations automatically:

```bash
# Run with default settings
python paper_trading/scheduler.py

# Custom settings
python paper_trading/scheduler.py \
  --confidence 0.6 \
  --sentiment 0.3 \
  --holding-days 5 \
  --summary-time 18:00 \
  --interval 600
```

### 3. Start the Dashboard Server

In a separate terminal, start the dashboard server:

```bash
python paper_trading_server.py
```

### 4. View Dashboard

Open `paper_trading_dashboard.html` in your browser to see:
- Live performance metrics
- Recent recommendations
- Active positions
- Performance charts
- Backtest comparison

## How It Works

### News Processing Flow

```
1. New article scraped → Database
         ↓
2. Scheduler detects new article
         ↓
3. Recommendation Engine analyzes:
   - Sentiment analysis
   - Theme extraction
   - Pattern performance lookup
   - Confidence calculation
         ↓
4. If confidence > threshold:
   → Generate recommendation
   → Log to database
   → Activate with current price
         ↓
5. Paper Trader tracks position
         ↓
6. After holding period:
   → Auto-close position
   → Calculate actual return
   → Record outcome (WIN/LOSS/NEUTRAL)
```

### Recommendation Generation

**Confidence Score** combines:
- **Sentiment confidence** (30%): How certain the sentiment model is
- **Sentiment strength** (30%): Absolute value of sentiment score
- **Theme correlation** (20%): Historical pattern correlation
- **Theme accuracy** (20%): Historical directional accuracy

**Thresholds** (configurable):
- Minimum confidence: 0.5 (50%)
- Minimum sentiment: 0.2 (absolute)

**Actions**:
- `BUY`: Positive sentiment above threshold
- `SELL/AVOID`: Negative sentiment above threshold (tracks inverse)

### Position Management

**Entry**:
- Price: Latest available close price
- Date: When recommendation is activated

**Exit**:
- Automatic after `holding_days` (default: 7)
- Price: Close price on exit date

**Outcome**:
- `WIN`: Return > 0.5%
- `LOSS`: Return < -0.5%
- `NEUTRAL`: Return between -0.5% and 0.5%

## Configuration

### Scheduler Parameters

**`--confidence`** (default: 0.5)
- Minimum confidence to generate recommendation
- Range: 0.0 to 1.0
- Higher = fewer but more confident trades

**`--sentiment`** (default: 0.2)
- Minimum absolute sentiment score
- Range: 0.0 to 1.0
- Higher = stronger sentiment required

**`--holding-days`** (default: 7)
- Days to hold position before auto-closing
- Typical: 3-14 days

**`--summary-time`** (default: 17:00)
- Time to generate daily summary
- Format: HH:MM (24-hour)

**`--interval`** (default: 300)
- Seconds between news checks
- Typical: 300 (5 min) to 3600 (1 hour)

**`--once`**
- Run once and exit (for cron jobs)

### Example Configurations

**Conservative Strategy**:
```bash
python paper_trading/scheduler.py \
  --confidence 0.7 \
  --sentiment 0.4 \
  --holding-days 10
```

**Aggressive Strategy**:
```bash
python paper_trading/scheduler.py \
  --confidence 0.4 \
  --sentiment 0.15 \
  --holding-days 3
```

**Daily Cron Job** (run once per day):
```bash
# Add to crontab: Run at 9 AM daily
0 9 * * * cd /path/to/StockTradingAI && python paper_trading/scheduler.py --once
```

## Daily Summaries

### Automatic Generation

Summaries are automatically generated at the configured time (default: 5 PM).

### Manual Generation

```bash
python paper_trading/daily_summary.py
```

### Summary Contents

**Today's Activity**:
- New recommendations
- Positions closed
- Details of each

**Active Positions**:
- Current open positions
- Days held
- Entry prices

**Performance Metrics**:
- Last 7 days: Win rate, returns
- Last 30 days: Win rate, returns
- High confidence performance

### Output Formats

Summaries are saved in three formats:
- **JSON**: `results/daily_summaries/summary_YYYY-MM-DD.json`
- **Text**: `results/daily_summaries/summary_YYYY-MM-DD.txt`
- **HTML**: `results/daily_summaries/summary_YYYY-MM-DD.html`

### Email Summaries

To send summaries via email, modify `daily_summary.py`:

```python
from paper_trading.daily_summary import DailySummaryGenerator

generator = DailySummaryGenerator('stock_data.db')
summary = generator.generate_summary()

smtp_config = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'username': 'your_email@gmail.com',
    'password': 'your_app_password',
    'from_email': 'your_email@gmail.com'
}

generator.send_email(summary, 'recipient@example.com', smtp_config)
```

## Dashboard

### Starting the Server

```bash
python paper_trading_server.py

# Custom port
python paper_trading_server.py --port 8001
```

### Dashboard Features

**Performance Metrics** (top cards):
- Total recommendations
- Win rate
- Total return
- High confidence win rate

**Performance Chart**:
- Cumulative return over time
- Shows growth of paper portfolio

**Win Rate Analysis**:
- All trades
- High confidence only
- Pattern-based vs sentiment-only

**Recommendations Table**:
- Tabs: All / Active / Closed / Today
- Details: Date, ticker, action, confidence, return, outcome

**Backtest Comparison**:
- Live performance vs backtest
- Win rate, average return, total return
- Identifies if live is meeting expectations

### Auto-Refresh

Dashboard auto-refreshes every 60 seconds.

## Database Schema

### paper_recommendations

Stores all recommendations and their outcomes:

```sql
CREATE TABLE paper_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    timestamp TEXT,
    ticker TEXT,
    action TEXT,  -- BUY, SELL/AVOID
    confidence REAL,

    sentiment TEXT,
    sentiment_score REAL,
    sentiment_confidence REAL,

    article_id INTEGER,
    article_title TEXT,
    article_source TEXT,

    themes TEXT,  -- JSON array
    theme_performance TEXT,  -- JSON object

    reasoning TEXT,
    pattern_based INTEGER,  -- 1 if using patterns, 0 if sentiment-only

    entry_price REAL,
    entry_date TEXT,
    exit_price REAL,
    exit_date TEXT,

    status TEXT,  -- PENDING, ACTIVE, CLOSED
    holding_days INTEGER,

    actual_return_pct REAL,
    outcome TEXT,  -- WIN, LOSS, NEUTRAL
    outcome_details TEXT
)
```

### paper_performance

Aggregated daily performance:

```sql
CREATE TABLE paper_performance (
    date TEXT PRIMARY KEY,
    total_recommendations INTEGER,
    active_positions INTEGER,
    closed_positions INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate REAL,
    total_return_pct REAL,
    avg_return_pct REAL,
    high_confidence_count INTEGER,
    high_confidence_win_rate REAL,
    summary_text TEXT
)
```

## Usage Examples

### Example 1: Start Everything

Terminal 1 - Scheduler:
```bash
python paper_trading/scheduler.py --confidence 0.6
```

Terminal 2 - Dashboard:
```bash
python paper_trading_server.py
```

Browser:
```
Open: paper_trading_dashboard.html
```

### Example 2: Test Recommendations

```python
from paper_trading.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()

# Test article
article = {
    'ticker': 'BHP',
    'title': 'BHP reports record profits',
    'content': 'BHP delivered strong earnings growth...',
    'source': 'AFR'
}

# Generate recommendation
rec = engine.generate_recommendation(article, min_confidence=0.5)

if rec:
    print(f"Action: {rec['action']}")
    print(f"Confidence: {rec['confidence']:.2f}")
    print(f"Reasoning: {rec['reasoning']}")
```

### Example 3: Manual Position Management

```python
from paper_trading.paper_trader import PaperTrader

trader = PaperTrader('stock_data.db')

# Log recommendation
trader.log_recommendation(recommendation_dict)

# Activate with price
trader.activate_recommendation('REC_001', 45.50)

# Later, close position
trader.close_recommendation('REC_001', 47.20)

# Get performance
summary = trader.get_performance_summary(days=7)
print(f"Win rate: {summary['win_rate']}%")
```

### Example 4: Query Performance

```python
import sqlite3

conn = sqlite3.connect('stock_data.db')

# Best performing recommendations
query = """
    SELECT ticker, action, confidence, actual_return_pct
    FROM paper_recommendations
    WHERE status = 'CLOSED'
    ORDER BY actual_return_pct DESC
    LIMIT 10
"""

for row in conn.execute(query):
    print(f"{row[0]}: {row[3]:+.2f}% (confidence: {row[2]:.2f})")
```

## Interpreting Results

### Good Performance Indicators

✓ **Win rate > 55%**: Better than random
✓ **High confidence win rate > 65%**: Pattern validation working
✓ **Live ≈ Backtest**: Strategy is robust
✓ **Avg return positive**: Profitable on average
✓ **Pattern-based > Sentiment-only**: Patterns adding value

### Warning Signs

⚠ **Win rate < 45%**: Strategy may need adjustment
⚠ **Live << Backtest**: Overfitting or market change
⚠ **High confidence failing**: Confidence scoring needs tuning
⚠ **Many neutral outcomes**: Thresholds too aggressive

### Optimization

**If win rate is low**:
- Increase confidence threshold
- Increase sentiment threshold
- Filter by specific themes

**If not enough trades**:
- Lower confidence threshold
- Lower sentiment threshold
- Reduce holding period

**If returns too small**:
- Focus on high-magnitude themes
- Increase holding period
- Filter by expected move size

## Troubleshooting

### "No new recommendations"

**Check**:
1. Are new articles being scraped?
   ```bash
   python -c "import sqlite3; conn=sqlite3.connect('stock_data.db'); print('Articles:', conn.execute('SELECT COUNT(*) FROM news_articles').fetchone()[0])"
   ```

2. Are thresholds too high?
   - Try `--confidence 0.3 --sentiment 0.1`

3. Is sentiment too neutral?
   - Check recent articles in database

### "Dashboard shows no data"

**Solutions**:
1. Start server: `python paper_trading_server.py`
2. Check server is running on port 8001
3. Refresh browser
4. Check browser console for errors

### "Recommendations not activating"

**Cause**: No price data for ticker

**Solution**:
```bash
# Check if stock prices exist
python -c "import sqlite3; conn=sqlite3.connect('stock_data.db'); print(conn.execute('SELECT COUNT(*) FROM stock_prices WHERE ticker=?', ('BHP',)).fetchone()[0])"

# Download if missing
python download_asx_top100.py
```

### "Scheduler crashed"

**Check logs** for errors:
- Database locked: Close other connections
- Import errors: Check dependencies installed
- Memory issues: Reduce check interval

## Best Practices

### 1. Start with Backtesting

Before paper trading:
1. Run backtest on historical data
2. Validate win rate and returns
3. Use backtest parameters for paper trading

### 2. Monitor Daily

- Check dashboard daily
- Review recommendations
- Analyze wins and losses
- Adjust thresholds as needed

### 3. Keep Patterns Updated

Periodically re-run pattern analysis:
```bash
python analyze_news_impact.py
python analysis/pattern_analyzer.py
```

### 4. Track Confidence Calibration

Monitor if high confidence really means high win rate:
- If high confidence fails often: Adjust confidence calculation
- If low confidence succeeds: Thresholds may be wrong

### 5. Version Control Settings

Document your configuration changes:
```bash
# Save current config
echo "confidence=0.6, sentiment=0.3, holding=7" > paper_trading_config.txt
```

### 6. Compare to Benchmark

Regularly compare to buy-and-hold:
- Are you beating the market?
- Is the effort worth the outperformance?

## Advanced Usage

### Custom Confidence Calculation

Modify `recommendation_engine.py`:

```python
def calculate_confidence_score(self, ...):
    # Add your own factors
    news_source_weight = 1.2 if article['source'] == 'AFR' else 1.0

    confidence = (
        base_confidence * 0.3 +
        sentiment_strength * 0.3 +
        theme_correlation * 0.2 +
        theme_accuracy * 0.2
    ) * news_source_weight

    return confidence
```

### Theme Filtering

Only trade specific themes:

```python
def generate_recommendation(self, article, ...):
    analysis = self.analyze_article(article)
    themes = analysis.get('themes', [])

    # Only earnings and acquisition themes
    if not any(t in ['earnings', 'acquisition'] for t in themes):
        return None

    # Continue with recommendation...
```

### Multi-Strategy

Run multiple strategies in parallel:

```bash
# Terminal 1: Conservative
python paper_trading/scheduler.py --confidence 0.7 --interval 600

# Terminal 2: Aggressive
python paper_trading/scheduler.py --confidence 0.4 --interval 300
```

Use different databases or add strategy tags.

## Integration with Live Trading

**After successful paper trading** (3+ months, consistent profits):

1. **Start small**: Use 1-5% of intended capital
2. **Match parameters**: Use exact same thresholds
3. **Monitor closely**: Compare live vs paper
4. **Scale gradually**: Increase position sizes slowly
5. **Automate carefully**: Test extensively first

**Never automate without**:
- Extensive paper trading validation
- Risk management controls
- Kill switches
- Position limits
- Drawdown limits

## Files

- `paper_trading/recommendation_engine.py`: Generates recommendations
- `paper_trading/paper_trader.py`: Tracks positions
- `paper_trading/daily_summary.py`: Creates summaries
- `paper_trading/scheduler.py`: Automated monitoring
- `paper_trading_dashboard.html`: Interactive dashboard
- `paper_trading_server.py`: Dashboard backend
- `results/daily_summaries/`: Summary outputs

## Next Steps

After getting comfortable with paper trading:

1. **Optimize**: Fine-tune thresholds based on results
2. **Analyze**: Study winning vs losing trades
3. **Validate**: Ensure live matches backtest
4. **Scale**: Increase virtual capital if successful
5. **Plan**: Develop transition plan to live trading

---

**Remember**: Paper trading is risk-free but market-realistic. Use it to validate your strategy before risking real capital.
