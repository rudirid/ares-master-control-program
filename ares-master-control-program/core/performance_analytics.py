"""
ARES Agent Lifecycle System - Performance Analytics
Analyzes agent performance, learning rates, and generates insights

Responsibilities:
- Calculate performance metrics and trends
- Detect learning plateaus
- Analyze pattern effectiveness
- Generate improvement recommendations
- Compare actual vs target performance
- Calculate ROI and resource efficiency
"""

import json
import yaml
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class PerformanceStats:
    """Complete performance statistics for an agent"""
    agent_id: str
    version: str

    # Core metrics
    total_invocations: int
    success_rate: float
    failure_rate: float

    # Time metrics
    avg_time_seconds: float
    min_time_seconds: float
    max_time_seconds: float
    target_time_seconds: float
    time_performance_ratio: float  # target/actual (>1.0 = faster than target)

    # Reflection metrics
    correction_rate: float
    deep_reflection_count: int
    shallow_reflection_count: int
    total_reflections: int
    deep_reflection_percentage: float

    # Learning metrics
    first_n_success_rate: float
    last_n_success_rate: float
    learning_velocity: float  # % improvement
    plateau_detected: bool

    # Pattern effectiveness
    pattern_stats: Dict[str, Dict[str, float]]  # pattern_id -> {usage, success, effectiveness}
    top_patterns: List[Tuple[str, float]]  # (pattern_id, effectiveness)

    # Comparison to targets
    meets_success_target: bool
    meets_time_target: bool
    overall_health: str  # 'excellent', 'good', 'needs_improvement', 'critical'

    # Recommendations
    recommendations: List[str]


@dataclass
class TrendAnalysis:
    """Trend analysis over time"""
    period_days: int
    success_rate_trend: str  # 'improving', 'stable', 'declining'
    time_trend: str  # 'faster', 'stable', 'slower'
    invocations_per_day: float
    projected_monthly_invocations: float


