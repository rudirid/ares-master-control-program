"""
Local Rule-Based Sentiment Analysis

No external APIs required. Uses:
- Financial keyword dictionaries
- Rule-based pattern matching
- Statistical text analysis

Author: Claude Code
Date: 2025-10-09
"""

import re
import logging
from typing import Dict, List, Set
from collections import Counter

logger = logging.getLogger(__name__)


# Financial sentiment lexicons
POSITIVE_WORDS = {
    # Performance
    'profit', 'profits', 'profitable', 'profitability', 'earnings', 'revenue', 'growth', 'grew',
    'increase', 'increased', 'increasing', 'rise', 'rose', 'rising', 'surge', 'surged', 'soar',
    'gain', 'gains', 'gained', 'record', 'strong', 'strength', 'robust', 'solid', 'healthy',
    'outperform', 'outperformed', 'beat', 'exceed', 'exceeded', 'exceeds', 'above',

    # Positive events
    'upgrade', 'upgraded', 'expansion', 'acquire', 'acquisition', 'merger', 'deal', 'contract',
    'win', 'wins', 'won', 'success', 'successful', 'breakthrough', 'innovation', 'launch',
    'approval', 'approved', 'boost', 'boosted', 'improve', 'improved', 'improvement',

    # Market sentiment
    'bullish', 'optimistic', 'positive', 'favorable', 'confident', 'confidence', 'opportunity',
    'upside', 'rally', 'rebound', 'recovery', 'recover', 'stabilize', 'stabilized',

    # Financial strength
    'dividend', 'buyback', 'cash', 'liquidity', 'capitalized', 'invest', 'investment'
}

NEGATIVE_WORDS = {
    # Performance
    'loss', 'losses', 'lost', 'decline', 'declined', 'decrease', 'decreased', 'drop', 'dropped',
    'fall', 'fell', 'falling', 'plunge', 'plunged', 'weak', 'weakness', 'poor', 'miss', 'missed',
    'underperform', 'underperformed', 'below', 'disappoint', 'disappointed', 'disappointing',

    # Negative events
    'downgrade', 'downgraded', 'cut', 'reduce', 'reduced', 'reduction', 'layoff', 'layoffs',
    'fire', 'fired', 'resignation', 'resign', 'scandal', 'fraud', 'investigation', 'probe',
    'lawsuit', 'sued', 'fine', 'penalty', 'warning', 'concern', 'concerns', 'worried', 'worry',

    # Market sentiment
    'bearish', 'pessimistic', 'negative', 'unfavorable', 'risk', 'risks', 'risky', 'volatile',
    'volatility', 'uncertainty', 'uncertain', 'threat', 'problem', 'problems', 'issue', 'issues',
    'crisis', 'collapse', 'struggle', 'struggling', 'fail', 'failed', 'failure',

    # Financial problems
    'debt', 'write-down', 'writedown', 'impairment', 'bankruptcy', 'insolvent', 'default'
}

# Intensifiers and negations
INTENSIFIERS = {'very', 'extremely', 'highly', 'significantly', 'substantially', 'sharply'}
NEGATIONS = {'not', 'no', 'never', 'neither', 'nor', 'none', 'nobody', 'nothing', "n't"}

# Financial themes
THEME_KEYWORDS = {
    'earnings': ['earnings', 'profit', 'ebitda', 'revenue', 'sales', 'income', 'results'],
    'acquisition': ['acquisition', 'merger', 'takeover', 'deal', 'acquire', 'bought', 'purchase'],
    'regulatory': ['regulator', 'regulatory', 'compliance', 'investigation', 'asic', 'accc'],
    'management': ['ceo', 'cfo', 'executive', 'board', 'director', 'management', 'leadership'],
    'dividend': ['dividend', 'payout', 'distribution', 'shareholder', 'return'],
    'market': ['market', 'share', 'competition', 'competitor', 'demand', 'supply'],
    'operations': ['production', 'operations', 'plant', 'facility', 'expansion', 'capacity'],
    'financial': ['debt', 'loan', 'funding', 'capital', 'cash', 'liquidity', 'credit'],
    'legal': ['lawsuit', 'litigation', 'legal', 'court', 'settlement', 'claim'],
    'outlook': ['outlook', 'forecast', 'guidance', 'expect', 'project', 'estimate']
}


