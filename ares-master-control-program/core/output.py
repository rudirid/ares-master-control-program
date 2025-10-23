"""
ARES Output Protocol - "Show Your Work"
Transparent reasoning format from ares-core-directives.md v2.1
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Any
from datetime import datetime
import json


@dataclass
class AresResponse:
    """
    Structured output format that shows your work

    Implements the "Show Your Work" protocol:
    - Result (what was done)
    - Reasoning (why this way)
    - Confidence score
    - Patterns applied
    - Alternatives considered
    """

    # Core output
    result: Any
    reasoning: str
    confidence_score: float
    confidence_level: str  # HIGH/MEDIUM/LOW

    # Transparency fields
    patterns_used: List[str]
    alternatives_considered: List[str]
    evidence: List[str]
    warnings: List[str]

    # Metadata
    timestamp: str
    ares_version: str = "2.5.0"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        """
        Format as markdown for human readability

        Example output:
        ```
        [EXECUTING] Task description

        Internal Validation:
        ✓ Challenge: Evidence for approach
        ✓ Simplify: Considered alternatives
        ✓ Validate: Proof from patterns
        ✓ Explain: Plain language analogy
        ✓ Confidence: HIGH (95%)

        Proceeding with implementation...
        ```
        """
        lines = []

        # Header with confidence
        if self.confidence_level == "HIGH":
            header = f"[EXECUTING] {self.result}"
        elif self.confidence_level == "MEDIUM":
            header = f"[PROCEEDING WITH CAVEATS] {self.result}"
        else:
            header = f"[ESCALATION REQUIRED] {self.result}"

        lines.append(header)
        lines.append("")

        # Internal Validation section
        lines.append("Internal Validation:")
        lines.append(f"✓ Confidence: {self.confidence_level} ({self.confidence_score*100:.0f}%)")

        if self.patterns_used:
            lines.append(f"✓ Patterns: {', '.join(self.patterns_used)}")

        if self.evidence:
            lines.append(f"✓ Evidence: {'; '.join(self.evidence)}")

        if self.alternatives_considered:
            lines.append(f"✓ Alternatives: {', '.join(self.alternatives_considered[:3])}")

        if self.warnings:
            lines.append("")
            lines.append("⚠️  Warnings:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")

        lines.append("")

        # Reasoning
        lines.append("Reasoning:")
        lines.append(self.reasoning)

        return "\n".join(lines)


class AresOutput:
    """
    Output formatter implementing "Show Your Work" protocol
    """

    @staticmethod
    def format_high_confidence(
        result: Any,
        reasoning: str,
        patterns_used: List[str],
        evidence: List[str],
        confidence_score: float = 0.95
    ) -> AresResponse:
        """
        Format high confidence decision (≥80%)

        Example from ares-core-directives.md:
        ```
        [EXECUTING] Creating modular scraper architecture

        Internal Validation:
        ✓ Challenge: Best approach? Yes - proven across 5+ scrapers
        ✓ Simplify: Considered monolithic, but modular wins for maintainability
        ✓ Validate: Evidence? Tier 1 pattern, industry standard
        ✓ Explain: Like LEGO blocks vs. gluing parts together
        ✓ Confidence: HIGH (95%)

        Proceeding with implementation...
        ```
        """
        return AresResponse(
            result=result,
            reasoning=reasoning,
            confidence_score=confidence_score,
            confidence_level="HIGH",
            patterns_used=patterns_used,
            alternatives_considered=[],
            evidence=evidence,
            warnings=[],
            timestamp=datetime.now().isoformat()
        )

    @staticmethod
    def format_medium_confidence(
        result: Any,
        reasoning: str,
        patterns_used: List[str],
        caveats: List[str],
        confidence_score: float = 0.65
    ) -> AresResponse:
        """
        Format medium confidence decision (50-79%)

        Example from ares-core-directives.md:
        ```
        [PROCEEDING WITH CAVEATS] Implementing sentiment analysis

        Internal Validation:
        ✓ Challenge: Best approach? Reasonable, but 37% accuracy is low
        ⚠ Simplify: Pure rules might suffice, but trying hybrid
        ⚠ Validate: Evidence mixed - works but needs improvement
        ✓ Explain: Rules catch 80%, AI enhances edge cases
        ⚠ Confidence: MEDIUM (60%)

        Proceeding with prototype. Will measure and iterate.
        ```
        """
        return AresResponse(
            result=result,
            reasoning=reasoning,
            confidence_score=confidence_score,
            confidence_level="MEDIUM",
            patterns_used=patterns_used,
            alternatives_considered=[],
            evidence=[],
            warnings=caveats,
            timestamp=datetime.now().isoformat()
        )

    @staticmethod
    def format_low_confidence(
        result: str,
        options: List[dict],
        confidence_score: float = 0.40
    ) -> AresResponse:
        """
        Format low confidence escalation (<50%)

        Example from ares-core-directives.md:
        ```
        [ESCALATION REQUIRED] Choosing between GraphQL vs REST

        Internal Validation:
        ? Challenge: Both valid, no clear winner
        ? Simplify: Complexity similar
        ? Validate: No evidence in our projects either way
        ? Explain: Can explain both, but uncertain which fits better
        ? Confidence: LOW (40%)

        Need input: Which architecture better fits your long-term vision?
        Option A: REST (simpler, we know it)
        Option B: GraphQL (more flexible, learning curve)
        ```
        """
        options_text = "\n".join([
            f"Option {chr(65+i)}: {opt['name']} ({opt['description']})"
            for i, opt in enumerate(options)
        ])

        return AresResponse(
            result=result,
            reasoning=f"Need input: {result}\n\nOptions:\n{options_text}",
            confidence_score=confidence_score,
            confidence_level="LOW",
            patterns_used=[],
            alternatives_considered=[opt['name'] for opt in options],
            evidence=[],
            warnings=["Confidence too low to proceed autonomously"],
            timestamp=datetime.now().isoformat()
        )

    @staticmethod
    def format_validation_result(validation_result) -> AresResponse:
        """
        Convert a ValidationResult into an AresResponse

        This is the bridge between validation and output formatting.
        """
        from .validation import ConfidenceLevel

        if validation_result.confidence_level == ConfidenceLevel.HIGH:
            return AresOutput.format_high_confidence(
                result=validation_result.decision,
                reasoning=validation_result.challenge_response,
                patterns_used=validation_result.patterns_referenced,
                evidence=[validation_result.validate_response],
                confidence_score=validation_result.confidence_score
            )
        elif validation_result.confidence_level == ConfidenceLevel.MEDIUM:
            return AresOutput.format_medium_confidence(
                result=validation_result.decision,
                reasoning=validation_result.challenge_response,
                patterns_used=validation_result.patterns_referenced,
                caveats=validation_result.warnings,
                confidence_score=validation_result.confidence_score
            )
        else:
            return AresOutput.format_low_confidence(
                result="Need additional input to proceed",
                options=[
                    {"name": alt, "description": "Alternative approach"}
                    for alt in validation_result.alternatives_considered[:3]
                ],
                confidence_score=validation_result.confidence_score
            )