class PerformanceAnalytics:
    """
    Analyzes agent performance and generates insights

    Analysis Types:
    - Current performance snapshot
    - Trend analysis (learning over time)
    - Pattern effectiveness
    - Resource efficiency (ROI)
    - Health assessment
    - Improvement recommendations
    """

    def __init__(
        self,
        agent_id: str,
        agents_dir: Optional[Path] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize performance analytics

        Args:
            agent_id: Agent identifier
            agents_dir: Path to agents directory
            config_path: Path to agent_lifecycle.yaml
        """
        self.agent_id = agent_id
        self.project_root = Path(__file__).parent.parent
        self.agents_dir = agents_dir or self.project_root / "agents"
        self.agent_dir = self.agents_dir / agent_id

        # Agent files
        self.agent_config_file = self.agent_dir / "agent-config.yaml"
        self.performance_file = self.agent_dir / "performance" / "metrics.json"
        self.episodic_db = self.agent_dir / "memory" / "episodic.db"

        # System config
        self.config_path = config_path or self.project_root / "config" / "agent_lifecycle.yaml"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load system configuration"""
        if not self.config_path.exists():
            return {}

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def get_stats(self, n_recent: int = 10) -> PerformanceStats:
        """
        Get complete performance statistics

        Args:
            n_recent: Number of recent tasks for learning rate calculation

        Returns:
            PerformanceStats with all metrics
        """
        # Load metrics
        if not self.performance_file.exists():
            raise FileNotFoundError(f"Performance metrics not found for {self.agent_id}")

        with open(self.performance_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)

        # Load agent config for targets
        agent_config = self._load_agent_config()

        # Extract core metrics
        core = metrics['metrics']['core_performance']
        total_invocations = core['total_invocations']
        success_rate = core['success_rate']
        failure_rate = 100.0 - success_rate

        # Time metrics
        time_perf = metrics['metrics'].get('time_performance', {})
        avg_time = time_perf.get('avg_time_seconds', 0.0)
        min_time = time_perf.get('min_time_seconds', 0.0)
        max_time = time_perf.get('max_time_seconds', 0.0)
        target_time = agent_config.get('target_time_seconds', 300)
        time_ratio = (target_time / avg_time) if avg_time > 0 else 0.0

        # Reflection metrics
        reflection = metrics['metrics'].get('reflection_quality', {})
        correction_rate = reflection.get('correction_rate', 0.0)
        depth = reflection.get('reflection_depth', {'shallow': 0, 'deep': 0})
        shallow_count = depth.get('shallow', 0)
        deep_count = depth.get('deep', 0)
        total_reflections = shallow_count + deep_count
        deep_percentage = (deep_count / total_reflections * 100) if total_reflections > 0 else 0.0

        # Learning rate
        first_n_rate, last_n_rate, velocity, plateau = self._calculate_learning_rate(n_recent)

        # Pattern effectiveness
        pattern_eff = metrics['metrics'].get('pattern_effectiveness', {})
        pattern_stats = {}
        for pattern_id, stats in pattern_eff.items():
            pattern_stats[pattern_id] = {
                'usage': stats['usage'],
                'success': stats['success'],
                'effectiveness': stats['effectiveness']
            }

        # Top patterns (sorted by effectiveness)
        top_patterns = sorted(
            [(pid, stats['effectiveness']) for pid, stats in pattern_stats.items()],
            key=lambda x: x[1],
            reverse=True
        )[:5]  # Top 5

        # Target comparison
        target_success = agent_config.get('target_success_rate', 85.0)
        meets_success = success_rate >= target_success
        meets_time = time_ratio >= 1.0  # Faster or equal to target

        # Health assessment
        health = self._assess_health(
            success_rate, target_success,
            time_ratio,
            correction_rate,
            total_invocations
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            success_rate, target_success,
            time_ratio,
            correction_rate,
            plateau,
            total_invocations,
            pattern_stats
        )

        return PerformanceStats(
            agent_id=self.agent_id,
            version=metrics['version'],
            total_invocations=total_invocations,
            success_rate=success_rate,
            failure_rate=failure_rate,
            avg_time_seconds=avg_time,
            min_time_seconds=min_time,
            max_time_seconds=max_time,
            target_time_seconds=target_time,
            time_performance_ratio=time_ratio,
            correction_rate=correction_rate,
            deep_reflection_count=deep_count,
            shallow_reflection_count=shallow_count,
            total_reflections=total_reflections,
            deep_reflection_percentage=deep_percentage,
            first_n_success_rate=first_n_rate,
            last_n_success_rate=last_n_rate,
            learning_velocity=velocity,
            plateau_detected=plateau,
            pattern_stats=pattern_stats,
            top_patterns=top_patterns,
            meets_success_target=meets_success,
            meets_time_target=meets_time,
            overall_health=health,
            recommendations=recommendations
        )

    def _load_agent_config(self) -> Dict:
        """Load agent configuration"""
        if not self.agent_config_file.exists():
            return {}

        with open(self.agent_config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _calculate_learning_rate(self, n: int) -> Tuple[float, float, float, bool]:
        """
        Calculate learning rate by comparing first N vs last N tasks

        Args:
            n: Number of tasks to compare

        Returns:
            (first_n_success_rate, last_n_success_rate, learning_velocity, plateau_detected)
        """
        if not self.episodic_db.exists():
            return 0.0, 0.0, 0.0, False

        try:
            conn = sqlite3.connect(self.episodic_db)
            cursor = conn.cursor()

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM episodic_memory")
            total = cursor.fetchone()[0]

            if total < n * 2:
                # Not enough data for comparison
                conn.close()
                return 0.0, 0.0, 0.0, False

            # First N tasks
            cursor.execute("""
                SELECT AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END)
                FROM (
                    SELECT success FROM episodic_memory
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
            """, (n,))
            first_n_rate = cursor.fetchone()[0] or 0.0

            # Last N tasks
            cursor.execute("""
                SELECT AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END)
                FROM (
                    SELECT success FROM episodic_memory
                    ORDER BY timestamp DESC
                    LIMIT ?
                )
            """, (n,))
            last_n_rate = cursor.fetchone()[0] or 0.0

            conn.close()

            # Learning velocity (% improvement)
            velocity = last_n_rate - first_n_rate

            # Plateau detection: If last N is within ±5% of first N and both are high
            plateau = (
                abs(velocity) < 5.0 and
                first_n_rate >= 80.0 and
                last_n_rate >= 80.0
            )

            return first_n_rate, last_n_rate, velocity, plateau

        except Exception:
            return 0.0, 0.0, 0.0, False

    def _assess_health(
        self,
        success_rate: float,
        target_success: float,
        time_ratio: float,
        correction_rate: float,
        total_invocations: int
    ) -> str:
        """
        Assess overall agent health

        Returns: 'excellent', 'good', 'needs_improvement', 'critical'
        """
        if total_invocations < 5:
            return 'insufficient_data'

        # Scoring system
        score = 0

        # Success rate (40 points max)
        if success_rate >= target_success + 10:
            score += 40
        elif success_rate >= target_success:
            score += 30
        elif success_rate >= target_success - 10:
            score += 20
        else:
            score += 10

        # Time performance (30 points max)
        if time_ratio >= 1.5:  # 1.5x faster than target
            score += 30
        elif time_ratio >= 1.0:
            score += 25
        elif time_ratio >= 0.8:
            score += 15
        else:
            score += 5

        # Correction rate (20 points max) - lower is better
        if correction_rate <= 5:
            score += 20
        elif correction_rate <= 10:
            score += 15
        elif correction_rate <= 20:
            score += 10
        else:
            score += 5

        # Invocation count (10 points max) - more data = more reliable
        if total_invocations >= 50:
            score += 10
        elif total_invocations >= 20:
            score += 7
        elif total_invocations >= 10:
            score += 5
        else:
            score += 2

        # Total: 100 points
        if score >= 85:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'needs_improvement'
        else:
            return 'critical'

    def _generate_recommendations(
        self,
        success_rate: float,
        target_success: float,
        time_ratio: float,
        correction_rate: float,
        plateau: bool,
        total_invocations: int,
        pattern_stats: Dict[str, Dict]
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Success rate recommendations
        if success_rate < target_success - 10:
            recommendations.append(
                f"⚠ Success rate ({success_rate:.1f}%) significantly below target ({target_success:.1f}%). "
                "Consider reviewing patterns or triggering evolution."
            )
        elif success_rate < target_success:
            recommendations.append(
                f"→ Success rate ({success_rate:.1f}%) slightly below target ({target_success:.1f}%). "
                "Monitor next 5-10 invocations."
            )

        # Time performance recommendations
        if time_ratio < 0.8:
            recommendations.append(
                f"⚠ Execution time slower than target (ratio: {time_ratio:.2f}). "
                "Consider optimizing patterns or prompts."
            )

        # Correction rate recommendations
        if correction_rate > 15:
            recommendations.append(
                f"⚠ High correction rate ({correction_rate:.1f}%). "
                "Agent is frequently self-correcting - may indicate unclear patterns or complex tasks."
            )

        # Plateau recommendations
        if plateau:
            recommendations.append(
                "✓ Learning plateau detected (stable high performance). "
                "Agent is mature. Consider checking for state-of-the-art updates."
            )

        # Data volume recommendations
        if total_invocations < 10:
            recommendations.append(
                f"ℹ Low invocation count ({total_invocations}). "
                "Confidence in metrics will improve with more data (target: 10+)."
            )
        elif total_invocations >= 10 and total_invocations < 50:
            recommendations.append(
                f"→ Invocation count ({total_invocations}) sufficient for initial analysis. "
                "Consider evolution after reaching 10 invocations if issues detected."
            )

        # Pattern recommendations
        if pattern_stats:
            ineffective_patterns = [
                (pid, stats['effectiveness'])
                for pid, stats in pattern_stats.items()
                if stats['usage'] >= 3 and stats['effectiveness'] < 60
            ]

            if ineffective_patterns:
                pattern_list = ', '.join([f"{p[0]} ({p[1]:.0f}%)" for p in ineffective_patterns])
                recommendations.append(
                    f"⚠ Low-effectiveness patterns detected: {pattern_list}. "
                    "Consider removing or revising these patterns."
                )

        # If no issues, positive feedback
        if not recommendations:
            recommendations.append("✓ Agent performing well. No immediate improvements needed.")

        return recommendations

    def get_trend_analysis(self, days: int = 30) -> Optional[TrendAnalysis]:
        """
        Analyze performance trends over time period

        Args:
            days: Number of days to analyze

        Returns:
            TrendAnalysis or None if insufficient data
        """
        if not self.episodic_db.exists():
            return None

        try:
            conn = sqlite3.connect(self.episodic_db)
            cursor = conn.cursor()

            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get tasks in period
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time_seconds) as avg_time
                FROM episodic_memory
                WHERE timestamp >= ?
            """, (cutoff_date,))

            row = cursor.fetchone()
            total_tasks = row[0]

            if total_tasks < 2:
                conn.close()
                return None

            current_success_rate = row[1] or 0.0
            current_avg_time = row[2] or 0.0

            # Compare first half vs second half for trends
            cursor.execute("""
                SELECT timestamp FROM episodic_memory
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (cutoff_date,))

            timestamps = [row[0] for row in cursor.fetchall()]
            midpoint_idx = len(timestamps) // 2

            if midpoint_idx < 1:
                conn.close()
                return None

            midpoint_time = timestamps[midpoint_idx]

            # First half stats
            cursor.execute("""
                SELECT
                    AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time_seconds) as avg_time
                FROM episodic_memory
                WHERE timestamp >= ? AND timestamp < ?
            """, (cutoff_date, midpoint_time))

            first_half = cursor.fetchone()
            first_success = first_half[0] or 0.0
            first_time = first_half[1] or 0.0

            # Second half stats
            cursor.execute("""
                SELECT
                    AVG(CASE WHEN success = 1 THEN 100.0 ELSE 0.0 END) as success_rate,
                    AVG(execution_time_seconds) as avg_time
                FROM episodic_memory
                WHERE timestamp >= ?
            """, (midpoint_time,))

            second_half = cursor.fetchone()
            second_success = second_half[0] or 0.0
            second_time = second_half[1] or 0.0

            conn.close()

            # Determine trends
            success_diff = second_success - first_success
            if success_diff > 5:
                success_trend = 'improving'
            elif success_diff < -5:
                success_trend = 'declining'
            else:
                success_trend = 'stable'

            time_diff = second_time - first_time
            if time_diff < -5:  # 5 seconds faster
                time_trend = 'faster'
            elif time_diff > 5:
                time_trend = 'slower'
            else:
                time_trend = 'stable'

            # Calculate invocations per day
            invocations_per_day = total_tasks / days
            projected_monthly = invocations_per_day * 30

            return TrendAnalysis(
                period_days=days,
                success_rate_trend=success_trend,
                time_trend=time_trend,
                invocations_per_day=invocations_per_day,
                projected_monthly_invocations=projected_monthly
            )

        except Exception:
            return None

    def generate_report(self, detailed: bool = False) -> str:
        """
        Generate formatted performance report

        Args:
            detailed: Include detailed pattern analysis

        Returns:
            Formatted report string
        """
        stats = self.get_stats()
        trend = self.get_trend_analysis(days=30)

        lines = []
        lines.append("=" * 70)
        lines.append(f"PERFORMANCE REPORT: {self.agent_id}")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Version: {stats.version}")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Health: {stats.overall_health.upper()}")
        lines.append("")

        # Core Metrics
        lines.append("CORE METRICS")
        lines.append("-" * 70)
        lines.append(f"Total Invocations:   {stats.total_invocations}")
        lines.append(f"Success Rate:        {stats.success_rate:.1f}% " +
                    ("✓" if stats.meets_success_target else "✗"))
        lines.append(f"Failure Rate:        {stats.failure_rate:.1f}%")
        lines.append(f"Correction Rate:     {stats.correction_rate:.1f}%")
        lines.append("")

        # Time Performance
        lines.append("TIME PERFORMANCE")
        lines.append("-" * 70)
        lines.append(f"Average Time:        {stats.avg_time_seconds:.2f}s")
        lines.append(f"Min Time:            {stats.min_time_seconds:.2f}s")
        lines.append(f"Max Time:            {stats.max_time_seconds:.2f}s")
        lines.append(f"Target Time:         {stats.target_time_seconds:.2f}s")
        lines.append(f"Performance Ratio:   {stats.time_performance_ratio:.2f}x " +
                    ("✓" if stats.meets_time_target else "✗"))
        lines.append("")

        # Reflection Quality
        lines.append("REFLECTION QUALITY")
        lines.append("-" * 70)
        lines.append(f"Total Reflections:   {stats.total_reflections}")
        lines.append(f"Shallow:             {stats.shallow_reflection_count} " +
                    f"({100 - stats.deep_reflection_percentage:.1f}%)")
        lines.append(f"Deep:                {stats.deep_reflection_count} " +
                    f"({stats.deep_reflection_percentage:.1f}%)")
        lines.append("")

        # Learning Rate
        lines.append("LEARNING RATE")
        lines.append("-" * 70)
        lines.append(f"First 10 Tasks:      {stats.first_n_success_rate:.1f}%")
        lines.append(f"Last 10 Tasks:       {stats.last_n_success_rate:.1f}%")
        lines.append(f"Learning Velocity:   {stats.learning_velocity:+.1f}%")
        lines.append(f"Plateau Detected:    {'Yes' if stats.plateau_detected else 'No'}")
        lines.append("")

        # Trend Analysis
        if trend:
            lines.append("TREND ANALYSIS (Last 30 Days)")
            lines.append("-" * 70)
            lines.append(f"Success Rate Trend:  {trend.success_rate_trend.upper()}")
            lines.append(f"Time Trend:          {trend.time_trend.upper()}")
            lines.append(f"Invocations/Day:     {trend.invocations_per_day:.1f}")
            lines.append(f"Projected Monthly:   {trend.projected_monthly_invocations:.0f}")
            lines.append("")

        # Pattern Effectiveness
        if stats.top_patterns and detailed:
            lines.append("TOP PATTERNS (by effectiveness)")
            lines.append("-" * 70)
            for i, (pattern_id, effectiveness) in enumerate(stats.top_patterns, 1):
                pattern_data = stats.pattern_stats[pattern_id]
                lines.append(
                    f"{i}. {pattern_id}: {effectiveness:.0f}% "
                    f"(used {pattern_data['usage']}x, succeeded {pattern_data['success']}x)"
                )
            lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        for rec in stats.recommendations:
            lines.append(f"  {rec}")
        lines.append("")

        lines.append("=" * 70)

        return "\n".join(lines)


def get_agent_stats(agent_id: str) -> PerformanceStats:
    """
    Convenience function to get agent stats

    Args:
        agent_id: Agent identifier

    Returns:
        PerformanceStats
    """
    analytics = PerformanceAnalytics(agent_id)
    return analytics.get_stats()


def generate_agent_report(agent_id: str, detailed: bool = False) -> str:
    """
    Convenience function to generate agent report

    Args:
        agent_id: Agent identifier
        detailed: Include detailed analysis

    Returns:
        Formatted report string
    """
    analytics = PerformanceAnalytics(agent_id)
    return analytics.generate_report(detailed=detailed)
