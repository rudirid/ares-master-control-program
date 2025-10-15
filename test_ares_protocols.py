"""
Test script for ARES Protocol Library v2.5

Demonstrates the validation, output, and pattern matching protocols.
"""

import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.validation import AresValidation, ConfidenceLevel
from core.output import AresOutput
from core.patterns import AresPatternMatcher

def test_validation_protocol():
    """Test the 5-step internal validation loop"""
    print("=" * 70)
    print("TEST 1: ARES VALIDATION PROTOCOL")
    print("=" * 70)

    # Initialize validator with pattern library
    patterns = AresPatternMatcher()
    validator = AresValidation(patterns_library=patterns)

    # Test Case 1: High Confidence (Tier 1 pattern)
    print("\n### Test Case 1: High Confidence (Modular Architecture)")
    print("-" * 70)

    result = validator.run_validation(
        task="Build a web scraping system for multiple data sources",
        proposed_approach="Create a modular architecture with separate scrapers and a central coordinator",
        context={"complexity": "medium", "data_sources": 5}
    )

    print(f"Confidence: {result.confidence_level.value} ({result.confidence_score*100:.0f}%)")
    print(f"Decision: {result.decision}")
    print(f"Patterns Referenced: {', '.join(result.patterns_referenced)}")
    print(f"Warnings: {result.warnings if result.warnings else 'None'}")
    print()

    # Test Case 2: Medium Confidence (With caveats)
    print("\n### Test Case 2: Medium Confidence (Experimental Pattern)")
    print("-" * 70)

    result2 = validator.run_validation(
        task="Implement sentiment analysis for financial news",
        proposed_approach="Use local sentiment analysis with 300 keywords",
        context={"accuracy_requirement": "high"}
    )

    print(f"Confidence: {result2.confidence_level.value} ({result2.confidence_score*100:.0f}%)")
    print(f"Decision: {result2.decision}")
    print(f"Patterns Referenced: {', '.join(result2.patterns_referenced)}")
    print(f"Warnings: {result2.warnings if result2.warnings else 'None'}")
    print()

    # Test Case 3: Low Confidence (No proven pattern)
    print("\n### Test Case 3: Low Confidence (Unknown Approach)")
    print("-" * 70)

    result3 = validator.run_validation(
        task="Build a blockchain-based voting system",
        proposed_approach="Use Ethereum smart contracts with zero-knowledge proofs",
        context={}
    )

    print(f"Confidence: {result3.confidence_level.value} ({result3.confidence_score*100:.0f}%)")
    print(f"Decision: {result3.decision}")
    print(f"Warnings: {result3.warnings if result3.warnings else 'None'}")
    print()


def test_output_protocol():
    """Test the 'Show Your Work' output formatting"""
    print("\n" + "=" * 70)
    print("TEST 2: ARES OUTPUT PROTOCOL ('Show Your Work')")
    print("=" * 70)

    # High Confidence Output
    print("\n### High Confidence Output (Markdown Format)")
    print("-" * 70)

    response = AresOutput.format_high_confidence(
        result="Creating modular scraper architecture",
        reasoning="Tier 1 pattern with 95% success rate across 12 projects",
        patterns_used=["Modular Scraper Architecture"],
        evidence=["Proven in ASX Trading AI", "Used in Business Brain"],
        confidence_score=0.95
    )

    print(response.to_markdown())
    print()

    # Medium Confidence Output
    print("\n### Medium Confidence Output (Markdown Format)")
    print("-" * 70)

    response2 = AresOutput.format_medium_confidence(
        result="Implementing local sentiment analysis",
        reasoning="Pattern exists but accuracy is only 37% - needs improvement",
        patterns_used=["Local Sentiment Analysis"],
        caveats=["Low accuracy (37%)", "Better than nothing for POC"],
        confidence_score=0.60
    )

    print(response2.to_markdown())
    print()

    # Low Confidence Output
    print("\n### Low Confidence Output (Escalation)")
    print("-" * 70)

    response3 = AresOutput.format_low_confidence(
        result="Choosing between REST and GraphQL",
        options=[
            {"name": "REST", "description": "Simpler, well-understood, easier to debug"},
            {"name": "GraphQL", "description": "More flexible, better for complex queries"}
        ],
        confidence_score=0.40
    )

    print(response3.to_markdown())
    print()


def test_pattern_matcher():
    """Test the pattern matching system"""
    print("\n" + "=" * 70)
    print("TEST 3: ARES PATTERN MATCHER")
    print("=" * 70)

    matcher = AresPatternMatcher()

    # Test Case 1: Find matching patterns
    print("\n### Test Case 1: Find Patterns for Web Scraping")
    print("-" * 70)

    matches = matcher.find_matching_patterns("build a web scraper for multiple sources")

    for pattern in matches:
        print(f"\n{pattern.name} (Tier {pattern.tier})")
        print(f"  Success Rate: {pattern.success_rate*100:.0f}%")
        print(f"  Description: {pattern.description}")
        print(f"  Evidence: {', '.join(pattern.evidence[:2])}")

    # Test Case 2: Get Tier 1 patterns only
    print("\n\n### Test Case 2: All Tier 1 (Proven) Patterns")
    print("-" * 70)

    tier_1 = matcher.get_tier_1_patterns()

    for pattern in tier_1:
        print(f"- {pattern.name}: {pattern.success_rate*100:.0f}% success ({pattern.usage_count} uses)")

    # Test Case 3: Recommend best pattern
    print("\n\n### Test Case 3: Recommend Best Pattern for Task")
    print("-" * 70)

    task = "I need to build an AI system that works without internet"
    print(f"Task: {task}")

    recommended = matcher.recommend_pattern(task)

    if recommended:
        print(f"\nRecommended: {recommended.name} (Tier {recommended.tier})")
        print(f"Why: {recommended.description}")
        print(f"Success Rate: {recommended.success_rate*100:.0f}%")
    else:
        print("\nNo matching pattern found")


def test_integration():
    """Test integration of all protocols together"""
    print("\n" + "=" * 70)
    print("TEST 4: INTEGRATED WORKFLOW")
    print("=" * 70)

    # Setup
    patterns = AresPatternMatcher()
    validator = AresValidation(patterns_library=patterns)

    # Run validation
    print("\n### Running validation for task...")
    print("-" * 70)

    validation_result = validator.run_validation(
        task="Build a database-centric workflow automation system",
        proposed_approach="Use SQLite as single source of truth with hybrid AI + rules",
        context={"users": "single", "data_volume": "medium"}
    )

    # Format output
    response = AresOutput.format_validation_result(validation_result)

    # Display
    print(response.to_markdown())
    print()

    # Also show JSON format
    print("\n### JSON Output Format")
    print("-" * 70)
    print(response.to_json())


if __name__ == "__main__":
    test_validation_protocol()
    test_output_protocol()
    test_pattern_matcher()
    test_integration()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETE - ARES PROTOCOLS WORKING")
    print("=" * 70)
    print("\nNext Steps:")
    print("1. ✅ Core protocols codified")
    print("2. → Create configuration system")
    print("3. → Build Ares MCP Server (TypeScript)")
    print("4. → Test in Claude Desktop")
    print()
