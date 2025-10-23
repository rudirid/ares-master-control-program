"""
Dynamic Exit Manager

Manages dynamic exits based on momentum, volatility, and technical indicators.
Replaces fixed 7-day holding period with adaptive exit strategy.

Author: Claude Code
Date: 2025-10-10
"""

import logging
from typing import Tuple, Optional, Dict
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class DynamicExitManager:
    """
    Manages dynamic position exits based on multiple factors:
    - Take profit targets
    - Trailing stops
    - Momentum reversal detection
    - Volatility-adjusted holding periods
    """

    def __init__(
        self,
        take_profit_pct: float = 10.0,
        trailing_stop_pct: float = 3.0,
        min_holding_days: int = 3,
        max_holding_days: int = 14
    ):
        """
        Initialize dynamic exit manager.

        Args:
            take_profit_pct: Take profit at this % gain
            trailing_stop_pct: Trailing stop loss %
            min_holding_days: Minimum holding period
            max_holding_days: Maximum holding period
        """
        self.take_profit_pct = take_profit_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.min_holding_days = min_holding_days
        self.max_holding_days = max_holding_days

    def calculate_optimal_holding_period(
        self,
        sentiment_strength: float,
        volatility_pct: float
    ) -> int:
        """
        Calculate optimal holding period based on signal strength and volatility.

        Args:
            sentiment_strength: Absolute sentiment score (0-1)
            volatility_pct: Daily volatility percentage

        Returns:
            Optimal holding period in days
        """
        base_days = 7

        # Adjust for sentiment strength
        if abs(sentiment_strength) > 0.7:
            base_days += 3  # Strong signals hold longer
        elif abs(sentiment_strength) < 0.3:
            base_days -= 2  # Weak signals exit faster

        # Adjust for volatility
        if volatility_pct > 3.0:  # High volatility (>3% daily)
            base_days -= 2  # Exit faster in volatile conditions
        elif volatility_pct < 1.0:  # Low volatility (<1% daily)
            base_days += 2  # Can hold longer in stable conditions

        # Clamp to min/max
        return max(self.min_holding_days, min(base_days, self.max_holding_days))

    def should_exit(
        self,
        entry_price: float,
        current_price: float,
        days_held: int,
        max_return_pct: float,
        sentiment: str,
        technical_signal: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Determine if position should be exited.

        Args:
            entry_price: Position entry price
            current_price: Current market price
            days_held: Days position has been held
            max_return_pct: Maximum return % achieved
            sentiment: Original sentiment ('positive', 'negative')
            technical_signal: Current technical signal ('BULLISH', 'BEARISH', 'NEUTRAL')

        Returns:
            Tuple of (should_exit, exit_reason)
        """
        # Calculate current return
        return_pct = ((current_price - entry_price) / entry_price) * 100

        # 1. Take Profit Target
        if return_pct >= self.take_profit_pct:
            return True, f"Take profit at {return_pct:.2f}%"

        # 2. Trailing Stop (only after position is profitable)
        if max_return_pct > 5.0:  # Only trail after 5% gain
            # Use trailing stop
            drawdown_from_peak = max_return_pct - return_pct
            if drawdown_from_peak >= self.trailing_stop_pct:
                return True, f"Trailing stop (peak: {max_return_pct:.2f}%, current: {return_pct:.2f}%)"

        # 3. Momentum Reversal Detection
        if technical_signal and sentiment == 'positive':
            if technical_signal == 'BEARISH' and days_held >= self.min_holding_days:
                return True, "Momentum reversal detected (technicals turned bearish)"

        # 4. Accelerated Exit on Deep Loss
        if return_pct < -4.0 and days_held >= self.min_holding_days:
            # Exit faster if losing badly
            return True, f"Accelerated exit on {return_pct:.2f}% loss"

        # No exit condition met
        return False, ""

    def update_max_return(
        self,
        current_max: float,
        current_return: float
    ) -> float:
        """
        Update maximum return achieved.

        Args:
            current_max: Current maximum return
            current_return: Current return percentage

        Returns:
            Updated maximum return
        """
        return max(current_max, current_return)


def main():
    """Test the dynamic exit manager."""
    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 80)
    print("DYNAMIC EXIT MANAGER TEST")
    print("=" * 80 + "\n")

    manager = DynamicExitManager(
        take_profit_pct=10.0,
        trailing_stop_pct=3.0,
        min_holding_days=3,
        max_holding_days=14
    )

    # Test Case 1: Strong signal, low volatility
    print("Test 1: Strong signal (0.8), Low volatility (0.8%)")
    holding_period = manager.calculate_optimal_holding_period(
        sentiment_strength=0.8,
        volatility_pct=0.8
    )
    print(f"  Optimal holding period: {holding_period} days\n")

    # Test Case 2: Weak signal, high volatility
    print("Test 2: Weak signal (0.2), High volatility (3.5%)")
    holding_period = manager.calculate_optimal_holding_period(
        sentiment_strength=0.2,
        volatility_pct=3.5
    )
    print(f"  Optimal holding period: {holding_period} days\n")

    # Test Case 3: Take profit scenario
    print("Test 3: Position up 11% (take profit)")
    should_exit, reason = manager.should_exit(
        entry_price=100.0,
        current_price=111.0,
        days_held=5,
        max_return_pct=11.0,
        sentiment='positive'
    )
    print(f"  Should exit: {should_exit}")
    print(f"  Reason: {reason}\n")

    # Test Case 4: Trailing stop scenario
    print("Test 4: Position peaked at 8%, now at 4% (trailing stop)")
    should_exit, reason = manager.should_exit(
        entry_price=100.0,
        current_price=104.0,
        days_held=7,
        max_return_pct=8.0,
        sentiment='positive'
    )
    print(f"  Should exit: {should_exit}")
    print(f"  Reason: {reason}\n")

    # Test Case 5: Momentum reversal
    print("Test 5: Technicals turned bearish (momentum reversal)")
    should_exit, reason = manager.should_exit(
        entry_price=100.0,
        current_price=102.0,
        days_held=5,
        max_return_pct=3.0,
        sentiment='positive',
        technical_signal='BEARISH'
    )
    print(f"  Should exit: {should_exit}")
    print(f"  Reason: {reason}\n")

    # Test Case 6: Deep loss
    print("Test 6: Position down 4.5% (accelerated exit)")
    should_exit, reason = manager.should_exit(
        entry_price=100.0,
        current_price=95.5,
        days_held=4,
        max_return_pct=0.0,
        sentiment='positive'
    )
    print(f"  Should exit: {should_exit}")
    print(f"  Reason: {reason}\n")

    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
