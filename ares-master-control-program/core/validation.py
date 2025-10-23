"""
ARES Internal Validation Protocol
Extracted from ares-core-directives.md v2.1

The 5-step validation loop that runs before every decision.
"""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence thresholds from Ares v2.1"""
    HIGH = "HIGH"      # ≥80% - Execute autonomously
    MEDIUM = "MEDIUM"  # 50-79% - Proceed with caveats
    LOW = "LOW"        # <50% - Escalate to user


@dataclass
class ValidationResult:
    """Result of running the 5-step validation protocol"""

    # The 5 validation steps
    challenge_response: str  # What could go wrong? Evidence for approach
    simplify_response: str   # Is there a simpler alternative?
    validate_response: str   # Do we have evidence this works?
    explain_response: str    # Can I explain in plain language?
    confidence_score: float  # 0.0 to 1.0

    # Derived values
    confidence_level: ConfidenceLevel
    should_proceed: bool
    alternatives_considered: List[str]
    patterns_referenced: List[str]
    warnings: List[str]

    @property
    def decision(self) -> str:
        """What action to take based on confidence"""
        if self.confidence_level == ConfidenceLevel.HIGH:
            return "EXECUTE - Show work and proceed autonomously"
        elif self.confidence_level == ConfidenceLevel.MEDIUM:
            return "PROCEED WITH CAVEATS - Note uncertainties"
        else:
            return "ESCALATE - Present options and ask for input"


class AresValidation:
    """
    The Internal Skeptic validation protocol from Ares v2.1

    Runs 5-step validation before any decision:
    1. Challenge: Is this the best approach?
    2. Simplify: Is there a simpler alternative?
    3. Validate: Do we have evidence this works?
    4. Explain: Can I explain this in plain language?
    5. Confidence: How certain am I?
    """

    def __init__(self, patterns_library=None, tech_matrix=None):
        """
        Initialize with optional knowledge bases

        Args:
            patterns_library: AresPatternMatcher instance
            tech_matrix: Technology success rates
        """
        self.patterns = patterns_library
        self.tech_matrix = tech_matrix

    def run_validation(
        self,
        task: str,
        proposed_approach: str,
        context: Optional[dict] = None
    ) -> ValidationResult:
        """
        Run the complete 5-step validation protocol

        Args:
            task: What needs to be done
            proposed_approach: How we plan to do it
            context: Additional context (tech stack, constraints, etc.)

        Returns:
            ValidationResult with all validation checks
        """
        context = context or {}

        # Step 1: Challenge
        challenge = self._challenge_approach(task, proposed_approach, context)

        # Step 2: Simplify
        simplify = self._find_simpler_alternatives(task, proposed_approach, context)

        # Step 3: Validate
        validate = self._check_evidence(proposed_approach, context)

        # Step 4: Explain
        explain = self._plain_language_explanation(proposed_approach)

        # Step 5: Confidence
        confidence = self._calculate_confidence(
            challenge, simplify, validate, explain
        )

        # Determine confidence level
        if confidence >= 0.80:
            level = ConfidenceLevel.HIGH
            should_proceed = True
        elif confidence >= 0.50:
            level = ConfidenceLevel.MEDIUM
            should_proceed = True
        else:
            level = ConfidenceLevel.LOW
            should_proceed = False

        return ValidationResult(
            challenge_response=challenge['response'],
            simplify_response=simplify['response'],
            validate_response=validate['response'],
            explain_response=explain['response'],
            confidence_score=confidence,
            confidence_level=level,
            should_proceed=should_proceed,
            alternatives_considered=simplify['alternatives'],
            patterns_referenced=validate['patterns'],
            warnings=challenge['warnings']
        )

    def _challenge_approach(self, task: str, approach: str, context: dict) -> dict:
        """
        Step 1: Challenge - What could go wrong? Is this the best approach?

        Returns evidence for the approach and potential issues.
        """
        warnings = []
        evidence = []

        # Check against known anti-patterns
        if "pure AI without fallback" in approach.lower():
            warnings.append("Anti-pattern detected: Pure AI without fallbacks")

        if "over-engineer" in approach.lower():
            warnings.append("Risk: Over-engineering before validation")

        # Check if approach matches context
        if context.get('complexity') == 'simple' and 'microservice' in approach.lower():
            warnings.append("May be over-complex for simple task")

        # Look for positive evidence
        if self.patterns:
            matching_patterns = self.patterns.find_matching_patterns(approach)
            if matching_patterns:
                evidence.extend([f"Matches proven pattern: {p.name}" for p in matching_patterns])

        response = f"Evidence: {'; '.join(evidence) if evidence else 'No proven patterns match'}"
        if warnings:
            response += f" | Warnings: {'; '.join(warnings)}"

        return {
            'response': response,
            'warnings': warnings,
            'evidence': evidence
        }

    def _find_simpler_alternatives(self, task: str, approach: str, context: dict) -> dict:
        """
        Step 2: Simplify - Is there a simpler alternative?

        Considers 2-3 alternatives and picks best with reasoning.
        """
        alternatives = []

        # Generate simpler alternatives based on approach complexity
        if "microservice" in approach.lower():
            alternatives.append("Monolithic app with modular structure (simpler deployment)")

        if "kubernetes" in approach.lower():
            alternatives.append("Docker Compose (simpler orchestration)")

        if "GraphQL" in approach.lower() and context.get('api_needs') == 'simple':
            alternatives.append("REST API (simpler, well-understood)")

        if "machine learning" in approach.lower():
            alternatives.append("Rule-based system (simpler, explainable)")

        if not alternatives:
            alternatives.append("Current approach appears appropriately simple")

        response = f"Alternatives considered: {', '.join(alternatives[:3])}"

        return {
            'response': response,
            'alternatives': alternatives
        }

    def _check_evidence(self, approach: str, context: dict) -> dict:
        """
        Step 3: Validate - Do we have evidence this works?

        Check against:
        - Riord's proven patterns (Tier 1/2/3)
        - External docs (if provided)
        - Industry standards (if provided)
        """
        patterns = []
        evidence_sources = []

        if self.patterns:
            matching = self.patterns.find_matching_patterns(approach)
            for pattern in matching:
                patterns.append(pattern.name)
                if pattern.tier == 1:
                    evidence_sources.append(f"Tier 1 pattern: {pattern.name} ({pattern.success_rate*100:.0f}% success)")
                elif pattern.tier == 2:
                    evidence_sources.append(f"Tier 2 pattern: {pattern.name} (needs more validation)")

        if self.tech_matrix:
            # Check technology success rates
            techs = self._extract_technologies(approach)
            for tech in techs:
                rate = self.tech_matrix.get(tech)
                if rate:
                    evidence_sources.append(f"{tech}: {rate['success_rate']*100:.0f}% success rate")

        response = '; '.join(evidence_sources) if evidence_sources else "No direct evidence in proven patterns"

        return {
            'response': response,
            'patterns': patterns
        }

    def _plain_language_explanation(self, approach: str) -> dict:
        """
        Step 4: Explain - Can I explain this in plain language?

        Draft an analogy (LEGO blocks vs glued parts style)
        """
        # Simple heuristic-based analogies
        analogies = {
            'modular': "Like LEGO blocks instead of gluing parts - easy to swap components",
            'monolithic': "Like a single toolbox - everything in one place",
            'microservice': "Like a kitchen with specialized stations - each does one job well",
            'database-centric': "Like a library catalog - single source of truth for all data",
            'hybrid ai': "Like a calculator with a smart assistant - rules handle basics, AI handles edge cases",
            'api': "Like a restaurant menu - defined options, consistent service",
            'fallback': "Like a backup generator - works without main power"
        }

        explanation = "Complex technical approach"
        for key, analogy in analogies.items():
            if key in approach.lower():
                explanation = analogy
                break

        return {'response': explanation}

    def _calculate_confidence(
        self,
        challenge: dict,
        simplify: dict,
        validate: dict,
        explain: dict
    ) -> float:
        """
        Step 5: Confidence - Calculate confidence score (0.0 to 1.0)

        Based on:
        - Evidence strength (proven patterns boost confidence)
        - Warnings (reduce confidence)
        - Simplicity (simpler = higher confidence for equivalent value)
        """
        confidence = 0.5  # Start at medium

        # Boost for proven patterns
        if "Tier 1" in validate['response']:
            confidence += 0.3
        elif "Tier 2" in validate['response']:
            confidence += 0.15

        # Reduce for warnings
        confidence -= 0.1 * len(challenge['warnings'])

        # Boost for clear explanation
        if explain['response'] != "Complex technical approach":
            confidence += 0.1

        # Cap between 0 and 1
        return max(0.0, min(1.0, confidence))

    def _extract_technologies(self, text: str) -> List[str]:
        """Extract technology names from text"""
        # Simple keyword matching (could be enhanced)
        known_techs = ['python', 'typescript', 'sqlite', 'postgresql', 'fastapi', 'react', 'docker']
        return [tech for tech in known_techs if tech in text.lower()]
