"""
Live Recommendation Engine

Generates real-time trading recommendations from live ASX announcements.

Key differences from historical backtest:
- Uses REAL-TIME pricing (not T+1)
- Applies TIME filter (<30 min old)
- Applies TIME-OF-DAY filter (10am-2pm optimal)
- Immediate signal generation

Author: Claude Code
Date: 2025-10-10
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
import pytz

logger = logging.getLogger(__name__)


class LiveRecommendationEngine:
    """
    Generates trading recommendations from live announcements.
    """

    def __init__(self, db_path: str):
        """
        Initialize live recommendation engine.

        Args:
            db_path: Database path
        """
        self.db_path = db_path
        self.tz = pytz.timezone('Australia/Sydney')

        # Initialize components
        self._initialize_components()

        # Create live recommendations table
        self._create_recommendations_table()

    def _initialize_components(self):
        """Initialize analysis components."""
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from analysis.local_sentiment_analyzer import LocalSentimentAnalyzer
        from analysis.behavioral_filters import MaterialityFilter, TimeFilter, TimeOfDayFilter, ContrarianSignals
        from analysis.technical_indicators import TechnicalIndicators
        from analysis.bayesian_confidence import SignalCombiner

        self.sentiment_analyzer = LocalSentimentAnalyzer()
        self.materiality_filter = MaterialityFilter(min_materiality_score=0.5)
        self.time_filter = TimeFilter(max_age_minutes=30)
        self.time_of_day_filter = TimeOfDayFilter(optimal_start_hour=10, optimal_end_hour=14)
        self.contrarian_signals = ContrarianSignals(extreme_threshold=0.85)
        self.technical_indicators = TechnicalIndicators(self.db_path)
        self.signal_combiner = SignalCombiner()  # NEW: Bayesian confidence scoring

    def _create_recommendations_table(self):
        """Create table for live recommendations."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS live_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                announcement_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                confidence REAL NOT NULL,
                entry_price REAL,
                sentiment TEXT,
                sentiment_score REAL,
                sentiment_confidence REAL,
                generated_timestamp TIMESTAMP NOT NULL,
                filters_passed TEXT,
                filters_failed TEXT,
                decision_log TEXT,
                FOREIGN KEY (announcement_id) REFERENCES live_announcements (id)
            )
        """)

        conn.commit()
        conn.close()

    def get_real_time_price(self, ticker: str) -> Optional[float]:
        """
        Get real-time stock price using yfinance.

        Args:
            ticker: ASX ticker (e.g., 'BHP')

        Returns:
            Current price or None
        """
        try:
            # ASX tickers need .AX suffix for yfinance
            symbol = f"{ticker}.AX"

            stock = yf.Ticker(symbol)

            # Get most recent price
            # Try intraday data first (1-minute intervals)
            hist = stock.history(period='1d', interval='1m')

            if not hist.empty:
                return float(hist['Close'].iloc[-1])

            # Fallback: Daily data
            hist = stock.history(period='1d')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])

            return None

        except Exception as e:
            logger.warning(f"Could not fetch price for {ticker}: {e}")
            return None

    def process_announcement(self, announcement_id: int) -> Optional[Dict]:
        """
        Process a live announcement and generate recommendation.

        Args:
            announcement_id: ID from live_announcements table

        Returns:
            Recommendation dictionary or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Fetch announcement
        cursor.execute("""
            SELECT id, ticker, title, announcement_type, price_sensitive,
                   asx_timestamp, detected_timestamp, age_minutes
            FROM live_announcements
            WHERE id = ? AND processed = 0
        """, (announcement_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        announcement = {
            'id': row[0],
            'ticker': row[1],
            'title': row[2],
            'announcement_type': row[3],
            'price_sensitive': row[4],
            'asx_timestamp': datetime.strptime(row[5], '%Y-%m-%d %H:%M:%S'),
            'detected_timestamp': datetime.strptime(row[6], '%Y-%m-%d %H:%M:%S'),
            'age_minutes': row[7]
        }

        logger.info(f"\nProcessing: {announcement['ticker']} - {announcement['title']}")

        # Decision log
        decision_log = []
        filters_passed = []
        filters_failed = []

        # 1. TIME FILTER
        now = datetime.now(self.tz)
        tradeable, reason, time_adj = self.time_filter.is_tradeable_by_time(
            announcement['asx_timestamp'], now
        )

        if not tradeable:
            filters_failed.append(f"TIME: {reason}")
            decision_log.append(f"❌ TIME FILTER: {reason}")
            self._mark_processed(announcement['id'], filtered=True, reason=reason)
            return None
        else:
            filters_passed.append(f"TIME: {reason}")
            decision_log.append(f"✓ TIME FILTER: {reason}")

        # 2. MATERIALITY FILTER
        is_material, mat_reason, mat_score = self.materiality_filter.assess_materiality(
            announcement_type=announcement['announcement_type'] or '',
            title=announcement['title'],
            content='',  # Content not fetched in real-time for speed
            price_sensitive=announcement['price_sensitive'] == 1
        )

        if not is_material:
            filters_failed.append(f"MATERIALITY: {mat_reason}")
            decision_log.append(f"❌ MATERIALITY FILTER: {mat_reason}")
            self._mark_processed(announcement['id'], filtered=True, reason=mat_reason)
            return None
        else:
            filters_passed.append(f"MATERIALITY: {mat_reason}")
            decision_log.append(f"✓ MATERIALITY FILTER: {mat_reason}")

        # 3. TIME-OF-DAY FILTER
        is_optimal, tod_reason, tod_adj = self.time_of_day_filter.is_optimal_time(now)

        if not is_optimal:
            filters_failed.append(f"TIME_OF_DAY: {tod_reason}")
            decision_log.append(f"❌ TIME-OF-DAY FILTER: {tod_reason}")
            self._mark_processed(announcement['id'], filtered=True, reason=tod_reason)
            return None
        else:
            filters_passed.append(f"TIME_OF_DAY: {tod_reason}")
            decision_log.append(f"✓ TIME-OF-DAY FILTER: {tod_reason}")

        # 4. SENTIMENT ANALYSIS
        analysis = self.sentiment_analyzer.analyze_article(
            title=announcement['title'],
            content='',
            ticker=announcement['ticker']
        )

        sentiment = analysis['sentiment']
        sentiment_score = analysis['sentiment_score']
        confidence = analysis['confidence']

        decision_log.append(
            f"SENTIMENT: {sentiment} (score: {sentiment_score:.2f}, confidence: {confidence:.2f})"
        )

        if sentiment not in ['positive', 'negative']:
            decision_log.append(f"❌ NEUTRAL SENTIMENT - No trade signal")
            self._mark_processed(announcement['id'], filtered=True, reason="Neutral sentiment")
            return None

        # 5. GET REAL-TIME PRICE
        entry_price = self.get_real_time_price(announcement['ticker'])

        if not entry_price:
            decision_log.append(f"❌ No price data available")
            self._mark_processed(announcement['id'], filtered=True, reason="No price data")
            return None

        decision_log.append(f"ENTRY PRICE: ${entry_price:.2f}")

        # 6. TECHNICAL ANALYSIS (Soft Modifier)
        tech_decision = self.technical_indicators.should_enter_trade(
            announcement['ticker'],
            sentiment,
            as_of_date=announcement['asx_timestamp'].strftime('%Y-%m-%d')
        )

        tech_indicators = None
        if 'Insufficient technical data' not in tech_decision['reason']:
            tech_indicators = {
                'rsi': tech_decision.get('rsi'),
                'macd': tech_decision.get('macd'),
                'ma_trend': tech_decision.get('ma_trend'),
                'confidence_adjustment': tech_decision['confidence_adjustment']
            }
            decision_log.append(
                f"TECHNICAL: {tech_decision['reason']} (adjustment: {tech_decision['confidence_adjustment']:+.2f})"
            )
        else:
            decision_log.append(f"⚠️ TECHNICAL: {tech_decision['reason']}")

        # 7. GET RECENT PRICE CHANGE FOR CONTRARIAN SIGNALS
        recent_price = self.get_price_days_ago(announcement['ticker'], days_ago=5)
        recent_price_change = None
        if recent_price:
            recent_price_change = ((entry_price - recent_price) / recent_price) * 100

        # 8. BAYESIAN CONFIDENCE COMBINATION (REPLACES ADDITIVE MODEL)
        # Convert to AEST time string for time-of-day calculation
        current_time_aest = now.strftime('%H:%M:%S')

        confidence, breakdown = self.signal_combiner.compute_confidence(
            sentiment_score=sentiment_score,
            announcement_age_minutes=announcement['age_minutes'],
            current_time_aest=current_time_aest,
            technical_indicators=tech_indicators,
            is_material=is_material,
            recent_price_change=recent_price_change
        )

        # Log Bayesian breakdown
        decision_log.append(f"\nBAYESIAN CONFIDENCE BREAKDOWN:")
        decision_log.append(f"  Base sentiment: {breakdown['base_sentiment']:.3f}")
        decision_log.append(f"  Time freshness boost: {breakdown['time_boost']:.3f}x")
        decision_log.append(f"  Time-of-day boost: {breakdown['time_of_day_boost']:.3f}x")
        decision_log.append(f"  Technical boost: {breakdown['technical_boost']:.3f}x")
        decision_log.append(f"  Materiality factor: {breakdown['materiality_factor']:.3f}x")
        decision_log.append(f"  Contrarian factor: {breakdown['contrarian_factor']:.3f}x")
        decision_log.append(f"  Combined odds: {breakdown['combined_odds']:.3f}")
        decision_log.append(f"FINAL CONFIDENCE: {confidence:.3f}")

        # 9. DECISION
        if confidence < 0.6:
            decision_log.append(f"❌ CONFIDENCE TOO LOW ({confidence:.2f} < 0.6)")
            self._mark_processed(announcement['id'], filtered=True, reason="Low confidence")
            return None

        # GENERATE RECOMMENDATION
        recommendation = {
            'announcement_id': announcement['id'],
            'ticker': announcement['ticker'],
            'recommendation': 'BUY' if sentiment == 'positive' else 'SELL',
            'confidence': confidence,
            'entry_price': entry_price,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'sentiment_confidence': analysis['confidence'],
            'generated_timestamp': datetime.now(self.tz),
            'filters_passed': ', '.join(filters_passed),
            'filters_failed': ', '.join(filters_failed),
            'decision_log': '\n'.join(decision_log)
        }

        # Store recommendation
        self._store_recommendation(recommendation)

        # Mark announcement as processed
        self._mark_processed(announcement['id'], recommended=True)

        logger.info(f"✓ RECOMMENDATION: {recommendation['recommendation']} {announcement['ticker']} @ ${entry_price:.2f} (Confidence: {confidence:.2f})")

        return recommendation

    def get_price_days_ago(self, ticker: str, days_ago: int = 5) -> Optional[float]:
        """Get price from N days ago."""
        try:
            symbol = f"{ticker}.AX"
            stock = yf.Ticker(symbol)
            hist = stock.history(period='10d')

            if len(hist) >= days_ago:
                return float(hist['Close'].iloc[-days_ago])

            return None
        except:
            return None

    def _store_recommendation(self, rec: Dict):
        """Store recommendation in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO live_recommendations (
                announcement_id, ticker, recommendation, confidence, entry_price,
                sentiment, sentiment_score, sentiment_confidence,
                generated_timestamp, filters_passed, filters_failed, decision_log
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec['announcement_id'],
            rec['ticker'],
            rec['recommendation'],
            rec['confidence'],
            rec['entry_price'],
            rec['sentiment'],
            rec['sentiment_score'],
            rec['sentiment_confidence'],
            rec['generated_timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            rec['filters_passed'],
            rec['filters_failed'],
            rec['decision_log']
        ))

        conn.commit()
        conn.close()

    def _mark_processed(self, announcement_id: int, filtered: bool = False, recommended: bool = False, reason: str = ''):
        """Mark announcement as processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE live_announcements
            SET processed = 1,
                recommendation_generated = ?
            WHERE id = ?
        """, (1 if recommended else 0, announcement_id))

        conn.commit()
        conn.close()

    def process_unprocessed_announcements(self) -> List[Dict]:
        """
        Process all unprocessed announcements.

        Returns:
            List of generated recommendations
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM live_announcements
            WHERE processed = 0
            ORDER BY asx_timestamp DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        recommendations = []

        for row in rows:
            rec = self.process_announcement(row[0])
            if rec:
                recommendations.append(rec)

        return recommendations


def main():
    """Test live recommendation engine."""
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import config

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    engine = LiveRecommendationEngine(config.DATABASE_PATH)

    # Process any unprocessed announcements
    recommendations = engine.process_unprocessed_announcements()

    print(f"\nGenerated {len(recommendations)} recommendations")


if __name__ == '__main__':
    main()
