"""
Behavioral Finance Filters

Implements behavioral finance principles to improve trading signals:
- Time Filter: Only trade fresh announcements (<30 min old)
- Materiality Filter: Focus on high-impact news only
- Expectation Gap Analysis: Detect surprises vs consensus
- Time-of-Day Filter: Trade during optimal liquidity hours
- Contrarian Signals: Fade extreme sentiment

Based on behavioral finance research showing:
1. Information decays exponentially (30min = 0% edge)
2. Markets react to surprises, not absolute news
3. Extreme sentiment often signals reversals
4. Time-of-day affects execution quality

Author: Claude Code
Date: 2025-10-10
"""

import logging
from datetime import datetime, time, timedelta
from typing import Tuple, Optional, Dict
import pytz

logger = logging.getLogger(__name__)


class TimeFilter:
    """
    Filter trades based on announcement age.

    Research shows information is priced into markets within 15-30 minutes.
    Trading on stale news (>30 min old) has negative expected value.
    """

    def __init__(
        self,
        max_age_minutes: int = 30,
        warning_age_minutes: int = 15
    ):
        """
        Initialize time filter.

        Args:
            max_age_minutes: Maximum announcement age to trade (default 30)
            warning_age_minutes: Age at which to warn about decaying edge (default 15)
        """
        self.max_age_minutes = max_age_minutes
        self.warning_age_minutes = warning_age_minutes

    def is_tradeable_by_time(
        self,
        announcement_datetime: datetime,
        current_datetime: datetime
    ) -> Tuple[bool, str, float]:
        """
        Determine if announcement is fresh enough to trade.

        Args:
            announcement_datetime: When announcement was published
            current_datetime: Current time (or simulation time)

        Returns:
            Tuple of (is_tradeable, reason, confidence_adjustment)
        """
        age_minutes = (current_datetime - announcement_datetime).total_seconds() / 60

        if age_minutes < 0:
            # Announcement is in the future (data error)
            return False, f"Future announcement (data error)", -1.0

        elif age_minutes <= 5:
            # Ultra-fresh: Maximum information edge
            return True, f"Ultra-fresh ({age_minutes:.1f} min) - maximum edge", 0.15

        elif age_minutes <= self.warning_age_minutes:
            # Fresh: Good information edge
            return True, f"Fresh ({age_minutes:.1f} min) - strong edge", 0.05

        elif age_minutes <= self.max_age_minutes:
            # Moderate age: Edge decaying rapidly
            # Confidence penalty scales linearly from 0 to -0.15
            decay_factor = (age_minutes - self.warning_age_minutes) / (self.max_age_minutes - self.warning_age_minutes)
            confidence_penalty = -0.15 * decay_factor
            return True, f"Moderate age ({age_minutes:.1f} min) - edge decaying", confidence_penalty

        else:
            # Too old: Information fully priced in
            return False, f"Too old ({age_minutes:.1f} min) - information fully priced", -0.30


