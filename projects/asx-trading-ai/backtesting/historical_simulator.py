"""
Historical Simulator

Simulates live trading on historical data with NO look-ahead bias.
Processes news articles in chronological order as if trading in real-time.

Author: Claude Code
Date: 2025-10-10
"""

import sys
import os
import sqlite3
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.local_sentiment_analyzer import LocalSentimentAnalyzer
from analysis.news_quality_filter import NewsQualityFilter
from analysis.technical_indicators import TechnicalIndicators
from analysis.behavioral_filters import (
    TimeFilter, TimeOfDayFilter, MaterialityFilter, ContrarianSignals
)
from analysis.bayesian_confidence import SignalCombiner
from paper_trading.risk_manager import RiskManager, RiskConfig
from backtesting.backtest_engine import TradingConfig

logger = logging.getLogger(__name__)


@dataclass
class SimulationEvent:
    """Represents a single event in the simulation timeline."""
    timestamp: str
    event_type: str  # NEWS, RECOMMENDATION, ENTRY, EXIT, STOP_LOSS, etc.
    ticker: str
    description: str
    details: Dict = field(default_factory=dict)


@dataclass
class SimulatedPosition:
    """A position in the simulation."""
    position_id: int
    ticker: str
    entry_date: str
    entry_price: float
    shares: int
    position_value: float
    recommendation_confidence: float
    sentiment: str
    sentiment_score: float
    themes: List[str]

    exit_date: Optional[str] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    return_pct: Optional[float] = None
    exit_reason: Optional[str] = None
    days_held: Optional[int] = None


