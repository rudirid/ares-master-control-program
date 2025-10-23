# Immediate Fixes - Implementation Guide

**Goal**: Improve win rate from 34% to 40%+ in Week 1
**Current Performance**: -5.87% return, 34.0% win rate

---

## Fix 1: Change Technical Analysis to Soft Modifier (Day 1)

### Problem
Current code in `historical_simulator.py` (lines 688-703):
```python
# Technical analysis confirmation (if enabled)
if self.technical_indicators:
    tech_decision = self.technical_indicators.should_enter_trade(...)

    if not tech_decision['should_enter']:
        # HARD REJECT - This is the problem!
        self.events.append(...)
        continue  # Skips the trade
```

This rejected 26 trades and made performance worse.

### Solution

**File**: `backtesting/historical_simulator.py`

**Replace lines 688-703 with**:
```python
# Technical analysis confidence adjustment (SOFT, not hard filter)
if self.technical_indicators:
    tech_analysis = self.technical_indicators.get_technical_analysis(
        article['ticker'],
        as_of_date=article_date
    )

    if tech_analysis.get('has_data'):
        # Adjust confidence based on technical agreement
        if sentiment == 'positive':
            if tech_analysis['is_bullish']:
                # Agreement - boost confidence
                confidence += 0.15
                reason = "Technical analysis confirms bullish sentiment"
            elif tech_analysis['is_bearish']:
                # Conflict - reduce confidence but DON'T reject
                confidence -= 0.15
                reason = "Technical analysis conflicts with sentiment"
            else:
                # Neutral - small adjustment
                confidence += 0.05
                reason = "Technical analysis neutral"

        # Also adjust for volatility
        if tech_analysis.get('volatility_pct', 0) > 3.0:
            confidence -= 0.05  # High volatility = less confident

        # Clamp confidence to valid range
        confidence = max(0.0, min(1.0, confidence))

        # Log the adjustment
        self.events.append(SimulationEvent(
            timestamp=article_date,
            event_type='TECH_ADJUSTED',
            ticker=article['ticker'],
            description=f"Technical analysis: {reason} (confidence: {confidence:.2f})",
            details={
                'reason': reason,
                'adjustment': tech_decision.get('confidence_adjustment', 0),
                'technical': tech_analysis
            }
        ))
    else:
        # No technical data - just log it, don't reject
        self.events.append(SimulationEvent(
            timestamp=article_date,
            event_type='TECH_UNAVAILABLE',
            ticker=article['ticker'],
            description="No technical data available",
            details={}
        ))
```

**Expected Result**: Accept previously rejected trades with adjusted confidence.

---

## Fix 2: Reduce Minimum Data Requirement (Day 1)

### Problem
`technical_indicators.py` line 209:
```python
if prices.empty or len(prices) < 30:
    return {
        'error': 'Insufficient price data',
        'has_data': False
    }
```

This causes "Insufficient technical data" errors early in the test period.

### Solution

**File**: `analysis/technical_indicators.py`

**Change line 209 to**:
```python
# Reduce from 30 to 20 days minimum
if prices.empty or len(prices) < 20:
    return {
        'error': 'Insufficient price data',
        'has_data': False
    }

# Add reliability score based on data quality
data_quality = len(prices) / 60.0  # 60 days = full quality
data_quality = min(1.0, data_quality)
```

**Also update line 207** (price history fetch):
```python
# Change from 60 to 50 days lookback
prices = self.get_price_history(ticker, days=50, end_date=as_of_date)
```

**Add data quality to return** (line 283+):
```python
return {
    'has_data': True,
    'data_quality': data_quality,  # NEW: 0-1 score
    'ticker': ticker,
    # ... rest of the fields
}
```

**Expected Result**: Fewer "Insufficient data" rejections.

---

## Fix 3: Integrate Dynamic Exits (Day 2-3)

### Current Issue
Fixed 7-day holding period ignores momentum and opportunity.

### Solution

**File**: `backtesting/historical_simulator.py`

**Step 1: Import DynamicExitManager** (add to top):
```python
from backtesting.dynamic_exit_manager import DynamicExitManager
```