class LocalSentimentAnalyzer:
    """
    Rule-based sentiment analyzer using financial lexicons.
    No external API calls required.
    """

    def __init__(self):
        """Initialize the analyzer."""
        self.positive_words = POSITIVE_WORDS
        self.negative_words = NEGATIVE_WORDS
        self.intensifiers = INTENSIFIERS
        self.negations = NEGATIONS
        self.theme_keywords = THEME_KEYWORDS

    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocess text into lowercase tokens.

        Args:
            text: Input text

        Returns:
            List of lowercase word tokens
        """
        # Convert to lowercase
        text = text.lower()

        # Remove special characters but keep letters, numbers, and apostrophes
        text = re.sub(r"[^\w\s']", ' ', text)

        # Split into words
        words = text.split()

        return words

    def calculate_sentiment_score(self, words: List[str]) -> Dict:
        """
        Calculate sentiment score based on word counts and rules.

        Args:
            words: List of word tokens

        Returns:
            Dictionary with sentiment metrics
        """
        positive_count = 0
        negative_count = 0

        # Track context for negations and intensifiers
        for i, word in enumerate(words):
            # Check for negation in previous 3 words
            is_negated = False
            if i > 0:
                prev_words = words[max(0, i-3):i]
                is_negated = any(neg in prev_words for neg in self.negations)

            # Check for intensifier
            is_intensified = False
            if i > 0 and words[i-1] in self.intensifiers:
                is_intensified = True

            # Calculate weight
            weight = 1.5 if is_intensified else 1.0

            # Count sentiment words
            if word in self.positive_words:
                if is_negated:
                    negative_count += weight  # Negated positive = negative
                else:
                    positive_count += weight
            elif word in self.negative_words:
                if is_negated:
                    positive_count += weight  # Negated negative = positive
                else:
                    negative_count += weight

        # Calculate metrics
        total = positive_count + negative_count

        if total == 0:
            sentiment = 'neutral'
            score = 0.0
            confidence = 0.3  # Low confidence for neutral
        else:
            net_score = positive_count - negative_count
            score = net_score / (total + 2)  # Normalize to roughly -1 to 1, with smoothing

            # Determine sentiment category
            if score > 0.15:
                sentiment = 'positive'
            elif score < -0.15:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            # Confidence based on total sentiment words found
            confidence = min(0.95, 0.4 + (total * 0.1))

        return {
            'sentiment': sentiment,
            'score': round(score, 3),
            'confidence': round(confidence, 2),
            'positive_words': int(positive_count),
            'negative_words': int(negative_count)
        }

    def extract_themes(self, words: List[str], top_n: int = 5) -> List[str]:
        """
        Extract key themes from the text.

        Args:
            words: List of word tokens
            top_n: Number of top themes to return

        Returns:
            List of theme names
        """
        theme_scores = {}

        for theme, keywords in self.theme_keywords.items():
            score = sum(1 for word in words if word in keywords)
            if score > 0:
                theme_scores[theme] = score

        # Sort by score and return top themes
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        return [theme for theme, score in sorted_themes[:top_n]]

    def assess_impact(self, sentiment: str, score: float, themes: List[str]) -> str:
        """
        Assess potential stock price impact.

        Args:
            sentiment: Sentiment category
            score: Sentiment score
            themes: Extracted themes

        Returns:
            Impact assessment string
        """
        # High impact themes
        high_impact_themes = {'earnings', 'acquisition', 'regulatory', 'legal', 'management'}
        has_high_impact = any(theme in high_impact_themes for theme in themes)

        # Determine impact level
        abs_score = abs(score)

        if abs_score > 0.5 and has_high_impact:
            level = "High"
        elif abs_score > 0.3 or has_high_impact:
            level = "Moderate"
        else:
            level = "Low"

        direction = "positive" if score > 0 else "negative" if score < 0 else "neutral"

        return f"{level} {direction} impact expected"

    def analyze_article(self, title: str, content: str, ticker: str) -> Dict:
        """
        Analyze a news article for sentiment and themes.

        Args:
            title: Article title
            content: Article content/preview
            ticker: Stock ticker symbol

        Returns:
            Dictionary with analysis results
        """
        try:
            # Combine title and content (weight title more heavily)
            full_text = f"{title} {title} {content}"  # Title appears twice for emphasis

            # Preprocess
            words = self.preprocess_text(full_text)

            # Calculate sentiment
            sentiment_result = self.calculate_sentiment_score(words)

            # Extract themes
            themes = self.extract_themes(words)

            # Assess impact
            impact = self.assess_impact(
                sentiment_result['sentiment'],
                sentiment_result['score'],
                themes
            )

            # Build summary
            summary = self._build_summary(sentiment_result, themes)

            return {
                'sentiment': sentiment_result['sentiment'],
                'sentiment_score': sentiment_result['score'],
                'confidence': sentiment_result['confidence'],
                'themes': themes,
                'summary': summary,
                'impact_assessment': impact,
                'positive_words': sentiment_result['positive_words'],
                'negative_words': sentiment_result['negative_words']
            }

        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return {
                'sentiment': 'neutral',
                'sentiment_score': 0.0,
                'confidence': 0.0,
                'themes': [],
                'summary': f'Analysis failed: {e}',
                'impact_assessment': 'Unable to assess',
                'error': str(e)
            }

    def _build_summary(self, sentiment_result: Dict, themes: List[str]) -> str:
        """
        Build a summary explanation.

        Args:
            sentiment_result: Sentiment calculation results
            themes: Extracted themes

        Returns:
            Summary string
        """
        sentiment = sentiment_result['sentiment']
        pos_count = sentiment_result['positive_words']
        neg_count = sentiment_result['negative_words']

        if sentiment == 'positive':
            summary = f"Positive sentiment detected ({pos_count} positive vs {neg_count} negative words)."
        elif sentiment == 'negative':
            summary = f"Negative sentiment detected ({neg_count} negative vs {pos_count} positive words)."
        else:
            if pos_count + neg_count == 0:
                summary = "Neutral - no strong sentiment indicators found."
            else:
                summary = f"Neutral - balanced sentiment ({pos_count} positive, {neg_count} negative words)."

        if themes:
            summary += f" Key themes: {', '.join(themes[:3])}."

        return summary


def test_local_analyzer():
    """
    Test the local sentiment analyzer.
    """
    print("\n" + "=" * 70)
    print("Testing Local Sentiment Analyzer")
    print("=" * 70 + "\n")

    analyzer = LocalSentimentAnalyzer()

    test_articles = [
        {
            "ticker": "BHP",
            "title": "BHP reports record profits amid strong commodity demand",
            "content": "Mining giant BHP has announced record annual profits, driven by strong iron ore prices and increased production."
        },
        {
            "ticker": "CBA",
            "title": "Commonwealth Bank faces regulatory scrutiny over lending practices",
            "content": "Australia's largest bank is under investigation by ASIC following allegations of improper lending assessments."
        },
        {
            "ticker": "WOW",
            "title": "Woolworths maintains market position despite competitive pressure",
            "content": "Woolworths reported steady sales growth, maintaining its market share in the face of increased competition."
        }
    ]

    for article in test_articles:
        print(f"\nArticle: {article['title']}")
        print("-" * 70)

        result = analyzer.analyze_article(
            title=article['title'],
            content=article['content'],
            ticker=article['ticker']
        )

        print(f"Sentiment: {result['sentiment']}")
        print(f"Score: {result['sentiment_score']:.3f}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Themes: {', '.join(result['themes']) if result['themes'] else 'None'}")
        print(f"Summary: {result['summary']}")
        print(f"Impact: {result['impact_assessment']}")
        print(f"Words: +{result['positive_words']} / -{result['negative_words']}")

    print("\n" + "=" * 70)
    print("Testing complete!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    test_local_analyzer()