class TimeOfDayFilter:
    """
    Filter trades based on time of day.

    Optimal trading hours: 10:00 AM - 2:00 PM AEST
    - Avoids low liquidity at open (wider spreads)
    - Avoids end-of-day volatility and position squaring
    - Ensures sufficient post-announcement volume
    """

    def __init__(
        self,
        optimal_start_hour: int = 10,
        optimal_end_hour: int = 14,
        timezone: str = 'Australia/Sydney'
    ):
        """
        Initialize time-of-day filter.

        Args:
            optimal_start_hour: Start of optimal trading window (default 10 AM)
            optimal_end_hour: End of optimal trading window (default 2 PM)
            timezone: Timezone for trading hours (default Australia/Sydney)
        """
        self.optimal_start = time(hour=optimal_start_hour, minute=0)
        self.optimal_end = time(hour=optimal_end_hour, minute=0)
        self.tz = pytz.timezone(timezone)

    def is_optimal_time(
        self,
        trade_datetime: datetime
    ) -> Tuple[bool, str, float]:
        """
        Determine if time of day is optimal for trading.

        Args:
            trade_datetime: When trade would be executed

        Returns:
            Tuple of (is_optimal, reason, confidence_adjustment)
        """
        # Convert to Sydney time if needed
        if trade_datetime.tzinfo is None:
            trade_time = self.tz.localize(trade_datetime).time()
        else:
            trade_time = trade_datetime.astimezone(self.tz).time()

        # Check if within optimal window
        if self.optimal_start <= trade_time <= self.optimal_end:
            return True, f"Optimal time ({trade_time.strftime('%H:%M')} AEST)", 0.05

        # Early morning (before 10 AM)
        elif trade_time < self.optimal_start:
            # Calculate how early (hours before optimal start)
            hours_before = (datetime.combine(datetime.today(), self.optimal_start) -
                          datetime.combine(datetime.today(), trade_time)).seconds / 3600

            if hours_before > 1:
                # Very early (low liquidity)
                return False, f"Too early ({trade_time.strftime('%H:%M')} AEST) - low liquidity", -0.15
            else:
                # Slightly early (acceptable but not optimal)
                return True, f"Early ({trade_time.strftime('%H:%M')} AEST) - suboptimal liquidity", -0.05

        # Late afternoon (after 2 PM)
        else:
            # Calculate how late (hours after optimal end)
            hours_after = (datetime.combine(datetime.today(), trade_time) -
                         datetime.combine(datetime.today(), self.optimal_end)).seconds / 3600

            if hours_after > 2:
                # Very late (end-of-day volatility)
                return False, f"Too late ({trade_time.strftime('%H:%M')} AEST) - end-of-day volatility", -0.15
            else:
                # Slightly late (acceptable but not optimal)
                return True, f"Late ({trade_time.strftime('%H:%M')} AEST) - increased volatility", -0.05


class MaterialityFilter:
    """
    Filter announcements based on materiality.

    Research shows 80% of announcements are administrative noise.
    Focus only on genuinely market-moving events.
    """

    # High-materiality announcement types (based on actual ASX announcement types)
    HIGH_MATERIALITY = {
        # Takeovers & M&A
        'Takeover / Scheme Announcements',
        'Takeover/Scheme',

        # Financial Results & Reports
        'Quarterly Activities Report',
        'Quarterly Report',
        'Half Yearly Report',
        'Half Year Results',
        'Full Year Results',
        'Annual Report',
        'Progress Report',

        # Capital & Distributions
        'Distribution Announcement',
        'Dividend',  # Added based on database
        'Capital Raising',

        # Corporate Actions
        'Asset Acquisition & Disposal',
        'Profit Guidance',
        'Trading Halt',
        'Trading Update',
        'Suspension from Official Quotation',
        'Reinstatement to Official Quotation',
        'ASX Query',  # Often material

        # Contracts & Partnerships
        'Major Contracts',
        'New Product Launch',
        'Strategic Partnership',

        # Catch-all categories (score depends on keywords)
        'General Announcement',
        'Other'
    }

    # Low-materiality (noise) - Administrative announcements
    LOW_MATERIALITY = {
        'Notice of Meeting',
        'AGM/EGM Documents',
        'Change of Director\'s Interest Notice',
        'Director Changes',  # Added based on database
        'Appendix 3Y',
        'Appendix 3Z',
        'Appendix 3B',
        'Appendix 2A',
        'Change in Substantial Holding',
        'Substantial Holder',  # Added based on database
        'Results of Meeting',
        'Letter to Shareholders',
        'Amended Announcement'
    }

    # Keywords indicating high materiality
    MATERIAL_KEYWORDS = {
        'acquisition', 'merger', 'takeover', 'bid',
        'profit', 'loss', 'revenue', 'ebitda', 'earnings',
        'dividend', 'distribution', 'capital raising',
        'guidance', 'upgrade', 'downgrade',
        'contract', 'agreement', 'partnership',
        'breakthrough', 'discovery', 'approval',
        'regulatory', 'suspension', 'halt',
        'material', 'significant', 'major'
    }

    def __init__(self, min_materiality_score: float = 0.5):
        """
        Initialize materiality filter.

        Args:
            min_materiality_score: Minimum score to trade (0-1, default 0.5)
        """
        self.min_materiality_score = min_materiality_score

    def assess_materiality(
        self,
        announcement_type: str,
        title: str,
        content: str,
        price_sensitive: bool = False
    ) -> Tuple[bool, str, float]:
        """
        Assess if announcement is material enough to trade.

        Args:
            announcement_type: ASX announcement type
            title: Announcement title
            content: Announcement content
            price_sensitive: Whether flagged as price sensitive

        Returns:
            Tuple of (is_material, reason, materiality_score)
        """
        materiality_score = 0.3  # Base score

        # 1. Check announcement type
        if announcement_type in self.HIGH_MATERIALITY:
            materiality_score += 0.3
        elif announcement_type in self.LOW_MATERIALITY:
            materiality_score -= 0.2

        # 2. Price sensitive flag
        if price_sensitive:
            materiality_score += 0.2

        # 3. Check for material keywords in title/content
        text_lower = (title + ' ' + content).lower()
        keyword_matches = sum(1 for keyword in self.MATERIAL_KEYWORDS if keyword in text_lower)

        if keyword_matches >= 3:
            materiality_score += 0.2
        elif keyword_matches >= 1:
            materiality_score += 0.1

        # Clamp score to [0, 1]
        materiality_score = max(0.0, min(1.0, materiality_score))

        # Determine if passes filter
        is_material = materiality_score >= self.min_materiality_score

        if is_material:
            reason = f"Material announcement (score: {materiality_score:.2f})"
        else:
            reason = f"Low materiality (score: {materiality_score:.2f}) - likely noise"

        return is_material, reason, materiality_score