**Step 2: Initialize in __init__** (line 123):
```python
self.technical_indicators = TechnicalIndicators(db_path) if use_technical_analysis else None

# Add this:
self.dynamic_exit_manager = DynamicExitManager(
    take_profit_pct=10.0,
    trailing_stop_pct=3.0,
    min_holding_days=3,
    max_holding_days=14
)
```

**Step 3: Add max_return tracking to SimulatedPosition** (line 56):
```python
@dataclass
class SimulatedPosition:
    # ... existing fields ...

    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    return_pct: Optional[float] = None
    exit_reason: Optional[str] = None
    days_held: Optional[int] = None
    max_return_pct: float = 0.0  # NEW: Track peak return
```

**Step 4: Replace check_holding_period** (lines 534-564):
```python
def check_dynamic_exit(
    self,
    ticker: str,
    current_date: str,
    current_price: float
) -> bool:
    """
    Check if position should exit using dynamic exit logic.
    """
    if ticker not in self.active_positions:
        return False

    position = self.active_positions[ticker]

    # Calculate current return
    current_return_pct = (
        (current_price - position.entry_price) / position.entry_price
    ) * 100

    # Update max return
    position.max_return_pct = max(position.max_return_pct, current_return_pct)

    # Calculate days held
    entry_dt = pd.to_datetime(position.entry_date)
    current_dt = pd.to_datetime(current_date)
    days_held = (current_dt - entry_dt).days

    # Get technical signal if available
    technical_signal = None
    if self.technical_indicators:
        tech = self.technical_indicators.get_technical_analysis(ticker, current_date)
        if tech.get('has_data'):
            technical_signal = tech['overall_signal']

    # Check exit conditions
    should_exit, exit_reason = self.dynamic_exit_manager.should_exit(
        entry_price=position.entry_price,
        current_price=current_price,
        days_held=days_held,
        max_return_pct=position.max_return_pct,
        sentiment=position.sentiment,
        technical_signal=technical_signal
    )

    if should_exit:
        self.exit_position(ticker, current_date, current_price, exit_reason)
        return True

    # Fallback: Maximum holding period (safety)
    if days_held >= 21:  # Hard limit at 3 weeks
        self.exit_position(ticker, current_date, current_price, "Maximum holding period reached")
        return True

    return False
```

**Step 5: Update simulation loop** (line 638):
```python
# Replace this line:
# self.check_holding_period(ticker, article_date, current_price)

# With this:
self.check_dynamic_exit(ticker, article_date, current_price)
```

**Expected Result**: Better exits, capture more upside, limit downside.

---

## Fix 4: Add Information Coefficient Calculation (Day 2)

### Purpose
Measure how well sentiment predicts price movement.

### New File: `analysis/signal_metrics.py`

