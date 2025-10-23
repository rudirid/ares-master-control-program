"""
News Pattern Analysis

Analyzes patterns in news sentiment and price movements to identify:
- Which themes predict price movements
- Time lag between news and price reaction
- Magnitude of typical moves
- False positive rate

Author: Claude Code
Date: 2025-10-09
"""

import pandas as pd
import numpy as np
import json
import logging
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class PatternAnalyzer:
    """
    Analyzes patterns in news sentiment and price impact data.
    """

    def __init__(self, csv_path: str):
        """
        Initialize the pattern analyzer.

        Args:
            csv_path: Path to news impact analysis CSV file
        """
        self.df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(self.df)} articles from {csv_path}")

    def analyze_theme_performance(self) -> Dict:
        """
        Analyze which themes best predict price movements.

        Returns:
            Dictionary with theme performance metrics
        """
        # Split themes (they're pipe-separated)
        theme_data = []

        for _, row in self.df.iterrows():
            themes = str(row['themes']).split('|') if pd.notna(row['themes']) else []

            for theme in themes:
                if theme:
                    theme_data.append({
                        'theme': theme.strip(),
                        'sentiment': row['sentiment'],
                        'sentiment_score': row['sentiment_score'],
                        'price_change_1d': row['price_change_pct_1d'],
                        'price_change_3d': row['price_change_pct_3d'],
                        'price_change_7d': row['price_change_pct_7d']
                    })

        theme_df = pd.DataFrame(theme_data)

        # Calculate metrics per theme
        results = []

        for theme in theme_df['theme'].unique():
            subset = theme_df[theme_df['theme'] == theme]

            # Filter out NaN price changes
            subset_1d = subset[subset['price_change_1d'].notna()]
            subset_3d = subset[subset['price_change_3d'].notna()]
            subset_7d = subset[subset['price_change_7d'].notna()]

            if len(subset_1d) < 3:  # Need at least 3 samples
                continue

            # Calculate correlation between sentiment and price change
            corr_1d = subset_1d[['sentiment_score', 'price_change_1d']].corr().iloc[0, 1] if len(subset_1d) > 1 else 0
            corr_3d = subset_3d[['sentiment_score', 'price_change_3d']].corr().iloc[0, 1] if len(subset_3d) > 1 else 0
            corr_7d = subset_7d[['sentiment_score', 'price_change_7d']].corr().iloc[0, 1] if len(subset_7d) > 1 else 0

            # Average magnitude
            avg_abs_1d = subset_1d['price_change_1d'].abs().mean()
            avg_abs_3d = subset_3d['price_change_3d'].abs().mean()
            avg_abs_7d = subset_7d['price_change_7d'].abs().mean()

            # Directional accuracy (did sentiment predict direction correctly?)
            correct_1d = ((subset_1d['sentiment_score'] > 0) == (subset_1d['price_change_1d'] > 0)).mean()
            correct_3d = ((subset_3d['sentiment_score'] > 0) == (subset_3d['price_change_3d'] > 0)).mean()
            correct_7d = ((subset_7d['sentiment_score'] > 0) == (subset_7d['price_change_7d'] > 0)).mean()

            results.append({
                'theme': theme,
                'count': len(subset),
                'correlation_1d': round(corr_1d, 3),
                'correlation_3d': round(corr_3d, 3),
                'correlation_7d': round(corr_7d, 3),
                'avg_magnitude_1d': round(avg_abs_1d, 2),
                'avg_magnitude_3d': round(avg_abs_3d, 2),
                'avg_magnitude_7d': round(avg_abs_7d, 2),
                'directional_accuracy_1d': round(correct_1d, 2),
                'directional_accuracy_3d': round(correct_3d, 2),
                'directional_accuracy_7d': round(correct_7d, 2)
            })

        # Sort by strongest 1-day correlation
        results.sort(key=lambda x: abs(x['correlation_1d']), reverse=True)

        return {
            'themes': results,
            'summary': {
                'total_themes': len(results),
                'avg_correlation_1d': np.mean([r['correlation_1d'] for r in results]),
                'avg_correlation_3d': np.mean([r['correlation_3d'] for r in results]),
                'avg_correlation_7d': np.mean([r['correlation_7d'] for r in results])
            }
        }

    def analyze_time_lag(self) -> Dict:
        """
        Analyze the time lag between news and price reaction.

        Returns:
            Dictionary with time lag analysis
        """
        # Filter rows with complete data
        complete = self.df[
            self.df['price_change_pct_1d'].notna() &
            self.df['price_change_pct_3d'].notna() &
            self.df['price_change_pct_7d'].notna()
        ].copy()

        if len(complete) == 0:
            return {'error': 'No complete data available'}

        # Calculate cumulative absolute changes
        complete['cumulative_abs_1d'] = complete['price_change_pct_1d'].abs()
        complete['cumulative_abs_3d'] = complete['price_change_pct_3d'].abs()
        complete['cumulative_abs_7d'] = complete['price_change_pct_7d'].abs()

        # Group by sentiment
        lag_by_sentiment = {}

        for sentiment in ['positive', 'negative', 'neutral']:
            subset = complete[complete['sentiment'] == sentiment]

            if len(subset) > 0:
                lag_by_sentiment[sentiment] = {
                    'count': len(subset),
                    'avg_move_1d': round(subset['cumulative_abs_1d'].mean(), 2),
                    'avg_move_3d': round(subset['cumulative_abs_3d'].mean(), 2),
                    'avg_move_7d': round(subset['cumulative_abs_7d'].mean(), 2),
                    # What % of total 7-day move happens in first day?
                    'pct_in_1d': round((subset['cumulative_abs_1d'].sum() / subset['cumulative_abs_7d'].sum() * 100), 1),
                    'pct_in_3d': round((subset['cumulative_abs_3d'].sum() / subset['cumulative_abs_7d'].sum() * 100), 1)
                }

        # Overall timing
        total_1d = complete['cumulative_abs_1d'].sum()
        total_3d = complete['cumulative_abs_3d'].sum()
        total_7d = complete['cumulative_abs_7d'].sum()

        return {
            'by_sentiment': lag_by_sentiment,
            'overall': {
                'pct_reaction_day1': round(total_1d / total_7d * 100, 1),
                'pct_reaction_day3': round(total_3d / total_7d * 100, 1),
                'pct_reaction_day7': 100.0
            }
        }

    def analyze_magnitude(self) -> Dict:
        """
        Analyze magnitude of price moves by news type.

        Returns:
            Dictionary with magnitude analysis
        """
        # By sentiment
        magnitude_by_sentiment = {}

        for sentiment in ['positive', 'negative', 'neutral']:
            subset = self.df[self.df['sentiment'] == sentiment]

            magnitude_by_sentiment[sentiment] = {
                'count': len(subset),
                'avg_1d': round(subset['price_change_pct_1d'].abs().mean(), 2),
                'max_1d': round(subset['price_change_pct_1d'].abs().max(), 2),
                'median_1d': round(subset['price_change_pct_1d'].abs().median(), 2),
                'avg_3d': round(subset['price_change_pct_3d'].abs().mean(), 2),
                'avg_7d': round(subset['price_change_pct_7d'].abs().mean(), 2)
            }

        # By confidence level
        magnitude_by_confidence = {}
        self.df['confidence_bucket'] = pd.cut(
            self.df['confidence'],
            bins=[0, 0.4, 0.7, 1.0],
            labels=['Low', 'Medium', 'High']
        )

        for conf in ['Low', 'Medium', 'High']:
            subset = self.df[self.df['confidence_bucket'] == conf]

            if len(subset) > 0:
                magnitude_by_confidence[conf] = {
                    'count': len(subset),
                    'avg_1d': round(subset['price_change_pct_1d'].abs().mean(), 2),
                    'median_1d': round(subset['price_change_pct_1d'].abs().median(), 2)
                }

        return {
            'by_sentiment': magnitude_by_sentiment,
            'by_confidence': magnitude_by_confidence
        }

    def analyze_false_positives(self, threshold: float = 0.5) -> Dict:
        """
        Analyze false positive rate - news that seemed important but price didn't move.

        Args:
            threshold: Price change threshold (%) to consider "no movement"

        Returns:
            Dictionary with false positive analysis
        """
        # Define "strong signal" as high confidence + strong sentiment
        strong_positive = self.df[
            (self.df['sentiment'] == 'positive') &
            (self.df['confidence'] > 0.6) &
            (self.df['sentiment_score'] > 0.3)
        ]

        strong_negative = self.df[
            (self.df['sentiment'] == 'negative') &
            (self.df['confidence'] > 0.6) &
            (self.df['sentiment_score'] < -0.3)
        ]

        # Count how many had minimal price movement
        def count_minimal_movement(subset, threshold):
            subset_1d = subset[subset['price_change_pct_1d'].notna()]
            minimal = subset_1d[subset_1d['price_change_pct_1d'].abs() < threshold]
            return len(minimal), len(subset_1d)

        pos_false, pos_total = count_minimal_movement(strong_positive, threshold)
        neg_false, neg_total = count_minimal_movement(strong_negative, threshold)

        # Also check wrong direction
        def count_wrong_direction(subset):
            subset_1d = subset[subset['price_change_pct_1d'].notna()]

            if subset['sentiment'].iloc[0] == 'positive':
                wrong = subset_1d[subset_1d['price_change_pct_1d'] < 0]
            else:
                wrong = subset_1d[subset_1d['price_change_pct_1d'] > 0]

            return len(wrong), len(subset_1d)

        pos_wrong, _ = count_wrong_direction(strong_positive) if len(strong_positive) > 0 else (0, 0)
        neg_wrong, _ = count_wrong_direction(strong_negative) if len(strong_negative) > 0 else (0, 0)

        return {
            'threshold_pct': threshold,
            'positive_signals': {
                'total': int(pos_total),
                'false_positives': int(pos_false),
                'wrong_direction': int(pos_wrong),
                'false_positive_rate': round(pos_false / pos_total * 100, 1) if pos_total > 0 else 0,
                'wrong_direction_rate': round(pos_wrong / pos_total * 100, 1) if pos_total > 0 else 0
            },
            'negative_signals': {
                'total': int(neg_total),
                'false_positives': int(neg_false),
                'wrong_direction': int(neg_wrong),
                'false_positive_rate': round(neg_false / neg_total * 100, 1) if neg_total > 0 else 0,
                'wrong_direction_rate': round(neg_wrong / neg_total * 100, 1) if neg_total > 0 else 0
            }
        }

    def generate_full_report(self, output_json: Optional[str] = None) -> Dict:
        """
        Generate complete pattern analysis report.

        Args:
            output_json: Optional path to save JSON report

        Returns:
            Dictionary with all analysis results
        """
        logger.info("Generating pattern analysis report...")

        report = {
            'metadata': {
                'total_articles': len(self.df),
                'articles_with_price_data': len(self.df[self.df['price_change_pct_1d'].notna()]),
                'date_range': {
                    'start': str(self.df['article_date'].min()),
                    'end': str(self.df['article_date'].max())
                }
            },
            'theme_performance': self.analyze_theme_performance(),
            'time_lag_analysis': self.analyze_time_lag(),
            'magnitude_analysis': self.analyze_magnitude(),
            'false_positive_analysis': self.analyze_false_positives()
        }

        if output_json:
            with open(output_json, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {output_json}")

        return report


def main():
    """
    Test the pattern analyzer.
    """
    import sys
    import os

    print("\n" + "=" * 70)
    print("Pattern Analysis")
    print("=" * 70 + "\n")

    csv_path = 'results/news_impact_analysis.csv'

    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found")
        print("Please run analyze_news_impact.py first")
        return

    analyzer = PatternAnalyzer(csv_path)
    report = analyzer.generate_full_report('results/pattern_analysis.json')

    # Print summary
    print("\n=== THEME PERFORMANCE ===")
    for theme in report['theme_performance']['themes'][:10]:
        print(f"\n{theme['theme']} (n={theme['count']})")
        print(f"  1-day correlation: {theme['correlation_1d']:.3f}")
        print(f"  Avg magnitude: {theme['avg_magnitude_1d']:.2f}%")
        print(f"  Directional accuracy: {theme['directional_accuracy_1d']:.0%}")

    print("\n=== TIME LAG ===")
    lag = report['time_lag_analysis']['overall']
    print(f"Reaction in Day 1: {lag['pct_reaction_day1']}%")
    print(f"Reaction by Day 3: {lag['pct_reaction_day3']}%")

    print("\n=== FALSE POSITIVES ===")
    fp = report['false_positive_analysis']
    print(f"Positive signals: {fp['positive_signals']['false_positive_rate']}% false positive rate")
    print(f"Negative signals: {fp['negative_signals']['false_positive_rate']}% false positive rate")

    print("\n" + "=" * 70)
    print(f"Full report saved to: results/pattern_analysis.json")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
