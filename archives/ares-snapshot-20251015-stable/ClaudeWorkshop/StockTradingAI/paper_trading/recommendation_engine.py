"""
Recommendation Engine for Paper Trading

Analyzes news articles using validated patterns and generates
trade recommendations with confidence scores.

Author: Claude Code
Date: 2025-10-09
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.local_sentiment_analyzer import LocalSentimentAnalyzer
from sentiment.finbert_analyzer import FinBERTSentimentAnalyzer
from analysis.news_quality_filter import NewsQualityFilter
from analysis.bayesian_confidence import SignalCombiner
from utils.asx_trading_hours import ASXTradingHours
from risk.position_sizer import KellyCriterionPositionSizer

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates trade recommendations based on news sentiment and
    validated pattern analysis.
    """

    def __init__(
        self,
        pattern_file: str = 'results/pattern_analysis.json',
        use_quality_filter: bool = True,
        use_finbert: bool = True,
        account_size: float = 10000.0
    ):
        """
        Initialize the recommendation engine.

        Args:
            pattern_file: Path to pattern analysis JSON with validated patterns
            use_quality_filter: Whether to use news quality filtering
            use_finbert: Whether to use FinBERT (True) or keyword sentiment (False)
            account_size: Starting account size for position sizing
        """
        # Sentiment analysis (FinBERT preferred, keyword fallback)
        if use_finbert:
            try:
                self.sentiment_analyzer = FinBERTSentimentAnalyzer()
                self.using_finbert = True
                logger.info("Using FinBERT sentiment analyzer (86-97% accuracy)")
            except Exception as e:
                logger.warning(f"FinBERT unavailable, falling back to keyword analyzer: {e}")
                self.sentiment_analyzer = LocalSentimentAnalyzer()
                self.using_finbert = False
        else:
            self.sentiment_analyzer = LocalSentimentAnalyzer()
            self.using_finbert = False
            logger.info("Using keyword sentiment analyzer (50% accuracy)")

        # Quality filter
        self.quality_filter = NewsQualityFilter() if use_quality_filter else None

        # Bayesian confidence scoring
        self.signal_combiner = SignalCombiner()

        # Position sizing with Kelly Criterion
        self.position_sizer = KellyCriterionPositionSizer(
            account_size=account_size,
            kelly_fraction=0.25,
            max_position_pct=0.10,
            max_risk_per_trade_pct=0.02,
            max_portfolio_heat_pct=0.10
        )
        logger.info(f"Position sizer initialized: ${account_size:,.0f} account")

        # Pattern data
        self.patterns = self._load_patterns(pattern_file)
        self.pattern_loaded = self.patterns is not None

    def _load_patterns(self, pattern_file: str) -> Optional[Dict]:
        """
        Load validated pattern analysis data.

        Args:
            pattern_file: Path to pattern analysis JSON

        Returns:
            Pattern data dictionary or None if not found
        """
        try:
            if os.path.exists(pattern_file):
                with open(pattern_file, 'r') as f:
                    patterns = json.load(f)
                logger.info(f"Loaded patterns from {pattern_file}")
                return patterns
            else:
                logger.warning(f"Pattern file not found: {pattern_file}")
                return None
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            return None

    def analyze_article(self, article: Dict) -> Dict:
        """
        Analyze a news article and return sentiment/theme analysis.

        Args:
            article: Dictionary with 'title', 'content', 'ticker'

        Returns:
            Analysis results dictionary
        """
        title = article.get('title', '')
        content = article.get('content', '')
        ticker = article.get('ticker', '')

        if self.using_finbert:
            # Use FinBERT (86-97% accuracy)
            text = f"{title}. {content}" if content else title
            result = self.sentiment_analyzer.analyze(text)

            # Convert FinBERT output to standard format
            # FinBERT score is 0-1 where 0.5=neutral, convert to -1 to +1
            sentiment_score = (result['score'] - 0.5) * 2

            analysis = {
                'sentiment': result['sentiment'],
                'score': sentiment_score,
                'confidence': result['confidence'],
                'themes': [],  # FinBERT doesn't extract themes
                'model': 'finbert'
            }
        else:
            # Use keyword analyzer (50% accuracy, legacy)
            analysis = self.sentiment_analyzer.analyze_article(title, content, ticker)
            analysis['model'] = 'keyword'

        return analysis

    def get_theme_performance(self, themes: List[str]) -> Dict:
        """
        Get performance metrics for given themes from validated patterns.

        Args:
            themes: List of theme strings

        Returns:
            Dictionary with aggregated theme performance metrics
        """
        if not self.pattern_loaded or not themes:
            return {
                'avg_correlation': 0.0,
                'avg_accuracy': 0.5,
                'avg_magnitude': 0.0,
                'theme_count': 0
            }

        theme_data = self.patterns.get('theme_performance', {}).get('themes', [])

        # Find matching themes
        matching_themes = [t for t in theme_data if t['theme'] in themes]

        if not matching_themes:
            return {
                'avg_correlation': 0.0,
                'avg_accuracy': 0.5,
                'avg_magnitude': 0.0,
                'theme_count': 0
            }

        # Aggregate metrics
        correlations = [t['correlation_1d'] for t in matching_themes]
        accuracies = [t['directional_accuracy_1d'] for t in matching_themes]
        magnitudes = [t['avg_magnitude_1d'] for t in matching_themes]

        return {
            'avg_correlation': sum(correlations) / len(correlations) if correlations else 0.0,
            'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0.5,
            'avg_magnitude': sum(magnitudes) / len(magnitudes) if magnitudes else 0.0,
            'theme_count': len(matching_themes),
            'themes_found': [t['theme'] for t in matching_themes]
        }

    def calculate_confidence_score(
        self,
        sentiment_confidence: float,
        sentiment_score: float,
        theme_performance: Dict,
        technical_indicators: Optional[Dict] = None,
        recent_price_change: Optional[float] = None,
        is_material: bool = True,
        current_datetime: Optional[datetime] = None
    ) -> Tuple[float, Dict]:
        """
        Calculate overall confidence score using Bayesian approach (REPLACES ADDITIVE MODEL).

        Properly combines independent signals using odds ratios rather than simple addition.

        Args:
            sentiment_confidence: Sentiment model confidence (0-1)
            sentiment_score: Sentiment score (-1 to +1)
            theme_performance: Theme performance metrics (legacy, for logging only)
            technical_indicators: Optional technical analysis results
            recent_price_change: Recent price movement percentage
            is_material: Whether announcement is material (quality filter)
            current_datetime: Current datetime for time-of-day analysis (default: now)

        Returns:
            Tuple of (confidence_score, breakdown_dict)
        """
        # Use real-time trading hours analysis
        if current_datetime is None:
            current_datetime = datetime.now()

        # Check if market is open and get time-of-day boost
        is_market_open = ASXTradingHours.is_market_open(current_datetime)
        is_optimal, time_reason = ASXTradingHours.is_optimal_trading_time(current_datetime)
        time_of_day_boost = ASXTradingHours.get_time_of_day_boost(current_datetime)

        # Format current time for Bayesian combiner
        current_time_aest = current_datetime.strftime('%H:%M:%S')

        # For paper trading (no real-time context), assume instant signal
        announcement_age_minutes = 0.0

        # Use Bayesian signal combiner
        confidence, breakdown = self.signal_combiner.compute_confidence(
            sentiment_score=abs(sentiment_score),  # Use strength (0 to 1)
            announcement_age_minutes=announcement_age_minutes,
            current_time_aest=current_time_aest,
            technical_indicators=technical_indicators,
            is_material=is_material,
            recent_price_change=recent_price_change
        )

        # Apply ASX-specific time-of-day adjustment (multiplicative)
        # This overrides the Bayesian combiner's generic time-of-day logic
        confidence = confidence * time_of_day_boost

        # Clamp to valid range
        confidence = max(0.0, min(1.0, confidence))

        # Add legacy theme performance to breakdown for compatibility
        breakdown['theme_performance'] = {
            'correlation': theme_performance.get('avg_correlation', 0.0),
            'accuracy': theme_performance.get('avg_accuracy', 0.5),
            'theme_count': theme_performance.get('theme_count', 0)
        }

        # Add ASX-specific time info to breakdown
        breakdown['asx_timing'] = {
            'market_open': is_market_open,
            'is_optimal_time': is_optimal,
            'time_reason': time_reason,
            'time_boost': time_of_day_boost,
            'current_time_aest': current_time_aest
        }

        return confidence, breakdown

    def generate_recommendation(
        self,
        article: Dict,
        min_confidence: float = 0.60,  # Raised from 0.5 with FinBERT
        min_sentiment: float = 0.2,
        current_price: Optional[float] = None,
        stop_loss_pct: float = 0.03  # 3% stop loss default
    ) -> Optional[Dict]:
        """
        Generate a trade recommendation from a news article.

        Args:
            article: Article dictionary with title, content, ticker, etc.
            min_confidence: Minimum confidence threshold (default: 0.60)
            min_sentiment: Minimum absolute sentiment score
            current_price: Current stock price (required for position sizing)
            stop_loss_pct: Stop loss percentage (default: 3%)

        Returns:
            Recommendation dictionary or None if no recommendation
        """
        # Apply quality filter first
        if self.quality_filter:
            quality_assessment = self.quality_filter.assess_quality(
                source=article.get('source', ''),
                announcement_type=article.get('announcement_type'),
                title=article.get('title', ''),
                content=article.get('content'),
                price_sensitive=article.get('price_sensitive', False)
            )

            if not quality_assessment['passes_filter']:
                logger.debug(
                    f"Article filtered out: {article.get('title', 'N/A')} "
                    f"(quality score: {quality_assessment['quality_score']:.2f})"
                )
                return None

            # Store quality score for later use
            article['quality_score'] = quality_assessment['quality_score']
            article['quality_reasons'] = quality_assessment['reasons']

        # Analyze article
        analysis = self.analyze_article(article)

        sentiment = analysis['sentiment']
        sentiment_score = analysis['score']
        sentiment_confidence = analysis['confidence']
        themes = analysis.get('themes', [])

        # Get theme performance
        theme_performance = self.get_theme_performance(themes)

        # Determine if material (assume yes if quality score >= 0.5)
        is_material = article.get('quality_score', 0.7) >= 0.5

        # Calculate confidence using Bayesian approach with ASX timing
        current_datetime = datetime.now()
        confidence, confidence_breakdown = self.calculate_confidence_score(
            sentiment_confidence,
            sentiment_score,
            theme_performance,
            technical_indicators=None,  # Paper trading doesn't use technical analysis by default
            recent_price_change=None,  # Would need historical price data
            is_material=is_material,
            current_datetime=current_datetime
        )

        # Generate human-readable explanation from breakdown
        asx_timing = confidence_breakdown.get('asx_timing', {})
        confidence_explanation = (
            f"Bayesian confidence: {confidence:.3f} "
            f"(base: {confidence_breakdown.get('base_sentiment', 0.5):.3f}, "
            f"time boost: {confidence_breakdown.get('time_boost', 1.0):.2f}x, "
            f"ASX time boost: {asx_timing.get('time_boost', 1.0):.2f}x [{asx_timing.get('time_reason', 'unknown')}], "
            f"tech: {confidence_breakdown.get('technical_boost', 1.0):.2f}x, "
            f"material: {confidence_breakdown.get('materiality_factor', 1.0):.2f}x)"
        )

        # Check thresholds
        if confidence < min_confidence:
            logger.debug(f"Confidence {confidence:.2f} below threshold {min_confidence}")
            return None

        if abs(sentiment_score) < min_sentiment:
            logger.debug(f"Sentiment score {sentiment_score:.2f} below threshold {min_sentiment}")
            return None

        # Check risk limits BEFORE making recommendation
        risk_status = self.position_sizer.check_risk_limits()
        if risk_status['status'] in ['CRITICAL', 'SHUTDOWN']:
            logger.warning(
                f"Risk limits prevent new positions: {risk_status['status']} "
                f"(max DD: {risk_status['max_drawdown']:.1%})"
            )
            return None
        elif risk_status['status'] == 'ALERT':
            # Raise confidence threshold during ALERT
            if confidence < 0.75:
                logger.debug(f"ALERT status requires confidence >= 0.75, got {confidence:.2f}")
                return None

        # Determine action
        if sentiment == 'positive' and sentiment_score > min_sentiment:
            action = 'BUY'
            reasoning = f"Positive sentiment ({sentiment_score:.2f}) on {', '.join(themes) if themes else 'general news'}"
        elif sentiment == 'negative' and sentiment_score < -min_sentiment:
            action = 'SELL/AVOID'
            reasoning = f"Negative sentiment ({sentiment_score:.2f}) on {', '.join(themes) if themes else 'general news'}"
        else:
            logger.debug("Neutral sentiment, no recommendation")
            return None

        # Expected move (if we have pattern data)
        expected_move_pct = theme_performance.get('avg_magnitude', 0.0)
        if sentiment == 'negative':
            expected_move_pct = -expected_move_pct

        # Calculate position size using Kelly Criterion
        position_details = None
        shares = 0
        risk_amount = 0.0

        if action == 'BUY' and current_price is not None:
            # Calculate stop loss price
            stop_loss_price = current_price * (1 - stop_loss_pct)
            take_profit_price = current_price * (1 + stop_loss_pct * 2)  # 2:1 R:R

            # Get position size from Kelly sizer
            shares, risk_amount, position_details = self.position_sizer.calculate_position_size(
                symbol=article.get('ticker', 'UNKNOWN'),
                entry_price=current_price,
                stop_loss_price=stop_loss_price,
                confidence=confidence
            )

            if shares == 0:
                logger.debug(f"Position sizer returned 0 shares (portfolio heat or insufficient capital)")
                return None

        elif action == 'BUY' and current_price is None:
            logger.warning("Cannot calculate position size without current_price")
            # Continue anyway for paper trading compatibility

        # Build recommendation
        recommendation = {
            'recommendation_id': self._generate_id(),
            'timestamp': datetime.now().isoformat(),
            'ticker': article.get('ticker', 'UNKNOWN'),
            'action': action,
            'confidence': confidence,
            'confidence_explanation': confidence_explanation,

            # Sentiment details
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'sentiment_confidence': sentiment_confidence,
            'sentiment_model': analysis.get('model', 'unknown'),

            # Position sizing (Kelly Criterion)
            'shares': shares,
            'risk_amount': risk_amount,
            'position_value': position_details['position_value'] if position_details else None,
            'entry_price': current_price,
            'stop_loss': position_details['stop_loss'] if position_details else None,
            'risk_per_share': position_details['risk_per_share'] if position_details else None,
            'portfolio_heat': position_details['portfolio_heat_after'] if position_details else None,
            'kelly_details': {
                'kelly_edge': position_details.get('kelly_edge', 0) if position_details else 0,
                'kelly_pct': position_details.get('kelly_pct', 0) if position_details else 0,
                'confidence_scale': position_details.get('confidence_scale', 0) if position_details else 0
            } if position_details else None,

            # Risk status
            'risk_status': risk_status['status'],
            'max_drawdown': risk_status['max_drawdown'],
            'portfolio_heat_current': risk_status['portfolio_heat'],

            # Article details
            'article_id': article.get('article_id'),
            'article_title': article.get('title', '')[:100],
            'article_source': article.get('source', 'UNKNOWN'),
            'article_url': article.get('url', ''),

            # Quality assessment (if available)
            'quality_score': article.get('quality_score'),
            'quality_reasons': article.get('quality_reasons'),

            # Theme analysis
            'themes': themes,
            'theme_performance': {
                'correlation': theme_performance.get('avg_correlation', 0.0),
                'accuracy': theme_performance.get('avg_accuracy', 0.5),
                'expected_move_pct': round(expected_move_pct, 2)
            },

            # Reasoning
            'reasoning': reasoning,
            'pattern_based': self.pattern_loaded,

            # For tracking
            'status': 'PENDING',  # PENDING, ACTIVE, CLOSED
            'outcome': None  # Will be filled after tracking period
        }

        logger.info(
            f"Generated {action} recommendation for {article.get('ticker')}: "
            f"Confidence {confidence:.2f}, "
            f"Shares: {shares}, "
            f"Risk: ${risk_amount:.2f}, "
            f"Model: {analysis.get('model', 'unknown')}"
        )

        return recommendation

    def generate_recommendations_batch(
        self,
        articles: List[Dict],
        min_confidence: float = 0.5,
        min_sentiment: float = 0.2
    ) -> List[Dict]:
        """
        Generate recommendations for a batch of articles.

        Args:
            articles: List of article dictionaries
            min_confidence: Minimum confidence threshold
            min_sentiment: Minimum absolute sentiment score

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        for article in articles:
            try:
                rec = self.generate_recommendation(
                    article,
                    min_confidence,
                    min_sentiment
                )
                if rec:
                    recommendations.append(rec)
            except Exception as e:
                logger.error(f"Error processing article {article.get('article_id')}: {e}")
                continue

        logger.info(f"Generated {len(recommendations)} recommendations from {len(articles)} articles")

        return recommendations

    def _generate_id(self) -> str:
        """
        Generate unique recommendation ID.

        Returns:
            Unique ID string
        """
        return f"REC_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"


def main():
    """
    Test the recommendation engine.
    """
    import sqlite3

    logging.basicConfig(level=logging.INFO)

    print("\n" + "=" * 70)
    print("RECOMMENDATION ENGINE TEST")
    print("=" * 70 + "\n")

    # Load pattern data
    engine = RecommendationEngine()

    if engine.pattern_loaded:
        print("Pattern data loaded successfully")
    else:
        print("Warning: No pattern data available, using sentiment only")

    print()

    # Get recent articles from database
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

    conn = sqlite3.connect(config.DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT article_id, ticker, source, title, content, url
        FROM news_articles
        ORDER BY created_at DESC
        LIMIT 10
    """)

    articles = []
    for row in cursor.fetchall():
        articles.append({
            'article_id': row[0],
            'ticker': row[1],
            'source': row[2],
            'title': row[3],
            'content': row[4],
            'url': row[5]
        })

    conn.close()

    print(f"Loaded {len(articles)} recent articles\n")

    # Add mock current prices for testing (would come from price scraper in production)
    for article in articles:
        article['current_price'] = 45.00  # Mock price

    # Generate recommendations
    recommendations = []
    for article in articles:
        try:
            rec = engine.generate_recommendation(
                article,
                min_confidence=0.4,  # Lower threshold for testing
                min_sentiment=0.1,
                current_price=article.get('current_price')
            )
            if rec:
                recommendations.append(rec)
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            continue

    print(f"\nGenerated {len(recommendations)} recommendations:\n")

    for rec in recommendations:
        print(f"{rec['action']} {rec['ticker']}")
        print(f"  Confidence: {rec['confidence']:.2f} ({rec['sentiment_model']} sentiment)")
        print(f"  Sentiment: {rec['sentiment']} ({rec['sentiment_score']:.2f})")
        print(f"  Position: {rec['shares']} shares @ ${rec['entry_price']:.2f}")
        print(f"  Risk: ${rec['risk_amount']:.2f}, Stop: ${rec['stop_loss']:.2f}")
        print(f"  Portfolio heat: {rec['portfolio_heat']:.1%}")
        print(f"  Risk status: {rec['risk_status']}")
        print(f"  Themes: {', '.join(rec['themes']) if rec['themes'] else 'None'}")
        print(f"  Expected move: {rec['theme_performance']['expected_move_pct']:+.2f}%")
        print(f"  Reasoning: {rec['reasoning']}")
        print()

    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
