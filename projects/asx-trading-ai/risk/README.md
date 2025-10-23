# Risk Management Module

Professional-grade risk management for ASX trading system.

## Overview

The `risk/` module provides Kelly Criterion-based position sizing with multi-layer risk controls and ATR-based volatility stops.

## Installation

```python
from risk import KellyCriterionPositionSizer, ATRStopLossCalculator, Position
```

## Quick Start

```python
from risk import KellyCriterionPositionSizer

# Initialize position sizer with $10,000 account
sizer = KellyCriterionPositionSizer(
    account_size=10000.0,
    kelly_fraction=0.25,          # Quarter-Kelly (conservative)
    max_position_pct=0.10,        # Max 10% per position
    max_risk_per_trade_pct=0.02,  # Max 2% risk per trade
    max_portfolio_heat_pct=0.10   # Max 10% total risk
)

# Calculate position size for a trade
shares, risk_amount, details = sizer.calculate_position_size(
    symbol='BHP',
    entry_price=45.00,
    stop_loss_price=43.00,
    confidence=0.75  # Model confidence [0-1]
)

# Open the position
position = sizer.open_position(
    symbol='BHP',
    entry_price=45.00,
    shares=shares,
    stop_loss=43.00,
    take_profit=48.00,
    risk_amount=risk_amount,
    confidence=0.75
)

# Check risk limits (do this before each trade)
risk_status = sizer.check_risk_limits()
if risk_status['status'] == 'ALERT':
    print("Risk alert - reduce position sizes by 50%")
elif risk_status['status'] == 'CRITICAL':
    print("Critical risk - no new positions")
elif risk_status['status'] == 'SHUTDOWN':
    print("SHUTDOWN - close all positions immediately")
```

## Components

### 1. KellyCriterionPositionSizer

Main position sizing engine with 4-layer risk controls.

**Key Methods:**
- `calculate_position_size()` - Calculate shares to buy based on confidence
- `open_position()` - Record opening a position
- `close_position()` - Close position and record P&L
- `check_risk_limits()` - 4-level alert system (NORMAL/ALERT/CRITICAL/SHUTDOWN)
- `get_statistics()` - Performance metrics (win rate, Sharpe, IC)
- `get_portfolio_heat()` - Total risk across all positions
- `get_daily_drawdown()` - Intraday losses
- `get_max_drawdown()` - Maximum drawdown from peak
- `reset_daily_tracking()` - Reset at market open

**Risk Alert Levels:**
- **NORMAL**: All parameters within limits
- **ALERT** (10% max DD or 8% daily DD):
  - Reduce positions by 50%
  - Tighten stops
  - Only high confidence trades (>0.75)
- **CRITICAL** (20% max DD or 15% daily DD):
  - Reduce positions by 75%
  - NO NEW POSITIONS
  - Review all trades
- **SHUTDOWN** (30% max DD):
  - CLOSE ALL POSITIONS
  - CEASE TRADING
  - Manual reset required

### 2. ATRStopLossCalculator

Volatility-based stop loss and position sizing using Average True Range.

**Key Methods:**
- `calculate_atr()` - Calculate ATR from OHLC data
- `calculate_stops()` - Generate stop loss and take profit from ATR
- `calculate_position_size_with_atr()` - ATR-based position sizing

**Example:**
```python
from risk import ATRStopLossCalculator

# Calculate ATR from price data
atr = ATRStopLossCalculator.calculate_atr(
    high_prices=[46.5, 47.0, 46.8, ...],
    low_prices=[45.0, 45.5, 45.2, ...],
    close_prices=[46.0, 46.5, 46.3, ...],
    period=14
)

# Get stop loss and take profit
stop_loss, take_profit = ATRStopLossCalculator.calculate_stops(
    entry_price=45.00,
    atr=1.50,
    direction='long',
    atr_multiplier_stop=2.0,
    risk_reward_ratio=2.0
)
# stop_loss = 42.00 (45 - 2*1.5)
# take_profit = 51.00 (45 + 2*2*1.5)
```

### 3. Position

Dataclass representing an open trading position.

**Fields:**
- `symbol` - Stock ticker
- `entry_price` - Entry price
- `shares` - Number of shares
- `stop_loss` - Stop loss price
- `take_profit` - Take profit price
- `risk_amount` - Dollar risk
- `confidence` - Model confidence
- `entry_time` - Entry timestamp
- `current_price` - Current market price
- `unrealized_pnl` - Unrealized profit/loss

## Risk Controls

### 4-Layer Protection System

1. **Kelly Fraction (0.25)**: Limits aggressive sizing
2. **Max Risk Per Trade (2%)**: Hard cap on single trade risk
3. **Max Position Size (10%)**: Limits concentration risk
4. **Portfolio Heat (10%)**: Limits total risk across all positions

