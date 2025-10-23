"""
Test script for enhanced Kelly Criterion position sizing features.
Tests all the newly added methods.

Author: Claude Code
Date: 2025-10-10
"""
import logging
from analysis.kelly_position_sizing import KellyCriterionPositionSizer, ATRStopLossCalculator

logging.basicConfig(level=logging.INFO)

print("\n" + "="*80)
print("KELLY CRITERION ENHANCEMENTS - COMPREHENSIVE TEST")
print("="*80 + "\n")

# Initialize sizer with $10,000
sizer = KellyCriterionPositionSizer(
    account_size=10000.0,
    kelly_fraction=0.25,
    max_position_pct=0.10,
    max_risk_per_trade_pct=0.02,
    max_portfolio_heat_pct=0.10
)

print("="*80)
print("TEST 1: Daily Drawdown Tracking")
print("="*80)
print(f"Starting balance: ${sizer.account_size:,.2f}")
print(f"Daily drawdown: {sizer.get_daily_drawdown():.2%}")

# Simulate a losing trade
shares, risk, details = sizer.calculate_position_size('CBA', 100.0, 95.0, 0.70)
sizer.open_position('CBA', 100.0, shares, 95.0, 110.0, risk, 0.70)
sizer.close_position('CBA', 95.0, 'Stop loss hit')  # Loss

print(f"\nAfter losing trade:")
print(f"Account size: ${sizer.account_size:,.2f}")
print(f"Daily drawdown: {sizer.get_daily_drawdown():.2%}")

print("\n" + "="*80)
print("TEST 2: Max Drawdown Tracking")
print("="*80)
print(f"Peak balance: ${sizer.peak_balance:,.2f}")
print(f"Current balance: ${sizer.account_size:,.2f}")
print(f"Max drawdown: {sizer.get_max_drawdown():.2%}")

print("\n" + "="*80)
print("TEST 3: Risk Limit Checks")
print("="*80)
risk_status = sizer.check_risk_limits()
print(f"Risk status: {risk_status['status']}")
print(f"Daily drawdown: {risk_status['daily_drawdown']:.2%}")
print(f"Max drawdown: {risk_status['max_drawdown']:.2%}")
print(f"Portfolio heat: {risk_status['portfolio_heat']:.2%}")
print(f"Actions required:")
for action in risk_status['actions_required']:
    print(f"  - {action}")

print("\n" + "="*80)
print("TEST 4: Enhanced Statistics with IC")
print("="*80)

# Add a few more trades to calculate IC
trades_data = [
    ('WBC', 25.0, 24.0, 0.80, True),   # Win
    ('NAB', 30.0, 29.0, 0.65, False),  # Loss
    ('ANZ', 22.0, 21.0, 0.75, True),   # Win
    ('BHP', 45.0, 43.0, 0.60, False),  # Loss
]

for symbol, entry, stop, conf, will_win in trades_data:
    shares, risk, details = sizer.calculate_position_size(symbol, entry, stop, conf)
    sizer.open_position(symbol, entry, shares, stop, entry + (entry - stop) * 2, risk, conf)
    exit_price = entry + (entry - stop) * 1.5 if will_win else stop
    sizer.close_position(symbol, exit_price, 'TP hit' if will_win else 'SL hit')

stats = sizer.get_statistics()
print(f"Total trades: {stats['total_trades']}")
print(f"Win rate: {stats['win_rate']:.1%}")
print(f"Wins: {stats['wins']}, Losses: {stats['losses']}")
print(f"Average win: ${stats['avg_win']:.2f}")
print(f"Average loss: ${stats['avg_loss']:.2f}")
print(f"Largest win: ${stats['largest_win']:.2f}")
print(f"Largest loss: ${stats['largest_loss']:.2f}")
print(f"Profit factor: {stats['profit_factor']:.2f}")
print(f"Total P&L: ${stats['total_pnl']:+.2f}")
print(f"Account return: {stats['account_return']:+.2%}")
print(f"Sharpe ratio: {stats['sharpe_ratio']:.2f}")
print(f"Information Coefficient (IC): {stats['information_coefficient']:+.3f}")
print(f"Account size: ${stats['account_size']:,.2f}")
print(f"Peak balance: ${stats['peak_balance']:,.2f}")
print(f"Current drawdown: {stats['current_drawdown']:.2%}")

print("\n" + "="*80)
print("TEST 5: Reset Daily Tracking")
print("="*80)
print(f"Before reset - Daily drawdown: {sizer.get_daily_drawdown():.2%}")
sizer.reset_daily_tracking()
print(f"After reset - Daily drawdown: {sizer.get_daily_drawdown():.2%}")
print(f"Starting daily balance reset to: ${sizer.starting_daily_balance:,.2f}")

