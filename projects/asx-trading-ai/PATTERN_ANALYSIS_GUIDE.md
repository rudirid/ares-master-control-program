# Pattern Analysis Dashboard Guide

## Overview

The Pattern Analysis Dashboard helps you discover which types of news articles reliably predict stock price movements. It analyzes historical correlations between news sentiment and actual price changes.

## Quick Start

### Step 1: Generate Analysis Data

First, make sure you've run the news impact analysis:

```bash
python analyze_news_impact.py
```

This creates `results/news_impact_analysis.csv` with all the article sentiment and price data.

### Step 2: Run Pattern Analysis

```bash
python analysis/pattern_analyzer.py
```

This generates `results/pattern_analysis.json` with computed metrics.

### Step 3: View Dashboard

Open `pattern_dashboard.html` in your browser to explore the interactive visualizations.

## What the Dashboard Shows

### 1. Theme Predictive Power

**Question**: Which news categories best predict price movements?

**Metrics**:
- **Correlation**: How strongly theme sentiment predicts price direction (-1 to +1)
- **High values** (>0.5): Strong predictive power
- **Low values** (<0.2): Weak/no predictive power

**Example**: If "earnings" theme has correlation of 0.7, earnings news strongly predicts price direction.

### 2. Time Lag Analysis

**Question**: How quickly does the market react to news?

**Insights**:
- What % of the eventual 7-day move happens in Day 1?
- When is the optimal time to act on news?
- Do different sentiments have different timing profiles?

**Example**: If 60% of movement happens Day 1, the market reacts quickly to this type of news.

### 3. Magnitude Analysis

**Question**: How big are the typical price moves?

**By Sentiment**:
- Average move for positive news
- Average move for negative news
- Comparison across 1-day, 3-day, 7-day periods

**By Confidence**:
- Do high-confidence predictions lead to bigger moves?

### 4. Directional Accuracy

**Question**: Does sentiment correctly predict direction?

**Metrics**:
- % of time positive sentiment → price increase
- % of time negative sentiment → price decrease

**Example**: 75% directional accuracy means sentiment correctly predicted direction 3 out of 4 times.

### 5. False Positive Analysis

**Question**: How often does "important" news fail to move the price?

**False Positive**: Strong sentiment signal but price barely moved (<0.5%)

**Wrong Direction**: Positive sentiment but price decreased (or vice versa)

**Use**: Understand when to ignore or discount certain signals

## Interpreting Results

### Theme Performance Table

Columns explained:

- **Articles**: Sample size (need at least 10 for reliable stats)
- **1D/3D/7D Correlation**: Predictive power over different timeframes
- **Avg Magnitude**: How big the moves typically are (in %)
- **Accuracy**: Directional accuracy (50% = random, 100% = perfect)

### Color Coding

**Correlation Badges**:
- 🟢 High (>0.5): Strong predictive power
- 🟡 Medium (0.3-0.5): Moderate predictive power
- 🔴 Low (<0.3): Weak/no predictive power

### What to Look For

**Good Predictive Themes**:
- High correlation (>0.5)
- High directional accuracy (>70%)
- Sufficient sample size (>20 articles)
- Low false positive rate (<30%)

**Poor Predictive Themes**:
- Near-zero correlation
- Directional accuracy ~50% (like flipping a coin)
- High false positive rate

## Example Analysis Questions

### 1. Which theme is most reliable?

Look at:
- Highest 1-day correlation
- High directional accuracy
- Low false positive rate

### 2. Should I act immediately or wait?

Check time lag chart:
- If >70% moves Day 1: Act quickly
- If <40% moves Day 1: Can wait, more reaction coming

### 3. Which news can I ignore?

Look for:
- Themes with correlation near 0
- High false positive rates
- Directional accuracy ~50%

### 4. Are negative or positive signals more reliable?

Compare in false positive chart:
- Which has lower false positive rate?
- Which has lower wrong direction rate?

## Advanced Analysis

### Filtering Strategy

1. **By Theme**: Focus on your best-performing themes
2. **By Confidence**: Filter for high-confidence predictions only
3. **By Sentiment**: Separate positive/negative signal analysis

### Building a Trading Strategy

**Example Strategy**:
1. Only act on themes with correlation >0.6
2. Require directional accuracy >75%
3. Ignore news from sources with high false positive rates
4. Trade within 24 hours if time lag shows quick reactions

### Exporting Data

The pattern analysis JSON contains raw data for further analysis in Python/R/Excel:

```python
import json
import pandas as pd

with open('results/pattern_analysis.json') as f:
    data = json.load(f)

# Extract theme performance
themes_df = pd.DataFrame(data['theme_performance']['themes'])

# Analyze further...
```

## Key Metrics Explained

### Correlation

**Range**: -1 to +1

- **+1**: Perfect positive correlation (sentiment always matches price direction)
- **0**: No correlation (sentiment doesn't predict price)
- **-1**: Perfect negative correlation (contrarian indicator)

**Statistical Significance**: Need at least 10 samples for reliable correlation

### Directional Accuracy

**Calculation**: % of times sentiment correctly predicted direction

- **>70%**: Excellent
- **60-70%**: Good
- **50-60%**: Weak
- **~50%**: Random (no predictive power)

### False Positive Rate

**Calculation**: % of strong signals with minimal price movement

**Lower is better**: Means signals are reliable

**High rate**: May indicate:
- Market already priced in the news
- News not as important as sentiment suggests
- Need to combine with other factors

## Troubleshooting

### "Pattern analysis not found"

Run the analysis first:
```bash
python analysis/pattern_analyzer.py
```

### "Not enough data"

You need:
- At least 10 articles with price data
- Articles spanning multiple dates
- Run `analyze_news_impact.py` on more articles

### Charts not showing

- Make sure `results/pattern_analysis.json` exists
- Check browser console for errors
- Try a different browser (Chrome/Firefox recommended)

## Next Steps

After identifying patterns:

1. **Validate findings**: Run analysis on new data to confirm patterns hold
2. **Backtest**: Test strategies on historical data
3. **Paper trade**: Test in real-time before committing capital
4. **Monitor**: Track which patterns remain reliable over time

## Files

- `analysis/pattern_analyzer.py`: Computes all metrics
- `pattern_dashboard.html`: Interactive visualization
- `results/pattern_analysis.json`: Analysis output (auto-generated)
- `results/news_impact_analysis.csv`: Input data (from analyze_news_impact.py)

## Tips

- **More data = better patterns**: Aim for 100+ articles
- **Check multiple timeframes**: Some themes predict short-term, others long-term
- **Context matters**: Market conditions affect news impact
- **Combine with fundamentals**: Don't rely solely on news sentiment
- **Monitor changes**: Patterns can evolve as markets adapt
