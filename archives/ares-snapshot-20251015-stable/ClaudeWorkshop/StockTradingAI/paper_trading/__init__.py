"""
Paper Trading Module

Real-time monitoring and paper trading system for news-based
trading strategies with comprehensive risk management.

Author: Claude Code
Date: 2025-10-09
"""

from .recommendation_engine import RecommendationEngine
from .paper_trader import PaperTrader
from .daily_summary import DailySummaryGenerator
from .scheduler import PaperTradingScheduler
from .risk_manager import RiskManager, RiskConfig

__all__ = [
    'RecommendationEngine',
    'PaperTrader',
    'DailySummaryGenerator',
    'PaperTradingScheduler',
    'RiskManager',
    'RiskConfig'
]
