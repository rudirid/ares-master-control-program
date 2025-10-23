"""
Risk Management System

Implements comprehensive risk controls including position sizing,
stop losses, diversification limits, and circuit breakers.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)


# Sector mapping for ASX stocks
SECTOR_MAP = {
    # Mining & Resources
    'BHP': 'Mining', 'RIO': 'Mining', 'FMG': 'Mining', 'MIN': 'Mining',
    'S32': 'Mining', 'NCM': 'Mining', 'IGO': 'Mining', 'OZL': 'Mining',

    # Banks
    'CBA': 'Banking', 'WBC': 'Banking', 'NAB': 'Banking', 'ANZ': 'Banking',
    'MQG': 'Banking', 'BOQ': 'Banking', 'BEN': 'Banking',

    # Healthcare
    'CSL': 'Healthcare', 'COH': 'Healthcare', 'RMD': 'Healthcare',
    'SHL': 'Healthcare', 'RHC': 'Healthcare',

    # Retail
    'WES': 'Retail', 'WOW': 'Retail', 'JBH': 'Retail', 'HVN': 'Retail',

    # Energy
    'WDS': 'Energy', 'STO': 'Energy', 'ORG': 'Energy', 'WHC': 'Energy',

    # Telecom
    'TLS': 'Telecom', 'TPG': 'Telecom',

    # Real Estate
    'GMG': 'Real Estate', 'SCG': 'Real Estate', 'GPT': 'Real Estate',
    'MGR': 'Real Estate', 'CHC': 'Real Estate',

    # Technology
    'WTC': 'Technology', 'XRO': 'Technology', 'CPU': 'Technology',
    'APX': 'Technology', 'TNE': 'Technology',

    # Industrials
    'QAN': 'Industrials', 'BXB': 'Industrials', 'TCL': 'Industrials',
    'APA': 'Industrials', 'SYD': 'Industrials',
}


class RiskConfig:
    """Risk management configuration."""

    def __init__(
        self,
        portfolio_value: float = 100000.0,
        max_risk_per_trade_pct: float = 2.0,
        stop_loss_pct: float = 5.0,
        max_positions_per_sector: int = 3,
        daily_loss_limit_pct: float = 5.0,
        min_confidence: float = 0.7,
        max_portfolio_exposure_pct: float = 80.0,
        max_correlation: float = 0.7
    ):
        """
        Initialize risk configuration.

        Args:
            portfolio_value: Total portfolio value
            max_risk_per_trade_pct: Max % of portfolio to risk per trade
            stop_loss_pct: Stop loss percentage
            max_positions_per_sector: Max positions in same sector
            daily_loss_limit_pct: Daily loss limit (circuit breaker)
            min_confidence: Minimum confidence for trades
            max_portfolio_exposure_pct: Max % of portfolio exposed
            max_correlation: Max correlation between positions
        """
        self.portfolio_value = portfolio_value
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_positions_per_sector = max_positions_per_sector
        self.daily_loss_limit_pct = daily_loss_limit_pct
        self.min_confidence = min_confidence
        self.max_portfolio_exposure_pct = max_portfolio_exposure_pct
        self.max_correlation = max_correlation


class RiskManager:
    """
    Manages risk controls for paper trading.
    """

    def __init__(self, db_path: str, config: RiskConfig):
        """
        Initialize risk manager.

        Args:
            db_path: Database path
            config: Risk configuration
        """
        self.db_path = db_path
        self.config = config
        self._init_database()

    def _init_database(self):
        """Initialize risk management tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Risk events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT,
                recommendation_id TEXT,
                ticker TEXT,
                action_taken TEXT,
                details TEXT
            )
        """)

        # Circuit breaker state
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS circuit_breaker_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                is_active INTEGER DEFAULT 0,
                activated_at TEXT,
                reason TEXT,
                daily_loss_pct REAL,
                deactivate_at TEXT
            )
        """)

        # Initialize circuit breaker state if not exists
        cursor.execute("""
            INSERT OR IGNORE INTO circuit_breaker_state (id, is_active)
            VALUES (1, 0)
        """)

        conn.commit()
        conn.close()

        logger.info("Risk management database initialized")

    def calculate_position_size(
        self,
        ticker: str,
        entry_price: float,
        confidence: float
    ) -> Tuple[float, str]:
        """
        Calculate position size based on risk rules.

        Args:
            ticker: Stock ticker
            entry_price: Entry price
            confidence: Recommendation confidence

        Returns:
            Tuple of (position_size, reason)
        """
        # Max risk per trade
        max_risk_amount = self.config.portfolio_value * (self.config.max_risk_per_trade_pct / 100)

        # Position size based on stop loss
        # If stop loss is 5%, we can risk $2000 (2% of $100k)
        # So position size = risk_amount / (stop_loss_pct / 100)
        base_position_size = max_risk_amount / (self.config.stop_loss_pct / 100)

        # Adjust based on confidence (scale down if confidence is not perfect)
        confidence_factor = min(confidence / self.config.min_confidence, 1.0)
        adjusted_position_size = base_position_size * confidence_factor

        # Calculate number of shares
        shares = int(adjusted_position_size / entry_price)
        actual_position_size = shares * entry_price

        reason = (
            f"Max risk: ${max_risk_amount:,.2f} ({self.config.max_risk_per_trade_pct}%), "
            f"Stop loss: {self.config.stop_loss_pct}%, "
            f"Confidence factor: {confidence_factor:.2f}, "
            f"Shares: {shares}"
        )

        return actual_position_size, reason

    def check_confidence_threshold(self, confidence: float) -> Tuple[bool, str]:
        """
        Check if confidence meets minimum threshold.

        Args:
            confidence: Recommendation confidence

        Returns:
            Tuple of (is_allowed, reason)
        """
        if confidence < self.config.min_confidence:
            return False, f"Confidence {confidence:.2f} below minimum {self.config.min_confidence}"

        return True, f"Confidence {confidence:.2f} meets threshold"

    def check_sector_diversification(self, ticker: str) -> Tuple[bool, str]:
        """
        Check sector diversification limits.

        Args:
            ticker: Stock ticker

        Returns:
            Tuple of (is_allowed, reason)
        """
        sector = SECTOR_MAP.get(ticker, 'Unknown')

        # Count active positions in this sector
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ticker
            FROM paper_recommendations
            WHERE status = 'ACTIVE'
        """)

        active_tickers = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Count positions in same sector
        sector_count = sum(1 for t in active_tickers if SECTOR_MAP.get(t, 'Unknown') == sector)

        if sector_count >= self.config.max_positions_per_sector:
            return False, f"Already have {sector_count} positions in {sector} sector (max: {self.config.max_positions_per_sector})"

        return True, f"{sector} sector exposure: {sector_count}/{self.config.max_positions_per_sector}"

    def check_portfolio_exposure(self) -> Tuple[bool, str]:
        """
        Check total portfolio exposure.

        Returns:
            Tuple of (is_allowed, reason)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT SUM(entry_price * 1) as total_exposure
            FROM paper_recommendations
            WHERE status = 'ACTIVE'
            AND entry_price IS NOT NULL
        """)

        row = cursor.fetchone()
        conn.close()

        total_exposure = row[0] or 0
        exposure_pct = (total_exposure / self.config.portfolio_value) * 100

        if exposure_pct >= self.config.max_portfolio_exposure_pct:
            return False, f"Portfolio exposure {exposure_pct:.1f}% exceeds limit {self.config.max_portfolio_exposure_pct}%"

        return True, f"Portfolio exposure: {exposure_pct:.1f}%"

    def check_circuit_breaker(self) -> Tuple[bool, str]:
        """
        Check if circuit breaker is active.

        Returns:
            Tuple of (is_active, reason)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT is_active, reason, daily_loss_pct, deactivate_at
            FROM circuit_breaker_state
            WHERE id = 1
        """)

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, "Circuit breaker not initialized"

        is_active, reason, daily_loss, deactivate_at = row

        if is_active:
            # Check if it's time to deactivate (new trading day)
            if deactivate_at:
                deactivate_dt = datetime.fromisoformat(deactivate_at)
                if datetime.now() >= deactivate_dt:
                    self.deactivate_circuit_breaker()
                    return False, "Circuit breaker expired, trading resumed"

            return True, f"Circuit breaker ACTIVE: {reason} (loss: {daily_loss:.2f}%)"

        return False, "Circuit breaker inactive"

    def calculate_daily_loss(self) -> float:
        """
        Calculate today's loss percentage.

        Returns:
            Daily loss percentage
        """
        today = datetime.now().strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get positions closed today
        cursor.execute("""
            SELECT SUM(actual_return_pct)
            FROM paper_recommendations
            WHERE DATE(exit_date) = ?
            AND status = 'CLOSED'
        """, (today,))

        row = cursor.fetchone()
        conn.close()

        return row[0] or 0.0

    def activate_circuit_breaker(self, daily_loss_pct: float):
        """
        Activate circuit breaker.

        Args:
            daily_loss_pct: Daily loss percentage that triggered breaker
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        now = datetime.now()
        # Deactivate at start of next trading day (9 AM next day)
        next_day = now + timedelta(days=1)
        deactivate_at = next_day.replace(hour=9, minute=0, second=0, microsecond=0)

        reason = f"Daily loss limit exceeded: {daily_loss_pct:.2f}%"

        cursor.execute("""
            UPDATE circuit_breaker_state
            SET is_active = 1,
                activated_at = ?,
                reason = ?,
                daily_loss_pct = ?,
                deactivate_at = ?
            WHERE id = 1
        """, (now.isoformat(), reason, daily_loss_pct, deactivate_at.isoformat()))

        conn.commit()
        conn.close()

        self.log_risk_event(
            event_type='CIRCUIT_BREAKER',
            severity='CRITICAL',
            description=reason,
            action_taken='All trading paused until next day'
        )

        logger.warning(f"CIRCUIT BREAKER ACTIVATED: {reason}")

    def deactivate_circuit_breaker(self):
        """Deactivate circuit breaker."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE circuit_breaker_state
            SET is_active = 0,
                activated_at = NULL,
                reason = NULL,
                daily_loss_pct = NULL,
                deactivate_at = NULL
            WHERE id = 1
        """)

        conn.commit()
        conn.close()

        logger.info("Circuit breaker deactivated")

    def check_stop_loss(self, recommendation_id: str, current_price: float) -> Tuple[bool, str]:
        """
        Check if position should be stopped out.

        Args:
            recommendation_id: Recommendation ID
            current_price: Current market price

        Returns:
            Tuple of (should_close, reason)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT entry_price, action, ticker
            FROM paper_recommendations
            WHERE recommendation_id = ?
            AND status = 'ACTIVE'
        """, (recommendation_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return False, "Position not found or not active"

        entry_price, action, ticker = row

        # Calculate current P/L
        if action == 'BUY':
            loss_pct = ((current_price - entry_price) / entry_price) * 100
        elif action == 'SELL/AVOID':
            loss_pct = ((entry_price - current_price) / entry_price) * 100
        else:
            return False, "Unknown action type"

        # Check stop loss
        if loss_pct <= -self.config.stop_loss_pct:
            reason = f"Stop loss triggered: {loss_pct:.2f}% loss (limit: {self.config.stop_loss_pct}%)"

            self.log_risk_event(
                event_type='STOP_LOSS',
                severity='HIGH',
                description=reason,
                recommendation_id=recommendation_id,
                ticker=ticker,
                action_taken='Position closed'
            )

            return True, reason

        return False, f"Current loss: {loss_pct:.2f}% (stop: {self.config.stop_loss_pct}%)"

    def validate_new_position(
        self,
        ticker: str,
        confidence: float,
        entry_price: float
    ) -> Tuple[bool, List[str], Dict]:
        """
        Validate if new position passes all risk checks.

        Args:
            ticker: Stock ticker
            confidence: Recommendation confidence
            entry_price: Entry price

        Returns:
            Tuple of (is_allowed, reasons, risk_details)
        """
        checks = []
        reasons = []

        # 1. Circuit breaker check
        breaker_active, breaker_reason = self.check_circuit_breaker()
        if breaker_active:
            return False, [breaker_reason], {'circuit_breaker': True}
        checks.append(('Circuit Breaker', True, breaker_reason))

        # 2. Confidence threshold
        conf_ok, conf_reason = self.check_confidence_threshold(confidence)
        checks.append(('Confidence', conf_ok, conf_reason))
        if not conf_ok:
            reasons.append(conf_reason)

        # 3. Sector diversification
        sector_ok, sector_reason = self.check_sector_diversification(ticker)
        checks.append(('Sector Diversification', sector_ok, sector_reason))
        if not sector_ok:
            reasons.append(sector_reason)

        # 4. Portfolio exposure
        exposure_ok, exposure_reason = self.check_portfolio_exposure()
        checks.append(('Portfolio Exposure', exposure_ok, exposure_reason))
        if not exposure_ok:
            reasons.append(exposure_reason)

        # Calculate position size
        position_size, size_reason = self.calculate_position_size(ticker, entry_price, confidence)
        checks.append(('Position Size', True, size_reason))

        # Determine if position is allowed
        is_allowed = all(check[1] for check in checks)

        risk_details = {
            'checks': checks,
            'position_size': position_size,
            'position_size_reason': size_reason,
            'is_allowed': is_allowed
        }

        return is_allowed, reasons, risk_details

    def log_risk_event(
        self,
        event_type: str,
        severity: str,
        description: str,
        recommendation_id: Optional[str] = None,
        ticker: Optional[str] = None,
        action_taken: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """
        Log a risk management event.

        Args:
            event_type: Type of event (STOP_LOSS, CIRCUIT_BREAKER, etc.)
            severity: LOW, MEDIUM, HIGH, CRITICAL
            description: Event description
            recommendation_id: Related recommendation ID
            ticker: Related ticker
            action_taken: Action taken in response
            details: Additional details dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO risk_events (
                timestamp, event_type, severity, description,
                recommendation_id, ticker, action_taken, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            event_type,
            severity,
            description,
            recommendation_id,
            ticker,
            action_taken,
            json.dumps(details) if details else None
        ))

        conn.commit()
        conn.close()

    def get_risk_summary(self) -> Dict:
        """
        Get current risk summary.

        Returns:
            Risk summary dictionary
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get active positions
        cursor.execute("""
            SELECT ticker, entry_price, confidence
            FROM paper_recommendations
            WHERE status = 'ACTIVE'
        """)

        active_positions = []
        total_exposure = 0
        sector_exposure = {}

        for ticker, entry_price, confidence in cursor.fetchall():
            sector = SECTOR_MAP.get(ticker, 'Unknown')
            position_value = entry_price  # Simplified

            active_positions.append({
                'ticker': ticker,
                'entry_price': entry_price,
                'confidence': confidence,
                'sector': sector,
                'position_value': position_value
            })

            total_exposure += position_value
            sector_exposure[sector] = sector_exposure.get(sector, 0) + 1

        # Get circuit breaker state
        cursor.execute("""
            SELECT is_active, reason, daily_loss_pct
            FROM circuit_breaker_state
            WHERE id = 1
        """)

        breaker_row = cursor.fetchone()
        circuit_breaker = {
            'is_active': bool(breaker_row[0]) if breaker_row else False,
            'reason': breaker_row[1] if breaker_row else None,
            'daily_loss_pct': breaker_row[2] if breaker_row else 0
        }

        # Get recent risk events
        cursor.execute("""
            SELECT event_type, severity, description, timestamp
            FROM risk_events
            ORDER BY timestamp DESC
            LIMIT 10
        """)

        recent_events = []
        for event_type, severity, description, timestamp in cursor.fetchall():
            recent_events.append({
                'type': event_type,
                'severity': severity,
                'description': description,
                'timestamp': timestamp
            })

        conn.close()

        exposure_pct = (total_exposure / self.config.portfolio_value) * 100
        daily_loss_pct = self.calculate_daily_loss()

        return {
            'portfolio_value': self.config.portfolio_value,
            'total_exposure': total_exposure,
            'exposure_pct': round(exposure_pct, 2),
            'available_capital': self.config.portfolio_value - total_exposure,
            'active_positions_count': len(active_positions),
            'active_positions': active_positions,
            'sector_exposure': sector_exposure,
            'daily_loss_pct': round(daily_loss_pct, 2),
            'circuit_breaker': circuit_breaker,
            'recent_events': recent_events,
            'risk_limits': {
                'max_risk_per_trade_pct': self.config.max_risk_per_trade_pct,
                'stop_loss_pct': self.config.stop_loss_pct,
                'max_positions_per_sector': self.config.max_positions_per_sector,
                'daily_loss_limit_pct': self.config.daily_loss_limit_pct,
                'min_confidence': self.config.min_confidence,
                'max_portfolio_exposure_pct': self.config.max_portfolio_exposure_pct
            }
        }


def main():
    """Test risk manager."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 70)
    print("RISK MANAGER TEST")
    print("=" * 70 + "\n")

    # Initialize risk manager
    risk_config = RiskConfig(
        portfolio_value=100000,
        max_risk_per_trade_pct=2.0,
        stop_loss_pct=5.0,
        max_positions_per_sector=3,
        daily_loss_limit_pct=5.0,
        min_confidence=0.7
    )

    risk_manager = RiskManager(config.DATABASE_PATH, risk_config)

    # Test position validation
    print("Testing position validation for BHP...")
    is_allowed, reasons, details = risk_manager.validate_new_position(
        ticker='BHP',
        confidence=0.75,
        entry_price=45.50
    )

    print(f"Allowed: {is_allowed}")
    if not is_allowed:
        print(f"Reasons: {', '.join(reasons)}")

    print(f"\nPosition size: ${details['position_size']:,.2f}")
    print(f"Reason: {details['position_size_reason']}")

    print("\nRisk checks:")
    for check_name, passed, reason in details['checks']:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check_name}: {reason}")

    # Get risk summary
    print("\n" + "=" * 70)
    print("RISK SUMMARY")
    print("=" * 70)

    summary = risk_manager.get_risk_summary()

    print(f"\nPortfolio Value: ${summary['portfolio_value']:,.2f}")
    print(f"Total Exposure: ${summary['total_exposure']:,.2f} ({summary['exposure_pct']}%)")
    print(f"Available Capital: ${summary['available_capital']:,.2f}")
    print(f"Active Positions: {summary['active_positions_count']}")
    print(f"Daily Loss: {summary['daily_loss_pct']:+.2f}%")

    if summary['circuit_breaker']['is_active']:
        print(f"\nCIRCUIT BREAKER ACTIVE:")
        print(f"  {summary['circuit_breaker']['reason']}")

    print(f"\nSector Exposure:")
    for sector, count in summary['sector_exposure'].items():
        print(f"  {sector}: {count} position(s)")

    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
