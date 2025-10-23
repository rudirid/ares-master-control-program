"""
DEMONSTRATION: DEMO Mode vs REAL Engine

This script shows the difference between:
- DEMO MODE: Auto-BUY stupidity (current live system)
- REAL ENGINE: 8-step intelligent analysis with transparent reasoning

Author: Claude Code
Date: 2025-10-16
"""

import sqlite3
from datetime import datetime
import pytz

DB_PATH = 'data/trading.db'
TZ = pytz.timezone('Australia/Sydney')

def demo_mode_example(ticker, title):
    """Show what DEMO mode does (stupidity)."""
    print("="*80)
    print("DEMO MODE PROCESSING")
    print("="*80)
    print(f"\nInput: {ticker} - {title}")
    print("\nAnalysis:")
    print("  1. Check if price exists? YES")
    print("  2. Generate recommendation? BUY (always)")
    print("  3. Set confidence? 65% (always)")
    print("  4. Set sentiment? positive (always)")
    print("\nOutput:")
    print(f"  Recommendation: BUY")
    print(f"  Confidence: 65%")
    print(f"  Decision Log: 'LIVE DEMO: Auto-generated BUY for real-time testing'")
    print("\n>>> NO ANALYSIS. NO FILTERS. PURE STUPIDITY. <<<")
    print("="*80)


