"""
Diagnose which filter is rejecting all trades.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from backtesting.historical_simulator import HistoricalSimulator
from paper_trading.risk_manager import RiskConfig

def diagnose():
    """Diagnose filter issues."""

    risk_config = RiskConfig(
        portfolio_value=10000.0,
        max_risk_per_trade_pct=2.0,
        stop_loss_pct=5.0,
        max_positions_per_sector=3,
        daily_loss_limit_pct=5.0,
        min_confidence=0.6
    )

    simulator = HistoricalSimulator(
        db_path=config.DATABASE_PATH,
        initial_capital=10000.0,
        risk_config=risk_config,
        use_quality_filter=True,
        use_technical_analysis=True,
        use_behavioral_filters=True
    )

    results = simulator.run_simulation(max_articles=300)

    print("\nEVENT TYPE BREAKDOWN:")
    print("="*60)

    event_counts = {}
    for e in results['events']:
        event_counts[e.event_type] = event_counts.get(e.event_type, 0) + 1

    for event_type, count in sorted(event_counts.items(), key=lambda x: -x[1]):
        print(f"{event_type:<30} {count:>5}")

    print("\nFiltered Totals:")
    print(f"  FILTERED (quality):         {event_counts.get('FILTERED', 0)}")
    print(f"  TIME_FILTERED:              {event_counts.get('TIME_FILTERED', 0)}")
    print(f"  MATERIALITY_FILTERED:       {event_counts.get('MATERIALITY_FILTERED', 0)}")
    print(f"  TOD_FILTERED:               {event_counts.get('TOD_FILTERED', 0)}")
    print(f"  TECH_REJECTED:              {event_counts.get('TECH_REJECTED', 0)}")
    print(f"  TECH_NO_DATA:               {event_counts.get('TECH_NO_DATA', 0)}")
    print(f"  REJECTED (risk):            {event_counts.get('REJECTED', 0)}")

    print(f"\nTOTAL TRADES: {results['total_trades']}")
    print(f"RECOMMENDATIONS: {event_counts.get('RECOMMENDATION', 0)}")

    # Sample a few filtered announcements to see why
    print("\nSAMPLE FILTERED ANNOUNCEMENTS (first 5):")
    print("="*60)

    count = 0
    for e in results['events']:
        if 'FILTERED' in e.event_type and count < 5:
            print(f"\n{e.event_type}: {e.ticker}")
            print(f"  Description: {e.description[:80]}")
            count += 1

if __name__ == '__main__':
    diagnose()
