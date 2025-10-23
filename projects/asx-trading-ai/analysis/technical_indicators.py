"""
Technical Indicators Module

Calculates technical analysis indicators (RSI, MACD, Moving Averages, ATR)
to confirm news-based trading signals.

Author: Claude Code
Date: 2025-10-10
"""

import sqlite3
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculate technical indicators for stock analysis."""

    def __init__(self, db_path: str):
        """
        Initialize technical indicators calculator.

        Args:
            db_path: Database path
        """
        self.db_path = db_path

    def get_price_history(
        self,
        ticker: str,
        days: int = 60,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get historical price data.

        Args:
            ticker: Stock ticker
            days: Number of days to retrieve
            end_date: End date (defaults to most recent)

        Returns:
            DataFrame with OHLCV data
        """
        conn = sqlite3.connect(self.db_path)

        if end_date:
            query = """
                SELECT date, open, high, low, close, volume
                FROM stock_prices
                WHERE ticker = ?
                  AND date <= ?
                ORDER BY date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(ticker, end_date, days))
        else:
            query = """
                SELECT date, open, high, low, close, volume
                FROM stock_prices
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
            """
            df = pd.read_sql_query(query, conn, params=(ticker, days))

        conn.close()

        if df.empty:
            return df

        # Reverse to chronological order
        df = df.iloc[::-1].reset_index(drop=True)
        df['date'] = pd.to_datetime(df['date'])

        return df

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index.

        Args:
            prices: Price series
            period: RSI period (default 14)

        Returns:
            RSI series
        """
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        Calculate MACD indicator.

        Args:
            prices: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Dictionary with macd, signal, and histogram series
        """
        ema_fast = prices.ewm(span=fast, adjust=False).mean()
        ema_slow = prices.ewm(span=slow, adjust=False).mean()

        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }

    def calculate_moving_averages(
        self,
        prices: pd.Series,
        periods: list = [20, 50]
    ) -> Dict[str, pd.Series]:
        """
        Calculate simple moving averages.

        Args:
            prices: Price series
            periods: List of MA periods

        Returns:
            Dictionary of MA series
        """
        mas = {}
        for period in periods:
            mas[f'ma{period}'] = prices.rolling(window=period).mean()

        return mas

    def calculate_atr(
        self,
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14
    ) -> pd.Series:
        """
        Calculate Average True Range (volatility measure).

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period

        Returns:
            ATR series
        """
        # True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))

        # True Range = max of the three
        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Average True Range
        atr = true_range.rolling(window=period).mean()

        return atr

    def get_technical_analysis(
        self,
        ticker: str,
        as_of_date: Optional[str] = None
    ) -> Dict:
        """
        Get comprehensive technical analysis for a ticker.

        Args:
            ticker: Stock ticker
            as_of_date: Analysis date (defaults to most recent)

        Returns:
            Dictionary with technical indicators and signals
        """
        # Get price history
        prices = self.get_price_history(ticker, days=60, end_date=as_of_date)

        if prices.empty or len(prices) < 30:
            return {
                'error': 'Insufficient price data',
                'has_data': False
            }

        # Calculate indicators
        rsi = self.calculate_rsi(prices['close'])
        macd_data = self.calculate_macd(prices['close'])
        mas = self.calculate_moving_averages(prices['close'], periods=[20, 50])
        atr = self.calculate_atr(prices['high'], prices['low'], prices['close'])

        # Get latest values
        current_price = prices['close'].iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        current_histogram = macd_data['histogram'].iloc[-1]
        current_ma20 = mas['ma20'].iloc[-1]
        current_ma50 = mas['ma50'].iloc[-1]
        current_atr = atr.iloc[-1]

        # Previous values for trend detection
        prev_histogram = macd_data['histogram'].iloc[-2] if len(macd_data['histogram']) > 1 else 0

        # Calculate volatility percentage
        volatility_pct = (current_atr / current_price) * 100 if current_price > 0 else 0

        # Generate signals
        signals = {
            # RSI signals
            'rsi_oversold': current_rsi < 30,
            'rsi_overbought': current_rsi > 70,
            'rsi_neutral': 30 <= current_rsi <= 70,

            # MACD signals
            'macd_bullish': current_macd > current_signal,
            'macd_bearish': current_macd < current_signal,
            'macd_crossover_up': current_histogram > 0 and prev_histogram <= 0,
            'macd_crossover_down': current_histogram < 0 and prev_histogram >= 0,

            # Moving average signals
            'price_above_ma20': current_price > current_ma20,
            'price_above_ma50': current_price > current_ma50,
            'ma20_above_ma50': current_ma20 > current_ma50,  # Uptrend

            # Combined trend
            'uptrend': current_ma20 > current_ma50,
            'downtrend': current_ma20 < current_ma50
        }

        # Overall bullish/bearish assessment
        bullish_count = sum([
            signals['rsi_neutral'] or signals['rsi_oversold'],  # Not overbought
            signals['macd_bullish'],
            signals['price_above_ma20'],
            signals['uptrend']
        ])

        bearish_count = sum([
            signals['rsi_overbought'],
            signals['macd_bearish'],
            not signals['price_above_ma20'],
            signals['downtrend']
        ])

        # Determine overall signal
        if bullish_count >= 3:
            overall_signal = 'BULLISH'
        elif bearish_count >= 3:
            overall_signal = 'BEARISH'
        else:
            overall_signal = 'NEUTRAL'

        return {
            'has_data': True,
            'ticker': ticker,
            'as_of_date': prices['date'].iloc[-1].strftime('%Y-%m-%d'),
            'current_price': round(current_price, 2),

            # Indicator values
            'rsi': round(current_rsi, 2) if not pd.isna(current_rsi) else None,
            'macd': round(current_macd, 4) if not pd.isna(current_macd) else None,
            'macd_signal': round(current_signal, 4) if not pd.isna(current_signal) else None,
            'macd_histogram': round(current_histogram, 4) if not pd.isna(current_histogram) else None,
            'ma20': round(current_ma20, 2) if not pd.isna(current_ma20) else None,
            'ma50': round(current_ma50, 2) if not pd.isna(current_ma50) else None,
            'atr': round(current_atr, 2) if not pd.isna(current_atr) else None,
            'volatility_pct': round(volatility_pct, 2),

            # Signals
            'signals': signals,
            'overall_signal': overall_signal,
            'bullish_score': bullish_count,
            'bearish_score': bearish_count,

            # Recommendations
            'is_bullish': overall_signal == 'BULLISH',
            'is_bearish': overall_signal == 'BEARISH',
            'is_neutral': overall_signal == 'NEUTRAL'
        }

    def should_enter_trade(
        self,
        ticker: str,
        news_sentiment: str,
        as_of_date: Optional[str] = None
    ) -> Dict:
        """
        Determine if technical indicators support entering a trade.

        Args:
            ticker: Stock ticker
            news_sentiment: News sentiment ('positive', 'negative', 'neutral')
            as_of_date: Analysis date

        Returns:
            Dictionary with recommendation and reasoning
        """
        tech = self.get_technical_analysis(ticker, as_of_date)

        if not tech.get('has_data'):
            return {
                'should_enter': False,
                'confidence_adjustment': 0.0,
                'reason': 'Insufficient technical data'
            }

        # Check if news and technicals agree
        news_bullish = news_sentiment == 'positive'
        tech_bullish = tech['is_bullish']
        tech_bearish = tech['is_bearish']

        if news_bullish and tech_bullish:
            # Both agree - strong buy signal
            confidence_boost = 0.15
            reason = f"News and technicals AGREE (bullish). RSI: {tech['rsi']}, MACD bullish, trend up"
            should_enter = True

        elif news_bullish and tech_bearish:
            # Conflict - news positive but technicals negative
            confidence_boost = -0.25
            reason = f"CONFLICT: News bullish but technicals bearish (RSI: {tech['rsi']}, trend down)"
            should_enter = False

        elif news_bullish and tech['is_neutral']:
            # News positive, technicals neutral - weak signal
            confidence_boost = 0.0
            reason = f"News bullish, technicals NEUTRAL (RSI: {tech['rsi']}). Proceed with caution"
            should_enter = True

        else:
            # Other cases (news negative, etc.)
            confidence_boost = 0.0
            reason = "Technical conditions not favorable"
            should_enter = False

        return {
            'should_enter': should_enter,
            'confidence_adjustment': confidence_boost,
            'reason': reason,
            'technical_analysis': tech
        }


def main():
    """Test the technical indicators module."""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 80)
    print("TECHNICAL INDICATORS TEST")
    print("=" * 80 + "\n")

    tech = TechnicalIndicators(config.DATABASE_PATH)

    # Test with a known ticker
    test_ticker = 'BHP'

    print(f"Analyzing {test_ticker}...\n")

    analysis = tech.get_technical_analysis(test_ticker)

    if analysis.get('has_data'):
        print(f"As of: {analysis['as_of_date']}")
        print(f"Current Price: ${analysis['current_price']:.2f}\n")

        print("INDICATORS:")
        print(f"  RSI (14):        {analysis['rsi']:.2f}")
        print(f"  MACD:            {analysis['macd']:.4f}")
        print(f"  MACD Signal:     {analysis['macd_signal']:.4f}")
        print(f"  MACD Histogram:  {analysis['macd_histogram']:.4f}")
        print(f"  MA(20):          ${analysis['ma20']:.2f}")
        print(f"  MA(50):          ${analysis['ma50']:.2f}")
        print(f"  ATR:             ${analysis['atr']:.2f}")
        print(f"  Volatility:      {analysis['volatility_pct']:.2f}%\n")

        print("SIGNALS:")
        signals = analysis['signals']
        print(f"  RSI Oversold:    {signals['rsi_oversold']}")
        print(f"  RSI Overbought:  {signals['rsi_overbought']}")
        print(f"  MACD Bullish:    {signals['macd_bullish']}")
        print(f"  Price > MA20:    {signals['price_above_ma20']}")
        print(f"  Price > MA50:    {signals['price_above_ma50']}")
        print(f"  Uptrend:         {signals['uptrend']}\n")

        print(f"OVERALL SIGNAL: {analysis['overall_signal']}")
        print(f"  Bullish Score: {analysis['bullish_score']}/4")
        print(f"  Bearish Score: {analysis['bearish_score']}/4\n")

        # Test trade entry decision
        print("-" * 80)
        print("TRADE ENTRY DECISION (with positive news):\n")

        decision = tech.should_enter_trade(test_ticker, 'positive')

        print(f"Should Enter: {decision['should_enter']}")
        print(f"Confidence Adjustment: {decision['confidence_adjustment']:+.2f}")
        print(f"Reason: {decision['reason']}")

    else:
        print(f"Error: {analysis.get('error')}")

    print("\n" + "=" * 80 + "\n")


if __name__ == '__main__':
    main()
