# Backtesting System Guide

## Overview

The backtesting system simulates historical trading based on news sentiment signals. It replays news day-by-day, generates buy/sell signals, simulates trades with realistic costs, and compares performance against a buy-and-hold benchmark.

## Quick Start

### Prerequisites

Before running backtests, you need historical data:

1. **Stock Price Data**: At least 2 years of historical prices
   ```bash
   python download_asx_top100.py
   ```

2. **News Articles**: Historical news with dates in the past
   - Import historical news or wait for scraped news to age
   - Articles need to be at least 7 days old for full analysis

3. **News Impact Analysis**: Sentiment analysis + price changes
   ```bash
   python analyze_news_impact.py
   ```

### Running a Backtest

Basic command:
```bash
python run_backtest.py
```

With custom parameters:
```bash
python run_backtest.py --capital 50000 --confidence 0.7 --holding-period 5
```

## Understanding the System

### Data Flow

```
Historical News Articles
         ↓
Sentiment Analysis (analyze_news_impact.py)
         ↓
Pattern Analysis (pattern_analyzer.py) [optional, for insights]
         ↓
Backtest Simulation (run_backtest.py)
         ↓
Performance Report + Trade Log
```

### Trading Strategy

The backtest implements a simple sentiment-based strategy:

**Buy Signal**:
- Positive sentiment
- Sentiment score > minimum threshold (default: 0.2)
- Confidence > minimum threshold (default: 0.5)
- No existing position in the stock

**Sell Signal**:
- Holding period reached (default: 7 days)
- End of backtest period

**Position Sizing**:
- Maximum 20% of portfolio per position (configurable)
- Integer shares only (no fractional)
- Requires sufficient cash

**Trading Costs**:
- Commission: 0.1% per trade (default)
- Slippage: 0.05% (default)
- Entry: Buy at next day's open + slippage
- Exit: Sell at target date + slippage

## Configuration Parameters

### Capital Settings

**`--capital`** (default: 100000)
- Initial trading capital in dollars
- Example: `--capital 50000` for $50k

### Trading Costs

**`--commission`** (default: 0.1)
- Commission as percentage of trade value
- Example: `--commission 0.15` for 0.15%

**`--slippage`** (default: 0.05)
- Slippage as percentage of price
- Models market impact and execution variance
- Example: `--slippage 0.1` for 0.1%

### Position Management

**`--max-position`** (default: 0.2)
- Maximum position size as fraction of portfolio
- 0.2 = 20% max per stock
- Example: `--max-position 0.15` for 15% max

**`--holding-period`** (default: 7)
- Number of days to hold positions
- Example: `--holding-period 14` for 2 weeks

### Signal Thresholds

**`--confidence`** (default: 0.5)
- Minimum confidence score to trade (0.0 to 1.0)
- Higher = fewer but more confident trades
- Example: `--confidence 0.7` for high confidence only

**`--sentiment-score`** (default: 0.2)
- Minimum absolute sentiment score to trade
- Higher = stronger sentiment required
- Example: `--sentiment-score 0.4` for strong sentiment only

### Advanced Options

**`--allow-shorting`**
- Enable short selling on negative sentiment
- Flag only, no value needed
- Example: `--allow-shorting`

**`--csv`** (default: results/news_impact_analysis.csv)
- Path to input CSV file
- Example: `--csv custom_data.csv`

**`--output`** (default: results/backtest_trades.csv)
- Path for detailed trade log export
- Example: `--output my_trades.csv`

## Output Explained

### Strategy Performance

```
Capital
  Initial: $100,000.00
  Final:   $105,240.00
  Total Return: +5.24%
```
- **Initial Capital**: Starting amount
- **Final Capital**: Ending cash + closed positions
- **Total Return**: Percentage gain/loss

```
Trades
  Total: 24
  Winning: 15 (62.5%)
  Losing: 9
```
- **Total Trades**: Number of completed buy/sell cycles
- **Winning Trades**: Trades with profit > $0
- **Win Rate**: Percentage of winning trades

```
Profitability
  Total P/L: $+5,240.00
  Avg Win: $+850.00
  Avg Loss: $-320.00
  Profit Factor: 2.66
```
- **Total P/L**: Sum of all profits and losses
- **Avg Win**: Average profit on winning trades
- **Avg Loss**: Average loss on losing trades
- **Profit Factor**: Ratio of avg win to avg loss (>1 is good)

```
Risk
  Max Drawdown: 8.45%
```
- **Max Drawdown**: Largest peak-to-trough decline
- Lower is better (less volatility)