```python
"""
Signal Quality Metrics

Measures how well trading signals predict price movements.
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr, spearmanr
from typing import Dict, Tuple


class SignalMetrics:
    """Calculate signal quality metrics."""

    def __init__(self):
        pass

    def calculate_ic(
        self,
        signals: pd.Series,
        returns: pd.Series,
        method: str = 'pearson'
    ) -> Tuple[float, float]:
        """
        Calculate Information Coefficient.

        IC measures correlation between signal and forward returns.

        Args:
            signals: Signal values (e.g., sentiment scores)
            returns: Forward returns (e.g., 1-day price change %)
            method: 'pearson' or 'spearman'

        Returns:
            (IC value, p-value)
        """
        # Remove NaN values
        mask = ~(signals.isna() | returns.isna())
        clean_signals = signals[mask]
        clean_returns = returns[mask]

        if len(clean_signals) < 10:
            return 0.0, 1.0

        # Calculate correlation
        if method == 'pearson':
            ic, p_value = pearsonr(clean_signals, clean_returns)
        else:
            ic, p_value = spearmanr(clean_signals, clean_returns)

        return ic, p_value

    def calculate_hit_rate_by_bucket(
        self,
        df: pd.DataFrame,
        signal_col: str = 'confidence',
        return_col: str = 'return_pct',
        n_buckets: int = 4
    ) -> pd.DataFrame:
        """
        Calculate win rate by confidence bucket.

        Win rate should increase with confidence (monotonic relationship).
        """
        # Create confidence buckets
        df['bucket'] = pd.qcut(
            df[signal_col],
            q=n_buckets,
            labels=[f'Q{i+1}' for i in range(n_buckets)],
            duplicates='drop'
        )

        # Calculate hit rate per bucket
        def hit_rate(group):
            wins = (group[return_col] > 0).sum()
            total = len(group)
            return wins / total if total > 0 else 0

        bucket_stats = df.groupby('bucket').agg({
            return_col: ['count', hit_rate, 'mean', 'std'],
            signal_col: ['min', 'max', 'mean']
        })

        return bucket_stats

    def signal_decay_analysis(
        self,
        df: pd.DataFrame,
        signal_col: str = 'sentiment_score',
        periods: list = [1, 3, 5, 7, 14]
    ) -> Dict[int, Tuple[float, float]]:
        """
        Analyze how signal predictive power decays over time.

        Args:
            df: DataFrame with signals and multiple return periods
            signal_col: Column name for signal
            periods: List of days to analyze

        Returns:
            Dict mapping period -> (IC, p-value)
        """
        results = {}

        for period in periods:
            return_col = f'return_{period}d'
            if return_col in df.columns:
                ic, p_value = self.calculate_ic(
                    df[signal_col],
                    df[return_col]
                )
                results[period] = (ic, p_value)

        return results

    def print_signal_report(
        self,
        df: pd.DataFrame,
        signal_col: str = 'sentiment_score',
        return_col: str = 'return_1d'
    ):
        """
        Print comprehensive signal quality report.
        """
        print("\n" + "=" * 70)
        print("SIGNAL QUALITY REPORT")
        print("=" * 70 + "\n")

        # Overall IC
        ic, p_value = self.calculate_ic(df[signal_col], df[return_col])
        print(f"Information Coefficient (IC): {ic:.4f}")
        print(f"P-value: {p_value:.4f}")
        print(f"Significant: {'Yes' if p_value < 0.05 else 'No'}")
        print(f"Quality: ", end="")
        if abs(ic) > 0.10:
            print("EXCELLENT")
        elif abs(ic) > 0.05:
            print("GOOD")
        elif abs(ic) > 0.02:
            print("FAIR")
        else:
            print("POOR (likely no edge)")

        # Hit rate by bucket
        print("\n" + "-" * 70)
        print("HIT RATE BY CONFIDENCE BUCKET")
        print("-" * 70 + "\n")

        bucket_stats = self.calculate_hit_rate_by_bucket(
            df,
            signal_col='confidence',
            return_col=return_col
        )
        print(bucket_stats)

        # Signal decay
        print("\n" + "-" * 70)
        print("SIGNAL DECAY ANALYSIS")
        print("-" * 70 + "\n")

        decay = self.signal_decay_analysis(df, signal_col)
        for period, (ic_val, p_val) in decay.items():
            print(f"{period}d IC: {ic_val:.4f} (p={p_val:.4f})")

        print("\n" + "=" * 70 + "\n")


def test_signal_metrics():
    """Test signal metrics calculation."""
    # Create sample data
    np.random.seed(42)
    n = 100

    df = pd.DataFrame({
        'sentiment_score': np.random.randn(n) * 0.3,
        'confidence': np.random.uniform(0.5, 1.0, n),
        'return_1d': np.random.randn(n) * 2.0,
        'return_3d': np.random.randn(n) * 3.0,
        'return_7d': np.random.randn(n) * 5.0,
    })

    # Add some correlation (simulate edge)
    df['return_1d'] += df['sentiment_score'] * 1.5

    metrics = SignalMetrics()
    metrics.print_signal_report(df)


if __name__ == '__main__':
    test_signal_metrics()
```

**Usage in backtest**:
```python
# After running backtest, analyze signal quality
from analysis.signal_metrics import SignalMetrics

metrics = SignalMetrics()

# Load backtest results
df = pd.read_csv('results/backtest_trades.csv')

# Calculate IC
ic, p_value = metrics.calculate_ic(
    df['sentiment_score'],
    df['return_pct']
)

print(f"Signal IC: {ic:.4f} (target: > 0.05)")
```

