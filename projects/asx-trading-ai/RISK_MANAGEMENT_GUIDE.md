# Risk Management Guide

## Overview

The risk management system implements comprehensive controls to protect capital and enforce disciplined trading:

1. **Position Sizing**: Max 2% risk per trade
2. **Stop Losses**: Auto-exit at 5% loss
3. **Sector Diversification**: Max 3 positions per sector
4. **Circuit Breaker**: Pause trading if daily loss exceeds 5%
5. **Confidence Threshold**: Only trades with 70%+ confidence

## Quick Start

### View Risk Dashboard

```bash
# Terminal 1: Start risk dashboard server
python risk_dashboard_server.py

# Terminal 2: (Optional) Run paper trading with risk management
python paper_trading/scheduler.py

# Browser: Open risk_dashboard.html
```

### Risk Dashboard Shows

- **Portfolio Exposure**: Current capital deployed vs available
- **Sector Diversification**: Position distribution across sectors
- **Active Positions**: Real-time P/L and stop loss levels
- **Correlation Matrix**: How positions move together
- **Worst Case Scenario**: Maximum loss if all stops hit
- **Risk Events Log**: History of risk-related actions

## Risk Rules Explained

### 1. Position Sizing (2% Max Risk)

**Rule**: Never risk more than 2% of portfolio on a single trade.

**How it Works**:
- Portfolio value: $100,000
- Max risk per trade: $2,000 (2%)
- Stop loss: 5%
- Position size = $2,000 / 0.05 = $40,000 max

**Example**:
```
Entry price: $45.50
Stop loss: 5% = $43.23
Max shares: $40,000 / $45.50 = 879 shares
Actual cost: 879 × $45.50 = $39,994.50
Risk: 879 × ($45.50 - $43.23) = $1,995.33 (~2%)
```

**Confidence Adjustment**:
- 70% confidence: Position size × 1.0
- 80% confidence: Position size × 1.14
- 90% confidence: Position size × 1.29

Lower confidence = smaller positions.

### 2. Stop Loss (5% Automatic Exit)

**Rule**: Automatically close position if loss reaches 5%.

**How it Works**:
- Entry: $45.50
- Stop loss price: $45.50 × 0.95 = $43.23
- System checks every update cycle
- Auto-closes if current price ≤ $43.23

**Monitoring**:
```python
# Checked automatically by scheduler
for position in active_positions:
    current_price = get_current_price(position.ticker)
    if current_price <= position.stop_loss_price:
        close_position(position, reason="Stop loss triggered")
```

**Why 5%**:
- Balances protection vs normal volatility
- With 2% risk, can have 50 losing trades before 100% loss
- Average ASX stock daily volatility: 1-3%

### 3. Sector Diversification (Max 3 per Sector)

**Rule**: Maximum 3 positions in the same sector.

**Sectors**:
- Mining & Resources (BHP, RIO, FMG, etc.)
- Banking (CBA, WBC, NAB, ANZ)
- Healthcare (CSL, COH, RMD)
- Retail (WES, WOW, JBH)
- Energy (WDS, STO, ORG)
- Telecom (TLS, TPG)
- Real Estate (GMG, SCG, GPT)
- Technology (WTC, XRO, CPU)
- Industrials (QAN, BXB, TCL)

**Why Limit**:
- Sector-specific events affect all stocks
- Banking royal commission: All banks down
- Mining commodity prices: All miners affected
- Limits concentration risk

**Example**:
```
Current positions:
- BHP (Mining) ✓
- RIO (Mining) ✓
- FMG (Mining) ✓

New recommendation: MIN (Mining)
Result: REJECTED - Already have 3 mining positions
```

### 4. Circuit Breaker (5% Daily Loss Limit)

**Rule**: Pause all trading if daily loss exceeds 5%.

**How it Works**:
```
Day starts: Daily P/L = 0%

Position 1 closed: -2.5%
Position 2 closed: -3.0%
Daily P/L: -5.5%

→ CIRCUIT BREAKER ACTIVATED
→ All new trades blocked
→ Existing positions held
→ Resets at 9 AM next day
```