```
Costs
  Total Commission: $650.00
  Total Slippage: $325.00
```
- **Commission**: Sum of all commission fees paid
- **Slippage**: Total cost of execution slippage

### Benchmark Comparison

```
Buy & Hold ASX200
  Final Value: $103,500.00
  Total Return: +3.50%
  Max Drawdown: 12.30%
```
- Shows what you'd earn from passive investing
- Uses equal-weight portfolio of all stocks in your news data

```
Comparison
  Strategy Return: +5.24%
  Benchmark Return: +3.50%
  Outperformance: +1.74%

  Strategy OUTPERFORMED benchmark by 1.74%
```
- **Positive outperformance**: Your strategy beat buy-and-hold
- **Negative outperformance**: Buy-and-hold was better

## Detailed Trade Log

After each backtest, a CSV file is generated with every trade:

**File**: `results/backtest_trades.csv`

**Columns**:
- `trade_id`: Unique trade identifier
- `ticker`: Stock symbol
- `signal`: BUY, SELL, SHORT, COVER
- `entry_date`: When position was opened
- `entry_price`: Execution price (including slippage)
- `exit_date`: When position was closed
- `exit_price`: Exit execution price
- `shares`: Number of shares traded
- `profit_loss`: Dollar profit/loss
- `return_pct`: Percentage return
- `commission`: Total commission paid (entry + exit)
- `slippage`: Total slippage cost
- `sentiment`: Article sentiment (positive/negative/neutral)
- `sentiment_score`: Numeric sentiment score
- `confidence`: Model confidence (0-1)
- `reason`: Why position was opened/closed

## Optimization Strategies

### Conservative Strategy

Focus on high-quality signals:
```bash
python run_backtest.py \
  --confidence 0.7 \
  --sentiment-score 0.4 \
  --max-position 0.1 \
  --holding-period 14
```

**Pros**: Lower risk, higher win rate
**Cons**: Fewer trades, may miss opportunities

### Aggressive Strategy

Trade more signals:
```bash
python run_backtest.py \
  --confidence 0.3 \
  --sentiment-score 0.1 \
  --max-position 0.3 \
  --holding-period 3
```

**Pros**: More trades, capture quick moves
**Cons**: Higher risk, more false signals

### Low-Cost Strategy

Minimize trading friction:
```bash
python run_backtest.py \
  --commission 0.05 \
  --slippage 0.02 \
  --holding-period 21
```

**Pros**: Lower costs, fewer trades
**Cons**: Slower to react

## Interpreting Results

### Good Performance Indicators

- **Win rate > 55%**: Better than random
- **Profit factor > 2.0**: Wins are much larger than losses
- **Outperformance > 5%**: Significantly beating benchmark
- **Max drawdown < 15%**: Reasonable risk level

### Warning Signs

- **Win rate < 45%**: Losing more often than winning
- **Profit factor < 1.2**: Wins barely cover losses
- **Underperformance vs benchmark**: Buy-and-hold is better
- **Max drawdown > 30%**: High volatility/risk

### Common Issues

**No trades executed**:
- Thresholds too high (lower `--confidence` and `--sentiment-score`)
- Not enough historical data
- No strong sentiment signals in data

**Poor performance**:
- Overfitting to small sample
- Market conditions changed
- Strategy parameters need optimization
- Data quality issues

**High costs eroding returns**:
- Too many trades (increase `--holding-period`)
- Position sizes too small (increase `--max-position`)
- Commission/slippage too high (reduce if unrealistic)

## Advanced Analysis

### Parameter Optimization

Test multiple configurations:

```bash
# Test different confidence thresholds
for conf in 0.3 0.5 0.7; do
  python run_backtest.py --confidence $conf --output "results/conf_${conf}.csv"
done
```

Then compare results to find optimal parameters.

### Walk-Forward Testing

Avoid overfitting by testing on out-of-sample data:

1. **Train period**: Optimize parameters on 2022-2023 data
2. **Test period**: Validate on 2024 data
3. **Live period**: Apply to future trading

### Combining with Pattern Analysis

Use pattern analysis to inform strategy:

1. Run pattern analysis:
   ```bash
   python analysis/pattern_analyzer.py
   ```

2. Identify best-performing themes (high correlation)

3. Filter backtest to only those themes:
   - Modify `backtest_engine.py` to check article themes
   - Only trade articles with high-correlation themes

## Data Requirements

### Minimum Data

- **10+ news articles** with complete price data
- **1+ month** of historical coverage
- **Price data** for all mentioned stocks

