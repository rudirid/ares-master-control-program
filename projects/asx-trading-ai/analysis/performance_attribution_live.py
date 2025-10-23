"""
Performance Attribution for Live Paper Trading

Analyzes live trading results to measure Information Coefficient and determine
if the system has real predictive power.

Key Questions:
1. Does sentiment have edge in LIVE trading? (vs historical IC = 0.000)
2. Do TIME filters improve performance?
3. Are we ready for real money trading?

Author: Claude Code
Date: 2025-10-10
"""

import logging
import sqlite3
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from analysis.performance_attribution import PerformanceAttributor, SignalPerformance

logger = logging.getLogger(__name__)


@dataclass
class LivePosition:
    """Simplified position for IC calculation."""
    ticker: str
    sentiment: str
    sentiment_score: float
    recommendation_confidence: float
    entry_price: float
    entry_timestamp: datetime
    exit_price: Optional[float] = None
    exit_timestamp: Optional[datetime] = None
    return_pct: Optional[float] = None
    days_held: Optional[int] = None
    themes: List[str] = None


class LivePerformanceAnalyzer:
    """
    Analyze live paper trading results to measure real edge.
    """

    def __init__(self, db_path: str):
        """
        Initialize live performance analyzer.

        Args:
            db_path: Database path
        """
        self.db_path = db_path
        self.attributor = PerformanceAttributor(db_path)

    def fetch_live_recommendations(self) -> List[Dict]:
        """Fetch all live recommendations from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                ticker,
                recommendation,
                confidence,
                entry_price,
                sentiment,
                sentiment_score,
                sentiment_confidence,
                generated_timestamp
            FROM live_recommendations
            ORDER BY generated_timestamp
        """)

        rows = cursor.fetchall()
        conn.close()

        recommendations = []
        for row in rows:
            recommendations.append({
                'id': row[0],
                'ticker': row[1],
                'recommendation': row[2],
                'confidence': row[3],
                'entry_price': row[4],
                'sentiment': row[5],
                'sentiment_score': row[6],
                'sentiment_confidence': row[7],
                'generated_timestamp': datetime.strptime(row[8], '%Y-%m-%d %H:%M:%S')
            })

        return recommendations

    def calculate_live_returns(
        self,
        recommendations: List[Dict],
        holding_period_days: int = 7
    ) -> List[LivePosition]:
        """
        Calculate returns for live recommendations.

        Args:
            recommendations: List of live recommendations
            holding_period_days: How many days to hold (default 7)

        Returns:
            List of LivePosition objects with returns calculated
        """
        import yfinance as yf

        positions = []

        for rec in recommendations:
            try:
                # Get current price and exit price
                ticker_symbol = f"{rec['ticker']}.AX"
                stock = yf.Ticker(ticker_symbol)

                # Entry price
                entry_price = rec['entry_price']
                entry_timestamp = rec['generated_timestamp']

                # Calculate exit date
                exit_date = entry_timestamp + timedelta(days=holding_period_days)

                # If exit date is in future, use latest price
                if exit_date > datetime.now():
                    hist = stock.history(period='1d')
                    if not hist.empty:
                        exit_price = float(hist['Close'].iloc[-1])
                        exit_timestamp = datetime.now()
                    else:
                        logger.warning(f"No price data for {rec['ticker']}")
                        continue
                else:
                    # Get historical exit price
                    start_date = exit_date - timedelta(days=3)  # Look back 3 days to handle weekends
                    end_date = exit_date + timedelta(days=3)

                    hist = stock.history(start=start_date, end=end_date)

                    if not hist.empty:
                        # Find closest date to exit_date
                        hist_dates = pd.to_datetime(hist.index).tz_localize(None)
                        closest_idx = (hist_dates - exit_date).abs().argmin()
                        exit_price = float(hist['Close'].iloc[closest_idx])
                        exit_timestamp = hist_dates[closest_idx]
                    else:
                        logger.warning(f"No exit price data for {rec['ticker']}")
                        continue

                # Calculate return
                if rec['recommendation'] == 'BUY':
                    return_pct = ((exit_price - entry_price) / entry_price) * 100
                else:  # SELL
                    return_pct = ((entry_price - exit_price) / entry_price) * 100

                # Calculate days held
                days_held = (exit_timestamp - entry_timestamp).days

                position = LivePosition(
                    ticker=rec['ticker'],
                    sentiment=rec['sentiment'],
                    sentiment_score=rec['sentiment_score'],
                    recommendation_confidence=rec['confidence'],
                    entry_price=entry_price,
                    entry_timestamp=entry_timestamp,
                    exit_price=exit_price,
                    exit_timestamp=exit_timestamp,
                    return_pct=return_pct,
                    days_held=days_held,
                    themes=[]
                )

                positions.append(position)

            except Exception as e:
                logger.warning(f"Error calculating return for {rec['ticker']}: {e}")
                continue

        return positions

    def analyze_live_performance(
        self,
        holding_period_days: int = 7
    ) -> Dict:
        """
        Analyze live trading performance and calculate IC.

        Args:
            holding_period_days: Holding period for calculating returns

        Returns:
            Analysis results dictionary
        """
        print("\n" + "="*80)
        print("LIVE TRADING PERFORMANCE ANALYSIS")
        print("="*80 + "\n")

        # Fetch recommendations
        recommendations = self.fetch_live_recommendations()

        if not recommendations:
            print("No live recommendations found in database")
            return {}

        print(f"Found {len(recommendations)} live recommendations")
        print(f"Calculating returns with {holding_period_days}-day holding period...\n")

        # Calculate returns
        positions = self.calculate_live_returns(recommendations, holding_period_days)

        if not positions:
            print("Could not calculate returns for any positions")
            return {}

        print(f"Successfully calculated returns for {len(positions)} positions\n")

        # Analyze signal quality
        signals = self.attributor.analyze_signal_quality(positions)

        # Calculate overall performance
        returns = [p.return_pct for p in positions if p.return_pct is not None]
        win_rate = sum(1 for r in returns if r > 0) / len(returns) * 100 if returns else 0
        avg_return = np.mean(returns) if returns else 0
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0

        results = {
            'total_recommendations': len(recommendations),
            'positions_analyzed': len(positions),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe,
            'signals': signals,
            'positions': positions
        }

        return results

    def generate_live_report(
        self,
        holding_period_days: int = 7,
        save_to_file: bool = True
    ) -> str:
        """
        Generate comprehensive live trading analysis report.

        Args:
            holding_period_days: Holding period for return calculation
            save_to_file: Whether to save report to file

        Returns:
            Report text
        """
        results = self.analyze_live_performance(holding_period_days)

        if not results:
            return "No data available for analysis"

        report = []
        report.append("# LIVE TRADING ANALYSIS REPORT\n")
        report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Holding Period**: {holding_period_days} days")
        report.append(f"**Positions Analyzed**: {results['positions_analyzed']}\n")

        report.append("---\n")
        report.append("## 1. Overall Performance\n")

        report.append(f"- **Win Rate**: {results['win_rate']:.1f}%")
        report.append(f"- **Average Return**: {results['avg_return']:.2f}%")
        report.append(f"- **Sharpe Ratio**: {results['sharpe_ratio']:.2f}\n")

        # Performance interpretation
        if results['win_rate'] >= 52 and results['sharpe_ratio'] > 0.5:
            report.append("**STRONG PERFORMANCE** - System shows clear edge!\n")
        elif results['win_rate'] >= 48 and results['sharpe_ratio'] > 0:
            report.append("**MODERATE PERFORMANCE** - System has potential edge\n")
        else:
            report.append("**WEAK PERFORMANCE** - System needs improvement\n")

        report.append("---\n")
        report.append("## 2. Information Coefficient (IC) Analysis\n")

        signals = results.get('signals', {})

        if signals:
            report.append("| Signal | IC | Win Rate | Avg Return | Status |")
            report.append("|--------|-----|----------|------------|--------|")

            for signal_name, perf in signals.items():
                status = "HAS EDGE" if perf.information_coefficient > 0.05 else "NO EDGE"
                report.append(
                    f"| {perf.signal_name} | {perf.information_coefficient:.3f} | "
                    f"{perf.win_rate:.1f}% | {perf.avg_return:.2f}% | {status} |"
                )

            report.append("\n**Key Findings**:\n")

            # Compare with historical
            sentiment_signal = signals.get('sentiment')
            if sentiment_signal:
                hist_ic = 0.000  # From historical backtest
                live_ic = sentiment_signal.information_coefficient

                report.append(f"- **Historical IC**: {hist_ic:.3f} (no edge)")
                report.append(f"- **Live IC**: {live_ic:.3f}")

                if live_ic > 0.05:
                    improvement = "SIGNIFICANT IMPROVEMENT"
                    report.append(f"- **Result**: {improvement} - Live data reveals real edge!")
                elif live_ic > hist_ic:
                    report.append(f"- **Result**: Improved but still marginal")
                else:
                    report.append(f"- **Result**: No improvement detected")

            report.append("")

        report.append("---\n")
        report.append("## 3. Filter Effectiveness\n")

        # This would require tracking which filters were applied
        # For now, provide placeholder
        report.append("Filter analysis requires additional tracking.\n")

        report.append("---\n")
        report.append("## 4. Go-Live Readiness Assessment\n")

        # Decision criteria
        ic_check = any(
            perf.information_coefficient > 0.05
            for perf in signals.values()
        ) if signals else False

        win_rate_check = results['win_rate'] >= 48
        sharpe_check = results['sharpe_ratio'] > 0
        sample_check = results['positions_analyzed'] >= 50

        report.append("**Criteria Check**:\n")
        report.append(f"- {'[x]' if ic_check else '[ ]'} IC > 0.05 (predictive signal detected)")
        report.append(f"- {'[x]' if win_rate_check else '[ ]'} Win Rate >= 48%")
        report.append(f"- {'[x]' if sharpe_check else '[ ]'} Sharpe Ratio > 0 (positive risk-adjusted return)")
        report.append(f"- {'[x]' if sample_check else '[ ]'} Sample Size >= 50 trades\n")

        passed_checks = sum([ic_check, win_rate_check, sharpe_check, sample_check])

        if passed_checks >= 3:
            report.append("**RECOMMENDATION**: PROCEED TO MICRO-CAPITAL LIVE TRADING\n")
            report.append("**Confidence**: HIGH\n")
            report.append("**Next Steps**:")
            report.append("1. Start with $100-500 per trade")
            report.append("2. Monitor performance closely")
            report.append("3. Scale up if edge persists")
        elif passed_checks >= 2:
            report.append("**RECOMMENDATION**: CAUTIOUS GO-LIVE\n")
            report.append("**Confidence**: MODERATE\n")
            report.append("**Next Steps**:")
            report.append("1. Collect more data (extend to 10 days)")
            report.append("2. Start with minimal capital ($50-100 per trade)")
            report.append("3. Reevaluate after 100 trades")
        else:
            report.append("**RECOMMENDATION**: DO NOT GO LIVE YET\n")
            report.append("**Confidence**: LOW\n")
            report.append("**Next Steps**:")
            report.append("1. Improve signal quality")
            report.append("2. Collect more live data")
            report.append("3. Revisit model assumptions")

        report.append("\n---\n")
        report.append("## 5. Detailed Position Analysis\n")

        # Top 5 winners and losers
        sorted_positions = sorted(
            results['positions'],
            key=lambda p: p.return_pct if p.return_pct else 0,
            reverse=True
        )

        report.append("**Top 5 Winners**:\n")
        for i, pos in enumerate(sorted_positions[:5], 1):
            report.append(
                f"{i}. {pos.ticker}: +{pos.return_pct:.2f}% "
                f"(Entry: ${pos.entry_price:.2f}, Exit: ${pos.exit_price:.2f}, "
                f"Confidence: {pos.recommendation_confidence:.2f})"
            )

        report.append("\n**Top 5 Losers**:\n")
        for i, pos in enumerate(sorted_positions[-5:], 1):
            report.append(
                f"{i}. {pos.ticker}: {pos.return_pct:.2f}% "
                f"(Entry: ${pos.entry_price:.2f}, Exit: ${pos.exit_price:.2f}, "
                f"Confidence: {pos.recommendation_confidence:.2f})"
            )

        report.append("\n---\n")

        report_text = '\n'.join(report)

        if save_to_file:
            filename = f"live_trading_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"\n[OK] Report saved to: {filename}\n")

        return report_text


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Analyze live trading performance')
    parser.add_argument(
        '--holding-period',
        type=int,
        default=7,
        help='Holding period in days (default: 7)'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Do not save report to file'
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    analyzer = LivePerformanceAnalyzer(config.DATABASE_PATH)

    report = analyzer.generate_live_report(
        holding_period_days=args.holding_period,
        save_to_file=not args.no_save
    )

    print(report)


if __name__ == '__main__':
    main()
