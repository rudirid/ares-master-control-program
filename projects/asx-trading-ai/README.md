# ASX Stock Trading Analysis System

A comprehensive Python-based system for collecting, analyzing, and backtesting news-driven trading strategies for ASX stocks.

## Features

### Data Collection
- **Stock Price Scraper**: Download historical OHLCV data via yfinance
- **ASX Announcements**: Scrape official company announcements
- **AFR News**: Collect articles from Australian Financial Review
- **Director Trades**: Track insider trading activity
- **HotCopper Sentiment**: Analyze forum discussions

### Analysis Tools
- **Local Sentiment Analyzer**: Rule-based NLP sentiment analysis (300+ financial keywords)
- **Price Impact Analysis**: Correlate news sentiment with actual price movements
- **Pattern Recognition**: Identify which news categories predict price changes
- **Theme Extraction**: Categorize news by theme (earnings, acquisitions, regulatory, etc.)

### Backtesting System
- **Historical Simulation**: Replay news day-by-day with realistic trading
- **Position Management**: Automated position sizing and risk management
- **Cost Modeling**: Realistic commission and slippage simulation
- **Benchmark Comparison**: Compare against buy-and-hold strategies
- **Detailed Trade Logs**: Track every decision with full audit trail

### Paper Trading System
- **Real-Time Monitoring**: Automated news monitoring and analysis
- **Pattern-Based Recommendations**: Uses validated patterns for confidence scoring
- **Position Tracking**: Monitors recommendations without executing real trades
- **Daily Summaries**: Automated performance reports
- **Live Dashboard**: Real-time visualization of performance vs backtest
- **Email Alerts**: Optional daily summary emails

### Visualization
- **Interactive Dashboards**: View stock data and news in real-time
- **Pattern Analysis Charts**: Visualize predictive power of news themes
- **Performance Reports**: Comprehensive backtest results with metrics
- **Paper Trading Dashboard**: Live performance tracking and comparison

## Quick Start

### Installation

```bash
# Clone or download the repository
cd StockTradingAI

# Install dependencies
pip install -r requirements.txt

# Configure your settings (if needed)
# Edit config.py with your custom settings
```

### Basic Workflow

```bash
# 1. Download historical stock prices
python download_asx_top100.py

# 2. Scrape news data (choose one or more)
python main.py asx          # ASX announcements
python main.py afr          # AFR news articles
python main.py director     # Director trades
python main.py hotcopper    # HotCopper sentiment

# 3. Analyze news sentiment and price impact
python analyze_news_impact.py

# 4. (Optional) Analyze patterns
python analysis/pattern_analyzer.py

# 5. Run backtest
python run_backtest.py

# 6. View results
# Open pattern_dashboard.html in browser
# Check results/backtest_trades.csv for trade log

# 7. Start paper trading (optional)
python paper_trading/scheduler.py  # Monitor and generate recommendations
python paper_trading_server.py     # Start dashboard (separate terminal)
# Open paper_trading_dashboard.html in browser
```

## Project Structure

```
StockTradingAI/
├── main.py                          # Main coordinator script
├── config.py                        # Configuration settings
├── stock_data.db                    # SQLite database
│
├── scrapers/                        # Data collection modules
│   ├── stock_prices.py              # Stock price downloader
│   ├── asx_announcements.py         # ASX official announcements
│   ├── afr_news.py                  # AFR news scraper
│   ├── director_trades.py           # Insider trading tracker
│   └── hotcopper_sentiment.py       # Forum sentiment analysis
│
├── analysis/                        # Analysis tools
│   ├── local_sentiment_analyzer.py  # Rule-based sentiment analysis
│   ├── price_analyzer.py            # Price change calculator
│   └── pattern_analyzer.py          # Pattern recognition
│
├── backtesting/                     # Backtesting system
│   ├── backtest_engine.py           # Core simulation engine
│   └── benchmark.py                 # Benchmark calculator
│
├── paper_trading/                   # Paper trading system
│   ├── recommendation_engine.py     # Generate trade recommendations
│   ├── paper_trader.py              # Track positions
│   ├── daily_summary.py             # Daily performance reports
│   └── scheduler.py                 # Automated monitoring
│
├── results/                         # Output files
│   ├── news_impact_analysis.csv     # Sentiment + price data
│   ├── pattern_analysis.json        # Pattern metrics
│   ├── backtest_trades.csv          # Trade history
│   └── daily_summaries/             # Paper trading summaries
│
├── dashboard.html                   # Data viewer dashboard
├── dashboard_server.py              # Dashboard backend
├── pattern_dashboard.html           # Pattern analysis viewer
├── paper_trading_dashboard.html     # Paper trading dashboard
├── paper_trading_server.py          # Paper trading API server
│
├── analyze_news_impact.py           # News analysis script
├── run_backtest.py                  # Backtest runner
├── download_asx_top100.py           # Price data downloader
│
└── docs/
    ├── README.md                    # This file
    ├── BACKTESTING_GUIDE.md         # Backtesting documentation
    ├── PATTERN_ANALYSIS_GUIDE.md    # Pattern analysis guide
    └── PAPER_TRADING_GUIDE.md       # Paper trading guide
```

