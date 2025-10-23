"""
Multi-Source News Validator

Analyzes news across multiple sources to calculate correlation-based
confidence scores with credibility weighting.

Author: Claude Code
Date: 2025-10-10
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class SourceCredibility:
    """Source credibility ratings and characteristics."""
    name: str
    credibility_score: float  # 0-1 scale
    bias_factor: float  # 0=neutral, -1=bearish bias, +1=bullish bias
    response_time: str  # 'fast', 'medium', 'slow'
    specialization: str  # 'general', 'business', 'finance', 'announcements'


# Australian media source credibility ratings
SOURCE_RATINGS = {
    'ASX': SourceCredibility(
        name='ASX Official',
        credibility_score=1.0,  # Highest - official source
        bias_factor=0.0,
        response_time='fast',
        specialization='announcements'
    ),
    'AFR': SourceCredibility(
        name='Australian Financial Review',
        credibility_score=0.95,  # Very high - specialist financial
        bias_factor=0.1,  # Slightly pro-business
        response_time='fast',
        specialization='finance'
    ),
    'ABC News': SourceCredibility(
        name='ABC News',
        credibility_score=0.90,  # High - public broadcaster
        bias_factor=0.0,  # Neutral
        response_time='medium',
        specialization='general'
    ),
    'SMH': SourceCredibility(
        name='Sydney Morning Herald',
        credibility_score=0.85,  # High - major newspaper
        bias_factor=-0.05,  # Slightly critical
        response_time='medium',
        specialization='business'
    ),
    'The Australian': SourceCredibility(
        name='The Australian',
        credibility_score=0.85,  # High - national newspaper
        bias_factor=0.15,  # Pro-business
        response_time='medium',
        specialization='business'
    ),
    'HotCopper': SourceCredibility(
        name='HotCopper Forum',
        credibility_score=0.50,  # Medium - retail sentiment
        bias_factor=0.2,  # Bullish retail bias
        response_time='fast',
        specialization='sentiment'
    )
}


class MultiSourceValidator:
    """
    Validates news stories across multiple sources and calculates
    weighted confidence scores.
    """

    def __init__(self, db_path: str):
        """
        Initialize validator.

        Args:
            db_path: Database path
        """
        self.db_path = db_path

    def get_related_articles(
        self,
        ticker: str,
        reference_date: datetime,
        time_window_hours: int = 48
    ) -> List[Dict]:
        """
        Get all articles about a ticker within a time window.

        Args:
            ticker: Stock ticker
            reference_date: Reference datetime
            time_window_hours: Hours before/after to search

        Returns:
            List of related articles from all sources
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_time = reference_date - timedelta(hours=time_window_hours)
        end_time = reference_date + timedelta(hours=time_window_hours)

        # Query news articles
        cursor.execute("""
            SELECT source, title, content, COALESCE(datetime, created_at) as pub_date, url
            FROM news_articles
            WHERE ticker = ?
              AND COALESCE(datetime, created_at) BETWEEN ? AND ?
            ORDER BY pub_date ASC
        """, (ticker, start_time.isoformat(), end_time.isoformat()))

        news_articles = cursor.fetchall()

        # Query ASX announcements
        cursor.execute("""
            SELECT 'ASX' as source, title, content, COALESCE(datetime, created_at) as pub_date, url
            FROM asx_announcements
            WHERE ticker = ?
              AND COALESCE(datetime, created_at) BETWEEN ? AND ?
            ORDER BY pub_date ASC
        """, (ticker, start_time.isoformat(), end_time.isoformat()))

        announcements = cursor.fetchall()

        conn.close()

        # Combine and format
        articles = []
        for row in news_articles + announcements:
            articles.append({
                'source': row[0] or 'Unknown',
                'title': row[1],
                'content': row[2] or '',
                'pub_date': row[3],
                'url': row[4]
            })

        return articles

    def calculate_topic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using keyword overlap.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Similarity score 0-1
        """
        # Extract key financial terms
        keywords1 = self._extract_keywords(text1)
        keywords2 = self._extract_keywords(text2)

        if not keywords1 or not keywords2:
            return 0.0

        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))

        return intersection / union if union > 0 else 0.0

    def _extract_keywords(self, text: str) -> set:
        """Extract important keywords from text."""
        if not text:
            return set()

        text = text.upper()

        # Financial keywords
        keywords = set()

        # Common financial terms
        financial_terms = [
            'PROFIT', 'REVENUE', 'EARNINGS', 'DIVIDEND', 'BUYBACK',
            'ACQUISITION', 'MERGER', 'EXPANSION', 'CLOSURE', 'RESTRUCTURE',
            'GROWTH', 'DECLINE', 'SURGE', 'PLUNGE', 'RISE', 'FALL',
            'UPGRADE', 'DOWNGRADE', 'GUIDANCE', 'FORECAST', 'OUTLOOK',
            'DEBT', 'EQUITY', 'CAPITAL', 'INVESTMENT', 'CONTRACT'
        ]

        for term in financial_terms:
            if term in text:
                keywords.add(term)

        # Extract numbers (could indicate financial figures)
        numbers = re.findall(r'\$[\d,]+|\d+%|\d+[BM]', text)
        for num in numbers[:5]:  # Limit to avoid noise
            keywords.add(num)

        return keywords

    def analyze_source_correlation(
        self,
        ticker: str,
        article_date: datetime,
        article_title: str,
        article_content: str
    ) -> Dict:
        """
        Analyze correlation across multiple sources.

        Args:
            ticker: Stock ticker
            article_date: Article publication date
            article_title: Article title
            article_content: Article content

        Returns:
            Correlation analysis with weighted confidence
        """
        # Get related articles from all sources
        related = self.get_related_articles(ticker, article_date, time_window_hours=48)

        if not related:
            return {
                'source_count': 0,
                'correlation_score': 0.0,
                'weighted_confidence': 0.5,  # Base confidence with no corroboration
                'sources': [],
                'credibility_weighted_score': 0.5
            }

        # Group by source
        sources_found = {}
        for article in related:
            source = article['source']
            if source not in sources_found:
                sources_found[source] = []
            sources_found[source].append(article)

        # Calculate correlation with each source
        source_correlations = []
        reference_text = f"{article_title} {article_content}"

        for source, articles in sources_found.items():
            # Get source credibility
            cred = SOURCE_RATINGS.get(source, SourceCredibility(
                name=source,
                credibility_score=0.7,
                bias_factor=0.0,
                response_time='medium',
                specialization='general'
            ))

            # Calculate max similarity with any article from this source
            max_similarity = 0.0
            for art in articles:
                art_text = f"{art['title']} {art['content']}"
                similarity = self.calculate_topic_similarity(reference_text, art_text)
                max_similarity = max(max_similarity, similarity)

            if max_similarity > 0.3:  # Threshold for related content
                source_correlations.append({
                    'source': source,
                    'similarity': max_similarity,
                    'credibility': cred.credibility_score,
                    'bias_factor': cred.bias_factor,
                    'article_count': len(articles)
                })

        # Calculate weighted confidence
        if not source_correlations:
            return {
                'source_count': 0,
                'correlation_score': 0.0,
                'weighted_confidence': 0.5,
                'sources': [],
                'credibility_weighted_score': 0.5
            }

        # Weighted average based on credibility and similarity
        total_weight = 0.0
        weighted_sum = 0.0

        for corr in source_correlations:
            weight = corr['credibility'] * corr['similarity']
            weighted_sum += weight
            total_weight += corr['credibility']

        # Normalize
        credibility_weighted_score = (weighted_sum / total_weight) if total_weight > 0 else 0.5

        # Bonus for multiple independent sources
        source_diversity_bonus = min(len(source_correlations) * 0.05, 0.20)

        # Final weighted confidence
        final_confidence = min(0.5 + credibility_weighted_score * 0.3 + source_diversity_bonus, 1.0)

        # Average correlation
        avg_correlation = sum(c['similarity'] for c in source_correlations) / len(source_correlations)

        return {
            'source_count': len(source_correlations),
            'correlation_score': round(avg_correlation, 3),
            'weighted_confidence': round(final_confidence, 3),
            'credibility_weighted_score': round(credibility_weighted_score, 3),
            'sources': [c['source'] for c in source_correlations],
            'source_details': source_correlations
        }

    def get_enhanced_confidence(
        self,
        ticker: str,
        article_date: datetime,
        article_title: str,
        article_content: str,
        base_sentiment_confidence: float
    ) -> Tuple[float, Dict]:
        """
        Get enhanced confidence score combining sentiment analysis
        with multi-source validation.

        Args:
            ticker: Stock ticker
            article_date: Article date
            article_title: Article title
            article_content: Article content
            base_sentiment_confidence: Base confidence from sentiment analyzer

        Returns:
            Tuple of (enhanced_confidence, validation_details)
        """
        # Get multi-source correlation
        validation = self.analyze_source_correlation(
            ticker, article_date, article_title, article_content
        )

        # Combine base sentiment confidence with multi-source validation
        # Formula: 60% base sentiment + 40% multi-source validation
        enhanced_confidence = (
            base_sentiment_confidence * 0.6 +
            validation['weighted_confidence'] * 0.4
        )

        validation['base_sentiment_confidence'] = base_sentiment_confidence
        validation['enhanced_confidence'] = round(enhanced_confidence, 3)
        validation['confidence_boost'] = round(enhanced_confidence - base_sentiment_confidence, 3)

        return enhanced_confidence, validation


def main():
    """Test the multi-source validator."""
    import sys
    sys.path.insert(0, '..')
    import config

    logging.basicConfig(level=logging.INFO)

    validator = MultiSourceValidator(config.DATABASE_PATH)

    # Test with a known ticker
    test_date = datetime(2024, 1, 15, 12, 0, 0)

    result = validator.analyze_source_correlation(
        ticker='BHP',
        article_date=test_date,
        article_title='BHP announces dividend increase',
        article_content='Mining giant BHP has announced a dividend increase following strong earnings.'
    )

    print("\nMulti-Source Validation Test:")
    print("=" * 60)
    print(f"Sources found: {result['source_count']}")
    print(f"Correlation score: {result['correlation_score']}")
    print(f"Weighted confidence: {result['weighted_confidence']}")
    print(f"Credibility score: {result['credibility_weighted_score']}")
    print(f"Sources: {', '.join(result['sources'])}")


if __name__ == '__main__':
    main()
