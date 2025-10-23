"""
Performance Attribution & Self-Improvement System

Analyzes which signals actually work and provides data-driven recommendations
for improving the trading system.

Key Concepts:
1. Information Coefficient (IC): Correlation between signal and returns
2. Factor Analysis: Which features drive wins vs losses
3. Adaptive Thresholds: Optimize decision boundaries based on actual results
4. Signal Quality Decay: Detect when signals stop working

Author: Claude Code
Date: 2025-10-10
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import sqlite3

logger = logging.getLogger(__name__)


@dataclass
class SignalPerformance:
    """Performance metrics for a specific signal."""
    signal_name: str
    information_coefficient: float  # Correlation with returns
    win_rate: float
    avg_return: float
    profit_factor: float
    sample_size: int
    sharpe_ratio: float
    recommendation: str  # "KEEP", "DISABLE", "FLIP", "OPTIMIZE"


@dataclass
class ThresholdOptimization:
    """Results from optimizing a decision threshold."""
    parameter_name: str
    current_value: float
    optimal_value: float
    current_sharpe: float
    optimal_sharpe: float
    improvement_pct: float


class PerformanceAttributor:
    """
    Analyzes trading results to determine which signals are predictive
    and provides data-driven optimization recommendations.
    """

    def __init__(self, db_path: str):
        """
        Initialize performance attributor.

        Args:
            db_path: Path to trading database
        """
        self.db_path = db_path

    def calculate_information_coefficient(
        self,
        signals: pd.Series,
        returns: pd.Series
    ) -> float:
        """
        Calculate Information Coefficient (IC).

        IC is the correlation between predicted signals and actual returns.
        - IC > 0.05: Signal has predictive power
        - IC < 0.05: Signal is noise
        - IC < 0: Signal is inversely predictive

        Args:
            signals: Predicted signal strength (e.g., sentiment confidence)
            returns: Actual forward returns

        Returns:
            Information Coefficient (Spearman correlation)
        """
        if len(signals) < 10:
            return 0.0

        # Use Spearman (rank) correlation to handle non-linear relationships
        correlation = signals.corr(returns, method='spearman')

        return correlation if not np.isnan(correlation) else 0.0

    def analyze_signal_quality(
        self,
        positions: List
    ) -> Dict[str, SignalPerformance]:
        """
        Analyze the quality of each signal type.

        Args:
            positions: List of completed positions from backtest

        Returns:
            Dictionary of signal name -> SignalPerformance
        """
        if not positions:
            return {}

        # Convert positions to DataFrame for analysis
        data = []
        for pos in positions:
            data.append({
                'ticker': pos.ticker,
                'sentiment': pos.sentiment,
                'sentiment_score': pos.sentiment_score,
                'confidence': pos.recommendation_confidence,
                'return_pct': pos.return_pct,
                'themes': ','.join(pos.themes) if pos.themes else '',
                'days_held': pos.days_held
            })

        df = pd.DataFrame(data)

        results = {}

        # 1. Sentiment Signal
        sentiment_ic = self.calculate_information_coefficient(
            df['sentiment_score'], df['return_pct']
        )

        sentiment_perf = self._calculate_signal_performance(
            df, 'sentiment_score', sentiment_ic
        )
        results['sentiment'] = SignalPerformance(
            signal_name='Sentiment Score',
            information_coefficient=sentiment_ic,
            win_rate=sentiment_perf['win_rate'],
            avg_return=sentiment_perf['avg_return'],
            profit_factor=sentiment_perf['profit_factor'],
            sample_size=len(df),
            sharpe_ratio=sentiment_perf['sharpe'],
            recommendation=self._get_recommendation(sentiment_ic, sentiment_perf['win_rate'])
        )

        # 2. Confidence Signal
        confidence_ic = self.calculate_information_coefficient(
            df['confidence'], df['return_pct']
        )

        confidence_perf = self._calculate_signal_performance(
            df, 'confidence', confidence_ic
        )
        results['confidence'] = SignalPerformance(
            signal_name='Recommendation Confidence',
            information_coefficient=confidence_ic,
            win_rate=confidence_perf['win_rate'],
            avg_return=confidence_perf['avg_return'],
            profit_factor=confidence_perf['profit_factor'],
            sample_size=len(df),
            sharpe_ratio=confidence_perf['sharpe'],
            recommendation=self._get_recommendation(confidence_ic, confidence_perf['win_rate'])
        )

        # 3. High vs Low Confidence Comparison
        high_conf = df[df['confidence'] >= 0.7]
        low_conf = df[df['confidence'] < 0.7]

        if len(high_conf) > 5 and len(low_conf) > 5:
            high_wr = (high_conf['return_pct'] > 0).mean() * 100
            low_wr = (low_conf['return_pct'] > 0).mean() * 100

            results['high_confidence_filter'] = SignalPerformance(
                signal_name='High Confidence Filter (>=0.7)',
                information_coefficient=0.0,  # Not applicable
                win_rate=high_wr,
                avg_return=high_conf['return_pct'].mean(),
                profit_factor=0.0,
                sample_size=len(high_conf),
                sharpe_ratio=0.0,
                recommendation="KEEP" if high_wr > low_wr else "REMOVE"
            )

        return results

    def _calculate_signal_performance(
        self,
        df: pd.DataFrame,
        signal_col: str,
        ic: float
    ) -> Dict:
        """Calculate performance metrics for a signal."""
        winners = df[df['return_pct'] > 0]
        losers = df[df['return_pct'] <= 0]

        win_rate = len(winners) / len(df) * 100 if len(df) > 0 else 0
        avg_return = df['return_pct'].mean()

        total_wins = winners['return_pct'].sum() if len(winners) > 0 else 0
        total_losses = abs(losers['return_pct'].sum()) if len(losers) > 0 else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Sharpe ratio (simplified)
        sharpe = (df['return_pct'].mean() / df['return_pct'].std()) * np.sqrt(252) if df['return_pct'].std() > 0 else 0

        return {
            'win_rate': win_rate,
            'avg_return': avg_return,
            'profit_factor': profit_factor,
            'sharpe': sharpe
        }

    def _get_recommendation(self, ic: float, win_rate: float) -> str:
        """Get recommendation based on IC and win rate."""
        if abs(ic) < 0.05 and win_rate < 45:
            return "DISABLE - No predictive power"
        elif ic < -0.05:
            return "FLIP - Inversely predictive (consider contrarian)"
        elif ic > 0.10 and win_rate > 50:
            return "KEEP - Strong signal"
        elif ic > 0.05:
            return "OPTIMIZE - Has potential, needs tuning"
        else:
            return "REVIEW - Marginal performance"

    def optimize_threshold(
        self,
        positions: List,
        parameter_name: str,
        current_value: float,
        test_range: np.ndarray
    ) -> ThresholdOptimization:
        """
        Optimize a decision threshold to maximize Sharpe ratio.

        Args:
            positions: Completed positions
            parameter_name: Name of parameter (e.g., 'min_confidence')
            current_value: Current threshold value
            test_range: Array of values to test

        Returns:
            Optimization results
        """
        if not positions:
            return None

        df = pd.DataFrame([{
            'confidence': pos.recommendation_confidence,
            'return_pct': pos.return_pct
        } for pos in positions])

        results = []

        for threshold in test_range:
            # Filter positions that would pass this threshold
            passed = df[df['confidence'] >= threshold]

            if len(passed) < 10:  # Need minimum sample size
                continue

            # Calculate Sharpe ratio for this threshold
            sharpe = (passed['return_pct'].mean() / passed['return_pct'].std()) * np.sqrt(252) if passed['return_pct'].std() > 0 else 0

            results.append({
                'threshold': threshold,
                'sharpe': sharpe,
                'win_rate': (passed['return_pct'] > 0).mean() * 100,
                'sample_size': len(passed)
            })

        if not results:
            return None

        results_df = pd.DataFrame(results)

        # Find optimal threshold
        optimal_idx = results_df['sharpe'].idxmax()
        optimal = results_df.loc[optimal_idx]

        # Current performance
        current_passed = df[df['confidence'] >= current_value]
        current_sharpe = (current_passed['return_pct'].mean() / current_passed['return_pct'].std()) * np.sqrt(252) if current_passed['return_pct'].std() > 0 else 0

        improvement_pct = ((optimal['sharpe'] - current_sharpe) / abs(current_sharpe) * 100) if current_sharpe != 0 else 0

        return ThresholdOptimization(
            parameter_name=parameter_name,
            current_value=current_value,
            optimal_value=optimal['threshold'],
            current_sharpe=current_sharpe,
            optimal_sharpe=optimal['sharpe'],
            improvement_pct=improvement_pct
        )

    def analyze_announcement_types(
        self,
        positions: List
    ) -> pd.DataFrame:
        """
        Analyze which announcement types are profitable.

        Args:
            positions: Completed positions

        Returns:
            DataFrame of announcement type performance
        """
        # This would require announcement_type to be tracked in positions
        # For now, return placeholder
        return pd.DataFrame()

    def generate_improvement_report(
        self,
        positions: List,
        current_config: Dict
    ) -> str:
        """
        Generate comprehensive improvement recommendations.

        Args:
            positions: Completed positions from backtest
            current_config: Current system configuration

        Returns:
            Markdown-formatted report with recommendations
        """
        report = []
        report.append("# SELF-IMPROVEMENT ANALYSIS REPORT")
        report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Sample Size**: {len(positions)} completed trades\n")

        report.append("---\n")
        report.append("## 1. Information Coefficient (IC) Analysis\n")

        # Analyze signal quality
        signals = self.analyze_signal_quality(positions)

        if signals:
            report.append("| Signal | IC | Win Rate | Avg Return | Recommendation |")
            report.append("|--------|-----|----------|------------|----------------|")

            for signal_name, perf in signals.items():
                report.append(
                    f"| {perf.signal_name} | {perf.information_coefficient:.3f} | "
                    f"{perf.win_rate:.1f}% | {perf.avg_return:.2f}% | "
                    f"{perf.recommendation} |"
                )

            report.append("\n**Interpretation**:")
            report.append("- IC > 0.10: Strong predictive signal")
            report.append("- IC 0.05-0.10: Moderate signal (optimize)")
            report.append("- IC < 0.05: No edge (disable)")
            report.append("- IC < 0: Inverse relationship (flip or fade)\n")

        report.append("---\n")
        report.append("## 2. Threshold Optimization\n")

        # Optimize confidence threshold
        test_range = np.arange(0.5, 0.9, 0.05)
        opt = self.optimize_threshold(
            positions,
            'min_confidence',
            current_config.get('min_confidence', 0.6),
            test_range
        )

        if opt:
            report.append(f"### Confidence Threshold\n")
            report.append(f"- **Current**: {opt.current_value:.2f} (Sharpe: {opt.current_sharpe:.2f})")
            report.append(f"- **Optimal**: {opt.optimal_value:.2f} (Sharpe: {opt.optimal_sharpe:.2f})")
            report.append(f"- **Improvement**: {opt.improvement_pct:+.1f}%\n")

            if abs(opt.improvement_pct) > 10:
                report.append(f"✅ **RECOMMENDATION**: Change min_confidence from {opt.current_value:.2f} to {opt.optimal_value:.2f}\n")
            else:
                report.append(f"ℹ️  Current threshold is near-optimal\n")

        report.append("---\n")
        report.append("## 3. Actionable Recommendations\n")

        # Generate prioritized recommendations based on analysis
        recommendations = []

        for signal_name, perf in signals.items():
            if "DISABLE" in perf.recommendation:
                recommendations.append({
                    'priority': 1,
                    'action': f"DISABLE {perf.signal_name} (IC: {perf.information_coefficient:.3f}, Win Rate: {perf.win_rate:.1f}%)",
                    'impact': 'High - Remove noise signal'
                })
            elif "FLIP" in perf.recommendation:
                recommendations.append({
                    'priority': 1,
                    'action': f"FLIP {perf.signal_name} - Use contrarian logic",
                    'impact': 'High - Signal is inversely predictive'
                })
            elif "OPTIMIZE" in perf.recommendation:
                recommendations.append({
                    'priority': 2,
                    'action': f"OPTIMIZE {perf.signal_name} thresholds",
                    'impact': 'Medium - Has potential'
                })

        # Sort by priority
        recommendations.sort(key=lambda x: x['priority'])

        if recommendations:
            report.append("### Priority Actions:\n")
            for i, rec in enumerate(recommendations, 1):
                report.append(f"{i}. **{rec['action']}**")
                report.append(f"   - Impact: {rec['impact']}\n")
        else:
            report.append("✅ No critical issues detected. System is performing as expected.\n")

        report.append("---\n")
        report.append("## 4. Next Steps\n")
        report.append("1. Implement recommended changes")
        report.append("2. Re-run backtest to validate improvements")
        report.append("3. Compare new IC scores with baseline")
        report.append("4. Repeat this analysis monthly to detect signal decay\n")

        return '\n'.join(report)


def main():
    """Test the performance attribution system."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import config
    from backtesting.historical_simulator import HistoricalSimulator
    from paper_trading.risk_manager import RiskConfig

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 80)
    print("PERFORMANCE ATTRIBUTION & SELF-IMPROVEMENT ANALYSIS")
    print("=" * 80 + "\n")

    # Run backtest
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

    print("Running 300-sample backtest...\n")
    results = simulator.run_simulation(max_articles=300)

    # Analyze performance
    attributor = PerformanceAttributor(config.DATABASE_PATH)

    report = attributor.generate_improvement_report(
        positions=results['positions'],
        current_config={'min_confidence': 0.6}
    )

    # Save report
    report_file = f"self_improvement_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] Report saved to: {report_file}")
    print("\nKey Findings:")

    # Print summary without unicode
    signals = attributor.analyze_signal_quality(results['positions'])
    for signal_name, perf in signals.items():
        print(f"\n{perf.signal_name}:")
        print(f"  IC: {perf.information_coefficient:.3f}")
        print(f"  Win Rate: {perf.win_rate:.1f}%")
        print(f"  Recommendation: {perf.recommendation}")


if __name__ == '__main__':
    main()
