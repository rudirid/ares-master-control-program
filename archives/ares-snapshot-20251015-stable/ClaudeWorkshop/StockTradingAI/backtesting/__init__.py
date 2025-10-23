"""
Backtesting Module

Contains classes and utilities for backtesting trading strategies
against historical data.

Author: Claude Code
Date: 2025-10-09
"""

from .backtest_engine import BacktestEngine, TradingConfig, Trade, SignalType
from .benchmark import BenchmarkCalculator

__all__ = [
    'BacktestEngine',
    'TradingConfig',
    'Trade',
    'SignalType',
    'BenchmarkCalculator'
]