---

## Fix 5: Earnings Detection (Day 3-4)

### New File: `analysis/earnings_detector.py`

```python
"""
Earnings Detection and Surprise Calculation
"""

import re
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class EarningsData:
    """Earnings data extracted from announcement."""
    metric: str  # 'revenue', 'profit', 'eps'
    actual: float
    unit: str  # 'M', 'B', etc.
    currency: str = 'AUD'


class EarningsDetector:
    """Detect and extract earnings information from announcements."""

    def __init__(self):
        # Earnings patterns
        self.patterns = {
            'revenue': [
                r'revenue of [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
                r'sales of [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
                r'total revenue:?\s*[\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
            ],
            'profit': [
                r'(?:net )?profit of [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
                r'(?:net )?income of [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
                r'earnings of [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
            ],
            'eps': [
                r'EPS of [\$A]*([\d.]+)',
                r'earnings per share:?\s*[\$A]*([\d.]+)',
            ],
            'guidance': [
                r'guidance of [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
                r'expects? [\$A]*([\d,]+\.?\d*)\s*([MB]illion|million|m|b)?',
            ]
        }

        # Result indicators
        self.beat_keywords = ['beat', 'exceed', 'surpass', 'above expectations', 'better than expected']
        self.miss_keywords = ['miss', 'below', 'disappoint', 'weaker than expected', 'fell short']

    def extract_earnings(self, text: str) -> Dict[str, EarningsData]:
        """
        Extract earnings metrics from text.

        Returns:
            Dict mapping metric name to EarningsData
        """
        results = {}

        for metric, pattern_list in self.patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Parse value
                    value_str = match.group(1).replace(',', '')
                    value = float(value_str)

                    # Parse unit
                    unit = 'M'  # Default millions
                    if len(match.groups()) > 1 and match.group(2):
                        unit_str = match.group(2).upper()
                        if 'B' in unit_str:
                            unit = 'B'
                            value *= 1000  # Convert to millions

                    results[metric] = EarningsData(
                        metric=metric,
                        actual=value,
                        unit='M',  # Standardize to millions
                    )
                    break  # Use first match

        return results

    def detect_surprise_direction(self, text: str) -> Optional[str]:
        """
        Detect if announcement indicates beat or miss.

        Returns:
            'beat', 'miss', or None
        """
        text_lower = text.lower()

        # Check for beat keywords
        if any(keyword in text_lower for keyword in self.beat_keywords):
            return 'beat'

        # Check for miss keywords
        if any(keyword in text_lower for keyword in self.miss_keywords):
            return 'miss'

        return None

    def adjust_sentiment_for_earnings(
        self,
        base_sentiment_score: float,
        article_text: str,
        earnings_data: Dict[str, EarningsData]
    ) -> float:
        """
        Adjust sentiment score based on earnings context.

        Args:
            base_sentiment_score: Original sentiment score
            article_text: Full article text
            earnings_data: Extracted earnings data

        Returns:
            Adjusted sentiment score
        """
        if not earnings_data:
            return base_sentiment_score

        # Detect surprise direction
        surprise = self.detect_surprise_direction(article_text)

        # Adjust sentiment
        adjusted_score = base_sentiment_score

        if surprise == 'beat':
            # Earnings beat - boost positive sentiment
            if base_sentiment_score > 0:
                adjusted_score = min(base_sentiment_score + 0.25, 1.0)
            else:
                # Even if sentiment negative, earnings beat is positive
                adjusted_score = 0.15

        elif surprise == 'miss':
            # Earnings miss - reduce sentiment
            if base_sentiment_score < 0:
                adjusted_score = max(base_sentiment_score - 0.25, -1.0)
            else:
                # Even if sentiment positive, miss is negative
                adjusted_score = -0.15

        return adjusted_score


# Integration example
def integrate_earnings_detection():
    """How to integrate into sentiment analyzer."""

    from analysis.local_sentiment_analyzer import LocalSentimentAnalyzer

    sentiment_analyzer = LocalSentimentAnalyzer()
    earnings_detector = EarningsDetector()

    def analyze_with_earnings(article_text: str, ticker: str) -> dict:
        # Base sentiment
        base_analysis = sentiment_analyzer.analyze_article(
            title="",  # Title in text
            content=article_text,
            ticker=ticker
        )

        # Extract earnings
        earnings_data = earnings_detector.extract_earnings(article_text)

        # Adjust for earnings if found
        if earnings_data:
            adjusted_score = earnings_detector.adjust_sentiment_for_earnings(
                base_sentiment_score=base_analysis['sentiment_score'],
                article_text=article_text,
                earnings_data=earnings_data
            )

            base_analysis['sentiment_score'] = adjusted_score
            base_analysis['has_earnings'] = True
            base_analysis['earnings_data'] = earnings_data
        else:
            base_analysis['has_earnings'] = False

        return base_analysis

    return analyze_with_earnings


if __name__ == '__main__':
    detector = EarningsDetector()

    # Test
    test_text = """
    BHP reports net profit of $15.3 billion, beating analyst expectations.
    Revenue came in at $55.7 billion for the full year.
    EPS of $3.15 exceeded consensus estimates of $2.95.
    """

    earnings = detector.extract_earnings(test_text)
    print("Extracted earnings:", earnings)

    surprise = detector.detect_surprise_direction(test_text)
    print(f"Surprise direction: {surprise}")

    adjusted = detector.adjust_sentiment_for_earnings(0.3, test_text, earnings)
    print(f"Sentiment: 0.3 -> {adjusted}")
```