**When Triggered**:
1. Log critical event
2. Update database state
3. Block all new recommendations
4. Send alert notification
5. Continue monitoring existing positions
6. Auto-deactivate next trading day

**Manual Override**:
```python
from paper_trading.risk_manager import RiskManager, RiskConfig

risk_manager = RiskManager('stock_data.db', RiskConfig())
risk_manager.deactivate_circuit_breaker()
```

**Why 5%**:
- Prevents cascading losses
- Forces re-evaluation of strategy
- Protects against system errors
- Allows time for analysis

### 5. Confidence Threshold (70% Minimum)

**Rule**: Only execute trades with ≥70% confidence.

**Confidence Calculation**:
```python
confidence = (
    sentiment_confidence × 0.3 +      # Model confidence
    sentiment_strength × 0.3 +        # Score strength
    theme_correlation × 0.2 +         # Historical pattern
    theme_accuracy × 0.2              # Prediction accuracy
)
```

**Example**:
```
Sentiment confidence: 0.80
Sentiment strength: 0.65
Theme correlation: 0.55
Theme accuracy: 0.75

Confidence = (0.80×0.3) + (0.65×0.3) + (0.55×0.2) + (0.75×0.2)
          = 0.24 + 0.195 + 0.11 + 0.15
          = 0.695 (69.5%)

Result: REJECTED - Below 70% threshold
```

**Why 70%**:
- Filters out weak signals
- Based on backtest optimization
- Balances quantity vs quality
- Can be adjusted based on results

## Risk Dashboard

### Metrics Cards

**Portfolio Exposure**:
- Current: $X deployed / $Y total
- Visual: Progress bar
- Alert: Red if >75%, Yellow if >60%

**Daily P/L**:
- Today's return: +X.XX%
- Limit: -5.00%
- Alert: Red if <-3%, Yellow if <0%

**Active Positions**:
- Count: X positions
- Max risk: 2% per trade
- Total at risk: $X

**Stop Loss Level**:
- Threshold: 5%
- Applied to: All positions
- Auto-exit: Yes

### Exposure Chart

Doughnut chart showing:
- **Deployed Capital**: Currently in positions
- **Available Capital**: Ready for new trades
- **Reserved for Risk**: 2% × active positions

### Sector Diversification Chart

Bar chart showing:
- Number of positions per sector
- Limit line at 3
- Alert if sector at/near limit

### Active Positions Table

For each position:
- Ticker & Sector
- Entry & Current Price
- Current P/L (%)
- Stop Loss Price
- Risk Level: Low/Medium/High

**Risk Levels**:
- Low: |P/L| < 1%
- Medium: 1% ≤ |P/L| < 3%
- High: |P/L| ≥ 3%

### Correlation Matrix

Shows correlation between all positions:
- Green (0.0-0.4): Low correlation (good)
- Yellow (0.4-0.7): Medium correlation
- Red (>0.7): High correlation (risky)

**High Correlation Risk**:
- Positions move together
- All go down together
- Reduces diversification benefits

**Example**:
```
        BHP   RIO   CBA
BHP     1.0   0.85  0.35
RIO     0.85  1.0   0.32
CBA     0.35  0.32  1.0
```
BHP & RIO: 0.85 = Very correlated (both mining)
BHP & CBA: 0.35 = Low correlation (different sectors)

### Worst Case Scenario Analysis

**Assumption**: All positions hit stop loss simultaneously

**Calculation**:
```
Position 1: $40,000 × 5% = $2,000 loss
Position 2: $35,000 × 5% = $1,750 loss
Position 3: $30,000 × 5% = $1,500 loss

Total at Risk: $105,000
Max Loss: $5,250 (5.25% of portfolio)
Portfolio After: $94,750
Recovery Needed: 5.54%
```

**Interpretation**:
- **< 5%**: Low risk, well-protected
- **5-10%**: Moderate risk, acceptable
- **> 10%**: High risk, reduce positions

### Risk Events Log

