"""
Kelly Criterion-based position sizing with portfolio heat monitoring.
Prevents catastrophic losses through systematic risk management.

Author: Claude Code
Date: 2025-10-10
"""
import numpy as np
from typing import Dict, Tuple, Optional, List
import logging
from dataclasses import dataclass, field
from datetime import datetime
from scipy.stats import spearmanr

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open trading position."""
    symbol: str
    entry_price: float
    shares: int
    stop_loss: float
    take_profit: float
    risk_amount: float
    confidence: float
    entry_time: datetime
    position_value: float = 0.0
    current_price: float = 0.0
    unrealized_pnl: float = 0.0


class KellyCriterionPositionSizer:
    """
    Position sizing using fractional Kelly Criterion.

    Full Kelly is too aggressive (40-50% drawdowns).
    We use quarter-Kelly (0.25×) for 10-20% drawdowns.
    """

    def __init__(
        self,
        account_size: float,
        kelly_fraction: float = 0.25,
        max_position_pct: float = 0.10,
        max_risk_per_trade_pct: float = 0.02,
        max_portfolio_heat_pct: float = 0.10
    ):
        """
        Args:
            account_size: Starting capital ($10,000)
            kelly_fraction: Fraction of Kelly to use (0.25 = quarter-Kelly)
            max_position_pct: Max position size as % of account (0.10 = 10%)
            max_risk_per_trade_pct: Max risk per trade (0.02 = 2%)
            max_portfolio_heat_pct: Max total risk across all positions (0.10 = 10%)
        """
        self.account_size = account_size
        self.kelly_fraction = kelly_fraction
        self.max_position_pct = max_position_pct
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.max_portfolio_heat_pct = max_portfolio_heat_pct

        self.open_positions: Dict[str, Position] = {}
        self.historical_trades: List[Dict] = []

        # Track daily/overall drawdown
        self.starting_daily_balance = account_size
        self.peak_balance = account_size
        self.daily_pnl = 0.0

        logger.info(
            f"Position sizer initialized: ${account_size:,.0f}, "
            f"Kelly={kelly_fraction:.2f}, MaxRisk={max_risk_per_trade_pct:.1%}"
        )

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss_price: float,
        confidence: float,
        current_portfolio_heat: Optional[float] = None
    ) -> Tuple[int, float, Dict]:
        """
        Calculate optimal position size for a trade.

        Args:
            symbol: Stock ticker
            entry_price: Planned entry price
            stop_loss_price: Stop loss price
            confidence: Model confidence [0,1]
            current_portfolio_heat: Current total risk % (auto-calculated if None)

        Returns:
            (shares_to_buy, risk_amount, details_dict)
        """

        # Calculate risk per share
        risk_per_share = abs(entry_price - stop_loss_price)

        if risk_per_share == 0:
            logger.error(f"Zero risk per share for {symbol}")
            return 0, 0.0, {'error': 'zero_risk'}

        # Get current portfolio heat
        if current_portfolio_heat is None:
            current_portfolio_heat = self.get_portfolio_heat()

        # Base Kelly calculation
        # Simplified: f* = edge / odds = (win_prob * avg_win - loss_prob * avg_loss) / avg_win
        # For confidence-based: approximate as f* ≈ (confidence - 0.5) * 2
        kelly_edge = max(0, (confidence - 0.5) * 2)  # 0.70 conf → 0.40 edge
        kelly_pct = kelly_edge * self.kelly_fraction

        # Apply confidence-based scaling
        if confidence >= 0.70:
            confidence_scale = 1.0  # Full position for high confidence
        elif confidence >= 0.60:
            confidence_scale = 0.75  # 75% for moderate-high
        elif confidence >= 0.50:
            confidence_scale = 0.50  # 50% for moderate
        else:
            confidence_scale = 0.25  # 25% for low (or skip)

        # Calculate risk amount
        base_risk_amount = self.account_size * kelly_pct * confidence_scale

        # Apply maximum risk per trade limit
        max_risk_allowed = self.account_size * self.max_risk_per_trade_pct
        risk_amount = min(base_risk_amount, max_risk_allowed)

        # Check portfolio heat limit
        new_heat = current_portfolio_heat + (risk_amount / self.account_size)
        if new_heat > self.max_portfolio_heat_pct:
            logger.warning(
                f"Portfolio heat limit: {current_portfolio_heat:.1%} + "
                f"{risk_amount/self.account_size:.1%} > {self.max_portfolio_heat_pct:.1%}"
            )
            # Reduce position to fit within heat limit
            available_heat = self.max_portfolio_heat_pct - current_portfolio_heat
            risk_amount = min(risk_amount, available_heat * self.account_size)

        if risk_amount <= 0:
            return 0, 0.0, {'reason': 'portfolio_heat_limit'}

        # Calculate shares
        shares = int(risk_amount / risk_per_share)

        # Calculate position value
        position_value = shares * entry_price

        # Apply maximum position size limit
        max_position_value = self.account_size * self.max_position_pct
        if position_value > max_position_value:
            shares = int(max_position_value / entry_price)
            position_value = shares * entry_price
            risk_amount = shares * risk_per_share
            logger.info(f"Position size capped at {self.max_position_pct:.0%} of account")

        # Final validation
        if shares <= 0:
            return 0, 0.0, {'reason': 'insufficient_capital'}

        # Calculate commission cost
        commission = max(6.0, position_value * 0.0008)  # IBKR: 0.08% with $6 min

        details = {
            'symbol': symbol,
            'shares': shares,
            'entry_price': entry_price,
            'stop_loss': stop_loss_price,
            'risk_per_share': risk_per_share,
            'risk_amount': risk_amount,
            'position_value': position_value,
            'commission': commission,
            'confidence': confidence,
            'kelly_edge': kelly_edge,
            'kelly_pct': kelly_pct,
            'confidence_scale': confidence_scale,
            'portfolio_heat_before': current_portfolio_heat,
            'portfolio_heat_after': current_portfolio_heat + (risk_amount / self.account_size)
        }

        logger.info(
            f"{symbol}: {shares} shares @ ${entry_price:.2f}, "
            f"Risk: ${risk_amount:.2f} ({risk_amount/self.account_size:.1%}), "
            f"Value: ${position_value:.2f}, "
            f"Conf: {confidence:.2f}"
        )

        return shares, risk_amount, details

    def get_portfolio_heat(self) -> float:
        """
        Calculate current portfolio heat (total risk as % of account).

        Returns:
            Portfolio heat percentage (0.0 to 1.0)
        """
        total_risk = sum(pos.risk_amount for pos in self.open_positions.values())
        return total_risk / self.account_size

    def get_daily_drawdown(self) -> float:
        """
        Calculate daily drawdown percentage.

        Returns:
            Daily drawdown as decimal (0.0 to 1.0)
        """
        if self.starting_daily_balance == 0:
            return 0.0
        return (self.starting_daily_balance - self.account_size) / self.starting_daily_balance

    def get_max_drawdown(self) -> float:
        """
        Calculate maximum drawdown from peak balance.

        Returns:
            Max drawdown as decimal (0.0 to 1.0)
        """
        if self.peak_balance == 0:
            return 0.0
        return (self.peak_balance - self.account_size) / self.peak_balance

    def check_risk_limits(self) -> Dict:
        """
        Check all risk limits and return status with required actions.

        Returns:
            Dict with 'status', 'daily_drawdown', 'max_drawdown', 'portfolio_heat', 'actions_required'
        """
        daily_dd = self.get_daily_drawdown()
        max_dd = self.get_max_drawdown()
        portfolio_heat = self.get_portfolio_heat()

        actions = []

        # Determine risk level based on drawdowns
        if max_dd >= 0.30:  # 30% max drawdown - SHUTDOWN
            status = 'SHUTDOWN'
            actions.append('CLOSE ALL POSITIONS IMMEDIATELY')
            actions.append('CEASE ALL TRADING UNTIL REVIEW')
            actions.append('SYSTEM REQUIRES MANUAL RESET')
            logger.critical(f"SHUTDOWN: Max drawdown {max_dd:.1%} >= 30%")

        elif max_dd >= 0.20 or daily_dd >= 0.15:  # 20% max or 15% daily - CRITICAL
            status = 'CRITICAL'
            actions.append('Reduce all positions by 75%')
            actions.append('NO NEW POSITIONS until drawdown < 15%')
            actions.append('Review all open trades immediately')
            logger.error(f"CRITICAL: Max DD {max_dd:.1%}, Daily DD {daily_dd:.1%}")

        elif max_dd >= 0.10 or daily_dd >= 0.08:  # 10% max or 8% daily - ALERT
            status = 'ALERT'
            actions.append('Reduce position sizes by 50%')
            actions.append('Tighten stop losses')
            actions.append('Only take highest confidence signals (>0.75)')
            logger.warning(f"ALERT: Max DD {max_dd:.1%}, Daily DD {daily_dd:.1%}")

        else:  # Normal operation
            status = 'NORMAL'
            actions.append('Operating within normal risk parameters')

        # Check portfolio heat limit
        if portfolio_heat > self.max_portfolio_heat_pct:
            if status == 'NORMAL':
                status = 'ALERT'
            actions.append(f'Portfolio heat {portfolio_heat:.1%} exceeds limit {self.max_portfolio_heat_pct:.1%}')
            actions.append('NO NEW POSITIONS until heat reduces')
            logger.warning(f"Portfolio heat limit exceeded: {portfolio_heat:.1%}")

        result = {
            'status': status,
            'daily_drawdown': daily_dd,
            'max_drawdown': max_dd,
            'portfolio_heat': portfolio_heat,
            'actions_required': actions,
            'account_size': self.account_size,
            'peak_balance': self.peak_balance,
            'daily_pnl': self.daily_pnl
        }

        return result

    def open_position(
        self,
        symbol: str,
        entry_price: float,
        shares: int,
        stop_loss: float,
        take_profit: float,
        risk_amount: float,
        confidence: float
    ) -> Position:
        """
        Record opening of a new position.

        Args:
            symbol: Stock ticker
            entry_price: Entry price
            shares: Number of shares
            stop_loss: Stop loss price
            take_profit: Take profit price
            risk_amount: Dollar risk amount
            confidence: Model confidence

        Returns:
            Position object
        """
        position = Position(
            symbol=symbol,
            entry_price=entry_price,
            shares=shares,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            confidence=confidence,
            entry_time=datetime.now(),
            position_value=shares * entry_price,
            current_price=entry_price
        )

        self.open_positions[symbol] = position

        logger.info(
            f"OPENED: {symbol} - {shares} shares @ ${entry_price:.2f}, "
            f"SL: ${stop_loss:.2f}, TP: ${take_profit:.2f}, "
            f"Risk: ${risk_amount:.2f}"
        )

        return position

    def close_position(
        self,
        symbol: str,
        exit_price: float,
        exit_reason: str
    ) -> Optional[Dict]:
        """
        Close a position and record the trade.

        Args:
            symbol: Stock ticker
            exit_price: Exit price
            exit_reason: Reason for exit

        Returns:
            Trade result dictionary
        """
        if symbol not in self.open_positions:
            logger.error(f"Cannot close position: {symbol} not found")
            return None

        position = self.open_positions[symbol]

        # Calculate P&L
        pnl = (exit_price - position.entry_price) * position.shares
        pnl_pct = (pnl / (position.entry_price * position.shares)) * 100

        # Commission on exit
        commission = max(6.0, (exit_price * position.shares) * 0.0008)
        net_pnl = pnl - commission

        # Update account size
        self.account_size += net_pnl
        self.daily_pnl += net_pnl

        # Track peak for drawdown calculation
        if self.account_size > self.peak_balance:
            self.peak_balance = self.account_size

        # Record trade
        trade = {
            'symbol': symbol,
            'entry_price': position.entry_price,
            'exit_price': exit_price,
            'shares': position.shares,
            'entry_time': position.entry_time,
            'exit_time': datetime.now(),
            'pnl': net_pnl,
            'pnl_pct': pnl_pct,
            'risk_amount': position.risk_amount,
            'confidence': position.confidence,
            'exit_reason': exit_reason,
            'win': net_pnl > 0
        }

        self.historical_trades.append(trade)

        # Remove from open positions
        del self.open_positions[symbol]

        logger.info(
            f"CLOSED: {symbol} @ ${exit_price:.2f} - "
            f"P/L: ${net_pnl:+.2f} ({pnl_pct:+.1f}%) - {exit_reason}"
        )

        return trade

    def update_position_price(self, symbol: str, current_price: float):
        """Update current price for a position."""
        if symbol in self.open_positions:
            position = self.open_positions[symbol]
            position.current_price = current_price
            position.unrealized_pnl = (current_price - position.entry_price) * position.shares

    def check_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        Check if position should be stopped out.

        Args:
            symbol: Stock ticker
            current_price: Current market price

        Returns:
            True if stop loss triggered
        """
        if symbol not in self.open_positions:
            return False

        position = self.open_positions[symbol]

        if current_price <= position.stop_loss:
            self.close_position(symbol, current_price, "Stop loss triggered")
            return True

        return False

    def check_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        Check if position should take profit.

        Args:
            symbol: Stock ticker
            current_price: Current market price

        Returns:
            True if take profit triggered
        """
        if symbol not in self.open_positions:
            return False

        position = self.open_positions[symbol]

        if current_price >= position.take_profit:
            self.close_position(symbol, current_price, "Take profit hit")
            return True

        return False

    def get_statistics(self) -> Dict:
        """
        Calculate comprehensive trading statistics.

        Returns:
            Dictionary of performance metrics including IC
        """
        if not self.historical_trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'profit_factor': 0.0,
                'total_pnl': 0.0,
                'account_return': 0.0,
                'sharpe_ratio': 0.0,
                'information_coefficient': 0.0
            }

        wins = [t for t in self.historical_trades if t['win']]
        losses = [t for t in self.historical_trades if not t['win']]

        total_pnl = sum(t['pnl'] for t in self.historical_trades)

        # Calculate starting balance (work backwards from current account size)
        starting_balance = self.account_size - total_pnl
        account_return = total_pnl / starting_balance if starting_balance > 0 else 0.0

        # Calculate Sharpe ratio (annualized)
        returns = [t['pnl_pct'] / 100 for t in self.historical_trades]
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            # Assume ~250 trading days per year
            sharpe_ratio = (avg_return / std_return) * np.sqrt(250) if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0

        # Calculate Information Coefficient (IC)
        # IC = correlation between predicted signal (confidence) and actual outcome
        if len(self.historical_trades) >= 3:
            confidences = [t['confidence'] for t in self.historical_trades]
            outcomes = [1 if t['win'] else 0 for t in self.historical_trades]

            # Spearman correlation (rank-based, more robust)
            try:
                ic, p_value = spearmanr(confidences, outcomes)
                if np.isnan(ic):
                    ic = 0.0
            except:
                ic = 0.0
        else:
            ic = 0.0

        stats = {
            'total_trades': len(self.historical_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': len(wins) / len(self.historical_trades) if self.historical_trades else 0.0,
            'avg_win': np.mean([t['pnl'] for t in wins]) if wins else 0.0,
            'avg_loss': np.mean([t['pnl'] for t in losses]) if losses else 0.0,
            'largest_win': max([t['pnl'] for t in wins]) if wins else 0.0,
            'largest_loss': min([t['pnl'] for t in losses]) if losses else 0.0,
            'profit_factor': abs(sum(t['pnl'] for t in wins) / sum(t['pnl'] for t in losses)) if losses and sum(t['pnl'] for t in losses) != 0 else 0.0,
            'total_pnl': total_pnl,
            'account_return': account_return,
            'sharpe_ratio': sharpe_ratio,
            'information_coefficient': ic,
            'account_size': self.account_size,
            'starting_balance': starting_balance,
            'peak_balance': self.peak_balance,
            'current_drawdown': self.get_max_drawdown(),
            'daily_drawdown': self.get_daily_drawdown(),
            'open_positions': len(self.open_positions),
            'portfolio_heat': self.get_portfolio_heat()
        }

        return stats

    def reset_daily_tracking(self):
        """Reset daily tracking variables (call at market open)."""
        self.starting_daily_balance = self.account_size
        self.daily_pnl = 0.0
        logger.info(f"Daily tracking reset. Starting balance: ${self.account_size:,.2f}")


class ATRStopLossCalculator:
    """
    Calculate stop-loss and take-profit using Average True Range (ATR).
    Volatility-based stops that adapt to market conditions.
    """

    @staticmethod
    def calculate_stops(
        entry_price: float,
        atr: float,
        direction: str = 'long',
        atr_multiplier_stop: float = 2.0,
        risk_reward_ratio: float = 2.0
    ) -> tuple:
        """
        Calculate stop-loss and take-profit based on ATR.

        Args:
            entry_price: Entry price for the trade
            atr: Average True Range value
            direction: 'long' or 'short'
            atr_multiplier_stop: ATR multiplier for stop loss (default: 2.0)
            risk_reward_ratio: Risk/reward ratio for take profit (default: 2.0)

        Returns:
            (stop_loss_price, take_profit_price)

        Example:
            entry = 45.00
            atr = 1.50
            stop, tp = ATRStopLossCalculator.calculate_stops(entry, atr)
            # stop = 42.00 (45 - 2*1.5)
            # tp = 51.00 (45 + 2*2*1.5)
        """
        if direction.lower() == 'long':
            # Long position
            stop_loss = entry_price - (atr * atr_multiplier_stop)
            take_profit = entry_price + (atr * atr_multiplier_stop * risk_reward_ratio)
        else:
            # Short position
            stop_loss = entry_price + (atr * atr_multiplier_stop)
            take_profit = entry_price - (atr * atr_multiplier_stop * risk_reward_ratio)

        return stop_loss, take_profit

    @staticmethod
    def calculate_atr(high_prices: list, low_prices: list, close_prices: list, period: int = 14) -> float:
        """
        Calculate Average True Range.

        Args:
            high_prices: List of high prices
            low_prices: List of low prices
            close_prices: List of close prices
            period: ATR period (default: 14)

        Returns:
            ATR value

        Example:
            highs = [46.5, 47.0, 46.8, ...]
            lows = [45.0, 45.5, 45.2, ...]
            closes = [46.0, 46.5, 46.3, ...]
            atr = ATRStopLossCalculator.calculate_atr(highs, lows, closes)
        """
        if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
            logger.warning(f"Insufficient data for ATR calculation (need {period} periods)")
            return 0.0

        true_ranges = []

        for i in range(1, len(close_prices)):
            high = high_prices[i]
            low = low_prices[i]
            prev_close = close_prices[i - 1]

            # True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)

        # ATR = average of last 'period' true ranges
        if len(true_ranges) >= period:
            atr = np.mean(true_ranges[-period:])
        else:
            atr = np.mean(true_ranges)

        return atr

    @staticmethod
    def calculate_position_size_with_atr(
        account_size: float,
        entry_price: float,
        atr: float,
        risk_pct: float = 0.02,
        atr_multiplier: float = 2.0
    ) -> tuple:
        """
        Calculate position size based on ATR and risk percentage.

        Args:
            account_size: Total account size
            entry_price: Entry price
            atr: Average True Range
            risk_pct: Risk as percentage of account (default: 0.02 = 2%)
            atr_multiplier: ATR multiplier for stop distance (default: 2.0)

        Returns:
            (shares, stop_loss_price, risk_amount)

        Example:
            shares, stop, risk = ATRStopLossCalculator.calculate_position_size_with_atr(
                account_size=10000,
                entry_price=45.00,
                atr=1.50,
                risk_pct=0.02
            )
            # risk_amount = $200 (2% of $10,000)
            # stop = $42.00 (45 - 2*1.5)
            # shares = 66 ($200 / $3.00 risk per share)
        """
        # Calculate stop loss based on ATR
        stop_loss = entry_price - (atr * atr_multiplier)

        # Risk per share
        risk_per_share = entry_price - stop_loss

        if risk_per_share <= 0:
            logger.error("Invalid stop loss calculation (risk_per_share <= 0)")
            return 0, stop_loss, 0.0

        # Total risk amount
        risk_amount = account_size * risk_pct

        # Calculate shares
        shares = int(risk_amount / risk_per_share)

        return shares, stop_loss, risk_amount