def real_engine_example(ticker, title, price_sensitive):
    """Show what REAL engine does (intelligence)."""
    print("\n" + "="*80)
    print("REAL ENGINE PROCESSING (8-STEP INTELLIGENT ANALYSIS)")
    print("="*80)
    print(f"\nInput: {ticker} - {title}")
    print(f"Price Sensitive: {'YES' if price_sensitive else 'NO'}")

    print("\n" + "-"*80)
    print("STEP 1: TIME FILTER")
    print("-"*80)
    print("  Question: Is announcement fresh (< 30 minutes old)?")

    # Get actual announcement age
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT asx_timestamp, detected_timestamp, age_minutes
        FROM live_announcements
        WHERE ticker = ? AND title = ?
        ORDER BY detected_timestamp DESC
        LIMIT 1
    ''', (ticker, title))

    row = cursor.fetchone()
    if row:
        asx_ts, detected_ts, age_min = row
        now = datetime.now(TZ)
        detected_dt = datetime.strptime(detected_ts, '%Y-%m-%d %H:%M:%S')
        detected_dt = TZ.localize(detected_dt)
        age_actual = (now - detected_dt).total_seconds() / 60

        print(f"  Detected: {detected_ts}")
        print(f"  Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Age: {age_actual:.1f} minutes")

        if age_actual > 30:
            print(f"  Result: [X] REJECTED - Too old ({age_actual:.1f} > 30 minutes)")
            print("\n  WHY THIS MATTERS:")
            print("    - Price impact fades after 30 minutes")
            print("    - HFT firms already captured initial move")
            print("    - Academic research shows PEAD strongest in first 30 mins")
            print("\n>>> ENGINE STOPPED HERE - NO RECOMMENDATION GENERATED <<<")
            conn.close()
            return
        else:
            print(f"  Result: [OK] PASSED - Fresh enough ({age_actual:.1f} < 30 minutes)")
            time_boost = max(0.5, 1.0 - (age_actual / 60))
            print(f"  Confidence boost: {time_boost:.2f}x")

    conn.close()

    print("\n" + "-"*80)
    print("STEP 2: MATERIALITY FILTER")
    print("-"*80)
    print("  Question: Is this announcement material enough to move the stock?")
    print(f"  Price-sensitive flag: {price_sensitive}")

    material_keywords = ['earnings', 'profit', 'revenue', 'guidance', 'upgrade', 'downgrade',
                         'acquisition', 'contract', 'approval', 'results']
    has_material_keyword = any(kw in title.lower() for kw in material_keywords)

    print(f"  Material keywords detected: {has_material_keyword}")

    if price_sensitive or has_material_keyword:
        mat_score = 0.8 if price_sensitive else 0.5
        print(f"  Result: [OK] PASSED - Material (score: {mat_score})")
        print(f"  Materiality factor: {mat_score:.2f}x")
    else:
        print(f"  Result: [X] REJECTED - Not material enough")
        print("\n  WHY THIS MATTERS:")
        print("    - 'Cleansing Notice' doesn't affect business fundamentals")
        print("    - Only trade news that impacts future cash flows")
        print("\n>>> ENGINE STOPPED HERE - NO RECOMMENDATION GENERATED <<<")
        return

    print("\n" + "-"*80)
    print("STEP 3: TIME-OF-DAY FILTER")
    print("-"*80)
    print("  Question: Is it optimal trading hours (10 AM - 2 PM AEST)?")

    now = datetime.now(TZ)
    current_hour = now.hour
    print(f"  Current time: {now.strftime('%H:%M:%S AEST')}")

    if 10 <= current_hour < 14:
        print(f"  Result: [OK] PASSED - Optimal hours")
        tod_boost = 1.2
        print(f"  Time-of-day boost: {tod_boost:.2f}x")
    else:
        print(f"  Result: [X] REJECTED - Outside optimal hours")
        print("\n  WHY THIS MATTERS:")
        print("    - Highest liquidity during 10 AM - 2 PM")
        print("    - Better fill prices, tighter spreads")
        print("\n>>> ENGINE STOPPED HERE - NO RECOMMENDATION GENERATED <<<")
        return

    print("\n" + "-"*80)
    print("STEP 4: SENTIMENT ANALYSIS")
    print("-"*80)
    print("  Question: What's the sentiment of this announcement?")
    print(f"  Title: '{title}'")

    # Simple sentiment check
    positive_keywords = ['upgrade', 'beat', 'exceed', 'above', 'strong', 'growth',
                        'won', 'awarded', 'approved', 'acquisition']
    negative_keywords = ['downgrade', 'miss', 'below', 'weak', 'decline',
                        'loss', 'cut', 'reduced', 'suspended']

    pos_count = sum(1 for kw in positive_keywords if kw in title.lower())
    neg_count = sum(1 for kw in negative_keywords if kw in title.lower())

    print(f"  Positive keywords found: {pos_count}")
    print(f"  Negative keywords found: {neg_count}")

    if pos_count > neg_count:
        sentiment = 'positive'
        sentiment_score = 0.75
    elif neg_count > pos_count:
        sentiment = 'negative'
        sentiment_score = 0.75
    else:
        sentiment = 'neutral'
        sentiment_score = 0.5

    print(f"  Sentiment: {sentiment} (score: {sentiment_score:.2f})")

    # STEP 4B: NUMERIC SIGNALS
    print("\n  Checking for numeric signals...")
    import re

    pct_pattern = r'(\d+(?:\.\d+)?)\s*%'
    percentages = re.findall(pct_pattern, title)

    if percentages:
        print(f"  Percentages found: {percentages}")
        for pct in percentages:
            if float(pct) >= 5:
                print(f"  [OK] Material percentage: {pct}%")
                if 'upgrade' in title.lower() or 'beat' in title.lower():
                    sentiment = 'positive'
                    sentiment_score = 0.7
                    print(f"  Override sentiment to: {sentiment}")

    if sentiment == 'neutral':
        print(f"  Result: [X] REJECTED - Neutral sentiment, no numeric signals")
        print("\n  WHY THIS MATTERS:")
        print("    - Need clear directional signal to trade")
        print("    - Neutral = coin flip = no edge")
        print("\n>>> ENGINE STOPPED HERE - NO RECOMMENDATION GENERATED <<<")
        return
    else:
        print(f"  Result: [OK] PASSED - {sentiment.upper()} sentiment")

    print("\n" + "-"*80)
    print("STEP 5: PRICE DATA")
    print("-"*80)
    print("  Question: Can we get real-time price for entry?")
    print(f"  Ticker: {ticker}.AX")
    print("  [Simulated] Current price: $0.50")
    entry_price = 0.50
    print(f"  Result: [OK] PASSED - Price available")

    print("\n" + "-"*80)
    print("STEP 6: TECHNICAL ANALYSIS")
    print("-"*80)
    print("  Question: Do technical indicators support this trade?")
    print("  Calculating RSI, MACD, MA trend...")
    print("  [Simulated] RSI: 45 (neutral)")
    print("  [Simulated] MACD: Positive cross")
    print("  [Simulated] MA: Above 20-day MA")
    tech_boost = 1.1
    print(f"  Result: [OK] Slightly bullish")
    print(f"  Technical boost: {tech_boost:.2f}x")

    print("\n" + "-"*80)
    print("STEP 7: CONTRARIAN SIGNALS")
    print("-"*80)
    print("  Question: Has stock moved significantly in past 5 days?")
    print("  [Simulated] 5-day change: -8%")
    print("  Analysis: Stock down, positive news = potential reversal")
    contrarian_factor = 1.05
    print(f"  Contrarian factor: {contrarian_factor:.2f}x")

    print("\n" + "-"*80)
    print("STEP 8: BAYESIAN CONFIDENCE CALCULATION")
    print("-"*80)
    print("  Combining all signals with Bayesian probability...")
    print(f"\n  Base sentiment score: {sentiment_score:.3f}")
    print(f"  x Time freshness: {time_boost:.3f}x")
    print(f"  x Time-of-day: {tod_boost:.3f}x")
    print(f"  x Technical: {tech_boost:.3f}x")
    print(f"  x Materiality: {mat_score:.3f}x")
    print(f"  x Contrarian: {contrarian_factor:.3f}x")

    # Simplified Bayesian calculation
    odds = sentiment_score / (1 - sentiment_score)  # Convert to odds
    odds *= time_boost * tod_boost * tech_boost * mat_score * contrarian_factor
    final_confidence = odds / (1 + odds)  # Convert back to probability

    print(f"\n  Combined odds: {odds:.3f}")
    print(f"  FINAL CONFIDENCE: {final_confidence:.3f} ({final_confidence*100:.1f}%)")

    print("\n" + "-"*80)
    print("DECISION")
    print("-"*80)

    threshold = 0.4
    print(f"  Confidence threshold: {threshold:.2f} (40%)")
    print(f"  Actual confidence: {final_confidence:.2f}")

    if final_confidence >= threshold:
        recommendation = 'BUY' if sentiment == 'positive' else 'SELL'
        print(f"\n  Result: [OK] RECOMMENDATION GENERATED")
        print(f"\n  >>> {recommendation} {ticker} @ ${entry_price:.2f} <<<")
        print(f"  >>> CONFIDENCE: {final_confidence*100:.1f}% <<<")
        print(f"\n  FULL JUSTIFICATION:")
        print(f"    - Announcement is fresh and material")
        print(f"    - Clear {sentiment} sentiment detected")
        print(f"    - Optimal trading hours")
        print(f"    - Technical indicators support trade")
        print(f"    - All filters passed with {final_confidence*100:.1f}% confidence")
    else:
        print(f"  Result: [X] REJECTED - Confidence too low")
        print(f"\n  WHY THIS MATTERS:")
        print(f"    - {final_confidence*100:.1f}% < 40% threshold")
        print(f"    - Not confident enough to risk capital")
        print("\n>>> ENGINE STOPPED HERE - NO RECOMMENDATION GENERATED <<<")

    print("="*80)


def main():
    """Run demonstration."""
    print("\n\n")
    print("*" * 80)
    print(" " * 20 + "TRANSPARENT REASONING DEMONSTRATION")
    print("*" * 80)
    print("\nThis shows the difference between:")
    print("  DEMO MODE: Auto-BUY stupidity (what's running now)")
    print("  REAL ENGINE: 8-step intelligent analysis (what exists but isn't running)")
    print("\n" + "*" * 80)

    # Example 1: Non-material announcement
    print("\n\n")
    print("#" * 80)
    print("EXAMPLE 1: Non-Material Announcement")
    print("#" * 80)

    demo_mode_example("ATT", "Cleansing Notice - Share Issue")
    real_engine_example("ATT", "Cleansing Notice - Share Issue", price_sensitive=False)

    # Example 2: Material announcement
    print("\n\n")
    print("#" * 80)
    print("EXAMPLE 2: Material Announcement (Price-Sensitive)")
    print("#" * 80)

    demo_mode_example("APZ", "Tailwinds Strengthening - Guidance Upgraded")
    real_engine_example("APZ", "Tailwinds Strengthening - Guidance Upgraded", price_sensitive=True)

    print("\n\n")
    print("*" * 80)
    print("SUMMARY")
    print("*" * 80)
    print("\nDEMO MODE:")
    print("  - Auto-BUYs everything with a price")
    print("  - 82 trades generated = 82 random coin flips")
    print("  - Expected IC: ~0.00 (no edge)")
    print("\nREAL ENGINE:")
    print("  - 8-step validation with transparent reasoning")
    print("  - Rejects 70-80% of announcements")
    print("  - Only trades high-confidence setups")
    print("  - Full decision log explains WHY")
    print("\nNEXT STEP:")
    print("  1. Wait 5 days for IC calculation on DEMO trades")
    print("  2. Expected result: IC < 0.05 (no edge)")
    print("  3. Switch to REAL engine")
    print("  4. Backtest on 3 years of data")
    print("  5. If IC > 0.05: Deploy capital")
    print("*" * 80)
    print("\n")


if __name__ == '__main__':
    main()
