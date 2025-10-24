"""
Suggestion Generator - Tier 2/3 Context-Aware Suggestions

Uses Claude API for complex, context-aware tactical suggestions.
Integrates pre-call context + real-time transcript.
"""

import os
import yaml
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from anthropic import Anthropic
from pattern_matcher import PatternMatcher, Suggestion, SuggestionUrgency, SuggestionCategory


@dataclass
class CallContext:
    """Complete context for suggestion generation"""
    pre_call_context: Dict
    recent_transcript: List[str]  # Last 2-3 minutes
    sales_stage: str  # discovery, demo, negotiation, close
    meddic_progress: Dict


class SuggestionGenerator:
    """
    Generate context-aware sales suggestions using Claude API.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize with Anthropic API key.

        Args:
            api_key: Anthropic API key (or reads from env ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found. Set via environment or pass to __init__")

        self.client = Anthropic(api_key=self.api_key)
        self.pattern_matcher = PatternMatcher()

        # Load sales frameworks
        frameworks_path = os.path.expanduser("~/.ares/applications/sales-coach/config/sales_frameworks.yaml")
        with open(frameworks_path) as f:
            self.frameworks = yaml.safe_load(f)

    def generate_suggestions(
        self,
        context: CallContext,
        urgency_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        Generate tactical suggestions based on call context.

        Args:
            context: Complete call context (pre-call + transcript)
            urgency_filter: Only return specific urgency ("high", "medium", "low")

        Returns:
            List of suggestion dicts with text, urgency, category, confidence
        """
        # First: Get instant suggestions from pattern matcher
        instant_suggestions = self._get_instant_suggestions(context)

        # Second: Get context-aware suggestions from Claude
        claude_suggestions = self._get_claude_suggestions(context)

        # Combine and deduplicate
        all_suggestions = instant_suggestions + claude_suggestions
        all_suggestions = self._deduplicate(all_suggestions)

        # Filter by urgency if specified
        if urgency_filter:
            all_suggestions = [
                s for s in all_suggestions
                if s["urgency"] == urgency_filter
            ]

        # Sort by urgency and confidence
        urgency_order = {"high": 0, "medium": 1, "low": 2}
        all_suggestions.sort(
            key=lambda s: (urgency_order.get(s["urgency"], 3), -s["confidence"])
        )

        return all_suggestions

    def _get_instant_suggestions(self, context: CallContext) -> List[Dict]:
        """Get instant pattern-matched suggestions"""
        if not context.recent_transcript:
            return []

        # Analyze last statement
        last_statement = context.recent_transcript[-1]
        suggestions = self.pattern_matcher.analyze(last_statement)

        return [self._suggestion_to_dict(s) for s in suggestions]

    def _get_claude_suggestions(self, context: CallContext) -> List[Dict]:
        """Get context-aware suggestions from Claude"""
        system_prompt = self._build_system_prompt(context)
        user_prompt = self._build_user_prompt(context)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Parse Claude's response into suggestions
            return self._parse_claude_response(response.content[0].text)

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return []

    def _build_system_prompt(self, context: CallContext) -> str:
        """Build system prompt with pre-call context and frameworks"""
        prospect_name = context.pre_call_context.get("prospect", {}).get("name", "Prospect")
        company = context.pre_call_context.get("prospect", {}).get("company", "their company")
        stage = context.sales_stage

        prompt = f"""You are an expert sales coach providing REAL-TIME tactical suggestions during a live sales call.

PROSPECT CONTEXT:
- Name: {prospect_name}
- Company: {company}
- Sales Stage: {stage}

PRE-CALL INTELLIGENCE:
{yaml.dump(context.pre_call_context, default_flow_style=False)}

YOUR ROLE:
- Analyze the prospect's latest statement
- Provide 1-3 tactical suggestions for what to say next
- Use Chris Voss tactical empathy and MEDDIC framework
- Be specific, actionable, and concise
- Prioritize high-value suggestions (objections, buying signals, closing opportunities)

FRAMEWORKS TO USE:
1. Chris Voss Tactical Empathy:
   - Mirror (repeat last 3 words)
   - Label emotions ("It sounds like...")
   - Calibrated questions ("How would...", "What would...")
   - Get "That's right" confirmation
   - No-oriented questions

2. MEDDIC Qualification:
   - Metrics: Quantify the pain
   - Economic Buyer: Find who can say yes
   - Decision Criteria: Understand how they'll decide
   - Decision Process: Map the buying steps
   - Identify Pain: Confirm real urgency
   - Champion: Find internal advocate

OUTPUT FORMAT:
For each suggestion, provide:
1. [URGENCY] high/medium/low
2. [CATEGORY] question/reframe/close/bridge/discovery
3. [TEXT] The exact tactical suggestion
4. [WHY] Brief explanation using pre-call context
5. [CONFIDENCE] 0-100%

URGENCY LEVELS:
- HIGH: Objections, buying signals, closing opportunities (show immediately)
- MEDIUM: Discovery questions, value propositions (show if relevant)
- LOW: Background info, context (nice to have)

REMEMBER:
- The user needs to see this in <2 seconds
- Be concise and actionable
- Reference pre-call context when relevant
- Don't generate generic advice - make it specific to THIS prospect
"""
        return prompt

    def _build_user_prompt(self, context: CallContext) -> str:
        """Build user prompt with recent transcript"""
        # Get last 5 statements for context (sliding window)
        recent = context.recent_transcript[-5:]
        transcript_text = "\n".join([
            f"{'Prospect' if i % 2 == 0 else 'You'}: {stmt}"
            for i, stmt in enumerate(recent)
        ])

        # Identify MEDDIC gaps
        meddic_gaps = self._identify_meddic_gaps(context.pre_call_context)

        prompt = f"""RECENT CONVERSATION:
{transcript_text}

MEDDIC PROGRESS:
{self._format_meddic_progress(context.pre_call_context)}

MEDDIC GAPS TO FILL:
{', '.join(meddic_gaps) if meddic_gaps else 'All components covered'}

LATEST PROSPECT STATEMENT:
"{context.recent_transcript[-1]}"

Provide 1-3 tactical suggestions for what to say next. Focus on:
1. Addressing their latest statement
2. Filling MEDDIC gaps if in discovery stage
3. Using Chris Voss techniques for objections
4. Advancing the sale toward close

Be specific, actionable, and reference the pre-call context.
"""
        return prompt

    def _identify_meddic_gaps(self, pre_call_context: Dict) -> List[str]:
        """Identify which MEDDIC components are missing"""
        gaps = []
        meddic = pre_call_context.get("meddic", {})

        if not meddic.get("metrics", {}).get("current_problem_cost"):
            gaps.append("Metrics (quantify pain)")

        if not meddic.get("economic_buyer", {}).get("name"):
            gaps.append("Economic Buyer (who can say yes)")

        if not meddic.get("decision_criteria", {}).get("must_haves"):
            gaps.append("Decision Criteria (how they'll decide)")

        if not meddic.get("decision_process", {}).get("steps"):
            gaps.append("Decision Process (buying steps)")

        if not meddic.get("pain", {}).get("identified_pains"):
            gaps.append("Pain (urgency/severity)")

        if not meddic.get("champion", {}).get("name"):
            gaps.append("Champion (internal advocate)")

        return gaps

    def _format_meddic_progress(self, pre_call_context: Dict) -> str:
        """Format MEDDIC progress for display"""
        meddic = pre_call_context.get("meddic", {})
        lines = []

        components = {
            "Metrics": bool(meddic.get("metrics", {}).get("current_problem_cost")),
            "Economic Buyer": bool(meddic.get("economic_buyer", {}).get("name")),
            "Decision Criteria": bool(meddic.get("decision_criteria", {}).get("must_haves")),
            "Decision Process": bool(meddic.get("decision_process", {}).get("steps")),
            "Pain": bool(meddic.get("pain", {}).get("identified_pains")),
            "Champion": bool(meddic.get("champion", {}).get("name"))
        }

        for component, complete in components.items():
            status = "✓" if complete else "✗"
            lines.append(f"{status} {component}")

        completed = sum(components.values())
        total = len(components)
        lines.append(f"\nProgress: {completed}/{total} ({int(completed/total*100)}%)")

        return "\n".join(lines)

    def _parse_claude_response(self, text: str) -> List[Dict]:
        """Parse Claude's text response into structured suggestions"""
        suggestions = []

        # Simple parsing - look for [URGENCY], [CATEGORY], [TEXT] patterns
        # In production, you'd use more robust parsing or ask Claude for JSON

        lines = text.split("\n")
        current_sug = {}

        for line in lines:
            line = line.strip()

            if line.startswith("[URGENCY]"):
                if current_sug:
                    suggestions.append(current_sug)
                current_sug = {"urgency": line.split("]")[1].strip().lower()}

            elif line.startswith("[CATEGORY]"):
                current_sug["category"] = line.split("]")[1].strip().lower()

            elif line.startswith("[TEXT]"):
                current_sug["text"] = line.split("]", 1)[1].strip()

            elif line.startswith("[WHY]"):
                current_sug["reasoning"] = line.split("]", 1)[1].strip()

            elif line.startswith("[CONFIDENCE]"):
                conf_str = line.split("]")[1].strip().rstrip("%")
                current_sug["confidence"] = float(conf_str) / 100

        if current_sug:
            suggestions.append(current_sug)

        # Add defaults for any missing fields
        for sug in suggestions:
            sug.setdefault("urgency", "medium")
            sug.setdefault("category", "question")
            sug.setdefault("confidence", 0.7)
            sug.setdefault("framework", "Claude Analysis")

        return suggestions

    def _suggestion_to_dict(self, sug: Suggestion) -> Dict:
        """Convert Suggestion dataclass to dict"""
        return {
            "text": sug.text,
            "urgency": sug.urgency.value,
            "category": sug.category.value,
            "confidence": sug.confidence,
            "framework": sug.framework,
            "trigger": sug.trigger_phrase
        }

    def _deduplicate(self, suggestions: List[Dict]) -> List[Dict]:
        """Remove duplicate suggestions (similar text)"""
        seen = set()
        unique = []

        for sug in suggestions:
            # Simple dedup: first 50 chars of text
            key = sug["text"][:50].lower()
            if key not in seen:
                seen.add(key)
                unique.append(sug)

        return unique

    def load_pre_call_context(self, filepath: str) -> Dict:
        """Load pre-call context from YAML file"""
        with open(os.path.expanduser(filepath)) as f:
            return yaml.safe_load(f)


