"""
ASX trading hours and optimal timing logic.
Ensures trades only occur during high-liquidity periods.
"""
from datetime import datetime, time
import pytz
from typing import Tuple

AEST = pytz.timezone('Australia/Sydney')


class ASXTradingHours:
    """Manages ASX-specific trading hours and optimal windows."""

    # ASX normal trading: 10:00-16:00 AEST
    MARKET_OPEN = time(10, 0)
    MARKET_CLOSE = time(16, 0)

    # Optimal trading window: 11:00-15:00 AEST
    OPTIMAL_START = time(11, 0)
    OPTIMAL_END = time(15, 0)

    # Avoid zones
    AVOID_FIRST_MINUTES = 45  # After open
    AVOID_LAST_MINUTES = 30   # Before close

    @staticmethod
    def is_market_open(dt: datetime = None) -> bool:
        """Check if ASX is currently open."""
        if dt is None:
            dt = datetime.now(AEST)

        # Convert to AEST if not already
        if dt.tzinfo is None:
            dt = AEST.localize(dt)
        else:
            dt = dt.astimezone(AEST)

        # Check if weekday
        if dt.weekday() >= 5:  # Saturday=5, Sunday=6
            return False

        # Check if within trading hours
        current_time = dt.time()
        return ASXTradingHours.MARKET_OPEN <= current_time <= ASXTradingHours.MARKET_CLOSE

    @staticmethod
    def is_optimal_trading_time(dt: datetime = None) -> Tuple[bool, str]:
        """
        Check if current time is optimal for trading.

        Returns:
            (is_optimal, reason)
        """
        if dt is None:
            dt = datetime.now(AEST)

        if dt.tzinfo is None:
            dt = AEST.localize(dt)
        else:
            dt = dt.astimezone(AEST)

        current_time = dt.time()

        # Check if market is open first
        if not ASXTradingHours.is_market_open(dt):
            return False, "market_closed"

        # Check if in optimal window
        if ASXTradingHours.OPTIMAL_START <= current_time <= ASXTradingHours.OPTIMAL_END:
            return True, "optimal_window"

        # Check if too close to open
        minutes_since_open = (
            dt.hour * 60 + dt.minute -
            (ASXTradingHours.MARKET_OPEN.hour * 60 + ASXTradingHours.MARKET_OPEN.minute)
        )
        if 0 <= minutes_since_open < ASXTradingHours.AVOID_FIRST_MINUTES:
            return False, "too_close_to_open"

        # Check if too close to close
        minutes_to_close = (
            ASXTradingHours.MARKET_CLOSE.hour * 60 + ASXTradingHours.MARKET_CLOSE.minute -
            (dt.hour * 60 + dt.minute)
        )
        if 0 <= minutes_to_close < ASXTradingHours.AVOID_LAST_MINUTES:
            return False, "too_close_to_close"

        # In market hours but outside optimal window
        return False, "suboptimal_time"

    @staticmethod
    def get_time_of_day_boost(dt: datetime = None) -> float:
        """
        Get confidence boost/penalty based on time of day.

        Returns:
            Multiplicative factor (0.9-1.08)
        """
        is_optimal, reason = ASXTradingHours.is_optimal_trading_time(dt)

        if reason == "optimal_window":
            return 1.08  # 8% boost for optimal time
        elif reason == "market_closed":
            return 0.70  # Major penalty
        elif reason in ["too_close_to_open", "too_close_to_close"]:
            return 0.90  # 10% penalty for risky times
        else:  # suboptimal_time but acceptable
            return 1.00  # Neutral


# Testing
if __name__ == "__main__":
    print("=== ASX Trading Hours Tests ===\n")

    # Test various times
    test_times = [
        datetime(2025, 10, 13, 9, 30),   # Before open
        datetime(2025, 10, 13, 10, 15),  # Just after open
        datetime(2025, 10, 13, 12, 30),  # Optimal window
        datetime(2025, 10, 13, 15, 45),  # Near close
        datetime(2025, 10, 13, 17, 0),   # After close
    ]

    for test_time in test_times:
        test_time = AEST.localize(test_time)
        is_open = ASXTradingHours.is_market_open(test_time)
        is_optimal, reason = ASXTradingHours.is_optimal_trading_time(test_time)
        boost = ASXTradingHours.get_time_of_day_boost(test_time)

        print(f"{test_time.strftime('%H:%M AEST')}")
        print(f"  Market Open: {is_open}")
        print(f"  Optimal: {is_optimal} ({reason})")
        print(f"  Boost: {boost:.2f}\n")