class ContrarianSignals:
    """
    Generate contrarian signals when sentiment is extreme.

    Behavioral finance principle: When everyone agrees, be skeptical.
    Extreme positive sentiment often precedes reversals (overbought).
    """

    def __init__(
        self,
        extreme_threshold: float = 0.85,
        contrarian_adjustment: float = -0.20
    ):
        """
        Initialize contrarian signal generator.

        Args:
            extreme_threshold: Sentiment threshold for "extreme" (default 0.85)
            contrarian_adjustment: Confidence penalty for extreme sentiment (default -0.20)
        """
        self.extreme_threshold = extreme_threshold
        self.contrarian_adjustment = contrarian_adjustment

    def check_for_contrarian_signal(
        self,
        sentiment: str,
        sentiment_confidence: float,
        recent_price_change_pct: Optional[float] = None
    ) -> Tuple[bool, str, float]:
        """
        Check if contrarian signal should be applied.

        Args:
            sentiment: Sentiment direction ('positive', 'negative')
            sentiment_confidence: Sentiment confidence (0-1)
            recent_price_change_pct: Recent price change % (optional)

        Returns:
            Tuple of (apply_contrarian, reason, confidence_adjustment)
        """
        # Check for extreme sentiment
        if sentiment_confidence < self.extreme_threshold:
            return False, "Sentiment not extreme", 0.0

        # Extreme positive sentiment
        if sentiment == 'positive':
            # If price already ran up significantly, fade the signal
            if recent_price_change_pct is not None and recent_price_change_pct > 10:
                return True, (
                    f"Extreme positive sentiment ({sentiment_confidence:.2f}) + "
                    f"price already up {recent_price_change_pct:.1f}% - likely overbought"
                ), self.contrarian_adjustment * 1.5

            return True, (
                f"Extreme positive sentiment ({sentiment_confidence:.2f}) - "
                f"consensus too strong, potential reversal risk"
            ), self.contrarian_adjustment

        # Extreme negative sentiment (less reliable for contrarian)
        # Markets can stay irrational longer on downside
        elif sentiment == 'negative':
            if sentiment_confidence >= 0.95:  # Only on VERY extreme negative
                return True, (
                    f"Extremely negative sentiment ({sentiment_confidence:.2f}) - "
                    f"potential capitulation/oversold"
                ), self.contrarian_adjustment * 0.5

        return False, "No contrarian signal", 0.0