if __name__ == "__main__":
    # Quick test (requires ANTHROPIC_API_KEY environment variable)
    import sys

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("Set it with: export ANTHROPIC_API_KEY=your_key_here")
        sys.exit(1)

    # Create sample context
    sample_context = CallContext(
        pre_call_context={
            "prospect": {
                "name": "Sarah Johnson",
                "company": "TechCorp Inc",
                "role": "VP of Sales"
            },
            "meddic": {
                "pain": {
                    "identified_pains": ["Manual call analysis taking 5 hours/week per rep"]
                },
                "metrics": {},
                "economic_buyer": {},
                "decision_criteria": {},
                "decision_process": {},
                "champion": {}
            },
            "competition": {
                "current_solution": "Gong"
            }
        },
        recent_transcript=[
            "Hi Sarah, thanks for taking the time today.",
            "No problem. So you mentioned this is similar to Gong?",
            "Similar in some ways, but there are key differences. What's working well with Gong for you?",
            "It's fine for post-call analysis, but we need real-time coaching. How does your solution handle that?"
        ],
        sales_stage="discovery",
        meddic_progress={}
    )

    print("Sales Coach Suggestion Generator - Test\n" + "="*60)
    generator = SuggestionGenerator()
    suggestions = generator.generate_suggestions(sample_context)

    print(f"\nGenerated {len(suggestions)} suggestions:\n")
    for i, sug in enumerate(suggestions, 1):
        print(f"{i}. [{sug['urgency'].upper()}] {sug['category']}")
        print(f"   {sug['text']}")
        print(f"   Framework: {sug['framework']} | Confidence: {int(sug['confidence']*100)}%")
        print()