### Daily Risk Management

```python
# At market open (9:00 AM AEST)
sizer.reset_daily_tracking()

# Before each trade
risk_status = sizer.check_risk_limits()

# After market close (4:00 PM AEST)
stats = sizer.get_statistics()
print(f"Daily P&L: ${sizer.daily_pnl:+.2f}")
print(f"Daily drawdown: {sizer.get_daily_drawdown():.2%}")
```

## Performance Metrics

The `get_statistics()` method provides comprehensive performance tracking:

```python
stats = sizer.get_statistics()

# Performance metrics
print(f"Win rate: {stats['win_rate']:.1%}")
print(f"Profit factor: {stats['profit_factor']:.2f}")
print(f"Sharpe ratio: {stats['sharpe_ratio']:.2f}")
print(f"Information Coefficient: {stats['information_coefficient']:+.3f}")
print(f"Account return: {stats['account_return']:+.2%}")

# Risk metrics
print(f"Max drawdown: {stats['current_drawdown']:.2%}")
print(f"Portfolio heat: {stats['portfolio_heat']:.2%}")
print(f"Open positions: {stats['open_positions']}")
```

### Information Coefficient (IC)

IC measures the correlation between predicted confidence and actual outcomes:
- **IC > 0.05**: Model has predictive power
- **IC > 0.10**: Strong predictive power
- **IC < 0**: Model is wrong more than right (reverse signals!)

## Integration Examples

### With Recommendation Engine

```python
from risk import KellyCriterionPositionSizer
from paper_trading.recommendation_engine import RecommendationEngine

sizer = KellyCriterionPositionSizer(account_size=10000)
rec_engine = RecommendationEngine()

# Get recommendation
rec = rec_engine.get_recommendation('BHP')

# Check risk limits first
risk_status = sizer.check_risk_limits()
if risk_status['status'] in ['CRITICAL', 'SHUTDOWN']:
    print("Risk limits exceeded - no new positions")
else:
    # Calculate position
    shares, risk, details = sizer.calculate_position_size(
        symbol='BHP',
        entry_price=rec['entry_price'],
        stop_loss_price=rec['stop_loss'],
        confidence=rec['confidence']
    )

    if shares > 0:
        # Execute trade
        pass
```

### With Backtesting

```python
from risk import KellyCriterionPositionSizer
from backtesting.historical_simulator import HistoricalSimulator

sizer = KellyCriterionPositionSizer(account_size=10000)
simulator = HistoricalSimulator(position_sizer=sizer)

# Run backtest
results = simulator.run_backtest(start_date='2024-01-01', end_date='2024-12-31')

# Check final statistics
stats = sizer.get_statistics()
print(f"Final return: {stats['account_return']:+.2%}")
print(f"IC: {stats['information_coefficient']:+.3f}")
```

## Best Practices

### 1. Daily Routine

```python
# Market open (9:00 AM AEST)
sizer.reset_daily_tracking()

# Before each trade
risk_status = sizer.check_risk_limits()
if risk_status['status'] != 'NORMAL':
    # Adjust strategy based on risk level
    pass

# Market close (4:00 PM AEST)
stats = sizer.get_statistics()
# Log daily performance
```

### 2. Position Sizing

```python
# ALWAYS check risk limits before trading
risk_status = sizer.check_risk_limits()

if risk_status['status'] == 'NORMAL':
    # Trade normally
    confidence_required = 0.60
elif risk_status['status'] == 'ALERT':
    # Reduce size, increase confidence threshold
    confidence_required = 0.75
else:
    # No new positions
    print("Risk limits exceeded")
    return
```

### 3. Monitoring

```python
# Check every hour during trading
portfolio_heat = sizer.get_portfolio_heat()
if portfolio_heat > 0.08:  # 8%
    print(f"Warning: Portfolio heat at {portfolio_heat:.1%}")

# Check drawdown
max_dd = sizer.get_max_drawdown()
if max_dd > 0.05:  # 5%
    print(f"Warning: Max drawdown at {max_dd:.1%}")
```

## Testing

The module includes comprehensive test coverage:

```bash
# Run module tests
python test_kelly_enhancements.py

# Quick validation
python -c "from risk import KellyCriterionPositionSizer; print('OK')"
```

## Files

- `position_sizer.py` - Main implementation
- `__init__.py` - Module exports
- `README.md` - This file

## Dependencies

- `numpy` - Numerical calculations
- `scipy` - Spearman correlation (IC calculation)
- `dataclasses` - Position dataclass
- `datetime` - Timestamp tracking
- `typing` - Type hints
- `logging` - Logging

## Version

**v3.4.0** (2025-10-10)

## License

Part of ASX Trading AI System

## Support

For issues or questions, see main project documentation.