Chronological log of:
- **STOP_LOSS**: Position closed due to stop
- **CIRCUIT_BREAKER**: Trading paused
- **POSITION_REJECTED**: Trade blocked by rules
- **SECTOR_LIMIT**: Sector diversification enforced
- **CONFIDENCE_REJECT**: Below confidence threshold

**Each Event Shows**:
- Timestamp
- Type
- Severity (Low/Medium/High/Critical)
- Description
- Action Taken

## Integration with Paper Trading

### Scheduler Integration

Risk management is automatically integrated:

```bash
python paper_trading/scheduler.py
```

**What Happens**:
1. Scheduler generates recommendation
2. Risk manager validates:
   - Circuit breaker check
   - Confidence threshold
   - Sector diversification
   - Portfolio exposure
3. If passed: Calculate position size
4. If rejected: Log and skip
5. During monitoring:
   - Check stop losses
   - Check daily loss
   - Trigger circuit breaker if needed

### Manual Risk Checks

```python
from paper_trading.risk_manager import RiskManager, RiskConfig

# Initialize
risk_config = RiskConfig(
    portfolio_value=100000,
    max_risk_per_trade_pct=2.0,
    stop_loss_pct=5.0,
    max_positions_per_sector=3,
    daily_loss_limit_pct=5.0,
    min_confidence=0.7
)

risk_manager = RiskManager('stock_data.db', risk_config)

# Validate new position
is_allowed, reasons, details = risk_manager.validate_new_position(
    ticker='BHP',
    confidence=0.75,
    entry_price=45.50
)

if is_allowed:
    print(f"Position size: ${details['position_size']:,.2f}")
else:
    print(f"Rejected: {', '.join(reasons)}")

# Check stop loss
should_close, reason = risk_manager.check_stop_loss('REC_001', 43.00)

# Get risk summary
summary = risk_manager.get_risk_summary()
print(f"Exposure: {summary['exposure_pct']}%")
print(f"Daily loss: {summary['daily_loss_pct']}%")
```

## Configuration

### Default Settings

```python
RiskConfig(
    portfolio_value=100000.0,          # $100k starting capital
    max_risk_per_trade_pct=2.0,        # Max 2% risk per trade
    stop_loss_pct=5.0,                 # 5% stop loss
    max_positions_per_sector=3,        # Max 3 per sector
    daily_loss_limit_pct=5.0,          # 5% daily circuit breaker
    min_confidence=0.7,                # 70% minimum confidence
    max_portfolio_exposure_pct=80.0,   # Max 80% deployed
    max_correlation=0.7                # Max 0.7 correlation
)
```

### Conservative Settings

```python
RiskConfig(
    max_risk_per_trade_pct=1.0,        # More conservative
    stop_loss_pct=3.0,                 # Tighter stops
    max_positions_per_sector=2,        # Less concentration
    daily_loss_limit_pct=3.0,          # Lower threshold
    min_confidence=0.8,                # Higher bar
    max_portfolio_exposure_pct=60.0    # More cash reserve
)
```

### Aggressive Settings

```python
RiskConfig(
    max_risk_per_trade_pct=3.0,        # More risk
    stop_loss_pct=7.0,                 # Wider stops
    max_positions_per_sector=5,        # More concentration OK
    daily_loss_limit_pct=7.0,          # Higher tolerance
    min_confidence=0.6,                # Lower bar
    max_portfolio_exposure_pct=90.0    # Fully invested
)
```

## Best Practices

### 1. Monitor Daily

Check risk dashboard every day:
- Current exposure level
- Stop loss proximity
- Sector concentration
- Daily P/L progress

### 2. Review Risk Events

Analyze why positions were rejected:
- Too many in sector? → Wait for sector exit
- Low confidence? → Improve signal quality
- Circuit breaker? → Review strategy

### 3. Adjust Based on Results

**If win rate drops**:
- Increase confidence threshold
- Tighten sector limits
- Reduce position sizes

**If too few trades**:
- Lower confidence threshold
- Relax sector limits
- But don't compromise core rules

### 4. Respect the Circuit Breaker

