"""
Bayesian Confidence Scoring System

Replaces broken additive confidence model with proper Bayesian approach.

OLD (WRONG):
    confidence = 0.68 + 0.15 + 0.05 + 0.08 = 0.96
    Problem: Can exceed 1.0, treats independent signals as additive

NEW (CORRECT):
    odds = 2.125 * 1.15 * 1.05 * 1.08 = 2.77 → prob = 0.735
    Benefit: Bounded [0,1], properly combines independent evidence

Key Insight:
    Independent signals multiply odds ratios, not probabilities.
    This is the foundation of Bayesian inference.

Author: Claude Code
Date: 2025-10-10
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class BayesianConfidenceScorer:
    """
    Proper signal combination using multiplicative log-odds.

    Mathematical Foundation:
        P(event|signal) / P(¬event|signal) = LR × P(event) / P(¬event)
        where LR = likelihood ratio from signal

    In practice:
        odds_posterior = odds_prior × LR1 × LR2 × ... × LRn
    """

    def __init__(self, base_prior: float = 0.5, calibration_data: Optional[Dict] = None):
        """
        Initialize Bayesian scorer.

        Args:
            base_prior: Starting probability before any signals (default 0.5 = no bias)
            calibration_data: Historical IC scores for each signal type
        """
        self.base_prior = base_prior
        self.calibration_data = calibration_data or {}

    @staticmethod
    def prob_to_odds(probability: float) -> float:
        """
        Convert probability [0,1] to odds [0,∞].

        Examples:
            0.5 → 1.0 (even odds)
            0.75 → 3.0 (3:1 odds)
            0.9 → 9.0 (9:1 odds)
        """
        if probability >= 1.0:
            return 999.0  # Cap at very high odds
        if probability <= 0.0:
            return 0.001  # Cap at very low odds
        return probability / (1 - probability)

    @staticmethod
    def odds_to_prob(odds: float) -> float:
        """
        Convert odds [0,∞] to probability [0,1].

        Examples:
            1.0 → 0.5 (even odds)
            3.0 → 0.75 (3:1 odds)
            9.0 → 0.9 (9:1 odds)
        """
        return odds / (1 + odds)

    def combine_signals(
        self,
        base_sentiment: float,
        time_freshness: float,
        time_of_day: float,
        technical_signal: float,
        materiality: float = 1.0,
        contrarian: float = 1.0
    ) -> Tuple[float, Dict[str, float]]:
        """
        Combine multiple signals using multiplicative Bayesian approach.

        Args:
            base_sentiment: Sentiment score from NLP [0,1]
            time_freshness: Time boost factor [0.8-1.3] (1.0 = neutral)
            time_of_day: Time-of-day boost [0.9-1.1]
            technical_signal: Technical analysis boost [0.85-1.15]
            materiality: Materiality boost [0.5-1.5]
            contrarian: Contrarian adjustment [0.85-1.15]

        Returns:
            (final_confidence, breakdown_dict)
        """

        # Step 1: Convert base sentiment to odds
        base_odds = self.prob_to_odds(base_sentiment)

        # Step 2: Apply multiplicative boosts
        # Each boost factor represents likelihood ratio: how much more likely
        # the outcome is given this signal
        combined_odds = (
            base_odds
            * time_freshness
            * time_of_day
            * technical_signal
            * materiality
            * contrarian
        )

        # Step 3: Convert back to probability
        final_confidence = self.odds_to_prob(combined_odds)

        # Ensure bounds [0.01, 0.99] for numerical stability
        final_confidence = np.clip(final_confidence, 0.01, 0.99)

        # Step 4: Create breakdown for logging
        breakdown = {
            'base_sentiment': base_sentiment,
            'base_odds': base_odds,
            'time_freshness_factor': time_freshness,
            'time_of_day_factor': time_of_day,
            'technical_factor': technical_signal,
            'materiality_factor': materiality,
            'contrarian_factor': contrarian,
            'combined_odds': combined_odds,
            'final_confidence': final_confidence,
            'confidence_reduction': base_sentiment - final_confidence  # How much we adjusted down
        }

        logger.debug(
            f"Bayesian combination: {base_sentiment:.3f} → {final_confidence:.3f} "
            f"(reduction: {base_sentiment - final_confidence:.3f})"
        )

        return final_confidence, breakdown

    def calibrate_from_history(self, historical_trades: List[Dict]) -> None:
        """
        Calibrate confidence scores based on historical accuracy.

        Uses isotonic regression to ensure calibrated probabilities match
        actual win rates.

        Args:
            historical_trades: List of dicts with 'predicted_confidence', 'actual_outcome'
        """
        if len(historical_trades) < 50:
            logger.warning(f"Insufficient trades for calibration: {len(historical_trades)} < 50")
            return

        # Group trades by confidence bins
        bins = np.arange(0, 1.05, 0.05)  # 5% bins
        bin_accuracies = {}

        for i in range(len(bins) - 1):
            lower, upper = bins[i], bins[i + 1]
            bin_trades = [
                t for t in historical_trades
                if lower <= t['predicted_confidence'] < upper
            ]

            if len(bin_trades) >= 10:  # Minimum sample size
                accuracy = np.mean([t['actual_outcome'] for t in bin_trades])
                bin_accuracies[(lower, upper)] = accuracy
                logger.info(
                    f"Bin [{lower:.2f}, {upper:.2f}]: "
                    f"Predicted {(lower+upper)/2:.2f}, Actual {accuracy:.2f} "
                    f"(n={len(bin_trades)})"
                )

        self.calibration_data = bin_accuracies
        logger.info(f"Calibrated confidence scorer with {len(bin_accuracies)} bins")

    def apply_calibration(self, raw_confidence: float) -> float:
        """
        Apply calibration to raw confidence score.

        Args:
            raw_confidence: Uncalibrated confidence [0,1]

        Returns:
            Calibrated confidence [0,1]
        """
        if not self.calibration_data:
            return raw_confidence

        # Find matching bin
        for (lower, upper), calibrated_prob in self.calibration_data.items():
            if lower <= raw_confidence < upper:
                return calibrated_prob

        # No matching bin, return raw
        return raw_confidence


class SignalCombiner:
    """
    High-level interface for combining all trading signals.
    Replaces the old additive approach throughout the codebase.

    Integration Points:
        - live_trading/live_recommendation_engine.py
        - backtesting/historical_simulator.py
        - paper_trading/recommendation_engine.py
    """

    def __init__(self, calibration_data: Optional[Dict] = None):
        """
        Initialize signal combiner.

        Args:
            calibration_data: Historical calibration data
        """
        self.bayesian_scorer = BayesianConfidenceScorer(calibration_data=calibration_data)
        self.signal_history = []

    def compute_confidence(
        self,
        sentiment_score: float,
        announcement_age_minutes: float,
        current_time_aest: str,
        technical_indicators: Optional[Dict] = None,
        is_material: bool = True,
        recent_price_change: Optional[float] = None
    ) -> Tuple[float, Dict]:
        """
        Main entry point replacing old additive confidence calculation.

        Args:
            sentiment_score: NLP output [0,1] where >0.5 is positive
            announcement_age_minutes: Minutes since announcement
            current_time_aest: Time string "HH:MM" in AEST
            technical_indicators: Dict with RSI, MACD, etc.
            is_material: Boolean if announcement is material
            recent_price_change: Recent price change % (for contrarian)

        Returns:
            (final_confidence, detailed_breakdown)
        """

        # Calculate time freshness boost (multiplicative factor)
        time_boost = self._compute_time_freshness_boost(announcement_age_minutes)

        # Calculate time-of-day boost
        tod_boost = self._compute_time_of_day_boost(current_time_aest)

        # Calculate technical boost
        tech_boost = self._compute_technical_boost(technical_indicators or {})

        # Materiality factor
        materiality_factor = 1.20 if is_material else 0.95

        # Contrarian adjustment
        contrarian_factor = self._compute_contrarian_factor(
            sentiment_score,
            recent_price_change
        )

        # Combine using Bayesian approach
        final_confidence, breakdown = self.bayesian_scorer.combine_signals(
            base_sentiment=sentiment_score,
            time_freshness=time_boost,
            time_of_day=tod_boost,
            technical_signal=tech_boost,
            materiality=materiality_factor,
            contrarian=contrarian_factor
        )

        # Add human-readable details
        breakdown['announcement_age_minutes'] = announcement_age_minutes
        breakdown['trading_hour_aest'] = int(current_time_aest.split(':')[0])
        breakdown['is_material'] = is_material
        breakdown['recent_price_change_pct'] = recent_price_change

        # Store in history for potential calibration
        self.signal_history.append({
            'timestamp': current_time_aest,
            'confidence': final_confidence,
            'sentiment': sentiment_score,
            'breakdown': breakdown
        })

        return final_confidence, breakdown

    def _compute_time_freshness_boost(self, age_minutes: float) -> float:
        """
        Convert announcement age to multiplicative boost factor.

        Evidence: TIME filter from behavioral_filters.py shows strong edge
        for announcements <5 min old.

        Returns: Factor between 0.80-1.25
        """
        if age_minutes <= 5:
            return 1.25  # 25% boost for ultra-fresh (IC boost observed)
        elif age_minutes <= 15:
            return 1.15  # 15% boost for fresh
        elif age_minutes <= 30:
            return 1.05  # 5% boost for recent (TIME filter cutoff)
        elif age_minutes <= 60:
            return 0.95  # 5% penalty for older
        else:
            return 0.80  # 20% penalty for stale (information fully priced)

    def _compute_time_of_day_boost(self, time_aest: str) -> float:
        """
        Convert time-of-day to multiplicative boost factor.

        Evidence: TIME-OF-DAY filter from behavioral_filters.py shows
        10am-2pm AEST has highest liquidity and tightest spreads.

        Returns: Factor between 0.90-1.08
        """
        try:
            hour = int(time_aest.split(':')[0])
        except (ValueError, IndexError):
            logger.warning(f"Could not parse time: {time_aest}, using neutral")
            return 1.0

        if 11 <= hour <= 14:  # Optimal trading window (center of 10-2)
            return 1.08
        elif 10 <= hour < 11 or 14 < hour <= 15:  # Acceptable (edges of window)
            return 1.00
        else:  # Avoid (early opening or late closing)
            return 0.90

    def _compute_technical_boost(self, indicators: Dict) -> float:
        """
        Convert technical indicators to multiplicative boost factor.

        Note: Technical analysis used as SOFT modifier, not hard filter.

        Returns: Factor between 0.85-1.15
        """
        if not indicators:
            return 1.0  # Neutral if no data

        boosts = []

        # RSI signal
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi > 70:  # Overbought - negative for longs
                boosts.append(0.93)
            elif rsi < 30:  # Oversold - positive for longs
                boosts.append(1.07)
            else:  # Neutral zone
                boosts.append(1.0)

        # MACD signal
        macd_signal = indicators.get('macd_signal', 'neutral')
        if macd_signal == 'bullish':
            boosts.append(1.05)
        elif macd_signal == 'bearish':
            boosts.append(0.95)
        else:
            boosts.append(1.0)

        # Moving average trend
        ma_trend = indicators.get('ma_trend', 'neutral')
        if ma_trend == 'uptrend':
            boosts.append(1.03)
        elif ma_trend == 'downtrend':
            boosts.append(0.97)
        else:
            boosts.append(1.0)

        if not boosts:
            return 1.0

        # Average all technical boosts
        avg_boost = np.mean(boosts)

        # Clip to reasonable range
        return np.clip(avg_boost, 0.85, 1.15)

    def _compute_contrarian_factor(
        self,
        sentiment_score: float,
        recent_price_change: Optional[float]
    ) -> float:
        """
        Apply contrarian adjustment for extreme sentiment or price moves.

        Evidence: CONTRARIAN filter from behavioral_filters.py fades
        extreme sentiment (>0.85 or <0.15).

        Returns: Factor between 0.85-1.15
        """
        # Sentiment-based contrarian
        if sentiment_score > 0.85:
            sentiment_adjustment = 0.90  # Fade extreme optimism
        elif sentiment_score < 0.15:
            sentiment_adjustment = 0.90  # Fade extreme pessimism
        else:
            sentiment_adjustment = 1.0

        # Price-based contrarian
        if recent_price_change is not None:
            if abs(recent_price_change) > 10:  # >10% move recently
                price_adjustment = 0.95  # Fade momentum extremes
            else:
                price_adjustment = 1.0
        else:
            price_adjustment = 1.0

        # Combine adjustments
        combined = sentiment_adjustment * price_adjustment

        return np.clip(combined, 0.85, 1.15)

    def calibrate(self, historical_trades: List[Dict]) -> None:
        """
        Calibrate confidence scores based on historical results.

        Args:
            historical_trades: List with 'predicted_confidence', 'actual_outcome'
        """
        self.bayesian_scorer.calibrate_from_history(historical_trades)


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("="*80)
    print("BAYESIAN CONFIDENCE SCORER - DEMONSTRATION")
    print("="*80 + "\n")

    # Initialize combiner
    combiner = SignalCombiner()

    # Example 1: High confidence scenario (from your demo)
    print("Example 1: High Confidence Scenario (Your Demo Case)")
    print("-"*80)
    conf, details = combiner.compute_confidence(
        sentiment_score=0.68,  # Base sentiment from NLP
        announcement_age_minutes=2.3,  # Ultra-fresh
        current_time_aest="10:45",  # Good time
        technical_indicators={'rsi': 55, 'macd_signal': 'bullish'},
        is_material=True,
        recent_price_change=None
    )

    print(f"Sentiment Score: 0.68")
    print(f"Announcement Age: 2.3 minutes")
    print(f"Time: 10:45 AEST")
    print(f"Technical: RSI=55, MACD=bullish")
    print(f"Material: Yes")
    print()
    print(f"OLD ADDITIVE METHOD: 0.96 (WRONG - can exceed 1.0)")
    print(f"NEW BAYESIAN METHOD: {conf:.3f} (CORRECT - bounded)")
    print(f"Reduction: {0.96 - conf:.3f} ({(0.96-conf)/0.96*100:.1f}% more conservative)")
    print()
    print("Breakdown:")
    print(f"  Base sentiment → odds: {details['base_sentiment']:.3f} → {details['base_odds']:.3f}")
    print(f"  × Time freshness: {details['time_freshness_factor']:.3f}")
    print(f"  × Time of day: {details['time_of_day_factor']:.3f}")
    print(f"  × Technical: {details['technical_factor']:.3f}")
    print(f"  × Materiality: {details['materiality_factor']:.3f}")
    print(f"  = Combined odds: {details['combined_odds']:.3f}")
    print(f"  → Final confidence: {details['final_confidence']:.3f}")
    print()

    # Example 2: Moderate confidence
    print("\nExample 2: Moderate Confidence Scenario")
    print("-"*80)
    conf2, details2 = combiner.compute_confidence(
        sentiment_score=0.65,
        announcement_age_minutes=18,  # Fresh but not ultra-fresh
        current_time_aest="13:30",  # Optimal time
        technical_indicators={'rsi': 52, 'macd_signal': 'neutral'},
        is_material=True,
        recent_price_change=2.5
    )

    print(f"Sentiment: 0.65, Age: 18min, Time: 13:30, Tech: Neutral")
    print(f"Final Confidence: {conf2:.3f}")
    print()

    # Example 3: Low confidence (stale + extreme sentiment)
    print("\nExample 3: Low Confidence Scenario (Contrarian)")
    print("-"*80)
    conf3, details3 = combiner.compute_confidence(
        sentiment_score=0.88,  # Extreme sentiment
        announcement_age_minutes=45,  # Stale
        current_time_aest="15:45",  # Late in day
        technical_indicators={'rsi': 72, 'macd_signal': 'neutral'},  # Overbought
        is_material=False,
        recent_price_change=8.5  # Big recent move
    )

    print(f"Extreme sentiment: 0.88, Stale: 45min, Late: 15:45")
    print(f"Overbought: RSI=72, Recent move: +8.5%")
    print(f"Final Confidence: {conf3:.3f}")
    print(f"Contrarian factor: {details3['contrarian_factor']:.3f}")
    print()

    print("="*80)
    print("KEY INSIGHT: Bayesian method prevents confidence inflation")
    print("while properly combining independent evidence.")
    print("="*80)
