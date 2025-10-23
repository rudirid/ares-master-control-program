"""
Quick test of the risk management module.
Verifies all imports and basic functionality.
"""

print("="*80)
print("RISK MODULE - QUICK TEST")
print("="*80 + "\n")

print("Test 1: Importing components...")
from risk import KellyCriterionPositionSizer, ATRStopLossCalculator, Position
print("[OK] All imports successful\n")

print("Test 2: Initializing position sizer...")
sizer = KellyCriterionPositionSizer(
    account_size=10000.0,
    kelly_fraction=0.25,
    max_position_pct=0.10,
    max_risk_per_trade_pct=0.02,
    max_portfolio_heat_pct=0.10
)
print(f"[OK] Sizer initialized with ${sizer.account_size:,.0f}\n")

print("Test 3: Calculating position size...")
shares, risk, details = sizer.calculate_position_size(
    symbol='BHP',
    entry_price=45.00,
    stop_loss_price=43.00,
    confidence=0.75
)
print(f"[OK] Position calculated: {shares} shares, ${risk:.2f} risk\n")

print("Test 4: Opening position...")
position = sizer.open_position(
    symbol='BHP',
    entry_price=45.00,
    shares=shares,
    stop_loss=43.00,
    take_profit=48.00,
    risk_amount=risk,
    confidence=0.75
)
print(f"[OK] Position opened: {position.symbol} - {position.shares} shares\n")

print("Test 5: Checking risk limits...")
risk_status = sizer.check_risk_limits()
print(f"[OK] Risk status: {risk_status['status']}")
print(f"     Portfolio heat: {risk_status['portfolio_heat']:.2%}")
print(f"     Max drawdown: {risk_status['max_drawdown']:.2%}\n")

print("Test 6: Closing position...")
trade = sizer.close_position('BHP', 48.00, 'Take profit hit')
print(f"[OK] Position closed: P/L ${trade['pnl']:+.2f}\n")

print("Test 7: Getting statistics...")
stats = sizer.get_statistics()
print(f"[OK] Statistics calculated:")
print(f"     Total trades: {stats['total_trades']}")
print(f"     Win rate: {stats['win_rate']:.0%}")
print(f"     Account return: {stats['account_return']:+.2%}\n")

print("Test 8: ATR calculations...")
highs = [46.5, 47.0, 46.8, 47.5, 47.2, 48.0, 47.8, 47.5, 48.2, 48.5,
         48.0, 48.8, 49.0, 48.5, 49.2]
lows = [45.0, 45.5, 45.2, 46.0, 45.8, 46.5, 46.2, 46.0, 46.8, 47.0,
        46.5, 47.2, 47.5, 47.0, 47.8]
closes = [46.0, 46.5, 46.3, 47.0, 46.5, 47.5, 47.0, 46.8, 47.5, 48.0,
          47.5, 48.0, 48.5, 48.0, 48.5]

atr = ATRStopLossCalculator.calculate_atr(highs, lows, closes)
print(f"[OK] ATR calculated: {atr:.2f}\n")

print("Test 9: ATR-based stops...")
stop, tp = ATRStopLossCalculator.calculate_stops(
    entry_price=48.5,
    atr=atr,
    direction='long',
    atr_multiplier_stop=2.0,
    risk_reward_ratio=2.0
)
print(f"[OK] Stops calculated:")
print(f"     Entry: $48.50")
print(f"     Stop: ${stop:.2f}")
print(f"     Take profit: ${tp:.2f}\n")

print("="*80)
print("ALL TESTS PASSED - RISK MODULE READY!")
print("="*80)
print("\nUsage:")
print("  from risk import KellyCriterionPositionSizer, ATRStopLossCalculator")
print("\nDocumentation:")
print("  See risk/README.md for detailed usage guide")
print("="*80 + "\n")