When triggered:
- **Don't override** without analysis
- Review what went wrong
- Adjust strategy if needed
- Use downtime to improve

### 5. Test Risk Rules

Before live trading:
- Run paper trading for 30+ days
- Verify stop losses trigger correctly
- Confirm circuit breaker works
- Check position sizing accuracy

## Troubleshooting

### "All recommendations rejected"

**Check**:
1. Confidence threshold too high?
   - Lower from 0.7 to 0.6
2. Circuit breaker active?
   - Check dashboard for alert
3. Sector limits hit?
   - Close some positions first
4. Portfolio fully exposed?
   - Wait for exits

### "Stop loss not triggering"

**Verify**:
1. Scheduler is running
2. Price data is updating
3. Check logs for errors
4. Manual test:
   ```python
   risk_manager.check_stop_loss('REC_001', test_price)
   ```

### "Circuit breaker stuck"

**Check**:
1. Database state:
   ```sql
   SELECT * FROM circuit_breaker_state;
   ```
2. Deactivate time passed?
3. Manual deactivate:
   ```python
   risk_manager.deactivate_circuit_breaker()
   ```

### "Risk dashboard shows wrong data"

**Solutions**:
1. Refresh browser
2. Restart server: `python risk_dashboard_server.py`
3. Check database connection
4. Verify port 8002 is available

## Database Schema

### risk_events

```sql
CREATE TABLE risk_events (
    event_id INTEGER PRIMARY KEY,
    timestamp TEXT,
    event_type TEXT,              -- STOP_LOSS, CIRCUIT_BREAKER, etc.
    severity TEXT,                -- LOW, MEDIUM, HIGH, CRITICAL
    description TEXT,
    recommendation_id TEXT,
    ticker TEXT,
    action_taken TEXT,
    details TEXT                  -- JSON
)
```

### circuit_breaker_state

```sql
CREATE TABLE circuit_breaker_state (
    id INTEGER PRIMARY KEY (always 1),
    is_active INTEGER,            -- 0 or 1
    activated_at TEXT,
    reason TEXT,
    daily_loss_pct REAL,
    deactivate_at TEXT
)
```

## Risk Metrics

### Key Indicators

**Portfolio Heat**:
```
Heat = (Total Exposure / Portfolio Value) × 100
```
- < 60%: Low heat (conservative)
- 60-80%: Medium heat (balanced)
- > 80%: High heat (aggressive)

**Risk Utilization**:
```
Risk Used = Active Positions × Max Risk Per Trade
```
- Example: 5 positions × 2% = 10% of capital at risk

**Diversification Score**:
```
Score = 1 - (Max Sector % / Total Positions)
```
- 1.0: Perfect diversification
- 0.0: All in one sector

## Advanced Topics

### Dynamic Position Sizing

Adjust position size based on volatility:

```python
# Higher volatility = smaller position
volatility_factor = min(1.0, 0.02 / stock_volatility)
adjusted_size = base_size × volatility_factor
```

### Correlation-Based Limits

Reject position if correlation with existing > 0.7:

```python
for existing in portfolio:
    correlation = calculate_correlation(new_ticker, existing.ticker)
    if correlation > 0.7:
        reject("High correlation with existing position")
```

### Time-Based Risk Scaling

Reduce position sizes near market close:

```python
if time_until_close < 30_minutes:
    position_size × 0.5  # Half size
```

## Files

- `paper_trading/risk_manager.py`: Core risk management logic
- `risk_dashboard.html`: Risk monitoring dashboard
- `risk_dashboard_server.py`: Dashboard backend
- `paper_trading/scheduler.py`: Integrated risk checks

## Next Steps

1. **Start Conservative**: Use default or conservative settings
2. **Monitor Closely**: Check dashboard daily
3. **Collect Data**: Run 30+ days to understand patterns
4. **Optimize**: Adjust thresholds based on results
5. **Validate**: Compare risk-managed vs unmanaged performance

---

**Remember**: Risk management protects capital. It's better to miss opportunities than to lose capital. The rules exist to enforce discipline and prevent emotional decisions.