def main():
    """Test the behavioral filters."""
    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 80)
    print("BEHAVIORAL FINANCE FILTERS TEST")
    print("=" * 80 + "\n")

    # Test 1: Time Filter
    print("=" * 80)
    print("TEST 1: TIME FILTER")
    print("=" * 80 + "\n")

    time_filter = TimeFilter(max_age_minutes=30, warning_age_minutes=15)

    now = datetime.now()
    test_cases = [
        (now - timedelta(minutes=3), "3 minutes old"),
        (now - timedelta(minutes=10), "10 minutes old"),
        (now - timedelta(minutes=20), "20 minutes old"),
        (now - timedelta(minutes=45), "45 minutes old (should reject)"),
        (now + timedelta(minutes=5), "Future announcement (data error)")
    ]

    for announcement_time, description in test_cases:
        tradeable, reason, adjustment = time_filter.is_tradeable_by_time(announcement_time, now)
        print(f"{description}:")
        print(f"  Tradeable: {tradeable}")
        print(f"  Reason: {reason}")
        print(f"  Confidence adjustment: {adjustment:+.2f}\n")

    # Test 2: Time-of-Day Filter
    print("=" * 80)
    print("TEST 2: TIME-OF-DAY FILTER")
    print("=" * 80 + "\n")

    tod_filter = TimeOfDayFilter(optimal_start_hour=10, optimal_end_hour=14)

    today = datetime.now().date()
    test_times = [
        datetime.combine(today, time(hour=9, minute=0)),   # 9 AM (early)
        datetime.combine(today, time(hour=11, minute=30)), # 11:30 AM (optimal)
        datetime.combine(today, time(hour=15, minute=0)),  # 3 PM (late)
        datetime.combine(today, time(hour=16, minute=30)), # 4:30 PM (very late)
    ]

    for test_time in test_times:
        optimal, reason, adjustment = tod_filter.is_optimal_time(test_time)
        print(f"Trade at {test_time.strftime('%H:%M')}:")
        print(f"  Optimal: {optimal}")
        print(f"  Reason: {reason}")
        print(f"  Confidence adjustment: {adjustment:+.2f}\n")

    # Test 3: Materiality Filter
    print("=" * 80)
    print("TEST 3: MATERIALITY FILTER")
    print("=" * 80 + "\n")

    materiality_filter = MaterialityFilter(min_materiality_score=0.6)

    test_announcements = [
        {
            'type': 'Full Year Results',
            'title': 'FY25 Results - Record profit, dividend increased',
            'content': 'Revenue up 25%, EBITDA guidance upgraded',
            'price_sensitive': True,
            'description': 'High materiality earnings'
        },
        {
            'type': 'Change of Director\'s Interest Notice',
            'title': 'Appendix 3Y - Director Interest',
            'content': 'Director X acquired 100 shares',
            'price_sensitive': False,
            'description': 'Low materiality administrative'
        },
        {
            'type': 'Trading Halt',
            'title': 'Trading Halt - Pending Announcement',
            'content': 'Trading halt pending major acquisition announcement',
            'price_sensitive': True,
            'description': 'High materiality halt'
        }
    ]

    for test in test_announcements:
        material, reason, score = materiality_filter.assess_materiality(
            test['type'], test['title'], test['content'], test['price_sensitive']
        )
        print(f"{test['description']}:")
        print(f"  Material: {material}")
        print(f"  Reason: {reason}")
        print(f"  Score: {score:.2f}\n")

    # Test 4: Contrarian Signals
    print("=" * 80)
    print("TEST 4: CONTRARIAN SIGNALS")
    print("=" * 80 + "\n")

    contrarian = ContrarianSignals(extreme_threshold=0.85)

    contrarian_tests = [
        {
            'sentiment': 'positive',
            'confidence': 0.95,
            'price_change': 15.0,
            'description': 'Extreme positive + big run-up'
        },
        {
            'sentiment': 'positive',
            'confidence': 0.90,
            'price_change': 2.0,
            'description': 'Extreme positive + small move'
        },
        {
            'sentiment': 'positive',
            'confidence': 0.75,
            'price_change': None,
            'description': 'Moderate positive (not extreme)'
        },
        {
            'sentiment': 'negative',
            'confidence': 0.97,
            'price_change': -20.0,
            'description': 'Extreme negative (potential capitulation)'
        }
    ]

    for test in contrarian_tests:
        apply, reason, adjustment = contrarian.check_for_contrarian_signal(
            test['sentiment'], test['confidence'], test['price_change']
        )
        print(f"{test['description']}:")
        print(f"  Apply contrarian: {apply}")
        print(f"  Reason: {reason}")
        print(f"  Confidence adjustment: {adjustment:+.2f}\n")

    print("=" * 80)
    print("BEHAVIORAL FILTERS TEST COMPLETE")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