## Database Schema

### Tables

**stock_prices**
- Daily OHLCV data for ASX stocks
- Fields: ticker, date, open, high, low, close, volume, dividends, stock_splits

**news_articles**
- News articles from various sources
- Fields: source, ticker, title, content, url, datetime, sentiment_score, themes

**asx_announcements**
- Official ASX company announcements
- Fields: ticker, title, announcement_type, datetime, url, pdf_url, num_pages, content

**director_trades**
- Insider trading activity
- Fields: ticker, company_name, director_name, transaction_date, transaction_type, shares, value, price, balance

**hotcopper_sentiment**
- Forum discussion sentiment
- Fields: ticker, post_date, author, sentiment_score, post_content, post_url, thread_title

**paper_recommendations**
- Paper trading recommendations
- Fields: recommendation_id, ticker, action, confidence, sentiment details, entry/exit prices, outcome

**paper_performance**
- Daily paper trading performance
- Fields: date, total_recommendations, win_rate, total_return_pct, high_confidence_win_rate

## Key Components

### 1. Sentiment Analysis

Uses rule-based NLP with financial keyword dictionaries:
- 300+ positive/negative keywords
- Negation handling
- Intensifier detection
- Theme extraction (12 categories)
- Confidence scoring

**No API required** - runs completely locally.

### 2. Price Impact Analysis

Calculates price changes at multiple timeframes:
- 1-day impact (immediate reaction)
- 3-day impact (short-term follow-through)
- 7-day impact (medium-term trend)

Correlates sentiment with actual price movements.

### 3. Pattern Recognition

Identifies predictive patterns:
- Theme performance (which categories predict best)
- Time lag analysis (when markets react)
- Magnitude analysis (typical move sizes)
- Directional accuracy (correct prediction rate)
- False positive rates (weak signal identification)

### 4. Backtesting Engine

Simulates realistic trading:
- Day-by-day replay of historical news
- Signal generation from sentiment
- Position sizing (max % per position)
- Trading costs (commission + slippage)
- Holding period management
- Performance metrics tracking

## Configuration

### Backtest Parameters

Adjustable via command line:
```bash
python run_backtest.py \
  --capital 100000 \           # Initial capital
  --commission 0.1 \           # Commission %
  --slippage 0.05 \            # Slippage %
  --max-position 0.2 \         # Max 20% per position
  --confidence 0.5 \           # Min confidence threshold
  --sentiment-score 0.2 \      # Min sentiment threshold
  --holding-period 7 \         # Days to hold
  --allow-shorting             # Enable short selling
```

## Analysis Guides

### Pattern Analysis

See **PATTERN_ANALYSIS_GUIDE.md** for:
- Understanding theme performance
- Time lag analysis
- Magnitude vs sentiment
- False positive identification
- Building trading strategies

### Backtesting

See **BACKTESTING_GUIDE.md** for:
- Running backtests
- Parameter optimization
- Interpreting results
- Troubleshooting issues
- Best practices

### Paper Trading

See **PAPER_TRADING_GUIDE.md** for:
- Setting up automated monitoring
- Generating recommendations
- Tracking performance
- Daily summaries
- Live dashboard
- Comparing vs backtest

## Usage Examples

### Example 1: Collecting Data

```bash
# Download 2 years of price data for ASX top 100
python download_asx_top100.py

# Scrape today's ASX announcements
python main.py asx

# Scrape AFR news articles
python main.py afr --pages 5

# Check database
python -c "import sqlite3; conn=sqlite3.connect('stock_data.db'); \
  print('Articles:', conn.execute('SELECT COUNT(*) FROM news_articles').fetchone()[0]); \
  print('Prices:', conn.execute('SELECT COUNT(*) FROM stock_prices').fetchone()[0])"
```

### Example 2: Analysis Pipeline