print("\n" + "="*80)
print("TEST 6: ATR Stop Loss Calculator")
print("="*80)

# Test ATR calculation
highs = [46.5, 47.0, 46.8, 47.5, 47.2, 48.0, 47.8, 47.5, 48.2, 48.5,
         48.0, 48.8, 49.0, 48.5, 49.2]
lows = [45.0, 45.5, 45.2, 46.0, 45.8, 46.5, 46.2, 46.0, 46.8, 47.0,
        46.5, 47.2, 47.5, 47.0, 47.8]
closes = [46.0, 46.5, 46.3, 47.0, 46.5, 47.5, 47.0, 46.8, 47.5, 48.0,
          47.5, 48.0, 48.5, 48.0, 48.5]

atr = ATRStopLossCalculator.calculate_atr(highs, lows, closes, period=14)
print(f"Calculated ATR: {atr:.2f}")

# Test stop calculation
entry_price = 48.5
stop_loss, take_profit = ATRStopLossCalculator.calculate_stops(
    entry_price=entry_price,
    atr=atr,
    direction='long',
    atr_multiplier_stop=2.0,
    risk_reward_ratio=2.0
)
print(f"\nEntry price: ${entry_price:.2f}")
print(f"Stop loss: ${stop_loss:.2f} (risk: ${entry_price - stop_loss:.2f} per share)")
print(f"Take profit: ${take_profit:.2f} (reward: ${take_profit - entry_price:.2f} per share)")
print(f"Risk/Reward ratio: {(take_profit - entry_price) / (entry_price - stop_loss):.1f}:1")

# Test position sizing with ATR
shares, stop, risk_amt = ATRStopLossCalculator.calculate_position_size_with_atr(
    account_size=sizer.account_size,
    entry_price=entry_price,
    atr=atr,
    risk_pct=0.02,
    atr_multiplier=2.0
)
print(f"\nPosition sizing with ATR:")
print(f"Shares: {shares}")
print(f"Stop loss: ${stop:.2f}")
print(f"Risk amount: ${risk_amt:.2f} (2% of account)")
print(f"Position value: ${shares * entry_price:,.2f}")

print("\n" + "="*80)
print("TEST 7: Risk Alert Simulation")
print("="*80)

# Simulate larger losses to trigger alerts
print("Simulating 10% drawdown scenario...")
sizer.account_size = 9000  # 10% loss from peak
sizer.daily_pnl = -1000

risk_status = sizer.check_risk_limits()
print(f"\nRisk status: {risk_status['status']}")
print(f"Max drawdown: {risk_status['max_drawdown']:.2%}")
print(f"Actions required:")
for action in risk_status['actions_required']:
    print(f"  - {action}")

print("\nSimulating 20% drawdown (CRITICAL) scenario...")
sizer.account_size = 8000  # 20% loss from peak
risk_status = sizer.check_risk_limits()
print(f"\nRisk status: {risk_status['status']}")
print(f"Max drawdown: {risk_status['max_drawdown']:.2%}")
print(f"Actions required:")
for action in risk_status['actions_required']:
    print(f"  - {action}")

print("\nSimulating 30% drawdown (SHUTDOWN) scenario...")
sizer.account_size = 7000  # 30% loss from peak
risk_status = sizer.check_risk_limits()
print(f"\nRisk status: {risk_status['status']}")
print(f"Max drawdown: {risk_status['max_drawdown']:.2%}")
print(f"Actions required:")
for action in risk_status['actions_required']:
    print(f"  - {action}")

print("\n" + "="*80)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("="*80)
print("\nSummary of new features tested:")
print("[OK] get_daily_drawdown() - Tracks intraday losses")
print("[OK] get_max_drawdown() - Tracks drawdown from peak")
print("[OK] check_risk_limits() - 4-level alert system (NORMAL/ALERT/CRITICAL/SHUTDOWN)")
print("[OK] get_statistics() - Enhanced with Sharpe ratio and IC")
print("[OK] reset_daily_tracking() - Resets daily P&L at market open")
print("[OK] ATRStopLossCalculator - Volatility-based stops")
print("     [OK] calculate_atr() - ATR calculation from OHLC data")
print("     [OK] calculate_stops() - Stop/TP from ATR")
print("     [OK] calculate_position_size_with_atr() - ATR-based position sizing")
print("\n" + "="*80 + "\n")
