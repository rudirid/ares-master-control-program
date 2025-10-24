"""
Pattern Matcher - Tier 1 Instant Suggestions (<100ms)

Detects common sales patterns in real-time and provides cached responses.
No API calls - pure pattern matching for speed.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SuggestionUrgency(Enum):
    """How urgently should this suggestion be shown?"""
    HIGH = "high"      # Show immediately (objections, buying signals)
    MEDIUM = "medium"  # Show if relevant
    LOW = "low"        # Background info


class SuggestionCategory(Enum):
    """Type of suggestion"""
    QUESTION = "question"           # Calibrated question to ask
    REFRAME = "reframe"            # Objection reframe
    CLOSE = "close"                # Closing prompt
    BRIDGE = "bridge"              # Silence recovery
    DISCOVERY = "discovery"        # MEDDIC/BANT question
    WARNING = "warning"            # Avoid this trap


@dataclass
class Suggestion:
    """A tactical suggestion to show the user"""
    text: str
    urgency: SuggestionUrgency
    category: SuggestionCategory
    confidence: float  # 0-1
    trigger_phrase: str
    framework: str  # "Chris Voss", "MEDDIC", etc.


class PatternMatcher:
    """
    Fast pattern matching for common sales scenarios.
    Pre-cached responses for instant delivery.
    """

    def __init__(self):
        self.patterns = self._build_patterns()

    def _build_patterns(self) -> List[Dict]:
        """
        Build pattern library with regex + cached responses.
        """
        return [
            # PRICING OBJECTIONS
            {
                "pattern": r"(?i)(how much|what.{0,10}cost|what.{0,10}price|too expensive|can't afford)",
                "suggestions": [
                    Suggestion(
                        text="Don't answer yet - qualify first: 'Great question. To give you accurate pricing, help me understand: what budget range are you working with?'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.REFRAME,
                        confidence=0.9,
                        trigger_phrase="pricing question",
                        framework="Chris Voss"
                    ),
                    Suggestion(
                        text="Label + calibrated question: 'It sounds like budget is a key concern. What would make the ROI worth the investment for you?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.85,
                        trigger_phrase="pricing concern",
                        framework="Chris Voss"
                    )
                ]
            },

            # COMPETITIVE OBJECTIONS
            {
                "pattern": r"(?i)(already using|current solution|happy with|why switch|competitor)",
                "suggestions": [
                    Suggestion(
                        text="Mirror + question: '[Current solution]... What's working well with them? What's not?'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.95,
                        trigger_phrase="competitive objection",
                        framework="Chris Voss - Mirroring"
                    ),
                    Suggestion(
                        text="Don't defend - discover: 'That's great you found something that works. What would it take to make you consider something new?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.85,
                        trigger_phrase="competitive",
                        framework="Chris Voss"
                    )
                ]
            },

            # TIMING/STALL OBJECTIONS
            {
                "pattern": r"(?i)(think about it|not ready|next quarter|revisit later|need time)",
                "suggestions": [
                    Suggestion(
                        text="Label + clarify: 'It seems like timing is the issue. What specifically would you like to think through? Maybe I can help clarify now?'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.9,
                        trigger_phrase="timing stall",
                        framework="Chris Voss - Labeling"
                    ),
                    Suggestion(
                        text="Urgency builder: 'I understand. What's the cost of waiting another quarter?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.8,
                        trigger_phrase="delay",
                        framework="Discovery"
                    )
                ]
            },

            # AUTHORITY OBJECTIONS
            {
                "pattern": r"(?i)(need to check|talk to (my )?(boss|team|manager)|not my decision|someone else)",
                "suggestions": [
                    Suggestion(
                        text="Calibrated question: 'How would your [boss/team] evaluate this? What criteria would they use?'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.9,
                        trigger_phrase="authority objection",
                        framework="Chris Voss"
                    ),
                    Suggestion(
                        text="Enable champion: 'What information would help you bring this to them? Would it be useful if I presented directly?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.85,
                        trigger_phrase="needs approval",
                        framework="MEDDIC - Champion"
                    )
                ]
            },

            # BUYING SIGNALS - HIGH PRIORITY
            {
                "pattern": r"(?i)(how long.{0,20}implement|when.{0,10}start|what.{0,10}contract|next steps|pilot|trial)",
                "suggestions": [
                    Suggestion(
                        text="BUYING SIGNAL DETECTED - Close: 'Great question. Before we dive into logistics, let me confirm this solves your [pain] problem...'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.CLOSE,
                        confidence=0.95,
                        trigger_phrase="implementation logistics",
                        framework="Closing"
                    ),
                    Suggestion(
                        text="Trial close: 'Most teams are live in 2 weeks. For your timeline, we'd need to start by [date]. Does that work?'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.CLOSE,
                        confidence=0.9,
                        trigger_phrase="timeline question",
                        framework="Closing"
                    )
                ]
            },

            # INTEREST SIGNALS (softer)
            {
                "pattern": r"(?i)(sounds interesting|that's cool|I like|makes sense|good point)",
                "suggestions": [
                    Suggestion(
                        text="Qualify the interest: 'What specifically interests you about that?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.8,
                        trigger_phrase="interest signal",
                        framework="Discovery"
                    ),
                    Suggestion(
                        text="Advance: 'I'm glad that resonates. How would you see this working in your environment?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.75,
                        trigger_phrase="positive signal",
                        framework="Discovery"
                    )
                ]
            },

            # CONFUSION/QUESTIONS
            {
                "pattern": r"(?i)(don't understand|confused|what do you mean|can you explain)",
                "suggestions": [
                    Suggestion(
                        text="Simplify: 'Let me explain that differently - [use analogy or concrete example]'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.REFRAME,
                        confidence=0.9,
                        trigger_phrase="confusion",
                        framework="Communication"
                    ),
                    Suggestion(
                        text="Clarify: 'What specifically would you like me to explain more?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.85,
                        trigger_phrase="needs clarification",
                        framework="Discovery"
                    )
                ]
            },

            # CONCERN/RISK SIGNALS
            {
                "pattern": r"(?i)(concerned|worried|risky|what if|guarantee)",
                "suggestions": [
                    Suggestion(
                        text="Label the fear: 'It sounds like [specific concern] is important to you. What would address that concern?'",
                        urgency=SuggestionUrgency.HIGH,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.9,
                        trigger_phrase="concern/risk",
                        framework="Chris Voss - Labeling"
                    ),
                    Suggestion(
                        text="De-risk: 'That's a valid concern. Here's how we handle that: [case study/guarantee]'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.REFRAME,
                        confidence=0.85,
                        trigger_phrase="risk aversion",
                        framework="Trust Building"
                    )
                ]
            },

            # MEDDIC DISCOVERY TRIGGERS
            {
                "pattern": r"(?i)(measure success|metrics|kpi|roi|track)",
                "suggestions": [
                    Suggestion(
                        text="MEDDIC Metrics: 'How are you measuring [problem] today? What would success look like in numbers?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.DISCOVERY,
                        confidence=0.85,
                        trigger_phrase="metrics discussion",
                        framework="MEDDIC - Metrics"
                    )
                ]
            },

            {
                "pattern": r"(?i)(decision|approve|budget|authority)",
                "suggestions": [
                    Suggestion(
                        text="MEDDIC Economic Buyer: 'Who has final budget authority for this? What's their involvement?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.DISCOVERY,
                        confidence=0.85,
                        trigger_phrase="authority discussion",
                        framework="MEDDIC - Economic Buyer"
                    )
                ]
            },

            # SILENCE BREAKERS (when call goes quiet)
            {
                "pattern": r"(?i)(uh|um|hmm|well|let me think)",
                "suggestions": [
                    Suggestion(
                        text="Bridge question: 'Let me ask you this - [relevant discovery question based on context]'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.BRIDGE,
                        confidence=0.7,
                        trigger_phrase="awkward pause",
                        framework="Conversation Flow"
                    ),
                    Suggestion(
                        text="Comfortable silence: Let them think. Don't fill every pause.",
                        urgency=SuggestionUrgency.LOW,
                        category=SuggestionCategory.WARNING,
                        confidence=0.8,
                        trigger_phrase="silence",
                        framework="Chris Voss"
                    )
                ]
            },

            # FEATURE REQUESTS (good sign - they're envisioning use)
            {
                "pattern": r"(?i)(can it|does it|will it|feature|integrate|work with)",
                "suggestions": [
                    Suggestion(
                        text="Qualify the need: 'Yes, we can. Help me understand - why is that important to you?'",
                        urgency=SuggestionUrgency.MEDIUM,
                        category=SuggestionCategory.QUESTION,
                        confidence=0.85,
                        trigger_phrase="feature question",
                        framework="Discovery"
                    ),
                    Suggestion(
                        text="Buying signal: This is a good sign - they're envisioning using it.",
                        urgency=SuggestionUrgency.LOW,
                        category=SuggestionCategory.WARNING,
                        confidence=0.9,
                        trigger_phrase="use case exploration",
                        framework="Sales Psychology"
                    )
                ]
            }
        ]

    def analyze(self, text: str) -> List[Suggestion]:
        """
        Analyze text for patterns and return instant suggestions.

        Args:
            text: Recent prospect statement (last 1-2 sentences)

        Returns:
            List of suggestions, sorted by urgency and confidence
        """
        suggestions = []

        for pattern_obj in self.patterns:
            if re.search(pattern_obj["pattern"], text):
                suggestions.extend(pattern_obj["suggestions"])

        # Sort by urgency (HIGH first) then confidence
        urgency_order = {
            SuggestionUrgency.HIGH: 0,
            SuggestionUrgency.MEDIUM: 1,
            SuggestionUrgency.LOW: 2
        }

        suggestions.sort(
            key=lambda s: (urgency_order[s.urgency], -s.confidence)
        )

        return suggestions

    def detect_sales_stage(self, transcript: List[str]) -> str:
        """
        Detect current sales stage based on conversation patterns.

        Args:
            transcript: List of recent statements

        Returns:
            Stage name: discovery, demo, negotiation, close
        """
        text = " ".join(transcript).lower()

        # Closing signals
        if any(word in text for word in ["contract", "pilot", "when start", "next steps", "move forward"]):
            return "close"

        # Negotiation signals
        if any(word in text for word in ["price", "cost", "budget", "terms", "discount"]):
            return "negotiation"

        # Demo signals
        if any(word in text for word in ["show me", "how does", "can it", "demo", "feature"]):
            return "demo"

        # Default to discovery
        return "discovery"

    def detect_meddic_gaps(self, context: Dict) -> List[Suggestion]:
        """
        Identify which MEDDIC components are missing and suggest questions.

        Args:
            context: Pre-call context dict with meddic section

        Returns:
            List of discovery questions to fill gaps
        """
        gaps = []

        if not context.get("meddic", {}).get("metrics", {}).get("current_problem_cost"):
            gaps.append(Suggestion(
                text="MEDDIC Gap - Metrics: 'How much is this problem costing you today?'",
                urgency=SuggestionUrgency.MEDIUM,
                category=SuggestionCategory.DISCOVERY,
                confidence=0.9,
                trigger_phrase="missing metrics",
                framework="MEDDIC"
            ))

        if not context.get("meddic", {}).get("economic_buyer", {}).get("name"):
            gaps.append(Suggestion(
                text="MEDDIC Gap - Economic Buyer: 'Who has final budget authority for this decision?'",
                urgency=SuggestionUrgency.MEDIUM,
                category=SuggestionCategory.DISCOVERY,
                confidence=0.9,
                trigger_phrase="missing economic buyer",
                framework="MEDDIC"
            ))

        if not context.get("meddic", {}).get("decision_process", {}).get("steps"):
            gaps.append(Suggestion(
                text="MEDDIC Gap - Decision Process: 'Walk me through how decisions like this typically get made at your company'",
                urgency=SuggestionUrgency.MEDIUM,
                category=SuggestionCategory.DISCOVERY,
                confidence=0.9,
                trigger_phrase="missing decision process",
                framework="MEDDIC"
            ))

        if not context.get("meddic", {}).get("champion", {}).get("name"):
            gaps.append(Suggestion(
                text="MEDDIC Gap - Champion: 'Who internally would be excited to advocate for this solution?'",
                urgency=SuggestionUrgency.MEDIUM,
                category=SuggestionCategory.DISCOVERY,
                confidence=0.85,
                trigger_phrase="missing champion",
                framework="MEDDIC"
            ))

        return gaps


if __name__ == "__main__":
    # Quick test
    matcher = PatternMatcher()

    # Test cases
    test_cases = [
        "How much does this cost?",
        "We're already using Gong for this",
        "I need to think about it and discuss with my team",
        "That sounds interesting. How long does implementation take?",
        "I'm concerned about the ROI timeline"
    ]

    print("Pattern Matcher Test\n" + "="*60)
    for test in test_cases:
        print(f"\nProspect: '{test}'")
        suggestions = matcher.analyze(test)
        if suggestions:
            for i, sug in enumerate(suggestions[:2], 1):  # Show top 2
                print(f"\n  [{sug.urgency.value.upper()}] {sug.framework}")
                print(f"  > {sug.text}")
        else:
            print("  (No instant suggestions)")

    print("\n" + "="*60)
