"""
ARES Pattern Matcher
Loads and matches tasks against proven-patterns.md
"""

import json
import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class Pattern:
    """A proven pattern from proven-patterns.md"""

    pattern_id: str
    tier: int  # 1, 2, or 3
    name: str
    description: str
    success_rate: float
    usage_count: int
    category: str  # architecture, data, api, etc.
    applies_to: List[str]  # keywords/contexts where this applies
    evidence: List[str]  # file references, metrics
    trade_offs: str  # benefits vs costs

    @property
    def is_tier_1(self) -> bool:
        """Tier 1 = Validated & Proven (5+ uses, metrics prove success)"""
        return self.tier == 1

    @property
    def is_tier_2(self) -> bool:
        """Tier 2 = Working, Needs More Validation (2-4 uses)"""
        return self.tier == 2

    @property
    def is_tier_3(self) -> bool:
        """Tier 3 = Experimental (1 use or less)"""
        return self.tier == 3


class AresPatternMatcher:
    """
    Loads proven-patterns.md and matches tasks to patterns

    This implements the pattern validation framework from Ares v2.1:
    - Tier 1 patterns: Use confidently (≥80% confidence)
    - Tier 2 patterns: Use with caveats (50-79% confidence)
    - Tier 3 patterns: Experimental (<50% confidence)
    """

    def __init__(self, patterns_file: Optional[str] = None):
        """
        Initialize pattern matcher

        Args:
            patterns_file: Path to proven-patterns.md
                          If None, uses default location
        """
        if patterns_file is None:
            # Default to ares-master-control-program/proven-patterns.md
            base_dir = Path(__file__).parent.parent
            patterns_file = base_dir / "proven-patterns.md"

        self.patterns_file = Path(patterns_file)
        self.patterns: List[Pattern] = []

        if self.patterns_file.exists():
            self._load_patterns()

    def _load_patterns(self):
        """
        Parse proven-patterns.md into Pattern objects

        This is a simple parser. In production, you might use
        a more robust markdown parser or convert to JSON first.
        """
        # For now, we'll create hardcoded patterns based on proven-patterns.md
        # In Phase 1, we'll build a proper parser

        self.patterns = [
            Pattern(
                pattern_id="modular_architecture_v1",
                tier=1,
                name="Modular Scraper Architecture",
                description="Unified coordinator with specialized scrapers",
                success_rate=0.95,
                usage_count=12,
                category="architecture",
                applies_to=["scraping", "data_collection", "multi_source", "modular"],
                evidence=[
                    "ASX Trading AI: 5+ scrapers",
                    "Business Brain: 3+ agents",
                    "Main coordinator: 687 lines"
                ],
                trade_offs="More files vs easier maintenance (acceptable)"
            ),
            Pattern(
                pattern_id="database_centric_v1",
                tier=1,
                name="Database-Centric Architecture",
                description="SQLite as single source of truth",
                success_rate=1.0,
                usage_count=15,
                category="data",
                applies_to=["database", "persistence", "sqlite", "single_source_truth"],
                evidence=[
                    "100% success rate across projects",
                    "10MB database = 100K+ records",
                    "Zero configuration"
                ],
                trade_offs="Perfect for <1M rows, migrate to PostgreSQL at scale"
            ),
            Pattern(
                pattern_id="hybrid_ai_rules_v1",
                tier=1,
                name="Rule-Based + AI Hybrid",
                description="Rules catch 80%, AI enhances edge cases",
                success_rate=0.90,
                usage_count=8,
                category="ai",
                applies_to=["ai", "machine_learning", "fallback", "hybrid", "rules"],
                evidence=[
                    "Business Brain: Works without API key",
                    "ASX Trading: Sentiment analysis with fallback",
                    "90% success rate"
                ],
                trade_offs="Works offline, explainable, but AI accuracy limited"
            ),
            Pattern(
                pattern_id="comprehensive_cli_v1",
                tier=1,
                name="Comprehensive CLI with Argparse",
                description="Professional command-line interfaces",
                success_rate=0.95,
                usage_count=10,
                category="interface",
                applies_to=["cli", "command_line", "argparse", "interface"],
                evidence=[
                    "Every Riord project has rich CLI",
                    "Dry-run mode, log levels, multiple modes"
                ],
                trade_offs="More code upfront, but saves time in usage"
            ),
            Pattern(
                pattern_id="graceful_degradation_v1",
                tier=1,
                name="Graceful Degradation",
                description="Works without APIs, fallback modes everywhere",
                success_rate=0.95,
                usage_count=10,
                category="reliability",
                applies_to=["error_handling", "fallback", "reliability", "graceful"],
                evidence=[
                    "All systems work without API keys",
                    "Hybrid AI + Rules pattern",
                    "Try/except with fallback"
                ],
                trade_offs="More code, but system never fully fails"
            ),
            Pattern(
                pattern_id="local_sentiment_v2",
                tier=2,
                name="Local Sentiment Analysis",
                description="300+ financial keywords, 37% accuracy",
                success_rate=0.37,
                usage_count=3,
                category="ai",
                applies_to=["sentiment", "nlp", "financial", "local"],
                evidence=[
                    "37% win rate in trading",
                    "300+ curated keywords",
                    "Negation and intensifier handling"
                ],
                trade_offs="Zero API costs, but low accuracy (needs improvement)"
            ),
        ]

    def find_matching_patterns(
        self,
        task_or_approach: str,
        tier_filter: Optional[int] = None
    ) -> List[Pattern]:
        """
        Find patterns that match a given task or approach

        Args:
            task_or_approach: Description of task or proposed approach
            tier_filter: Only return patterns of this tier (1, 2, or 3)

        Returns:
            List of matching patterns, sorted by tier (1 first) then success rate
        """
        matches = []
        text_lower = task_or_approach.lower()

        for pattern in self.patterns:
            # Check if any of the pattern's keywords appear in the text
            if any(keyword in text_lower for keyword in pattern.applies_to):
                if tier_filter is None or pattern.tier == tier_filter:
                    matches.append(pattern)

        # Sort by tier (1 first) then success rate
        matches.sort(key=lambda p: (p.tier, -p.success_rate))

        return matches

    def get_pattern_by_id(self, pattern_id: str) -> Optional[Pattern]:
        """Get a specific pattern by ID"""
        for pattern in self.patterns:
            if pattern.pattern_id == pattern_id:
                return pattern
        return None

    def get_tier_1_patterns(self) -> List[Pattern]:
        """Get all Tier 1 (validated & proven) patterns"""
        return [p for p in self.patterns if p.tier == 1]

    def get_tier_2_patterns(self) -> List[Pattern]:
        """Get all Tier 2 (working, needs validation) patterns"""
        return [p for p in self.patterns if p.tier == 2]

    def get_tier_3_patterns(self) -> List[Pattern]:
        """Get all Tier 3 (experimental) patterns"""
        return [p for p in self.patterns if p.tier == 3]

    def recommend_pattern(
        self,
        task: str,
        prefer_tier_1: bool = True
    ) -> Optional[Pattern]:
        """
        Recommend the best pattern for a given task

        Args:
            task: Description of what needs to be done
            prefer_tier_1: Prefer Tier 1 patterns even if Tier 2 matches better

        Returns:
            Best matching pattern or None if no matches
        """
        matches = self.find_matching_patterns(task)

        if not matches:
            return None

        if prefer_tier_1:
            # Return first Tier 1 match if exists
            tier_1_matches = [m for m in matches if m.tier == 1]
            if tier_1_matches:
                return tier_1_matches[0]

        # Return highest confidence match
        return matches[0]

    def to_json(self) -> str:
        """Export all patterns to JSON"""
        patterns_dict = [
            {
                "pattern_id": p.pattern_id,
                "tier": p.tier,
                "name": p.name,
                "description": p.description,
                "success_rate": p.success_rate,
                "usage_count": p.usage_count,
                "category": p.category,
                "applies_to": p.applies_to,
                "evidence": p.evidence,
                "trade_offs": p.trade_offs
            }
            for p in self.patterns
        ]
        return json.dumps(patterns_dict, indent=2)