### Recommended Data

- **100+ news articles** for statistical significance
- **6+ months** of historical data
- **Multiple sources** (AFR, ASX announcements, etc.)
- **Various market conditions** (up, down, sideways)

### Data Quality Checklist

- [ ] Articles have accurate publication dates
- [ ] Stock prices available for all trade dates
- [ ] Sentiment analysis completed
- [ ] Price changes calculated (1d, 3d, 7d)
- [ ] No major gaps in price data
- [ ] Sufficient variety in stocks/sectors

## Troubleshooting

### "No trades executed"

**Check**:
1. Are there articles with price data?
   ```bash
   python -c "import pandas as pd; df=pd.read_csv('results/news_impact_analysis.csv'); print('Articles with price data:', df['price_change_pct_1d'].notna().sum())"
   ```

2. Are thresholds too restrictive?
   - Try `--confidence 0.3 --sentiment-score 0.1`

3. Is sentiment too neutral?
   - Check sentiment distribution in CSV

### "No price data available"

**Solutions**:
1. Download historical prices:
   ```bash
   python download_asx_top100.py
   ```

2. Check database has data:
   ```bash
   python -c "import sqlite3; conn=sqlite3.connect('stock_data.db'); print('Total prices:', conn.execute('SELECT COUNT(*) FROM stock_prices').fetchone()[0]); conn.close()"
   ```

3. Verify stock tickers match:
   - News articles use ASX format (e.g., "BHP")
   - Price data should match exactly

### "ValueError: NaTType does not support strftime"

**Cause**: All article dates are NaT (Not a Time)

**Solution**:
1. Check CSV has valid dates:
   ```bash
   python -c "import pandas as pd; df=pd.read_csv('results/news_impact_analysis.csv'); print(df['article_date'].head())"
   ```

2. Re-run news impact analysis:
   ```bash
   python analyze_news_impact.py
   ```

## Best Practices

### 1. Start Simple

Begin with default parameters:
```bash
python run_backtest.py
```

Analyze results, then adjust one parameter at a time.

### 2. Validate Assumptions

- Are costs realistic? (Check your broker's fees)
- Is slippage reasonable? (Higher for illiquid stocks)
- Is holding period appropriate? (Match your trading style)

### 3. Consider Transaction Costs

Trading costs add up quickly:
- $100k portfolio, 0.1% commission = $100 per trade
- 50 trades = $5,000 in fees
- Could turn 10% gain into 5% gain

### 4. Don't Overfit

- Test on out-of-sample data
- Use walk-forward validation
- Keep strategies simple
- Require statistical significance (30+ trades)

### 5. Monitor Performance

After live trading:
- Compare actual vs backtest results
- Track slippage (real vs assumed)
- Adjust parameters based on real data
- Re-run backtests periodically

## Next Steps

After backtesting:

1. **Validate**: Run on different time periods
2. **Optimize**: Fine-tune parameters for your style
3. **Paper Trade**: Test in real-time without money
4. **Review**: Analyze every trade decision
5. **Deploy**: Start with small capital
6. **Monitor**: Track performance vs backtest

## Files

- **`run_backtest.py`**: Main backtest runner (CLI interface)
- **`backtesting/backtest_engine.py`**: Core simulation engine
- **`backtesting/benchmark.py`**: Buy-and-hold comparison
- **`results/backtest_trades.csv`**: Detailed trade log (output)

## Support

For issues or questions:
1. Check this guide
2. Review code comments in `backtest_engine.py`
3. Examine trade log CSV for debugging
4. Verify input data quality first

## Example Workflow

Complete end-to-end example:

```bash
# 1. Download price data
python download_asx_top100.py

# 2. Run news analysis
python analyze_news_impact.py

# 3. Run pattern analysis (optional)
python analysis/pattern_analyzer.py

# 4. Run backtest with default settings
python run_backtest.py

# 5. Review results
cat results/backtest_trades.csv

# 6. Optimize - try higher confidence
python run_backtest.py --confidence 0.7

# 7. Compare results
# Look at win rate, return, and outperformance

# 8. Export for further analysis
python run_backtest.py --confidence 0.7 --output results/optimized_trades.csv
```

## Important Notes

- **Past performance does not guarantee future results**
- Backtesting can overestimate performance (look-ahead bias, survivor bias)
- Real trading involves emotions, which backtests don't capture
- Always start with paper trading before real money
- Consider taxes, which aren't modeled in backtests
- Market conditions change - strategies can stop working
