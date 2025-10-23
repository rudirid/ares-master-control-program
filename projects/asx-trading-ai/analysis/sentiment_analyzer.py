"""
News Sentiment Analysis using Claude API

This module uses Anthropic's Claude API to analyze news articles and extract:
- Sentiment (positive/negative/neutral)
- Key themes and topics
- Impact assessment

Author: Claude Code
Date: 2025-10-09
"""

import os
import json
import logging
from typing import Dict, Optional
from anthropic import Anthropic

# Setup logging
logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyzes news articles using Claude API to extract sentiment and themes.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the sentiment analyzer.

        Args:
            api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.
        """
        if api_key is None:
            api_key = os.environ.get('ANTHROPIC_API_KEY')

        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model

    def analyze_article(self, title: str, content: str, ticker: str) -> Dict:
        """
        Analyze a news article for sentiment and themes.

        Args:
            title: Article title
            content: Article content/preview
            ticker: Stock ticker symbol

        Returns:
            Dictionary with:
                - sentiment: 'positive', 'negative', or 'neutral'
                - sentiment_score: float from -1.0 (very negative) to 1.0 (very positive)
                - confidence: float from 0.0 to 1.0
                - themes: list of key themes/topics
                - summary: brief summary of analysis
                - impact_assessment: potential impact on stock price
        """
        try:
            # Build the prompt
            prompt = self._build_analysis_prompt(title, content, ticker)

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            response_text = message.content[0].text
            result = self._parse_response(response_text)

            logger.debug(f"Analysis complete for {ticker}: {result['sentiment']}")
            return result

        except Exception as e:
            logger.error(f"Error analyzing article: {e}")
            return self._get_error_result(str(e))

    def _build_analysis_prompt(self, title: str, content: str, ticker: str) -> str:
        """
        Build the analysis prompt for Claude.

        Args:
            title: Article title
            content: Article content
            ticker: Stock ticker

        Returns:
            Formatted prompt string
        """
        prompt = f"""Analyze this news article about {ticker} and provide a structured sentiment analysis.

ARTICLE TITLE:
{title}

ARTICLE CONTENT:
{content}

Please provide your analysis in the following JSON format:

{{
  "sentiment": "positive" | "negative" | "neutral",
  "sentiment_score": <float from -1.0 to 1.0>,
  "confidence": <float from 0.0 to 1.0>,
  "themes": ["theme1", "theme2", "theme3"],
  "summary": "Brief 1-2 sentence summary of why you classified it this way",
  "impact_assessment": "Brief assessment of potential stock price impact"
}}

Guidelines:
- sentiment: Overall tone (positive/negative/neutral for the company/stock)
- sentiment_score: -1.0 (very negative) to 1.0 (very positive), 0.0 is neutral
- confidence: How confident you are in this assessment (0.0-1.0)
- themes: 3-5 key themes or topics (e.g., "earnings", "acquisition", "regulatory", "management")
- summary: Explain your reasoning briefly
- impact_assessment: Likely short-term impact on stock price

IMPORTANT: Return ONLY the JSON object, no additional text or markdown formatting."""

        return prompt

    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse Claude's JSON response.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed dictionary
        """
        try:
            # Clean up response (remove markdown code blocks if present)
            text = response_text.strip()
            if text.startswith('```'):
                # Remove markdown code blocks
                lines = text.split('\n')
                text = '\n'.join(lines[1:-1]) if len(lines) > 2 else text

            # Parse JSON
            result = json.loads(text)

            # Validate and normalize
            result['sentiment'] = result.get('sentiment', 'neutral').lower()
            result['sentiment_score'] = float(result.get('sentiment_score', 0.0))
            result['confidence'] = float(result.get('confidence', 0.5))
            result['themes'] = result.get('themes', [])
            result['summary'] = result.get('summary', '')
            result['impact_assessment'] = result.get('impact_assessment', '')

            # Clamp values
            result['sentiment_score'] = max(-1.0, min(1.0, result['sentiment_score']))
            result['confidence'] = max(0.0, min(1.0, result['confidence']))

            # Validate sentiment
            if result['sentiment'] not in ['positive', 'negative', 'neutral']:
                logger.warning(f"Invalid sentiment: {result['sentiment']}, defaulting to neutral")
                result['sentiment'] = 'neutral'

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text: {response_text}")
            return self._get_error_result(f"JSON parse error: {e}")
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return self._get_error_result(str(e))

    def _get_error_result(self, error_msg: str) -> Dict:
        """
        Return a default result for errors.

        Args:
            error_msg: Error message

        Returns:
            Default result dictionary
        """
        return {
            'sentiment': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'themes': [],
            'summary': f'Analysis failed: {error_msg}',
            'impact_assessment': 'Unable to assess',
            'error': error_msg
        }

    def analyze_batch(self, articles: list, delay: float = 1.0) -> list:
        """
        Analyze multiple articles with rate limiting.

        Args:
            articles: List of article dictionaries with 'title', 'content', 'ticker'
            delay: Delay between API calls in seconds

        Returns:
            List of analysis results
        """
        import time

        results = []
        for idx, article in enumerate(articles):
            logger.info(f"Analyzing article {idx + 1}/{len(articles)}: {article.get('ticker')}")

            result = self.analyze_article(
                title=article.get('title', ''),
                content=article.get('content', ''),
                ticker=article.get('ticker', '')
            )

            result['article_id'] = article.get('id')
            results.append(result)

            # Rate limiting
            if idx < len(articles) - 1:
                time.sleep(delay)

        return results


# Test function
def test_sentiment_analyzer():
    """
    Test the sentiment analyzer with sample articles.
    """
    print("\n" + "=" * 70)
    print("Testing Sentiment Analyzer")
    print("=" * 70 + "\n")

    analyzer = SentimentAnalyzer()

    # Test articles
    test_articles = [
        {
            "id": 1,
            "ticker": "BHP",
            "title": "BHP reports record profits amid strong commodity demand",
            "content": "Mining giant BHP has announced record annual profits, driven by strong iron ore prices and increased production across its portfolio."
        },
        {
            "id": 2,
            "ticker": "CBA",
            "title": "Commonwealth Bank faces regulatory scrutiny over lending practices",
            "content": "Australia's largest bank is under investigation by ASIC following allegations of improper lending assessments."
        },
        {
            "id": 3,
            "ticker": "WOW",
            "title": "Woolworths maintains market position despite competitive pressure",
            "content": "Woolworths reported steady sales growth, maintaining its market share in the face of increased competition from discount retailers."
        }
    ]

    for article in test_articles:
        print(f"\nAnalyzing: {article['title']}")
        print("-" * 70)

        result = analyzer.analyze_article(
            title=article['title'],
            content=article['content'],
            ticker=article['ticker']
        )

        print(f"Sentiment: {result['sentiment']}")
        print(f"Score: {result['sentiment_score']:.2f}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Themes: {', '.join(result['themes'])}")
        print(f"Summary: {result['summary']}")
        print(f"Impact: {result['impact_assessment']}")

        if 'error' in result:
            print(f"ERROR: {result['error']}")

    print("\n" + "=" * 70)
    print("Testing complete!")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    test_sentiment_analyzer()
