"""
Information Coefficient (IC) tracking for continuous model improvement.
Measures correlation between predicted confidence and actual outcomes.

Author: Claude Code
Date: 2025-10-10
"""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class ICTracker:
    """
    Track Information Coefficient for trading signals.
    IC measures predictive skill: correlation between forecasts and outcomes.

    Good IC benchmarks:
    - IC > 0.10: Excellent predictive power
    - IC > 0.05: Good predictive power
    - IC > 0.02: Modest predictive power
    - IC < 0.02: No meaningful skill
    - IC < 0: Inverse relationship (check logic!)
    """

    def __init__(self, min_samples: int = 30):
        """
        Args:
            min_samples: Minimum trades needed before calculating IC (default: 30)
        """
        self.min_samples = min_samples
        self.predictions: List[Dict] = []
        self.ic_history = []

    def record_prediction(
        self,
        prediction_id: str,
        symbol: str,
        confidence: float,
        predicted_direction: str,
        timestamp: datetime,
        signal_components: Optional[Dict] = None
    ) -> None:
        """
        Record a prediction when trade is made.

        Args:
            prediction_id: Unique identifier
            symbol: Stock ticker
            confidence: Model confidence [0,1]
            predicted_direction: 'long' or 'short'
            timestamp: When prediction was made
            signal_components: Dict of individual signal contributions
        """
        self.predictions.append({
            'id': prediction_id,
            'symbol': symbol,
            'confidence': confidence,
            'direction': predicted_direction,
            'timestamp': timestamp,
            'signals': signal_components or {},
            'outcome': None,  # Fill in later
            'return': None,
            'exit_timestamp': None
        })

        logger.debug(f"Recorded prediction {prediction_id}: {symbol} @ {confidence:.3f}")

    def record_outcome(
        self,
        prediction_id: str,
        actual_return: float,
        exit_timestamp: datetime
    ) -> None:
        """
        Record actual outcome when trade closes.

        Args:
            prediction_id: Matches prediction
            actual_return: Actual return achieved (can be negative)
            exit_timestamp: When trade closed
        """
        # Find the prediction
        for pred in self.predictions:
            if pred['id'] == prediction_id:
                pred['outcome'] = 1 if actual_return > 0 else 0  # Binary outcome
                pred['return'] = actual_return
                pred['exit_timestamp'] = exit_timestamp
                pred['hold_duration_hours'] = (
                    (exit_timestamp - pred['timestamp']).total_seconds() / 3600
                )
                logger.debug(
                    f"Recorded outcome {prediction_id}: "
                    f"Return={actual_return:+.2%}, Win={pred['outcome']}"
                )
                return

        logger.warning(f"Could not find prediction {prediction_id} to record outcome")

    def calculate_ic(
        self,
        method: str = 'spearman',
        lookback_days: Optional[int] = None
    ) -> Dict:
        """
        Calculate Information Coefficient.

        IC = correlation(predicted_confidence, actual_outcome)

        Spearman (rank correlation) is more robust to outliers.
        Pearson (linear correlation) is more sensitive to extreme values.

        Args:
            method: 'spearman' (rank correlation) or 'pearson' (linear)
            lookback_days: Only use trades from last N days (None = all)

        Returns:
            Dict with IC, p-value, sample size, interpretation
        """
        # Filter to completed predictions
        completed = [p for p in self.predictions if p['outcome'] is not None]

        if lookback_days:
            cutoff = datetime.now() - timedelta(days=lookback_days)
            completed = [p for p in completed if p['timestamp'] >= cutoff]

        if len(completed) < self.min_samples:
            return {
                'ic': None,
                'n_samples': len(completed),
                'min_samples': self.min_samples,
                'status': 'insufficient_data'
            }

        # Extract confidence scores and outcomes
        confidences = np.array([p['confidence'] for p in completed])
        outcomes = np.array([p['outcome'] for p in completed])

        # Calculate correlation
        if method == 'spearman':
            ic, p_value = spearmanr(confidences, outcomes)
        else:  # pearson
            ic, p_value = pearsonr(confidences, outcomes)

        # Interpret IC
        if ic is None or np.isnan(ic):
            interpretation = 'undefined'
        elif ic > 0.20:
            interpretation = 'exceptional_skill'
        elif ic > 0.10:
            interpretation = 'excellent_skill'
        elif ic > 0.05:
            interpretation = 'good_skill'
        elif ic > 0.02:
            interpretation = 'modest_skill'
        elif ic > -0.02:
            interpretation = 'no_skill'
        else:
            interpretation = 'inverse_skill_check_logic'

        result = {
            'ic': float(ic) if not np.isnan(ic) else 0.0,
            'p_value': float(p_value) if not np.isnan(p_value) else 1.0,
            'n_samples': len(completed),
            'method': method,
            'lookback_days': lookback_days,
            'interpretation': interpretation,
            'statistically_significant': p_value < 0.05 if not np.isnan(p_value) else False,
            'calculation_time': datetime.now().isoformat()
        }

        # Store in history
        self.ic_history.append(result)

        logger.info(
            f"IC calculated: {result['ic']:.4f} "
            f"({result['interpretation']}, n={result['n_samples']})"
        )

        return result

    def calculate_signal_ics(self) -> Dict[str, float]:
        """
        Calculate IC for each individual signal component.
        Identifies which signals actually contribute predictive value.

        Use this to:
        - Identify which signals to weight more heavily
        - Remove signals with negative IC (hurting performance)
        - Focus improvement efforts on low-IC signals

        Returns:
            Dict mapping signal names to their ICs (sorted by absolute IC)
        """
        completed = [p for p in self.predictions if p['outcome'] is not None and p['signals']]

        if len(completed) < self.min_samples:
            return {}

        # Get all signal names
        signal_names = set()
        for pred in completed:
            signal_names.update(pred['signals'].keys())

        signal_ics = {}

        for signal_name in signal_names:
            # Extract this signal's values
            signal_values = []
            outcomes = []

            for pred in completed:
                if signal_name in pred['signals']:
                    signal_values.append(pred['signals'][signal_name])
                    outcomes.append(pred['outcome'])

            if len(signal_values) >= self.min_samples:
                ic, _ = spearmanr(signal_values, outcomes)
                signal_ics[signal_name] = float(ic) if not np.isnan(ic) else 0.0

        # Sort by absolute IC
        signal_ics = dict(sorted(signal_ics.items(), key=lambda x: abs(x[1]), reverse=True))

        logger.info(f"Signal ICs calculated: {signal_ics}")

        return signal_ics

    def get_performance_by_confidence_bucket(self, n_buckets: int = 5) -> pd.DataFrame:
        """
        Analyze win rate by confidence level to check calibration.

        Well-calibrated model: 90% confidence → 90% win rate
        Overconfident model: 90% confidence → 60% win rate
        Underconfident model: 60% confidence → 90% win rate

        Args:
            n_buckets: Number of confidence buckets (default 5 = quintiles)

        Returns:
            DataFrame with confidence ranges and win rates
        """
        completed = [p for p in self.predictions if p['outcome'] is not None]

        if not completed:
            return pd.DataFrame()

        df = pd.DataFrame(completed)

        # Create confidence buckets
        try:
            df['confidence_bucket'] = pd.qcut(
                df['confidence'],
                q=n_buckets,
                labels=[f'Q{i+1}' for i in range(n_buckets)],
                duplicates='drop'
            )
        except ValueError:
            # If not enough unique values, use cut instead
            df['confidence_bucket'] = pd.cut(
                df['confidence'],
                bins=n_buckets,
                labels=[f'Q{i+1}' for i in range(n_buckets)]
            )

        # Calculate stats per bucket
        bucket_stats = df.groupby('confidence_bucket', observed=True).agg({
            'confidence': ['min', 'max', 'mean'],
            'outcome': ['sum', 'count', 'mean'],
            'return': 'mean'
        }).round(3)

        bucket_stats.columns = [
            'conf_min', 'conf_max', 'conf_avg',
            'wins', 'trades', 'win_rate',
            'avg_return'
        ]

        return bucket_stats

    def get_summary_stats(self) -> Dict:
        """
        Get comprehensive summary statistics.

        Returns:
            Dict with overall stats, IC, calibration, etc.
        """
        completed = [p for p in self.predictions if p['outcome'] is not None]

        if not completed:
            return {'status': 'no_data'}

        df = pd.DataFrame(completed)

        # Overall stats
        total_trades = len(completed)
        wins = df['outcome'].sum()
        win_rate = wins / total_trades if total_trades > 0 else 0

        avg_return = df['return'].mean()
        avg_win = df[df['outcome'] == 1]['return'].mean() if wins > 0 else 0
        avg_loss = df[df['outcome'] == 0]['return'].mean() if (total_trades - wins) > 0 else 0

        # IC stats
        ic_result = self.calculate_ic() if total_trades >= self.min_samples else {'ic': None}

        return {
            'total_predictions': len(self.predictions),
            'completed_trades': total_trades,
            'pending_trades': len(self.predictions) - total_trades,
            'wins': int(wins),
            'losses': total_trades - int(wins),
            'win_rate': win_rate,
            'avg_return': avg_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'ic': ic_result.get('ic'),
            'ic_interpretation': ic_result.get('interpretation'),
            'avg_confidence': df['confidence'].mean(),
            'avg_hold_hours': df['hold_duration_hours'].mean() if 'hold_duration_hours' in df else None
        }

    def save_to_file(self, filepath: str) -> None:
        """Save IC tracking data to JSON file."""
        data = {
            'predictions': self.predictions,
            'ic_history': self.ic_history,
            'saved_at': datetime.now().isoformat()
        }

        # Convert datetime objects to strings
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=datetime_handler)

        logger.info(f"IC data saved to {filepath}")

    def load_from_file(self, filepath: str) -> None:
        """Load IC tracking data from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        # Convert ISO strings back to datetime
        for pred in data['predictions']:
            pred['timestamp'] = datetime.fromisoformat(pred['timestamp'])
            if 'exit_timestamp' in pred and pred['exit_timestamp']:
                pred['exit_timestamp'] = datetime.fromisoformat(pred['exit_timestamp'])

        self.predictions = data['predictions']
        self.ic_history = data['ic_history']

        logger.info(f"IC data loaded from {filepath}: {len(self.predictions)} predictions")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("IC TRACKER - TESTING")
    print("="*80 + "\n")

    tracker = ICTracker(min_samples=10)

    # Simulate 50 trades with realistic correlation
    np.random.seed(42)

    print("Simulating 50 trades...")
    for i in range(50):
        # Generate prediction
        confidence = np.random.beta(5, 2)  # Skewed toward higher confidence
        direction = 'long'

        pred_id = f"trade_{i:03d}"
        tracker.record_prediction(
            prediction_id=pred_id,
            symbol='TEST',
            confidence=confidence,
            predicted_direction=direction,
            timestamp=datetime.now() - timedelta(days=50-i),
            signal_components={
                'sentiment': confidence * 0.7,
                'time_freshness': np.random.uniform(0.9, 1.2),
                'technical': np.random.uniform(0.85, 1.15)
            }
        )

        # Simulate outcome (higher confidence = higher win probability)
        # This creates IC > 0 (positive correlation)
        win_prob = 0.35 + (confidence * 0.4)  # 35-75% win rate based on confidence
        actual_win = np.random.random() < win_prob
        actual_return = np.random.normal(0.02, 0.03) if actual_win else np.random.normal(-0.015, 0.02)

        tracker.record_outcome(
            prediction_id=pred_id,
            actual_return=actual_return,
            exit_timestamp=datetime.now() - timedelta(days=50-i-0.5)
        )

    print("\n" + "="*80)
    print("OVERALL IC CALCULATION")
    print("="*80 + "\n")

    # Calculate IC
    ic_result = tracker.calculate_ic()
    print(f"IC: {ic_result['ic']:.4f}")
    print(f"P-value: {ic_result['p_value']:.4f}")
    print(f"Interpretation: {ic_result['interpretation']}")
    print(f"Statistically Significant: {ic_result['statistically_significant']}")
    print(f"Sample Size: {ic_result['n_samples']}")
    print(f"Method: {ic_result['method']}")

    print("\n" + "="*80)
    print("SIGNAL-LEVEL ICs")
    print("="*80 + "\n")

    # Signal-level ICs
    signal_ics = tracker.calculate_signal_ics()
    print("Individual Signal ICs:")
    for signal, ic in signal_ics.items():
        status = "[Good]" if ic > 0.05 else "[Weak]" if ic > 0 else "[Negative]"
        print(f"  {signal:20s}: {ic:+.4f}  {status}")

    print("\n" + "="*80)
    print("CONFIDENCE CALIBRATION")
    print("="*80 + "\n")

    # Calibration check
    calibration = tracker.get_performance_by_confidence_bucket()
    print("Win rate by confidence level:")
    print(calibration.to_string())

    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80 + "\n")

    # Summary
    summary = tracker.get_summary_stats()
    print(f"Total Predictions: {summary['total_predictions']}")
    print(f"Completed Trades: {summary['completed_trades']}")
    print(f"Win Rate: {summary['win_rate']:.1%}")
    print(f"Average Return: {summary['avg_return']:+.2%}")
    print(f"Average Win: {summary['avg_win']:+.2%}")
    print(f"Average Loss: {summary['avg_loss']:+.2%}")
    print(f"IC: {summary['ic']:.4f} ({summary['ic_interpretation']})")
    print(f"Average Confidence: {summary['avg_confidence']:.3f}")

    print("\n" + "="*80)
    print("IC TRACKER READY FOR PRODUCTION!")
    print("="*80 + "\n")
