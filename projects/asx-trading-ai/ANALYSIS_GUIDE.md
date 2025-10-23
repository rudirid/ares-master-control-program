# News Sentiment & Price Impact Analysis Guide

## Overview

This analysis tool correlates news sentiment with stock price movements using Claude AI for sentiment analysis.

## Features

1. **Sentiment Analysis**: Uses Claude API to analyze:
   - Sentiment (positive/negative/neutral)
   - Sentiment score (-1.0 to +1.0)
   - Confidence level
   - Key themes and topics
   - Impact assessment

2. **Price Impact Analysis**: Calculates stock price changes:
   - 1-day, 3-day, and 7-day percentage changes
   - Absolute price changes
   - Baseline volatility (30-day standard deviation)

3. **CSV Export**: Comprehensive data export for further analysis in Excel, Python, R, etc.

## Prerequisites

### 1. Anthropic API Key

You need an Anthropic API key to use Claude for sentiment analysis.

**Get your API key:**
- Sign up at: https://console.anthropic.com
- Navigate to API Keys section
- Create a new API key

**Set your API key as an environment variable:**

Windows (PowerShell):
```powershell
$env:ANTHROPIC_API_KEY = "your-api-key-here"
```

Windows (Command Prompt):
```cmd
set ANTHROPIC_API_KEY=your-api-key-here
```

Linux/Mac:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 2. Data Requirements

- News articles in the `news_articles` table with dates
- Stock price data in the `stock_prices` table

## Usage

### Basic Usage

Analyze all articles in the database:

```bash
python analyze_news_impact.py
```

### Analyze Specific Tickers

```bash
python analyze_news_impact.py --tickers BHP,CBA,NAB
```

### Limit Number of Articles

For testing or quick analysis:

```bash
python analyze_news_impact.py --limit 10
```

### Custom Output File

```bash
python analyze_news_impact.py --output my_analysis.csv
```

### Adjust API Rate Limiting

```bash
python analyze_news_impact.py --api-delay 2.0
```

## Output CSV Columns

The analysis produces a CSV file with the following columns:

### Article Information
- `article_id`: Unique article ID
- `ticker`: Stock ticker symbol
- `source`: News source (e.g., 'AFR')
- `article_date`: Publication date
- `title`: Article title
- `url`: Article URL

### Sentiment Analysis
- `sentiment`: positive/negative/neutral
- `sentiment_score`: -1.0 (very negative) to +1.0 (very positive)
- `confidence`: 0.0 to 1.0 (how confident Claude is)
- `themes`: Key themes (pipe-separated)
- `summary`: Brief explanation of sentiment classification
- `impact_assessment`: Expected price impact

### 1-Day Price Impact
- `price_change_1d`: Absolute price change ($)
- `price_change_pct_1d`: Percentage change (%)
- `start_price_1d`: Starting price
- `end_price_1d`: Ending price

### 3-Day Price Impact
- `price_change_3d`: Absolute price change ($)
- `price_change_pct_3d`: Percentage change (%)
- `start_price_3d`: Starting price
- `end_price_3d`: Ending price

### 7-Day Price Impact
- `price_change_7d`: Absolute price change ($)
- `price_change_pct_7d`: Percentage change (%)
- `start_price_7d`: Starting price
- `end_price_7d`: Ending price

### Baseline Metrics
- `baseline_volatility_30d`: 30-day volatility (%)
- `status`: success/error
- `error`: Error message if any

## Example Analysis Workflow

### 1. Initial Test

Test on a small sample first:

```bash
python analyze_news_impact.py --limit 5
```

### 2. Analyze Specific Stocks

Focus on stocks of interest:

```bash
python analyze_news_impact.py --tickers BHP,RIO,FMG
```

### 3. Full Historical Analysis

Run on all articles (may take time):

```bash
python analyze_news_impact.py
```

### 4. Analyze Results in Excel/Python

Open the CSV file and perform analysis:
- Correlation between sentiment score and price changes
- Which themes correlate with positive/negative moves
- Average price impact by sentiment category
- Comparison with baseline volatility

## Sample Analysis Questions

### In Excel/Python:

1. **Do positive sentiment articles correlate with price increases?**
   - Plot sentiment_score vs price_change_pct_1d
   - Calculate correlation coefficient

2. **Which themes have the strongest price impact?**
   - Group by themes
   - Calculate average price changes per theme

3. **Is sentiment analysis accurate?**
   - Compare predicted impact_assessment with actual price_change
   - Calculate accuracy metrics

4. **What's the optimal holding period?**
   - Compare 1-day vs 3-day vs 7-day returns
   - Find which period shows strongest correlation

5. **Does confidence matter?**
   - Filter by high confidence (>0.7)
   - Check if accuracy improves

## Cost Estimation

**Anthropic API Pricing** (as of 2024):
- Claude 3.5 Sonnet: ~$0.003 per article
- 100 articles: ~$0.30
- 1000 articles: ~$3.00

**Note**: Always check current pricing at https://www.anthropic.com/pricing

## Testing Individual Components

### Test Sentiment Analyzer

```bash
cd analysis
python sentiment_analyzer.py
```

### Test Price Analyzer

```bash
cd analysis
python price_analyzer.py
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- Ensure you've set the environment variable
- Check it's set in the same terminal session where you run the script

### "No articles found"
- Check that articles exist in the database
- Verify articles have dates (datetime or created_at)
- Try without --tickers filter first

### "No price data available"
- Ensure stock_prices table has data for the tickers
- Check date ranges match between articles and price data
- Run download_asx_top100.py to populate price data

### API Rate Limiting
- Increase --api-delay parameter
- Anthropic has generous rate limits, but if hitting limits, try:
  ```bash
  python analyze_news_impact.py --api-delay 2.0
  ```

## Next Steps

After running the analysis:

1. **Open the CSV** in Excel or your analysis tool of choice
2. **Create pivot tables** to explore sentiment by ticker, theme, etc.
3. **Calculate correlations** between sentiment scores and price changes
4. **Visualize results** with scatter plots, histograms, etc.
5. **Build predictive models** using the features extracted

## Example Python Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load results
df = pd.read_csv('results/news_impact_analysis.csv')

# Basic statistics
print(df.groupby('sentiment')['price_change_pct_1d'].describe())

# Correlation
corr = df[['sentiment_score', 'price_change_pct_1d']].corr()
print(f"Correlation: {corr.iloc[0, 1]:.3f}")

# Visualization
plt.scatter(df['sentiment_score'], df['price_change_pct_1d'])
plt.xlabel('Sentiment Score')
plt.ylabel('1-Day Price Change (%)')
plt.title('News Sentiment vs Price Impact')
plt.show()
```

## Support

For issues or questions:
- Check logs in the `logs/` directory
- Review error messages in the CSV file
- Ensure all dependencies are installed: `pip install -r requirements.txt`