---

## Testing the Fixes

### Run Updated Backtest

```bash
# Test with all fixes applied
python run_300_sample_test.py

# Compare results:
# Before: -5.87% return, 34.0% win rate, 47 trades
# Target: -2% to +2% return, 40%+ win rate, 55+ trades
```

### Measure Improvements

```python
# Add to run_300_sample_test.py
from analysis.signal_metrics import SignalMetrics

# After simulation completes
if results['total_trades'] > 0:
    # Calculate IC
    metrics = SignalMetrics()

    trades_df = pd.DataFrame([
        {
            'sentiment_score': p.sentiment_score,
            'confidence': p.recommendation_confidence,
            'return_pct': p.return_pct
        }
        for p in results['positions']
    ])

    ic, p_value = metrics.calculate_ic(
        trades_df['sentiment_score'],
        trades_df['return_pct']
    )

    print(f"\nSignal Quality:")
    print(f"  IC: {ic:.4f} (target: > 0.05)")
    print(f"  P-value: {p_value:.4f}")
    print(f"  Significant: {'Yes' if p_value < 0.05 else 'No'}")
```

---

## Success Criteria

**After implementing these fixes, you should see**:

| Metric | Before | Target After Fixes | Stretch Goal |
|--------|--------|-------------------|--------------|
| Win Rate | 34.0% | 40%+ | 45%+ |
| Return | -5.87% | -2% to +2% | +3% to +5% |
| Total Trades | 47 | 55-65 | 60+ |
| Avg Win | $51.51 | $55+ | $60+ |
| Avg Loss | -$42.64 | -$40 | -$38 |
| IC | Unknown | > 0.05 | > 0.10 |
| Profit Factor | 0.62 | 0.90+ | 1.10+ |

**If you achieve**:
- Win Rate > 42% → Proceed to Week 2 (regime detection + earnings)
- Win Rate < 40% → Review and debug, may need sentiment model improvement first

---

## Debugging Tips

**If win rate doesn't improve**:

1. **Check IC first**
   ```python
   # If IC < 0.02, sentiment has no edge
   # Must improve base signal before anything else
   ```

2. **Analyze rejected trades**
   ```python
   # Were they actually profitable?
   rejected_trades = [e for e in events if e.event_type == 'TECH_REJECTED']
   # Check if we should have taken them
   ```

3. **Review confidence adjustments**
   ```python
   # Are adjustments helping or hurting?
   plt.scatter(df['confidence'], df['return_pct'])
   # Should see positive correlation
   ```

---

**End of Implementation Guide**

*Focus on these 5 fixes first. They're specific, testable, and have the highest expected impact on performance.*
