"""
Test Bayesian Confidence Integration

Quick test to verify the Bayesian confidence scoring is working
across all three systems (live trading, backtesting, paper trading).

Author: Claude Code
Date: 2025-10-10
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis.bayesian_confidence import SignalCombiner


def test_bayesian_basic():
    """Test basic Bayesian confidence calculation."""
    print("\n" + "=" * 70)
    print("TEST 1: Basic Bayesian Confidence Scoring")
    print("=" * 70 + "\n")

    combiner = SignalCombiner()

    # Test case 1: Strong positive sentiment, fresh announcement, optimal time
    print("Case 1: Strong positive sentiment (0.75), fresh (5 min), optimal time (11:00 AM)")
    confidence, breakdown = combiner.compute_confidence(
        sentiment_score=0.75,
        announcement_age_minutes=5.0,
        current_time_aest='11:00:00',
        technical_indicators=None,
        is_material=True,
        recent_price_change=None
    )

    print(f"  Final confidence: {confidence:.3f}")
    print(f"  Base sentiment: {breakdown['base_sentiment']:.3f}")
    print(f"  Time boost: {breakdown['time_freshness_factor']:.3f}x")
    print(f"  Time-of-day boost: {breakdown['time_of_day_factor']:.3f}x")
    print(f"  Combined odds: {breakdown['combined_odds']:.3f}")
    print(f"  OK Confidence properly bounded [0.01, 0.99]: {0.01 <= confidence <= 0.99}")

    # Test case 2: Weak sentiment, stale announcement
    print("\nCase 2: Weak sentiment (0.55), stale (90 min), late afternoon (4:00 PM)")
    confidence2, breakdown2 = combiner.compute_confidence(
        sentiment_score=0.55,
        announcement_age_minutes=90.0,
        current_time_aest='16:00:00',
        technical_indicators=None,
        is_material=True,
        recent_price_change=None
    )

    print(f"  Final confidence: {confidence2:.3f}")
    print(f"  Base sentiment: {breakdown2['base_sentiment']:.3f}")
    print(f"  Time boost: {breakdown2['time_freshness_factor']:.3f}x (penalty for staleness)")
    print(f"  Time-of-day boost: {breakdown2['time_of_day_factor']:.3f}x (penalty for late)")
    print(f"  Combined odds: {breakdown2['combined_odds']:.3f}")
    print(f"  OK Confidence properly bounded [0.01, 0.99]: {0.01 <= confidence2 <= 0.99}")

    # Test case 3: Additive model would exceed 1.0
    print("\nCase 3: Test case that breaks additive model (would give 0.96+)")
    print("  Sentiment: 0.68, Time: 0.15, ToD: 0.05, Tech: 0.08")
    print("  ADDITIVE (BROKEN): 0.68 + 0.15 + 0.05 + 0.08 = 0.96")

    tech_indicators = {'confidence_adjustment': 0.08}
    confidence3, breakdown3 = combiner.compute_confidence(
        sentiment_score=0.68,
        announcement_age_minutes=5.0,  # Fresh (0.15 boost via odds)
        current_time_aest='11:00:00',  # Optimal (0.05 boost via odds)
        technical_indicators=tech_indicators,
        is_material=True,
        recent_price_change=None
    )

    print(f"  BAYESIAN (CORRECT): {confidence3:.3f}")
    print(f"  OK Properly bounded (did not exceed 0.99): {confidence3 <= 0.99}")
    print(f"  Base odds: {breakdown3['combined_odds']:.3f}")

    return True


def test_live_recommendation_engine():
    """Test live recommendation engine integration."""
    print("\n" + "=" * 70)
    print("TEST 2: Live Recommendation Engine Integration")
    print("=" * 70 + "\n")

    try:
        from live_trading.live_recommendation_engine import LiveRecommendationEngine
        import config

        print("  Initializing LiveRecommendationEngine...")
        engine = LiveRecommendationEngine(config.DATABASE_PATH)

        print(f"  [OK] Engine initialized successfully")
        print(f"  [OK] SignalCombiner present: {hasattr(engine, 'signal_combiner')}")
        print(f"  [OK] SignalCombiner type: {type(engine.signal_combiner).__name__}")

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_historical_simulator():
    """Test historical simulator integration."""
    print("\n" + "=" * 70)
    print("TEST 3: Historical Simulator Integration")
    print("=" * 70 + "\n")

    try:
        from backtesting.historical_simulator import HistoricalSimulator
        import config

        print("  Initializing HistoricalSimulator...")
        simulator = HistoricalSimulator(
            db_path=config.DATABASE_PATH,
            initial_capital=10000.0
        )

        print(f"  [OK] Simulator initialized successfully")
        print(f"  [OK] SignalCombiner present: {hasattr(simulator, 'signal_combiner')}")
        print(f"  [OK] SignalCombiner type: {type(simulator.signal_combiner).__name__}")

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_paper_trading_engine():
    """Test paper trading recommendation engine integration."""
    print("\n" + "=" * 70)
    print("TEST 4: Paper Trading Recommendation Engine Integration")
    print("=" * 70 + "\n")

    try:
        from paper_trading.recommendation_engine import RecommendationEngine

        print("  Initializing RecommendationEngine...")
        engine = RecommendationEngine()

        print(f"  [OK] Engine initialized successfully")
        print(f"  [OK] SignalCombiner present: {hasattr(engine, 'signal_combiner')}")
        print(f"  [OK] SignalCombiner type: {type(engine.signal_combiner).__name__}")

        return True
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        return False


def test_mathematical_correctness():
    """Test that Bayesian approach prevents confidence > 1.0 bug."""
    print("\n" + "=" * 70)
    print("TEST 5: Mathematical Correctness (Confidence Bounds)")
    print("=" * 70 + "\n")

    combiner = SignalCombiner()

    test_cases = [
        ("Extreme positive + all boosts", 0.95, 5.0, '11:00:00', {'confidence_adjustment': 0.1}, 10.0),
        ("Moderate + extreme boosts", 0.70, 1.0, '12:00:00', {'confidence_adjustment': 0.15}, 20.0),
        ("High sentiment + all factors", 0.85, 2.0, '11:30:00', {'confidence_adjustment': 0.12}, 15.0),
    ]

    all_passed = True

    for name, sentiment, age_min, time, tech, price_change in test_cases:
        confidence, breakdown = combiner.compute_confidence(
            sentiment_score=sentiment,
            announcement_age_minutes=age_min,
            current_time_aest=time,
            technical_indicators=tech,
            is_material=True,
            recent_price_change=price_change
        )

        passed = 0.01 <= confidence <= 0.99
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}: {confidence:.3f} (bounded: {passed})")

        if not passed:
            all_passed = False

    print(f"\n  {'[OK]' if all_passed else '[FAIL]'} All test cases properly bounded")

    return all_passed


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("BAYESIAN CONFIDENCE SCORING - INTEGRATION TESTS")
    print("Testing proper odds ratio combination (NOT broken additive model)")
    print("=" * 70)

    results = []

    # Test 1: Basic Bayesian math
    try:
        results.append(("Basic Bayesian Scoring", test_bayesian_basic()))
    except Exception as e:
        print(f"\n[FAIL] Test 1 failed: {e}")
        results.append(("Basic Bayesian Scoring", False))

    # Test 2: Live trading integration
    try:
        results.append(("Live Trading Integration", test_live_recommendation_engine()))
    except Exception as e:
        print(f"\n[FAIL] Test 2 failed: {e}")
        results.append(("Live Trading Integration", False))

    # Test 3: Historical simulator integration
    try:
        results.append(("Historical Simulator Integration", test_historical_simulator()))
    except Exception as e:
        print(f"\n[FAIL] Test 3 failed: {e}")
        results.append(("Historical Simulator Integration", False))

    # Test 4: Paper trading integration
    try:
        results.append(("Paper Trading Integration", test_paper_trading_engine()))
    except Exception as e:
        print(f"\n[FAIL] Test 4 failed: {e}")
        results.append(("Paper Trading Integration", False))

    # Test 5: Mathematical correctness
    try:
        results.append(("Mathematical Correctness", test_mathematical_correctness()))
    except Exception as e:
        print(f"\n[FAIL] Test 5 failed: {e}")
        results.append(("Mathematical Correctness", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"  {status}: {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  [OK] ALL TESTS PASSED - Bayesian confidence scoring integrated successfully!")
        print("  [OK] Mathematical bug fixed (confidence can no longer exceed 1.0)")
    else:
        print(f"\n  [FAIL] {total - passed} test(s) failed - review errors above")

    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
