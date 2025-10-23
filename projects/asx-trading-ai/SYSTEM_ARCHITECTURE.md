# ASX Stock Trading AI - System Architecture

**Version**: 3.0.0
**Date**: 2025-10-10
**Status**: Production-ready for live paper trading

---

## Table of Contents

1. [Overview](#overview)
2. [System Structure](#system-structure)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Database Schema](#database-schema)
6. [Deployment](#deployment)

---

## Overview

The ASX Stock Trading AI is a comprehensive automated trading system that:
- Monitors ASX announcements in real-time
- Analyzes sentiment using NLP
- Applies behavioral finance filters
- Generates trading recommendations
- Tracks performance and self-improves
- Provides interactive dashboards and reporting

**Key Innovation**: TIME-based filtering - only trades fresh news (<30 min old) to capture information edge before it's priced in.

---

## System Structure

```
StockTradingAI/
│
├── analysis/                    # Signal generation and analysis
│   ├── behavioral_filters.py   # TIME, MATERIALITY, TIME-OF-DAY, CONTRARIAN filters
│   ├── local_sentiment_analyzer.py  # Rule-based sentiment analysis
│   ├── performance_attribution.py   # IC calculation, signal quality
│   ├── performance_attribution_live.py  # Live IC analysis
│   ├── technical_indicators.py      # RSI, MACD, MA, ATR
│   ├── pattern_analyzer.py          # Price pattern recognition
│   ├── price_analyzer.py            # Price movement analysis
│   ├── news_quality_filter.py       # Filter low-quality announcements
│   ├── multi_source_validator.py    # Cross-source news validation
│   └── sentiment_analyzer.py        # Advanced sentiment (future ML model)
│
├── backtesting/                 # Historical simulation
│   ├── backtest_engine.py      # Core backtesting logic
│   ├── historical_simulator.py # No look-ahead bias simulator
│   ├── dynamic_exit_manager.py # Adaptive exit strategies
│   └── benchmark.py            # Performance benchmarking
│
├── live_trading/               # Real-time trading (NEW in v3.0)
│   ├── announcement_monitor.py     # Monitor ASX for announcements
│   ├── live_recommendation_engine.py  # Generate real-time signals
│   ├── live_paper_trader.py        # Main orchestrator (runs 5 days)
│   ├── check_stats.py              # Quick stats dashboard
│   ├── daily_report.py             # Daily performance summary
│   ├── readiness_report.py         # Go-live decision framework
│   ├── gui_demo.py                 # Interactive demo (basic)
│   └── enhanced_gui_demo.py        # Interactive demo (detailed AI analysis)
│
├── paper_trading/              # Paper trading engine
│   ├── paper_trader.py         # Paper trading executor
│   ├── recommendation_engine.py    # Generate recommendations
│   ├── risk_manager.py         # 5-rule risk management
│   ├── daily_summary.py        # Daily P&L summaries
│   └── scheduler.py            # Automated scheduling
│
├── scrapers/                   # Data collection
│   ├── stock_prices.py         # yfinance price data
│   ├── asx_announcements.py    # ASX official announcements
│   ├── afr_news.py             # Australian Financial Review
│   ├── abc_news.py             # ABC News (WIP)
│   ├── smh_news.py             # Sydney Morning Herald (WIP)
│   ├── director_trades.py      # Insider trading data
│   ├── hotcopper.py            # Forum sentiment (WIP)
│   └── utils.py                # Scraping utilities
│
├── database/                   # Database management
│   └── init_db.py             # Database initialization
│
├── data/                       # Data storage
│   └── trading.db             # SQLite database (all tables)
│
├── logs/                       # System logs
│   └── [various log files]
│
├── results/                    # Analysis outputs
│   └── news_impact_analysis.csv
│
├── examples/                   # Code examples
│   └── afr_scraper_examples.py
│
└── [Documentation & Scripts]  # Root-level files (see below)
```

---

## Core Components

### 1. Live Trading System (v3.0 - NEW)

**Purpose**: Real-time announcement monitoring and signal generation

**Key Files**:
- `live_trading/announcement_monitor.py` (400 lines)
  - Monitors ASX website every 60 seconds
  - Captures announcement age (critical for TIME filter)
  - Stores in `live_announcements` table
  - Market hours detection (7 AM - 4:30 PM AEST)

- `live_trading/live_recommendation_engine.py` (423 lines)
  - Processes announcements in REAL-TIME
  - Applies ALL behavioral filters
  - Gets current market price via yfinance
  - Generates BUY/SELL recommendations
  - Stores full decision audit trail

- `live_trading/live_paper_trader.py` (279 lines)
  - Main orchestrator (combines monitor + engine)
  - Runs continuously for 5 days
  - Real-time console output
  - Session statistics tracking

**Data Flow**:
```
ASX Website → announcement_monitor.py → live_announcements table
                                     ↓
                         live_recommendation_engine.py
                                     ↓
                         live_recommendations table
```

### 2. Behavioral Filters (v3.0 - NEW)

**Purpose**: Filter out noise and apply behavioral finance principles

**File**: `analysis/behavioral_filters.py` (490 lines)

**Filters**:

1. **TimeFilter** (CRITICAL)
   - Reject announcements >30 minutes old
   - Ultra-fresh (<5 min): +0.15 confidence boost
   - Fresh (<30 min): +0.05 confidence boost
   - **Only active in LIVE mode** (not applicable to T+1 backtest)

2. **MaterialityFilter**
   - Filter 80% of announcements (administrative noise)
   - High materiality: Earnings, dividends, trading updates
   - Low materiality: Director notices, routine filings
   - Keyword-based scoring (0.0-1.0)

3. **TimeOfDayFilter**
   - Optimal: 10 AM - 2 PM AEST (+0.05 confidence)
   - Suboptimal: Opening/closing hours
   - **Only active in LIVE mode** (can't control entry time in backtest)

4. **ContrarianSignals**
   - Fade extreme sentiment (>0.85 or <-0.85)
   - When everyone loves a stock, reduce confidence (-0.15)
   - Protect against "priced in" moves

### 3. Self-Improvement System (v3.0 - NEW)

**Purpose**: Measure signal quality and optimize thresholds

**File**: `analysis/performance_attribution.py` (491 lines)

**Key Metrics**:

1. **Information Coefficient (IC)**
   - Spearman correlation between signal and returns
   - IC > 0.05: Signal has edge
   - IC < 0.05: No predictive power
   - IC < 0: Inverse relationship (flip logic)

2. **Threshold Optimization**
   - Tests confidence thresholds (0.5-0.9)
   - Optimizes for maximum Sharpe ratio
   - Prevents overfitting with validation

3. **Signal Quality Tracking**
   - Identifies which signals work (sentiment, technical, etc.)
   - Recommends KEEP / DISABLE / FLIP / OPTIMIZE
   - Generates actionable improvement reports

**Historical Results** (300-sample backtest):
```
Sentiment Score IC: 0.000 → NO EDGE (disable for historical)
Recommendation Confidence IC: -0.117 → INVERSE (use contrarian)
Win Rate: 34.0%
Sharpe: -2.91
```

**Hypothesis**: Live data IC > 0.05 (fresh news has edge)

### 4. Historical Backtesting

**Purpose**: Test strategies on historical data

**File**: `backtesting/historical_simulator.py` (600+ lines)

**Features**:
- No look-ahead bias validation
- Event log tracking all decisions
- Quality filter integration
- Technical analysis (soft modifier)
- Behavioral filters (mode-specific)

**Mode-Specific Configuration**:

**Backtest Mode:**
- TIME filter: DISABLED (not applicable to T+1)
- TIME-OF-DAY filter: DISABLED
- MATERIALITY filter: ENABLED
- CONTRARIAN filter: ENABLED
- Technical: SOFT modifier

**Live Mode:**
- TIME filter: ENABLED (critical)
- TIME-OF-DAY filter: ENABLED
- MATERIALITY filter: ENABLED
- CONTRARIAN filter: ENABLED
- Technical: SOFT modifier

### 5. Sentiment Analysis

**Current**: Rule-based (local_sentiment_analyzer.py)
- Positive/negative keyword matching
- 37% accuracy on historical data

**Future**: Transformer-based NLP model
- Fine-tuned on ASX announcements
- Target: 60%+ accuracy

### 6. Technical Analysis

**File**: `analysis/technical_indicators.py` (400+ lines)

**Indicators**:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Moving Averages (50-day, 200-day)
- ATR (Average True Range)

**Usage**: Soft modifier (adjusts confidence, doesn't reject trades)

### 7. Risk Management

**File**: `paper_trading/risk_manager.py`

**5-Rule System**:
1. Position sizing: 2% of capital per trade
2. Stop loss: 5% per trade
3. Daily loss limit: 5% of total capital
4. Max positions: 10 concurrent
5. Sector limits: 3 per sector max

### 8. Data Collection

**Scrapers**:
- `stock_prices.py` - yfinance API (real-time pricing)
- `asx_announcements.py` - ASX official announcements
- `afr_news.py` - Australian Financial Review
- `director_trades.py` - Insider trading data

**Status**:
- ✅ Stock prices (working)
- ✅ ASX announcements (working)
- ⚠️ AFR news (needs subscription)
- ⚠️ ABC/SMH (HTML selectors need update)
- ⚠️ HotCopper (rate limited)

---

## Data Flow

### Historical Backtest Flow

```
Database (historical data)
    ↓
historical_simulator.py
    ↓
For each announcement:
    1. Sentiment analysis
    2. Materiality filter (ENABLED)
    3. Contrarian signals (ENABLED)
    4. Technical analysis (soft modifier)
    5. TIME filter (DISABLED - not T+1 applicable)
    6. TIME-OF-DAY filter (DISABLED - can't control entry)
    7. Generate recommendation if confidence >= 0.6
    ↓
Position tracking (T+1 entry, 7-day hold)
    ↓
Performance attribution
    ↓
IC calculation, signal quality analysis
```

### Live Trading Flow (Monday Oct 13 - Friday Oct 17)

```
ASX Website (every 60 seconds)
    ↓
announcement_monitor.py
    ↓
live_announcements table (with timestamp and age)
    ↓
live_recommendation_engine.py
    ↓
For each announcement:
    1. TIME filter (ENABLED - reject if >30 min)
    2. MATERIALITY filter (ENABLED)
    3. TIME-OF-DAY filter (ENABLED - 10am-2pm optimal)
    4. Sentiment analysis
    5. Get REAL-TIME price (yfinance)
    6. Technical analysis (soft modifier)
    7. Contrarian signals (ENABLED)
    8. Generate recommendation if confidence >= 0.6
    ↓
live_recommendations table (with full decision log)
    ↓
[After 5 days]
    ↓
performance_attribution_live.py
    ↓
Calculate IC, win rate, Sharpe
    ↓
readiness_report.py
    ↓
GO / NO-GO decision for live trading
```

---

## Database Schema

### Tables

**1. stock_prices**
```sql
- id (primary key)
- ticker TEXT
- date DATE
- open, high, low, close REAL
- volume INTEGER
- adj_close REAL
```

**2. asx_announcements**
```sql
- id (primary key)
- ticker TEXT
- title TEXT
- announcement_type TEXT
- price_sensitive INTEGER (0/1)
- date_published TIMESTAMP
- content TEXT
- url TEXT UNIQUE
```

**3. news_articles**
```sql
- id (primary key)
- ticker TEXT
- title TEXT
- content TEXT
- source TEXT (AFR, ABC, SMH)
- published_date TIMESTAMP
- url TEXT UNIQUE
```

**4. live_announcements** (NEW in v3.0)
```sql
- id (primary key)
- ticker TEXT
- title TEXT
- announcement_type TEXT
- price_sensitive INTEGER
- asx_timestamp TIMESTAMP       -- When ASX published
- detected_timestamp TIMESTAMP  -- When we detected it
- age_minutes REAL              -- Critical for TIME filter
- url TEXT UNIQUE
- processed INTEGER (0/1)
- recommendation_generated INTEGER (0/1)
```

**5. live_recommendations** (NEW in v3.0)
```sql
- id (primary key)
- announcement_id INTEGER (FK)
- ticker TEXT
- recommendation TEXT (BUY/SELL)
- confidence REAL
- entry_price REAL              -- Real-time market price
- sentiment TEXT
- sentiment_score REAL
- sentiment_confidence REAL
- generated_timestamp TIMESTAMP
- filters_passed TEXT           -- Audit trail
- filters_failed TEXT
- decision_log TEXT             -- Full reasoning
```

---

## Documentation

### User Guides

**Getting Started**:
- `README.md` - Project overview and quick start
- `READY_TO_START.md` - Monday morning checklist for live trading
- `HOW_IT_WORKS_SIMPLE.md` - Layman's explanation of entire system

**Setup & Configuration**:
- `LIVE_TRADING_SETUP.md` - Live trading system setup (technical)
- `SCRAPER_SETUP.md` - Scraper configuration
- `requirements.txt` - Python dependencies
- `install_dependencies.bat` - Automated installation script

**Usage Guides**:
- `MAIN_USAGE.md` - Using main.py for data collection
- `PAPER_TRADING_GUIDE.md` - Paper trading system usage
- `BACKTESTING_GUIDE.md` - Historical backtesting
- `ANALYSIS_GUIDE.md` - News analysis and sentiment
- `PATTERN_ANALYSIS_GUIDE.md` - Price pattern recognition
- `RISK_MANAGEMENT_GUIDE.md` - 5-rule risk system
- `MULTI_SOURCE_GUIDE.md` - Multi-source validation

### Analysis & Results

**Performance Reports**:
- `BEHAVIORAL_FILTERS_RESULTS.md` - Filter comparison results
- `IMPLEMENTATION_SUMMARY.md` - v2.0 results and lessons learned
- `ENHANCEMENT_RECOMMENDATIONS.md` - 12 improvement strategies
- `ANALYSIS_SUMMARY.md` - Quantitative analysis results
- `QUANTITATIVE_ANALYSIS.md` - Statistical analysis

**Technical Documentation**:
- `AFR_SCRAPER_SUMMARY.md` - AFR scraper implementation
- `scrapers/AFR_SCRAPER_README.md` - AFR scraper details
- `scrapers/ASX_ANNOUNCEMENTS_IMPLEMENTATION.md` - ASX scraper
- `scrapers/README_DIRECTOR_TRADES.md` - Director trades scraper

---

## Deployment

### Development

```bash
# Clone repository
git clone https://github.com/rudirid/asx-trading-ai.git
cd asx-trading-ai

# Install dependencies
pip install -r requirements.txt
# Or use: install_dependencies.bat

# Initialize database
python database/init_db.py

# Test with GUI demo
python live_trading/enhanced_gui_demo.py
```

### Live Paper Trading (Oct 13-17, 2025)

```bash
# Monday 7:00 AM - Start monitoring
python live_trading/live_paper_trader.py --duration-days 5

# Check progress anytime
python live_trading/check_stats.py

# Daily report (5 PM)
python live_trading/daily_report.py

# Friday 5 PM - Final analysis
python analysis/performance_attribution_live.py
python live_trading/readiness_report.py
```

### Production (If IC > 0.05)

```bash
# Micro-capital testing ($500-1000)
python paper_trading/paper_trader.py --capital 1000 --position-size 50

# Monitor risk
python risk_dashboard_server.py

# Daily summaries
python paper_trading/daily_summary.py
```

---

## Key Scripts

**Data Collection**:
- `main.py` - Main coordinator for scraping (all sources)
- `download_asx_top100.py` - Get ASX top 100 tickers

**Backtesting**:
- `run_backtest.py` - Custom backtest runner
- `run_300_sample_test.py` - 300-sample proof-of-concept
- `create_historical_test_data.py` - Generate test data

**Analysis**:
- `analyze_news_impact.py` - News impact analysis
- `diagnose_filters.py` - Filter diagnostics
- `test_filter_comparison.py` - Compare filter strategies

**Dashboards**:
- `dashboard_server.py` - Main performance dashboard
- `paper_trading_server.py` - Paper trading dashboard
- `risk_dashboard_server.py` - Risk management dashboard
- `pattern_dashboard.html` - Pattern analysis visualization

**Testing**:
- `test_scraper.py` - Test stock price scraper
- `test_afr_scraper.py` - Test AFR scraper
- `test_director_scraper.py` - Test director trades scraper
- `test_hotcopper_scraper.py` - Test HotCopper scraper

---

## Technology Stack

**Core**:
- Python 3.11
- SQLite (database)
- yfinance (real-time prices)

**ML & NLP**:
- PyTorch (deep learning)
- Transformers (HuggingFace)
- scikit-learn (traditional ML)
- pandas, numpy (data processing)

**Web & APIs**:
- BeautifulSoup4 (web scraping)
- requests (HTTP)
- Flask (dashboard servers)

**Monitoring**:
- MLflow (experiment tracking)
- Prometheus (metrics)

**Testing**:
- pytest (unit tests)
- pytest-cov (coverage)

---

## Version History

**v3.0.0** (2025-10-10):
- ✅ Live trading system (complete)
- ✅ Behavioral filters (TIME, MATERIALITY, TIME-OF-DAY, CONTRARIAN)
- ✅ Self-improvement system (IC analysis)
- ✅ Interactive GUI demos
- ✅ Comprehensive documentation

**v2.0.0** (2025-10-09):
- News quality filtering
- Multi-source validation
- Technical analysis integration
- Dynamic exit manager
- Historical backtesting enhancements

**v1.0.0** (Initial):
- Basic scraping (stock prices, ASX announcements, AFR, director trades)
- Rule-based sentiment analysis
- Simple backtest engine
- Paper trading framework
- Risk management (5 rules)

---

## Next Steps

**Week of Oct 13-17, 2025**:
1. Run live paper trading for 5 days
2. Collect 100-300 recommendations
3. Measure IC (target: >0.05)
4. Make go-live decision

**If IC > 0.05** (Edge Detected):
1. Start micro-capital trading ($500-1000)
2. $50-100 per trade
3. Monitor for 2 weeks
4. Scale up if edge persists

**If IC < 0.05** (No Edge):
1. Improve sentiment model (fine-tune transformer)
2. Add earnings surprise detection
3. Fix ABC/SMH scrapers
4. Collect more data and re-test

---

## Contributing

**Priority Improvements**:
1. Fine-tune sentiment model on ASX data
2. Implement earnings surprise detection
3. Fix multi-source news scrapers
4. Add automated execution via Interactive Brokers
5. Implement walk-forward validation

**Code Quality**:
- All new code must include tests
- Follow PEP 8 style guide
- Document all functions
- Update relevant guides

---

## License

MIT License - See LICENSE file for details

---

## Contact

**Repository**: https://github.com/rudirid/asx-trading-ai
**Issues**: https://github.com/rudirid/asx-trading-ai/issues

---

**Last Updated**: 2025-10-10
**System Status**: Production-ready for live paper trading
**Confidence Level**: 85% (infrastructure solid, data source pending validation)