```bash
# Analyze news sentiment and price impact
python analyze_news_impact.py

# Generate pattern insights
python analysis/pattern_analyzer.py

# View pattern dashboard
# Open pattern_dashboard.html in browser
```

### Example 3: Backtesting Strategy

```bash
# Conservative strategy (high confidence only)
python run_backtest.py \
  --confidence 0.7 \
  --sentiment-score 0.4 \
  --max-position 0.15 \
  --holding-period 14

# Aggressive strategy (more trades)
python run_backtest.py \
  --confidence 0.3 \
  --sentiment-score 0.1 \
  --max-position 0.25 \
  --holding-period 3
```

### Example 4: Paper Trading

```bash
# Start automated monitoring (Terminal 1)
python paper_trading/scheduler.py --confidence 0.6

# Start dashboard server (Terminal 2)
python paper_trading_server.py

# Open paper_trading_dashboard.html in browser

# Generate daily summary manually
python paper_trading/daily_summary.py
```

### Example 5: Custom Analysis

```python
import pandas as pd
import sqlite3

# Load trade history
trades = pd.read_csv('results/backtest_trades.csv')

# Analyze by sentiment
print(trades.groupby('sentiment')['return_pct'].mean())

# Find best trades
best_trades = trades.nlargest(10, 'profit_loss')
print(best_trades[['ticker', 'entry_date', 'profit_loss', 'return_pct']])

# Check theme performance
conn = sqlite3.connect('stock_data.db')
articles = pd.read_sql('SELECT * FROM news_articles', conn)
print(articles['themes'].value_counts())
```

## Performance Metrics

### Backtest Metrics

- **Total Return**: Overall percentage gain/loss
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Ratio of average win to average loss
- **Max Drawdown**: Largest peak-to-trough decline
- **Outperformance**: Return vs buy-and-hold benchmark

### Pattern Metrics

- **Correlation**: Sentiment vs price direction (-1 to +1)
- **Directional Accuracy**: % correct predictions
- **False Positive Rate**: % strong signals with no movement
- **Time Lag**: When price reactions occur
- **Magnitude**: Typical move sizes by category

## Data Requirements

### Minimum for Backtesting

- 10+ news articles with price data
- 1+ month historical coverage
- Price data for all mentioned stocks

### Recommended for Reliability

- 100+ news articles
- 6+ months historical data
- Multiple news sources
- Various market conditions

## Limitations & Disclaimers

### System Limitations

- **Sentiment Analysis**: Rule-based, not AI/ML
- **Look-ahead Bias**: Backtests can overestimate performance
- **Survivorship Bias**: Only includes existing stocks
- **Cost Modeling**: Simplified commission/slippage
- **Market Impact**: Not modeled for large orders

### Legal Disclaimers

**This system is for educational and research purposes only.**

- Not financial advice
- Past performance ≠ future results
- Always do your own research
- Consider consulting a financial advisor
- Test thoroughly before live trading
- Understand all risks involved

### Ethical Scraping

- Respects robots.txt
- Rate limiting implemented
- User-agent identification
- For personal use only

## Troubleshooting

### Common Issues

**"No articles with price data"**
- Articles need to be 7+ days old for full analysis
- Run `python download_asx_top100.py` first
- Check database has data

**"Module not found"**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (3.11+ recommended)

**"Database locked"**
- Close dashboard_server.py if running
- Close any database browsers

**Scraper errors**
- Website structure may have changed
- Check internet connection
- Verify URLs in config.py

## Development

### Adding New Scrapers

1. Create new file in `scrapers/`
2. Inherit from base scraper class
3. Implement required methods
4. Add to `main.py` coordinator
5. Update database schema if needed

### Extending Analysis

1. Create new analyzer in `analysis/`
2. Load data from database or CSV
3. Compute custom metrics
4. Export results to JSON/CSV

### Custom Trading Strategies

Modify `backtesting/backtest_engine.py`:
- Update `generate_signal()` method
- Add new strategy parameters
- Implement in `execute_buy()` logic

## Version History

**v1.0.0** (2025-10-09)
- Initial release
- Complete data collection pipeline
- Local sentiment analysis
- Pattern recognition system
- Full backtesting engine
- Paper trading system
- Interactive dashboards
- Automated monitoring and recommendations
- Comprehensive documentation

## Credits

**Author**: Claude Code
**Date**: 2025-10-09
**License**: MIT (educational use)

---

**Remember**: This is a research and educational tool. Always validate findings, test thoroughly, and understand the risks before any real trading.
