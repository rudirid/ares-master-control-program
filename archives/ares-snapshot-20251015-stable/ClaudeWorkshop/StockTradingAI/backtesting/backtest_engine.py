"""
Backtesting Engine for News-Based Trading Strategies

Simulates historical trading based on news sentiment signals.
Includes realistic trading costs, slippage, and position management.

Author: Claude Code
Date: 2025-10-09
"""

import pandas as pd
import numpy as np
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Trade signal types"""
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"
    HOLD = "HOLD"


@dataclass
class TradingConfig:
    """Configuration for backtesting"""
    initial_capital: float = 100000.0  # Starting capital
    commission_pct: float = 0.1  # 0.1% per trade
    slippage_pct: float = 0.05  # 0.05% slippage
    max_position_size: float = 0.2  # Max 20% of portfolio per position
    min_confidence: float = 0.5  # Minimum confidence for signal
    min_sentiment_score: float = 0.2  # Minimum abs(sentiment) for signal
    holding_period_days: int = 7  # How long to hold positions
    allow_shorting: bool = False  # Allow short selling


@dataclass
class Trade:
    """Represents a single trade"""
    trade_id: int
    ticker: str
    signal_type: SignalType
    entry_date: str
    entry_price: float
    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    shares: int = 0
    commission: float = 0.0
    slippage: float = 0.0
    profit_loss: Optional[float] = None
    return_pct: Optional[float] = None
    article_id: Optional[int] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    confidence: Optional[float] = None
    reason: str = ""


@dataclass
class PortfolioState:
    """Current portfolio state"""
    cash: float
    positions: Dict[str, Trade] = field(default_factory=dict)  # ticker -> Trade
    closed_trades: List[Trade] = field(default_factory=list)
    total_value: float = 0.0


class BacktestEngine:
    """
    Backtesting engine that simulates trading based on news signals.
    """

    def __init__(self, config: TradingConfig, db_path: str):
        """
        Initialize the backtesting engine.

        Args:
            config: Trading configuration
            db_path: Path to SQLite database
        """
        self.config = config
        self.db_path = db_path
        self.portfolio = PortfolioState(cash=config.initial_capital)
        self.trade_counter = 0
        self.trade_log = []

    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Load news impact analysis data.

        Args:
            csv_path: Path to news impact CSV

        Returns:
            DataFrame with news and price data
        """
        df = pd.read_csv(csv_path)
        df['article_date'] = pd.to_datetime(df['article_date'])
        df = df.sort_values('article_date').reset_index(drop=True)

        logger.info(f"Loaded {len(df)} articles for backtesting")
        return df

    def get_price(self, ticker: str, date: str, offset_days: int = 0) -> Optional[float]:
        """
        Get stock price for a ticker on a given date.

        Args:
            ticker: Stock ticker
            date: Date string
            offset_days: Days to offset (positive = future, negative = past)

        Returns:
            Close price or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            target_date = pd.to_datetime(date) + timedelta(days=offset_days)
            target_date_str = target_date.strftime('%Y-%m-%d')

            query = """
                SELECT close FROM stock_prices
                WHERE ticker = ? AND date >= ?
                ORDER BY date ASC
                LIMIT 1
            """

            result = pd.read_sql_query(query, conn, params=(ticker, target_date_str))
            conn.close()

            if len(result) > 0:
                return float(result['close'].iloc[0])
            return None

        except Exception as e:
            logger.error(f"Error getting price for {ticker} on {date}: {e}")
            return None

    def generate_signal(self, article: pd.Series) -> Tuple[SignalType, str]:
        """
        Generate trading signal from article sentiment.

        Args:
            article: Article data row

        Returns:
            Tuple of (signal_type, reason)
        """
        sentiment = article['sentiment']
        score = article['sentiment_score']
        confidence = article['confidence']

        # Check minimum thresholds
        if confidence < self.config.min_confidence:
            return SignalType.HOLD, f"Confidence too low: {confidence:.2f}"

        if abs(score) < self.config.min_sentiment_score:
            return SignalType.HOLD, f"Sentiment score too weak: {score:.2f}"

        # Generate signal based on sentiment
        if sentiment == 'positive' and score > self.config.min_sentiment_score:
            return SignalType.BUY, f"Positive sentiment: {score:.2f} (conf: {confidence:.2f})"

        elif sentiment == 'negative' and score < -self.config.min_sentiment_score:
            if self.config.allow_shorting:
                return SignalType.SHORT, f"Negative sentiment: {score:.2f} (conf: {confidence:.2f})"
            else:
                return SignalType.HOLD, "Negative sentiment but shorting disabled"

        return SignalType.HOLD, f"Neutral or unclear signal"

    def calculate_position_size(self, price: float) -> int:
        """
        Calculate number of shares to buy based on position sizing rules.

        Args:
            price: Stock price

        Returns:
            Number of shares
        """
        max_investment = self.portfolio.cash * self.config.max_position_size
        shares = int(max_investment / price)
        return max(1, shares)  # At least 1 share

    def apply_costs(self, price: float, shares: int, is_buy: bool) -> Tuple[float, float, float]:
        """
        Apply trading costs (commission and slippage).

        Args:
            price: Base price
            shares: Number of shares
            is_buy: True for buy, False for sell

        Returns:
            Tuple of (execution_price, commission, slippage_cost)
        """
        trade_value = price * shares

        # Commission
        commission = trade_value * (self.config.commission_pct / 100)

        # Slippage (worse price for us)
        slippage_factor = self.config.slippage_pct / 100
        if is_buy:
            execution_price = price * (1 + slippage_factor)
        else:
            execution_price = price * (1 - slippage_factor)

        slippage_cost = abs(execution_price - price) * shares

        return execution_price, commission, slippage_cost

    def execute_buy(self, ticker: str, date: str, article: pd.Series) -> Optional[Trade]:
        """
        Execute a buy trade.

        Args:
            ticker: Stock ticker
            date: Trade date
            article: Article that generated signal

        Returns:
            Trade object or None if failed
        """
        # Get entry price
        price = self.get_price(ticker, date, offset_days=1)  # Next day's price
        if price is None:
            logger.warning(f"No price data for {ticker} on {date}")
            return None

        # Calculate position size
        shares = self.calculate_position_size(price)

        # Apply costs
        execution_price, commission, slippage = self.apply_costs(price, shares, is_buy=True)

        total_cost = (execution_price * shares) + commission

        # Check if we have enough cash
        if total_cost > self.portfolio.cash:
            logger.debug(f"Insufficient cash for {ticker}: need ${total_cost:.2f}, have ${self.portfolio.cash:.2f}")
            return None

        # Execute trade
        self.trade_counter += 1
        trade = Trade(
            trade_id=self.trade_counter,
            ticker=ticker,
            signal_type=SignalType.BUY,
            entry_date=date,
            entry_price=execution_price,
            shares=shares,
            commission=commission,
            slippage=slippage,
            article_id=article.get('article_id'),
            sentiment=article.get('sentiment'),
            sentiment_score=article.get('sentiment_score'),
            confidence=article.get('confidence'),
            reason=f"Buy signal from {article.get('source')} article"
        )

        # Update portfolio
        self.portfolio.cash -= total_cost
        self.portfolio.positions[ticker] = trade

        self.trade_log.append({
            'date': date,
            'action': 'BUY',
            'ticker': ticker,
            'shares': shares,
            'price': execution_price,
            'cost': total_cost,
            'cash_remaining': self.portfolio.cash
        })

        logger.info(f"BUY {shares} shares of {ticker} at ${execution_price:.2f}")

        return trade

    def close_position(self, ticker: str, date: str, reason: str = "") -> Optional[Trade]:
        """
        Close an existing position.

        Args:
            ticker: Stock ticker
            date: Exit date
            reason: Reason for closing

        Returns:
            Completed trade or None
        """
        if ticker not in self.portfolio.positions:
            return None

        trade = self.portfolio.positions[ticker]

        # Get exit price
        exit_price = self.get_price(ticker, date, offset_days=0)
        if exit_price is None:
            logger.warning(f"No exit price for {ticker} on {date}")
            return None

        # Apply exit costs
        execution_price, commission, slippage = self.apply_costs(
            exit_price, trade.shares, is_buy=False
        )

        # Calculate profit/loss
        proceeds = (execution_price * trade.shares) - commission
        cost_basis = (trade.entry_price * trade.shares) + trade.commission
        profit_loss = proceeds - cost_basis
        return_pct = (profit_loss / cost_basis) * 100

        # Update trade
        trade.exit_date = date
        trade.exit_price = execution_price
        trade.commission += commission
        trade.slippage += slippage
        trade.profit_loss = profit_loss
        trade.return_pct = return_pct

        # Update portfolio
        self.portfolio.cash += proceeds
        del self.portfolio.positions[ticker]
        self.portfolio.closed_trades.append(trade)

        self.trade_log.append({
            'date': date,
            'action': 'SELL',
            'ticker': ticker,
            'shares': trade.shares,
            'price': execution_price,
            'proceeds': proceeds,
            'profit_loss': profit_loss,
            'return_pct': return_pct,
            'cash_after': self.portfolio.cash,
            'reason': reason
        })

        logger.info(f"SELL {trade.shares} shares of {ticker} at ${execution_price:.2f} - P/L: ${profit_loss:.2f} ({return_pct:+.2f}%)")

        return trade

    def check_position_exits(self, current_date: str):
        """
        Check if any positions should be closed based on holding period.

        Args:
            current_date: Current backtest date
        """
        current_dt = pd.to_datetime(current_date)
        positions_to_close = []

        for ticker, trade in self.portfolio.positions.items():
            entry_dt = pd.to_datetime(trade.entry_date)
            days_held = (current_dt - entry_dt).days

            if days_held >= self.config.holding_period_days:
                positions_to_close.append(ticker)

        for ticker in positions_to_close:
            self.close_position(ticker, current_date, reason=f"Holding period ({self.config.holding_period_days} days) reached")

    def run_backtest(self, csv_path: str) -> Dict:
        """
        Run the backtest simulation.

        Args:
            csv_path: Path to news impact analysis CSV

        Returns:
            Dictionary with backtest results
        """
        logger.info("=" * 70)
        logger.info("Starting Backtest")
        logger.info("=" * 70)

        # Load data
        df = self.load_data(csv_path)

        # Filter out articles without price data
        df = df[df['price_change_pct_1d'].notna()].reset_index(drop=True)

        logger.info(f"Articles with price data: {len(df)}")

        # Check if we have any valid data
        if len(df) == 0:
            logger.warning("No articles with price data found")
            return {
                'total_trades': 0,
                'error': 'No articles with price data. Articles need to be at least 7 days old for full analysis.'
            }

        logger.info(f"Date range: {df['article_date'].min()} to {df['article_date'].max()}")

        # Replay day by day
        for idx, article in df.iterrows():
            date = article['article_date'].strftime('%Y-%m-%d')
            ticker = article['ticker']

            # Check exits first
            self.check_position_exits(date)

            # Skip if we already have a position in this ticker
            if ticker in self.portfolio.positions:
                continue

            # Generate signal
            signal, reason = self.generate_signal(article)

            # Execute trade if signal
            if signal == SignalType.BUY:
                self.execute_buy(ticker, date, article)
            elif signal == SignalType.SHORT and self.config.allow_shorting:
                # Short selling logic (simplified for now)
                pass

        # Close all remaining positions at end
        final_date = df['article_date'].max().strftime('%Y-%m-%d')
        for ticker in list(self.portfolio.positions.keys()):
            self.close_position(ticker, final_date, reason="End of backtest")

        # Calculate final metrics
        results = self.calculate_metrics()

        logger.info("=" * 70)
        logger.info("Backtest Complete")
        logger.info("=" * 70)

        return results

    def calculate_metrics(self) -> Dict:
        """
        Calculate performance metrics.

        Returns:
            Dictionary with performance metrics
        """
        trades = self.portfolio.closed_trades

        if len(trades) == 0:
            return {
                'total_trades': 0,
                'error': 'No trades executed'
            }

        # Basic metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.profit_loss > 0]
        losing_trades = [t for t in trades if t.profit_loss <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        # Profit/Loss
        total_pnl = sum(t.profit_loss for t in trades)
        avg_win = np.mean([t.profit_loss for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t.profit_loss for t in losing_trades]) if losing_trades else 0

        # Returns
        final_value = self.portfolio.cash
        total_return = ((final_value - self.config.initial_capital) / self.config.initial_capital) * 100

        # Drawdown
        equity_curve = [self.config.initial_capital]
        running_capital = self.config.initial_capital

        for trade in sorted(trades, key=lambda t: t.exit_date):
            running_capital += trade.profit_loss
            equity_curve.append(running_capital)

        peak = equity_curve[0]
        max_drawdown = 0

        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)

        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate * 100, 2),
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'total_return_pct': round(total_return, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'initial_capital': self.config.initial_capital,
            'final_capital': round(final_value, 2),
            'total_commission': round(sum(t.commission for t in trades), 2),
            'total_slippage': round(sum(t.slippage for t in trades), 2)
        }

    def export_trades(self, output_path: str):
        """
        Export trade history to CSV.

        Args:
            output_path: Output file path
        """
        trades_data = []

        for trade in self.portfolio.closed_trades:
            trades_data.append({
                'trade_id': trade.trade_id,
                'ticker': trade.ticker,
                'signal': trade.signal_type.value,
                'entry_date': trade.entry_date,
                'entry_price': trade.entry_price,
                'exit_date': trade.exit_date,
                'exit_price': trade.exit_price,
                'shares': trade.shares,
                'profit_loss': trade.profit_loss,
                'return_pct': trade.return_pct,
                'commission': trade.commission,
                'slippage': trade.slippage,
                'sentiment': trade.sentiment,
                'sentiment_score': trade.sentiment_score,
                'confidence': trade.confidence,
                'reason': trade.reason
            })

        df = pd.DataFrame(trades_data)
        df.to_csv(output_path, index=False)
        logger.info(f"Trades exported to {output_path}")
