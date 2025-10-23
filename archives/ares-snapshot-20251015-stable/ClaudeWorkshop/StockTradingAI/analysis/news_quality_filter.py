"""
News Quality Filter

Filters news and announcements to improve signal quality by focusing on
market-moving events and excluding administrative noise.

Author: Claude Code
Date: 2025-10-10
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsQualityFilter:
    """
    Filters news and announcements based on quality criteria to improve
    trading signal accuracy.
    """

    # High-quality announcement types (market-moving)
    HIGH_QUALITY_ANNOUNCEMENTS = {
        'Takeover / Scheme Announcements',
        'Distribution Announcement',
        'Quarterly Activities Report',
        'Quarterly Cash Flow Report',
        'Half Yearly Report',
        'Full Year Results',
        'Preliminary Final Report',
        'Asset Acquisition & Disposal',
        'Profit Guidance',
        'Earnings Results',
        'Dividend',
        'Strategic Partnership',
        'Major Contract',
        'Capital Raising',
        'Company Administration'
    }

    # Low-quality announcement types (administrative noise)
    LOW_QUALITY_ANNOUNCEMENTS = {
        'Notice of Meeting',
        'AGM/EGM Documents',
        'Letter to Shareholders',
        'Change of Director\'s Interest Notice',
        'Appendix 3Y',
        'Appendix 3Z',
        'Corporate Directory',
        'Final Director\'s Interest Notice',
        'Initial Director\'s Interest Notice',
        'Change in substantial holding',
        'Becoming a substantial holder',
        'Ceasing to be a substantial holder',
        'ASX Query',
        'ASX Announcement',
        'Reinstatement to Official Quotation',
        'Trading Halt',
        'Voluntary Suspension',
        'Response to Media Speculation',
        'Cleansing Notice',
        'Section 708A Notice'
    }

    # High-impact keywords in title/content
    HIGH_IMPACT_KEYWORDS = {
        # Financial Results
        'PROFIT', 'REVENUE', 'EARNINGS', 'EBITDA', 'GUIDANCE', 'FORECAST',
        'RESULTS', 'PERFORMANCE',

        # Dividends & Capital
        'DIVIDEND', 'SPECIAL DIVIDEND', 'CAPITAL RETURN', 'BUYBACK',
        'SHARE BUYBACK', 'CAPITAL RAISING', 'PLACEMENT', 'SPP',

        # Corporate Actions
        'ACQUISITION', 'MERGER', 'TAKEOVER', 'SCHEME', 'DISPOSAL',
        'DIVESTMENT', 'SALE OF BUSINESS',

        # Major Events
        'CONTRACT', 'MAJOR CONTRACT', 'PARTNERSHIP', 'JOINT VENTURE',
        'APPROVAL', 'REGULATORY APPROVAL', 'LICENSE', 'PERMIT',

        # Business Changes
        'EXPANSION', 'CLOSURE', 'RESTRUCTURE', 'COST REDUCTION',
        'STRATEGIC REVIEW', 'IMPAIRMENT',

        # Market Impact
        'UPGRADE', 'DOWNGRADE', 'PRICE TARGET', 'RATING CHANGE',
        'BROKER UPDATE'
    }

    # Low-impact keywords (administrative)
    LOW_IMPACT_KEYWORDS = {
        'APPENDIX', 'NOTICE', 'AGM', 'EGM', 'DIRECTOR', 'INTEREST NOTICE',
        'SUBSTANTIAL HOLDER', 'QUERY', 'RESPONSE', 'CLEANSING',
        'VOLUNTARY SUSPENSION', 'REINSTATEMENT', 'TRADING HALT'
    }

    def __init__(self):
        """Initialize the filter."""
        pass

    def assess_quality(
        self,
        source: str,
        announcement_type: Optional[str],
        title: str,
        content: Optional[str],
        price_sensitive: bool = False
    ) -> Dict:
        """
        Assess the quality of a news article or announcement.

        Args:
            source: Source of the news ('ASX', 'AFR', etc.)
            announcement_type: Type of ASX announcement (if applicable)
            title: Article/announcement title
            content: Article/announcement content
            price_sensitive: Whether marked as price sensitive (ASX only)

        Returns:
            Quality assessment dict with score and reasons
        """
        quality_score = 0.5  # Base score
        reasons = []

        # 1. Source credibility (already handled in multi_source_validator)
        # ASX announcements are official source
        if source == 'ASX':
            quality_score += 0.1
            reasons.append("Official ASX announcement")

        # 2. Price sensitive flag (ASX only)
        if price_sensitive:
            quality_score += 0.2
            reasons.append("Marked as price sensitive")

        # 3. Announcement type quality (ASX only)
        if announcement_type:
            if announcement_type in self.HIGH_QUALITY_ANNOUNCEMENTS:
                quality_score += 0.2
                reasons.append(f"High-quality announcement type: {announcement_type}")
            elif announcement_type in self.LOW_QUALITY_ANNOUNCEMENTS:
                quality_score -= 0.3
                reasons.append(f"Low-quality announcement type: {announcement_type}")

        # 4. Title keyword analysis
        title_upper = title.upper()

        high_impact_count = sum(1 for kw in self.HIGH_IMPACT_KEYWORDS if kw in title_upper)
        low_impact_count = sum(1 for kw in self.LOW_IMPACT_KEYWORDS if kw in title_upper)

        if high_impact_count > 0:
            boost = min(high_impact_count * 0.1, 0.3)
            quality_score += boost
            reasons.append(f"Title contains {high_impact_count} high-impact keywords")

        if low_impact_count > 0:
            penalty = min(low_impact_count * 0.1, 0.2)
            quality_score -= penalty
            reasons.append(f"Title contains {low_impact_count} low-impact keywords")

        # 5. Content analysis (if available)
        if content:
            content_upper = content.upper()

            # Look for financial figures
            has_dollar_amounts = '$' in content
            has_percentages = '%' in content

            if has_dollar_amounts and has_percentages:
                quality_score += 0.15
                reasons.append("Contains financial figures")

        # 6. Specific high-value patterns
        combined_text = f"{title} {content or ''}".upper()

        # Earnings/profit announcements
        if any(word in combined_text for word in ['PROFIT UP', 'REVENUE UP', 'EARNINGS BEAT', 'GUIDANCE UPGRADE']):
            quality_score += 0.15
            reasons.append("Positive earnings indicator")

        if any(word in combined_text for word in ['PROFIT DOWN', 'REVENUE DOWN', 'EARNINGS MISS', 'GUIDANCE DOWNGRADE']):
            quality_score += 0.15
            reasons.append("Negative earnings indicator (tradeable)")

        # M&A activity
        if any(word in combined_text for word in ['ACQUISITION', 'MERGER', 'TAKEOVER BID', 'SCHEME OF ARRANGEMENT']):
            quality_score += 0.2
            reasons.append("M&A activity detected")

        # Major contracts
        if 'CONTRACT' in combined_text and any(word in combined_text for word in ['SECURED', 'AWARDED', 'WON', 'SIGNED']):
            quality_score += 0.15
            reasons.append("Major contract announced")

        # Cap quality score at 1.0
        quality_score = min(quality_score, 1.0)

        # Determine pass/fail
        passes_filter = quality_score >= 0.6  # Threshold for trading consideration

        return {
            'quality_score': round(quality_score, 3),
            'passes_filter': passes_filter,
            'reasons': reasons,
            'recommendation': 'TRADE' if passes_filter else 'SKIP'
        }

    def filter_batch(self, articles: List[Dict]) -> List[Dict]:
        """
        Filter a batch of articles/announcements.

        Args:
            articles: List of article dicts with keys:
                - source, announcement_type, title, content, price_sensitive

        Returns:
            Filtered list of articles that pass quality threshold
        """
        filtered = []

        for article in articles:
            assessment = self.assess_quality(
                source=article.get('source', ''),
                announcement_type=article.get('announcement_type'),
                title=article.get('title', ''),
                content=article.get('content'),
                price_sensitive=article.get('price_sensitive', False)
            )

            article['quality_assessment'] = assessment

            if assessment['passes_filter']:
                filtered.append(article)

        logger.info(f"Quality filter: {len(filtered)}/{len(articles)} articles passed ({len(filtered)/len(articles)*100:.1f}%)")

        return filtered


def main():
    """Test the quality filter."""
    logging.basicConfig(level=logging.INFO)

    filter = NewsQualityFilter()

    # Test cases
    test_articles = [
        {
            'source': 'ASX',
            'announcement_type': 'Half Yearly Report',
            'title': 'Half Year Results - Profit up 25%',
            'content': 'Revenue $150M, profit $30M, dividend $0.15',
            'price_sensitive': True
        },
        {
            'source': 'ASX',
            'announcement_type': 'Notice of Meeting',
            'title': 'Notice of Annual General Meeting',
            'content': 'AGM to be held on...',
            'price_sensitive': False
        },
        {
            'source': 'ASX',
            'announcement_type': 'Asset Acquisition & Disposal',
            'title': 'Acquisition of Mining Asset for $500M',
            'content': 'Company announces acquisition...',
            'price_sensitive': True
        },
        {
            'source': 'AFR',
            'announcement_type': None,
            'title': 'BHP announces record dividend',
            'content': 'Mining giant announces dividend increase of 15%',
            'price_sensitive': False
        },
        {
            'source': 'ASX',
            'announcement_type': 'Appendix 3Y',
            'title': 'Change of Director\'s Interest Notice',
            'content': 'Director acquired 10,000 shares',
            'price_sensitive': False
        }
    ]

    print("\nNews Quality Filter Test:")
    print("=" * 80)

    for article in test_articles:
        assessment = filter.assess_quality(
            source=article['source'],
            announcement_type=article['announcement_type'],
            title=article['title'],
            content=article['content'],
            price_sensitive=article['price_sensitive']
        )

        print(f"\nTitle: {article['title']}")
        print(f"Type: {article.get('announcement_type', 'N/A')}")
        print(f"Quality Score: {assessment['quality_score']}")
        print(f"Decision: {assessment['recommendation']}")
        print(f"Reasons: {', '.join(assessment['reasons'])}")

    print("\n" + "=" * 80)

    # Test batch filtering
    filtered = filter.filter_batch(test_articles)
    print(f"\nBatch Filter Results: {len(filtered)}/{len(test_articles)} articles passed")
    print("\nPassed articles:")
    for article in filtered:
        print(f"  - {article['title']} (score: {article['quality_assessment']['quality_score']})")


if __name__ == '__main__':
    main()