class HistoricalSimulator:
    """
    Simulates live trading on historical data with strict chronological ordering
    and no look-ahead bias.
    """

    def __init__(
        self,
        db_path: str,
        initial_capital: float = 10000.0,
        trading_config: Optional[TradingConfig] = None,
        risk_config: Optional[RiskConfig] = None,
        use_quality_filter: bool = True,
        use_technical_analysis: bool = True,
        use_behavioral_filters: bool = True
    ):
        """
        Initialize simulator.

        Args:
            db_path: Database path
            initial_capital: Starting capital
            trading_config: Trading configuration
            risk_config: Risk management configuration
            use_quality_filter: Whether to use news quality filtering
            use_technical_analysis: Whether to use technical analysis confirmation
            use_behavioral_filters: Whether to use behavioral finance filters
        """
        self.db_path = db_path
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Default configs
        if trading_config is None:
            trading_config = TradingConfig(
                initial_capital=initial_capital,
                commission_pct=0.1,
                slippage_pct=0.05,
                max_position_size=0.2,
                min_confidence=0.7,  # Risk management requirement
                min_sentiment_score=0.2,
                holding_period_days=7,
                allow_shorting=False
            )

        if risk_config is None:
            risk_config = RiskConfig(
                portfolio_value=initial_capital,
                max_risk_per_trade_pct=2.0,
                stop_loss_pct=5.0,
                max_positions_per_sector=3,
                daily_loss_limit_pct=5.0,
                min_confidence=0.7
            )

        self.trading_config = trading_config
        self.risk_config = risk_config

        # Initialize components
        self.sentiment_analyzer = LocalSentimentAnalyzer()
        self.quality_filter = NewsQualityFilter() if use_quality_filter else None
        self.technical_indicators = TechnicalIndicators(db_path) if use_technical_analysis else None
        self.signal_combiner = SignalCombiner()  # NEW: Bayesian confidence scoring

        # Behavioral finance filters
        # NOTE: In backtest mode (T+1 entry), TIME and TIME-OF-DAY filters are disabled
        # because we're not doing intraday trading. These filters are for real-time mode only.
        if use_behavioral_filters:
            self.time_filter = None  # DISABLED for backtest (not applicable to T+1 trading)
            self.time_of_day_filter = None  # DISABLED for backtest (can't control entry time in historical data)
            self.materiality_filter = MaterialityFilter(min_materiality_score=0.5)  # ENABLED - filter noise
            self.contrarian_signals = ContrarianSignals(extreme_threshold=0.85)  # ENABLED - fade extremes
        else:
            self.time_filter = None
            self.time_of_day_filter = None
            self.materiality_filter = None
            self.contrarian_signals = None

        # Simulation state
        self.active_positions: Dict[str, SimulatedPosition] = {}
        self.closed_positions: List[SimulatedPosition] = []
        self.events: List[SimulationEvent] = []
        self.position_counter = 0

        # Circuit breaker state
        self.circuit_breaker_active = False
        self.daily_pnl = 0.0
        self.current_date = None

    def load_historical_news(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Load historical news in chronological order from both news_articles and asx_announcements.
        Only includes tickers that have price data available.

        Args:
            limit: Maximum number of articles to load

        Returns:
            DataFrame of news articles sorted by date
        """
        conn = sqlite3.connect(self.db_path)

        # Query both news_articles and asx_announcements and combine them
        # Only include tickers that have price data
        query = """
            WITH tickers_with_prices AS (
                SELECT DISTINCT ticker FROM stock_prices
            )
            SELECT
                'NEWS' as source_table,
                n.ticker,
                n.source,
                n.title,
                n.content,
                COALESCE(n.datetime, n.created_at) as created_at,
                n.url,
                NULL as announcement_type,
                0 as price_sensitive
            FROM news_articles n
            INNER JOIN tickers_with_prices t ON n.ticker = t.ticker
            WHERE n.ticker IS NOT NULL
              AND COALESCE(n.datetime, n.created_at) IS NOT NULL

            UNION ALL

            SELECT
                'ANNOUNCEMENT' as source_table,
                a.ticker,
                'ASX' as source,
                a.title,
                a.content,
                COALESCE(a.datetime, a.created_at) as created_at,
                a.url,
                a.announcement_type,
                a.price_sensitive
            FROM asx_announcements a
            INNER JOIN tickers_with_prices t ON a.ticker = t.ticker
            WHERE a.ticker IS NOT NULL
              AND a.title IS NOT NULL
              AND COALESCE(a.datetime, a.created_at) IS NOT NULL

            ORDER BY created_at ASC
        """

        if limit:
            query = f"SELECT * FROM ({query}) LIMIT {limit}"

        df = pd.read_sql_query(query, conn)
        conn.close()

        df['created_at'] = pd.to_datetime(df['created_at'])

        logger.info(f"Loaded {len(df)} historical articles (news + announcements) for tickers with price data")

        return df

    def get_price_at_date(
        self,
        ticker: str,
        target_date: str,
        days_forward: int = 0
    ) -> Optional[float]:
        """
        Get stock price at or after a specific date (NO LOOK-BACK).

        Args:
            ticker: Stock ticker
            target_date: Target date
            days_forward: Days to look forward (for exit prices)

        Returns:
            Price or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate target date with offset
        target_dt = pd.to_datetime(target_date) + timedelta(days=days_forward)
        target_str = target_dt.strftime('%Y-%m-%d')

        # Get first available price ON OR AFTER target date
        cursor.execute("""
            SELECT close, date FROM stock_prices
            WHERE ticker = ? AND date >= ?
            ORDER BY date ASC
            LIMIT 1
        """, (ticker, target_str))

        row = cursor.fetchone()
        conn.close()

        if row:
            return float(row[0])
        return None

    def analyze_news(self, article: pd.Series) -> Tuple[str, float, float, List[str]]:
        """
        Analyze news article for sentiment.

        Args:
            article: Article data

        Returns:
            Tuple of (sentiment, score, confidence, themes)
        """
        analysis = self.sentiment_analyzer.analyze_article(
            title=article['title'],
            content=article['content'] or '',
            ticker=article['ticker']
        )

        return (
            analysis['sentiment'],
            analysis['sentiment_score'],
            analysis['confidence'],
            analysis.get('themes', [])
        )

    def calculate_position_size(
        self,
        entry_price: float,
        confidence: float
    ) -> Tuple[int, float]:
        """
        Calculate position size with risk management.

        Args:
            entry_price: Entry price
            confidence: Recommendation confidence

        Returns:
            Tuple of (shares, position_value)
        """
        # Max risk per trade (2%)
        max_risk = self.current_capital * (self.risk_config.max_risk_per_trade_pct / 100)

        # Position size based on stop loss
        base_position_value = max_risk / (self.risk_config.stop_loss_pct / 100)

        # Adjust for confidence
        confidence_factor = min(confidence / self.risk_config.min_confidence, 1.0)
        adjusted_value = base_position_value * confidence_factor

        # Also respect max position size from trading config
        max_by_portfolio = self.current_capital * self.trading_config.max_position_size
        final_value = min(adjusted_value, max_by_portfolio)

        # Calculate shares
        shares = int(final_value / entry_price)
        actual_value = shares * entry_price

        return shares, actual_value

    def can_enter_position(
        self,
        ticker: str,
        confidence: float,
        sentiment_score: float
    ) -> Tuple[bool, str]:
        """
        Check if we can enter a position (risk management).

        Args:
            ticker: Stock ticker
            confidence: Confidence score
            sentiment_score: Sentiment score

        Returns:
            Tuple of (can_enter, reason)
        """
        # Circuit breaker check
        if self.circuit_breaker_active:
            return False, "Circuit breaker active"

        # Confidence threshold
        if confidence < self.risk_config.min_confidence:
            return False, f"Confidence {confidence:.2f} below {self.risk_config.min_confidence}"

        # Sentiment threshold
        if abs(sentiment_score) < self.trading_config.min_sentiment_score:
            return False, f"Sentiment {abs(sentiment_score):.2f} too weak"

        # Already have position in this ticker
        if ticker in self.active_positions:
            return False, f"Already have position in {ticker}"

        # Check we have enough capital
        if self.current_capital < 100:  # Minimum $100 to trade
            return False, "Insufficient capital"

        return True, "Passed risk checks"

    def enter_position(
        self,
        ticker: str,
        entry_date: str,
        entry_price: float,
        confidence: float,
        sentiment: str,
        sentiment_score: float,
        themes: List[str]
    ) -> Optional[SimulatedPosition]:
        """
        Enter a new position.

        Args:
            ticker: Stock ticker
            entry_date: Entry date
            entry_price: Entry price
            confidence: Confidence score
            sentiment: Sentiment
            sentiment_score: Sentiment score
            themes: News themes

        Returns:
            Position object or None
        """
        # Calculate position size
        shares, position_value = self.calculate_position_size(entry_price, confidence)

        if shares == 0:
            return None

        # Apply trading costs
        commission = position_value * (self.trading_config.commission_pct / 100)
        slippage_factor = self.trading_config.slippage_pct / 100
        execution_price = entry_price * (1 + slippage_factor)

        total_cost = (execution_price * shares) + commission

        if total_cost > self.current_capital:
            return None

        # Create position
        self.position_counter += 1
        position = SimulatedPosition(
            position_id=self.position_counter,
            ticker=ticker,
            entry_date=entry_date,
            entry_price=execution_price,
            shares=shares,
            position_value=position_value,
            recommendation_confidence=confidence,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            themes=themes
        )

        # Update capital
        self.current_capital -= total_cost

        # Add to active positions
        self.active_positions[ticker] = position

        # Log event
        self.events.append(SimulationEvent(
            timestamp=entry_date,
            event_type='ENTRY',
            ticker=ticker,
            description=f"BUY {shares} shares at ${execution_price:.2f}",
            details={
                'shares': shares,
                'price': execution_price,
                'cost': total_cost,
                'confidence': confidence,
                'sentiment': sentiment,
                'themes': themes
            }
        ))

        logger.info(f"ENTRY: {ticker} - {shares} shares @ ${execution_price:.2f}")

        return position

    def exit_position(
        self,
        ticker: str,
        exit_date: str,
        exit_price: float,
        reason: str
    ) -> Optional[SimulatedPosition]:
        """
        Exit a position.

        Args:
            ticker: Stock ticker
            exit_date: Exit date
            exit_price: Exit price
            reason: Exit reason

        Returns:
            Closed position or None
        """
        if ticker not in self.active_positions:
            return None

        position = self.active_positions[ticker]

        # Apply exit costs
        commission = (exit_price * position.shares) * (self.trading_config.commission_pct / 100)
        slippage_factor = self.trading_config.slippage_pct / 100
        execution_price = exit_price * (1 - slippage_factor)

        # Calculate P/L
        proceeds = (execution_price * position.shares) - commission
        cost_basis = (position.entry_price * position.shares)
        profit_loss = proceeds - cost_basis
        return_pct = (profit_loss / cost_basis) * 100

        # Calculate days held
        entry_dt = pd.to_datetime(position.entry_date)
        exit_dt = pd.to_datetime(exit_date)
        days_held = (exit_dt - entry_dt).days

        # Update position
        position.exit_date = exit_date
        position.exit_price = execution_price
        position.profit_loss = profit_loss
        position.return_pct = return_pct
        position.exit_reason = reason
        position.days_held = days_held

        # Update capital
        self.current_capital += proceeds

        # Track daily P/L for circuit breaker
        if exit_date == self.current_date:
            self.daily_pnl += return_pct

        # Move to closed
        del self.active_positions[ticker]
        self.closed_positions.append(position)

        # Log event
        self.events.append(SimulationEvent(
            timestamp=exit_date,
            event_type='EXIT',
            ticker=ticker,
            description=f"SELL {position.shares} shares at ${execution_price:.2f} - {reason}",
            details={
                'shares': position.shares,
                'price': execution_price,
                'proceeds': proceeds,
                'profit_loss': profit_loss,
                'return_pct': return_pct,
                'days_held': days_held,
                'reason': reason
            }
        ))

        logger.info(
            f"EXIT: {ticker} - P/L: ${profit_loss:+.2f} ({return_pct:+.2f}%) - {reason}"
        )

        return position

    def check_stop_loss(
        self,
        ticker: str,
        current_date: str,
        current_price: float
    ) -> bool:
        """
        Check if position should be stopped out.

        Args:
            ticker: Stock ticker
            current_date: Current date
            current_price: Current price

        Returns:
            True if stop loss triggered
        """
        if ticker not in self.active_positions:
            return False

        position = self.active_positions[ticker]

        # Calculate current loss
        loss_pct = ((current_price - position.entry_price) / position.entry_price) * 100

        if loss_pct <= -self.risk_config.stop_loss_pct:
            self.exit_position(ticker, current_date, current_price, "Stop loss triggered")
            return True

        return False

    def check_holding_period(
        self,
        ticker: str,
        current_date: str,
        current_price: float
    ) -> bool:
        """
        Check if holding period is reached.

        Args:
            ticker: Stock ticker
            current_date: Current date
            current_price: Current price

        Returns:
            True if should exit
        """
        if ticker not in self.active_positions:
            return False

        position = self.active_positions[ticker]

        entry_dt = pd.to_datetime(position.entry_date)
        current_dt = pd.to_datetime(current_date)
        days_held = (current_dt - entry_dt).days

        if days_held >= self.trading_config.holding_period_days:
            self.exit_position(ticker, current_date, current_price, "Holding period reached")
            return True

        return False

    def check_circuit_breaker(self, current_date: str):
        """
        Check if circuit breaker should activate.

        Args:
            current_date: Current date
        """
        # Reset daily P/L on new day
        if current_date != self.current_date:
            self.daily_pnl = 0.0
            self.circuit_breaker_active = False
            self.current_date = current_date

        # Check threshold
        if self.daily_pnl <= -self.risk_config.daily_loss_limit_pct:
            if not self.circuit_breaker_active:
                self.circuit_breaker_active = True
                self.events.append(SimulationEvent(
                    timestamp=current_date,
                    event_type='CIRCUIT_BREAKER',
                    ticker='',
                    description=f"Circuit breaker activated - Daily loss: {self.daily_pnl:.2f}%",
                    details={'daily_loss': self.daily_pnl}
                ))
                logger.warning(f"CIRCUIT BREAKER ACTIVATED: {self.daily_pnl:.2f}%")

    def run_simulation(
        self,
        max_articles: int = 300
    ) -> Dict:
        """
        Run the full simulation.

        Args:
            max_articles: Maximum articles to process

        Returns:
            Simulation results dictionary
        """
        logger.info("=" * 70)
        logger.info("Starting Historical Simulation")
        logger.info(f"Initial Capital: ${self.initial_capital:,.2f}")
        logger.info(f"Max Articles: {max_articles}")
        logger.info("=" * 70)

        # Load historical news
        news_df = self.load_historical_news(limit=max_articles)

        if len(news_df) == 0:
            return {'error': 'No historical news data found'}

        # Process each article chronologically
        for idx, article in news_df.iterrows():
            article_date = article['created_at'].strftime('%Y-%m-%d')

            # Log news event
            self.events.append(SimulationEvent(
                timestamp=article_date,
                event_type='NEWS',
                ticker=article['ticker'],
                description=article['title'][:100],
                details={'source': article['source']}
            ))

            # Check circuit breaker daily
            self.check_circuit_breaker(article_date)

            # Update active positions (check stop loss and holding period)
            for ticker in list(self.active_positions.keys()):
                current_price = self.get_price_at_date(ticker, article_date)
                if current_price:
                    self.check_stop_loss(ticker, article_date, current_price)
                    self.check_holding_period(ticker, article_date, current_price)

            # Apply quality filter first
            if self.quality_filter:
                quality_assessment = self.quality_filter.assess_quality(
                    source=article['source'],
                    announcement_type=article.get('announcement_type'),
                    title=article['title'],
                    content=article['content'],
                    price_sensitive=article.get('price_sensitive', False)
                )

                if not quality_assessment['passes_filter']:
                    self.events.append(SimulationEvent(
                        timestamp=article_date,
                        event_type='FILTERED',
                        ticker=article['ticker'],
                        description=f"Filtered: {article['title'][:60]}... (quality: {quality_assessment['quality_score']:.2f})",
                        details={'quality_score': quality_assessment['quality_score'], 'reasons': quality_assessment['reasons']}
                    ))
                    continue  # Skip low-quality news

            # Behavioral Finance Filters
            behavioral_adjustments = 0.0  # Track cumulative confidence adjustments

            # 1. TIME FILTER: Reject stale announcements
            if self.time_filter:
                announcement_time = article['created_at']
                # Simulate real-time decision: would we trade this now?
                # For backtesting, use the article date as "current time"
                simulation_time = announcement_time + timedelta(minutes=5)  # Assume we see it 5 min later

                tradeable, reason, time_adj = self.time_filter.is_tradeable_by_time(
                    announcement_time, simulation_time
                )

                if not tradeable:
                    self.events.append(SimulationEvent(
                        timestamp=article_date,
                        event_type='TIME_FILTERED',
                        ticker=article['ticker'],
                        description=f"Time filter rejected: {reason}",
                        details={'reason': reason}
                    ))
                    continue

                behavioral_adjustments += time_adj

            # 2. MATERIALITY FILTER: Only trade material announcements
            if self.materiality_filter:
                is_material, reason, mat_score = self.materiality_filter.assess_materiality(
                    announcement_type=article.get('announcement_type', ''),
                    title=article['title'],
                    content=article['content'] or '',
                    price_sensitive=article.get('price_sensitive', False)
                )

                if not is_material:
                    self.events.append(SimulationEvent(
                        timestamp=article_date,
                        event_type='MATERIALITY_FILTERED',
                        ticker=article['ticker'],
                        description=f"Materiality filter rejected: {reason}",
                        details={'materiality_score': mat_score}
                    ))
                    continue

            # 3. TIME-OF-DAY FILTER: Check optimal trading hours
            if self.time_of_day_filter:
                # Entry would be T+1, so check if that's during optimal hours
                entry_time = article['created_at'] + timedelta(days=1)
                entry_time = entry_time.replace(hour=10, minute=30)  # Assume entry at 10:30 AM next day

                is_optimal, reason, tod_adj = self.time_of_day_filter.is_optimal_time(entry_time)

                if not is_optimal:
                    self.events.append(SimulationEvent(
                        timestamp=article_date,
                        event_type='TOD_FILTERED',
                        ticker=article['ticker'],
                        description=f"Time-of-day filter rejected: {reason}",
                        details={'reason': reason}
                    ))
                    continue

                behavioral_adjustments += tod_adj

            # Analyze news
            sentiment, score, base_confidence, themes = self.analyze_news(article)

            # Generate recommendation (skip neutrals and negative)
            if sentiment == 'positive' and score > 0:
                action = 'BUY'
            elif sentiment == 'negative' and score < 0:
                action = 'SELL/AVOID'  # We don't short in this sim
                continue  # Skip negative for now
            else:
                continue  # Neutral

            # 4. GET RECENT PRICE CHANGE FOR CONTRARIAN SIGNALS
            entry_price_temp = self.get_price_at_date(article['ticker'], article_date, days_forward=1)
            recent_price = self.get_price_at_date(article['ticker'], article_date, days_forward=-5)

            recent_price_change = None
            if entry_price_temp and recent_price:
                recent_price_change = ((entry_price_temp - recent_price) / recent_price) * 100

            # 5. TECHNICAL ANALYSIS
            tech_indicators = None
            if self.technical_indicators:
                tech_decision = self.technical_indicators.should_enter_trade(
                    article['ticker'],
                    sentiment,
                    as_of_date=article_date
                )

                # Skip only if we truly have no technical data
                if 'Insufficient technical data' in tech_decision['reason']:
                    self.events.append(SimulationEvent(
                        timestamp=article_date,
                        event_type='TECH_NO_DATA',
                        ticker=article['ticker'],
                        description=f"No technical data available: {tech_decision['reason']}",
                        details={'reason': tech_decision['reason']}
                    ))
                    continue
                else:
                    tech_indicators = {
                        'rsi': tech_decision.get('rsi'),
                        'macd': tech_decision.get('macd'),
                        'ma_trend': tech_decision.get('ma_trend'),
                        'confidence_adjustment': tech_decision['confidence_adjustment']
                    }

            # 6. BAYESIAN CONFIDENCE COMBINATION (REPLACES ADDITIVE MODEL)
            # For backtesting (T+1 entry), we don't have real-time timestamps
            # Assume announcement age = 0 (instant) and time-of-day = 10:30 AM
            announcement_age_minutes = 0.0  # Backtest assumes instant signal
            current_time_aest = '10:30:00'  # Assume optimal entry time

            confidence, breakdown = self.signal_combiner.compute_confidence(
                sentiment_score=score,
                announcement_age_minutes=announcement_age_minutes,
                current_time_aest=current_time_aest,
                technical_indicators=tech_indicators,
                is_material=is_material,  # From materiality filter above
                recent_price_change=recent_price_change
            )

            # Log recommendation with Bayesian confidence
            self.events.append(SimulationEvent(
                timestamp=article_date,
                event_type='RECOMMENDATION',
                ticker=article['ticker'],
                description=f"{action} recommendation - Confidence: {confidence:.3f} (Bayesian)",
                details={
                    'action': action,
                    'confidence': confidence,
                    'sentiment': sentiment,
                    'score': score,
                    'themes': themes,
                    'bayesian_breakdown': breakdown
                }
            ))

            # Check if we can enter
            can_enter, reason = self.can_enter_position(
                article['ticker'],
                confidence,
                score
            )

            if not can_enter:
                self.events.append(SimulationEvent(
                    timestamp=article_date,
                    event_type='REJECTED',
                    ticker=article['ticker'],
                    description=f"Position rejected: {reason}",
                    details={'reason': reason}
                ))
                continue

            # Get entry price (next day)
            entry_price = self.get_price_at_date(article['ticker'], article_date, days_forward=1)

            if not entry_price:
                continue

            # Enter position
            self.enter_position(
                ticker=article['ticker'],
                entry_date=article_date,
                entry_price=entry_price,
                confidence=confidence,
                sentiment=sentiment,
                sentiment_score=score,
                themes=themes
            )

        # Close all remaining positions
        final_date = news_df['created_at'].max().strftime('%Y-%m-%d')
        for ticker in list(self.active_positions.keys()):
            exit_price = self.get_price_at_date(ticker, final_date)
            if exit_price:
                self.exit_position(ticker, final_date, exit_price, "End of simulation")

        # Calculate final metrics
        results = self.calculate_results()

        logger.info("=" * 70)
        logger.info("Simulation Complete")
        if 'final_capital' in results:
            logger.info(f"Final Capital: ${results['final_capital']:,.2f}")
            logger.info(f"Total Return: {results['total_return_pct']:+.2f}%")
            logger.info(f"Total Trades: {results['total_trades']}")
            logger.info(f"Win Rate: {results['win_rate']:.1f}%")
        else:
            logger.info(f"Total Trades: {results.get('total_trades', 0)}")
        logger.info("=" * 70)

        return results

    def calculate_results(self) -> Dict:
        """
        Calculate simulation results.

        Returns:
            Results dictionary
        """
        total_trades = len(self.closed_positions)

        if total_trades == 0:
            return {
                'initial_capital': self.initial_capital,
                'final_capital': self.current_capital,
                'total_return_pct': 0.0,
                'total_pl': 0.0,
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'max_drawdown_pct': 0.0,
                'total_events': len(self.events),
                'positions': [],
                'events': self.events,
                'error': 'No trades executed'
            }

        winning_trades = [p for p in self.closed_positions if p.profit_loss > 0]
        losing_trades = [p for p in self.closed_positions if p.profit_loss <= 0]

        win_rate = (len(winning_trades) / total_trades) * 100

        total_pnl = sum(p.profit_loss for p in self.closed_positions)
        avg_win = sum(p.profit_loss for p in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(p.profit_loss for p in losing_trades) / len(losing_trades) if losing_trades else 0

        final_capital = self.current_capital
        total_return_pct = ((final_capital - self.initial_capital) / self.initial_capital) * 100

        # Calculate max drawdown
        equity_curve = [self.initial_capital]
        running_capital = self.initial_capital

        for position in sorted(self.closed_positions, key=lambda p: p.exit_date):
            running_capital += position.profit_loss
            equity_curve.append(running_capital)

        peak = equity_curve[0]
        max_drawdown = 0

        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100
            max_drawdown = max(max_drawdown, drawdown)

        return {
            'initial_capital': self.initial_capital,
            'final_capital': round(final_capital, 2),
            'total_return_pct': round(total_return_pct, 2),
            'total_pnl': round(total_pnl, 2),
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': round(win_rate, 1),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'max_drawdown_pct': round(max_drawdown, 2),
            'total_events': len(self.events),
            'positions': self.closed_positions,
            'events': self.events
        }


def main():
    """Test the simulator."""
    import config

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 70)
    print("HISTORICAL SIMULATION TEST")
    print("=" * 70 + "\n")

    simulator = HistoricalSimulator(
        db_path=config.DATABASE_PATH,
        initial_capital=10000.0
    )

    results = simulator.run_simulation(max_articles=50)

    if 'error' not in results:
        print(f"\nFinal Capital: ${results['final_capital']:,.2f}")
        print(f"Total Return: {results['total_return_pct']:+.2f}%")
        print(f"Total Trades: {results['total_trades']}")
        print(f"Win Rate: {results['win_rate']}%")
        print(f"Max Drawdown: {results['max_drawdown_pct']}%")
        print(f"\nTotal Events: {results['total_events']}")


if __name__ == '__main__':
    main()
