"""
Compare Performance: With vs Without Behavioral Filters

Tests the impact of behavioral finance filters on trading performance.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from backtesting.historical_simulator import HistoricalSimulator
from paper_trading.risk_manager import RiskConfig

def run_comparison():
    """Run both tests and compare."""

    risk_config = RiskConfig(
        portfolio_value=10000.0,
        max_risk_per_trade_pct=2.0,
        stop_loss_pct=5.0,
        max_positions_per_sector=3,
        daily_loss_limit_pct=5.0,
        min_confidence=0.6
    )

    print("=" * 80)
    print("BEHAVIORAL FILTER COMPARISON TEST")
    print("=" * 80)
    print()

    # Test 1: WITHOUT behavioral filters
    print("TEST 1: WITHOUT Behavioral Filters")
    print("-" * 80)

    simulator1 = HistoricalSimulator(
        db_path=config.DATABASE_PATH,
        initial_capital=10000.0,
        risk_config=risk_config,
        use_quality_filter=True,
        use_technical_analysis=True,
        use_behavioral_filters=False  # DISABLED
    )

    results1 = simulator1.run_simulation(max_articles=300)

    print(f"\nResults WITHOUT Behavioral Filters:")
    print(f"  Total Trades: {results1['total_trades']}")
    print(f"  Win Rate: {results1['win_rate']:.1f}%")
    print(f"  Return: {results1['total_return_pct']:+.2f}%")
    print(f"  Final Capital: ${results1['final_capital']:,.2f}")

    # Count filtered events
    filtered1 = sum(1 for e in results1['events'] if 'FILTERED' in e.event_type)
    print(f"  Filtered Announcements: {filtered1}")

    print()
    print("=" * 80)
    print()

    # Test 2: WITH behavioral filters
    print("TEST 2: WITH Behavioral Filters")
    print("-" * 80)

    simulator2 = HistoricalSimulator(
        db_path=config.DATABASE_PATH,
        initial_capital=10000.0,
        risk_config=risk_config,
        use_quality_filter=True,
        use_technical_analysis=True,
        use_behavioral_filters=True  # ENABLED
    )

    results2 = simulator2.run_simulation(max_articles=300)

    print(f"\nResults WITH Behavioral Filters:")
    print(f"  Total Trades: {results2['total_trades']}")
    print(f"  Win Rate: {results2['win_rate']:.1f}%")
    print(f"  Return: {results2['total_return_pct']:+.2f}%")
    print(f"  Final Capital: ${results2['final_capital']:,.2f}")

    # Count filtered events
    filtered2 = sum(1 for e in results2['events'] if 'FILTERED' in e.event_type)
    print(f"  Filtered Announcements: {filtered2}")

    print()
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()

    print(f"Trades: {results1['total_trades']} → {results2['total_trades']} ({results2['total_trades'] - results1['total_trades']:+d})")
    print(f"Win Rate: {results1['win_rate']:.1f}% → {results2['win_rate']:.1f}% ({results2['win_rate'] - results1['win_rate']:+.1f}%)")
    print(f"Return: {results1['total_return_pct']:+.2f}% → {results2['total_return_pct']:+.2f}% ({results2['total_return_pct'] - results1['total_return_pct']:+.2f}%)")
    print(f"Filtered: {filtered1} → {filtered2} ({filtered2 - filtered1:+d})")

    print()

    # Analyze filter breakdown for Test 2
    if results2['total_trades'] == 0:
        print("WARNING: No trades with behavioral filters!")
        print()
        print("Filter Breakdown:")
        event_types = {}
        for e in results2['events']:
            event_types[e.event_type] = event_types.get(e.event_type, 0) + 1

        for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
            print(f"  {event_type:<30} {count:>5}")

if __name__ == '__main__':
    run_comparison()
