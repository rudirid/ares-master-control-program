#!/usr/bin/env python3
"""
Backtest Runner

Runs backtest simulations and compares against buy-and-hold benchmarks.

Usage:
    python run_backtest.py

    # Custom parameters
    python run_backtest.py --capital 50000 --confidence 0.6

Author: Claude Code
Date: 2025-10-09
"""

import argparse
import sys
import os
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from backtesting.backtest_engine import BacktestEngine, TradingConfig
from backtesting.benchmark import BenchmarkCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_results(results: dict, title: str = "BACKTEST RESULTS"):
    """
    Print backtest results in a formatted way.

    Args:
        results: Results dictionary
        title: Section title
    """
    print("\n" + "=" * 70)
    print(f"{title}")
    print("=" * 70)

    if 'error' in results:
        print(f"Error: {results['error']}")
        return

    print(f"\nCapital")
    print(f"  Initial: ${results['initial_capital']:,.2f}")
    print(f"  Final:   ${results['final_capital']:,.2f}")
    print(f"  Total Return: {results['total_return_pct']:+.2f}%")

    print(f"\nTrades")
    print(f"  Total: {results['total_trades']}")
    print(f"  Winning: {results['winning_trades']} ({results['win_rate']:.1f}%)")
    print(f"  Losing: {results['losing_trades']}")

    print(f"\nProfitability")
    print(f"  Total P/L: ${results['total_pnl']:+,.2f}")
    print(f"  Avg Win: ${results['avg_win']:+,.2f}")
    print(f"  Avg Loss: ${results['avg_loss']:+,.2f}")
    if results['avg_loss'] != 0:
        profit_factor = abs(results['avg_win'] / results['avg_loss'])
        print(f"  Profit Factor: {profit_factor:.2f}")

    print(f"\nRisk")
    print(f"  Max Drawdown: {results['max_drawdown_pct']:.2f}%")

    print(f"\nCosts")
    print(f"  Total Commission: ${results['total_commission']:,.2f}")
    print(f"  Total Slippage: ${results['total_slippage']:,.2f}")


def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description='Run backtest simulation')
    parser.add_argument('--capital', type=float, default=100000,
                       help='Initial capital (default: 100000)')
    parser.add_argument('--commission', type=float, default=0.1,
                       help='Commission percentage (default: 0.1)')
    parser.add_argument('--slippage', type=float, default=0.05,
                       help='Slippage percentage (default: 0.05)')
    parser.add_argument('--max-position', type=float, default=0.2,
                       help='Max position size as fraction of portfolio (default: 0.2)')
    parser.add_argument('--confidence', type=float, default=0.5,
                       help='Minimum confidence threshold (default: 0.5)')
    parser.add_argument('--sentiment-score', type=float, default=0.2,
                       help='Minimum sentiment score threshold (default: 0.2)')
    parser.add_argument('--holding-period', type=int, default=7,
                       help='Holding period in days (default: 7)')
    parser.add_argument('--allow-shorting', action='store_true',
                       help='Allow short selling')
    parser.add_argument('--csv', type=str, default='results/news_impact_analysis.csv',
                       help='Input CSV file')
    parser.add_argument('--output', type=str, default='results/backtest_trades.csv',
                       help='Output trades CSV file')

    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("NEWS-BASED TRADING BACKTEST")
    print("=" * 70 + "\n")

    # Check input file
    if not os.path.exists(args.csv):
        print(f"Error: Input file not found: {args.csv}")
        print("Please run analyze_news_impact.py first")
        return

    # Create configuration
    trading_config = TradingConfig(
        initial_capital=args.capital,
        commission_pct=args.commission,
        slippage_pct=args.slippage,
        max_position_size=args.max_position,
        min_confidence=args.confidence,
        min_sentiment_score=args.sentiment_score,
        holding_period_days=args.holding_period,
        allow_shorting=args.allow_shorting
    )

    print("Configuration:")
    print(f"  Initial Capital: ${trading_config.initial_capital:,.2f}")
    print(f"  Commission: {trading_config.commission_pct}%")
    print(f"  Slippage: {trading_config.slippage_pct}%")
    print(f"  Max Position Size: {trading_config.max_position_size * 100}%")
    print(f"  Min Confidence: {trading_config.min_confidence}")
    print(f"  Min Sentiment Score: {trading_config.min_sentiment_score}")
    print(f"  Holding Period: {trading_config.holding_period_days} days")
    print(f"  Allow Shorting: {trading_config.allow_shorting}")
    print()

    # Initialize engine
    print("Initializing backtest engine...")
    engine = BacktestEngine(trading_config, config.DATABASE_PATH)

    # Run backtest
    print("Running backtest simulation...")
    start_time = datetime.now()

    results = engine.run_backtest(args.csv)

    elapsed = (datetime.now() - start_time).total_seconds()

    # Print results
    print_results(results, "STRATEGY PERFORMANCE")

    # Export trades
    if results.get('total_trades', 0) > 0:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        engine.export_trades(args.output)
        print(f"\nDetailed trade log: {args.output}")

    # Calculate benchmark
    print("\n" + "=" * 70)
    print("BENCHMARK COMPARISON")
    print("=" * 70)

    try:
        benchmark_calc = BenchmarkCalculator(config.DATABASE_PATH)
        benchmark_results = benchmark_calc.calculate_buy_and_hold(
            args.csv,
            initial_capital=trading_config.initial_capital
        )

        if 'error' not in benchmark_results:
            print(f"\nBuy & Hold ASX200")
            print(f"  Final Value: ${benchmark_results['final_value']:,.2f}")
            print(f"  Total Return: {benchmark_results['total_return_pct']:+.2f}%")
            print(f"  Max Drawdown: {benchmark_results['max_drawdown_pct']:.2f}%")

            # Compare
            if results.get('total_trades', 0) > 0:
                print(f"\nComparison")
                strategy_return = results['total_return_pct']
                benchmark_return = benchmark_results['total_return_pct']
                outperformance = strategy_return - benchmark_return

                print(f"  Strategy Return: {strategy_return:+.2f}%")
                print(f"  Benchmark Return: {benchmark_return:+.2f}%")
                print(f"  Outperformance: {outperformance:+.2f}%")

                if outperformance > 0:
                    print(f"\n  Strategy OUTPERFORMED benchmark by {outperformance:.2f}%")
                else:
                    print(f"\n  Strategy UNDERPERFORMED benchmark by {abs(outperformance):.2f}%")
        else:
            print(f"Benchmark calculation failed: {benchmark_results['error']}")

    except Exception as e:
        print(f"Error calculating benchmark: {e}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Simulation completed in {elapsed:.1f} seconds")

    if results.get('total_trades', 0) > 0:
        print(f"Executed {results['total_trades']} trades")
        print(f"Win rate: {results['win_rate']:.1f}%")
        print(f"Final return: {results['total_return_pct']:+.2f}%")
    else:
        print("No trades executed - adjust strategy parameters")

    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
