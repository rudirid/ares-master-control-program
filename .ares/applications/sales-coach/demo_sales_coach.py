#!/usr/bin/env python3
"""
Sales Coach Demo - Proof of Concept

Simulates a live sales call and shows real-time suggestions.
Tests both instant pattern matching and Claude-powered suggestions.
"""

import os
import sys
import time
from pathlib import Path

# Add core directory to path
core_path = Path(__file__).parent / "core"
sys.path.insert(0, str(core_path))

from pattern_matcher import PatternMatcher
from suggestion_generator import SuggestionGenerator, CallContext


class SalesCoachDemo:
    """Demo the sales coach system with a simulated call"""

    def __init__(self, context_file: str, use_claude: bool = True):
        """
        Initialize demo.

        Args:
            context_file: Path to pre-call context YAML
            use_claude: If True, use Claude API for suggestions (requires ANTHROPIC_API_KEY)
        """
        self.use_claude = use_claude
        self.pattern_matcher = PatternMatcher()

        if use_claude:
            if not os.getenv("ANTHROPIC_API_KEY"):
                print("Warning: ANTHROPIC_API_KEY not set - using pattern matching only")
                self.use_claude = False
            else:
                self.generator = SuggestionGenerator()
                self.pre_call_context = self.generator.load_pre_call_context(context_file)
        else:
            # Still load context for pattern matcher
            import yaml
            with open(context_file) as f:
                self.pre_call_context = yaml.safe_load(f)

        self.transcript = []
        self.call_stage = "discovery"

    def simulate_call(self):
        """Simulate a discovery call with real-time suggestions"""

        print("\n" + "="*80)
        print("SALES COACH - LIVE CALL SIMULATION")
        print("="*80)

        # Show pre-call context summary
        self._show_pre_call_brief()

        # Simulated call conversation
        conversation = [
            ("You", "Hi Sarah, thanks for taking the time today. I saw your LinkedIn post about scaling coaching with the new hires - that's exactly what we built this for."),
            ("Sarah", "Yes, that's a huge pain point for us. We're hiring 5 new reps in Q1 and I'm worried about our ability to coach them effectively."),
            ("You", "That makes sense. How long does it typically take for a new rep to ramp up right now?"),
            ("Sarah", "About 6 months to full productivity, which is way too long. We need them contributing in Q1."),
            ("You", "Six months is significant. What's the cost of that extended ramp time?"),
            ("Sarah", "Good question. Each rep should be closing $50k/month at full productivity, so 3 months lost is roughly $150k per rep in missed revenue."),
            ("You", "So with 5 new hires, that's $750k at risk. What have you tried to speed that up?"),
            ("Sarah", "We use Gong for post-call analysis, but honestly it doesn't help much in the moment. Managers still have to spend hours reviewing calls and coaching."),
            ("You", "What's working well with Gong? What's not?"),
            ("Sarah", "The insights are good for understanding trends, but it doesn't help reps in real-time. By the time we review a call, they've already lost the deal."),
            ("You", "That's exactly the gap we fill - coaching DURING the call, not after. How much time are your managers spending on call reviews?"),
            ("Sarah", "Probably 20 hours a week across all managers. It's unsustainable."),
            ("You", "20 hours a week... What would they do with that time back?"),
            ("Sarah", "Honestly? Close deals themselves. Our managers are still carrying quota."),
            ("You", "This sounds like a high-priority problem. What happens if you don't solve it before Q1?"),
            ("Sarah", "We miss our revenue targets. The new hires won't ramp fast enough."),
            ("You", "Walk me through how decisions like this typically get made at TechCorp."),
            ("Sarah", "I'd need to demo it for the team, then get CFO approval from Michael. He'll want to see clear ROI."),
            ("You", "What metrics would Michael use to evaluate this?"),
            ("Sarah", "Probably cost per rep, time to value, and impact on win rate or ramp time."),
            ("You", "Perfect. What if we could run a 30-day pilot with 3 reps - including one new hire - and show measurable improvement in their performance? Would that give you the data to take to Michael?"),
            ("Sarah", "That sounds reasonable. What would implementation look like?"),
            ("You", "Most teams are live in 2 weeks. For your timeline, we'd need to start the pilot by early November to have data before your Q1 hires start. Does that work?"),
            ("Sarah", "Potentially. I need to think about it and discuss with the team."),
        ]

        # Run through conversation with suggestions
        for i, (speaker, text) in enumerate(conversation):
            print(f"\n{'-'*80}")
            print(f"[{speaker.upper()}]: {text}")

            if speaker == "Sarah":
                # Prospect spoke - generate suggestions
                self.transcript.append(text)
                self._show_suggestions(text)

                # Pause for dramatic effect
                time.sleep(0.5)

        # Call summary
        self._show_call_summary()

    def _show_pre_call_brief(self):
        """Display pre-call context summary"""
        prospect = self.pre_call_context.get("prospect", {})
        pain = self.pre_call_context.get("meddic", {}).get("pain", {})
        strategy = self.pre_call_context.get("strategy", {})

        print(f"\nPRE-CALL BRIEF")
        print(f"-" * 80)
        print(f"Prospect: {prospect.get('name')} - {prospect.get('role')} at {prospect.get('company')}")
        print(f"Call Type: {self.pre_call_context.get('call_metadata', {}).get('call_type')}")
        print(f"\nKey Pains:")
        for p in pain.get("identified_pains", [])[:3]:
            print(f"  • {p}")
        print(f"\nPrimary Goal: {strategy.get('primary_goal')}")
        print(f"\nMEDDIC Progress:")
        self._show_meddic_progress()
        print(f"\n{'-'*80}")
        input("\nPress Enter to start the call simulation...")

    def _show_meddic_progress(self):
        """Show MEDDIC completion status"""
        meddic = self.pre_call_context.get("meddic", {})

        components = {
            "Metrics": bool(meddic.get("metrics", {}).get("current_problem_cost")),
            "Economic Buyer": bool(meddic.get("economic_buyer", {}).get("name")),
            "Decision Criteria": bool(meddic.get("decision_criteria", {}).get("must_haves")),
            "Decision Process": bool(meddic.get("decision_process", {}).get("steps")),
            "Pain": bool(meddic.get("pain", {}).get("identified_pains")),
            "Champion": bool(meddic.get("champion", {}).get("name"))
        }

        for component, complete in components.items():
            status = "[X]" if complete else "[ ]"
            print(f"  {status} {component}")

    def _show_suggestions(self, prospect_statement: str):
        """Generate and display suggestions for prospect's statement"""

        print(f"\n  SUGGESTIONS:")

        # Always use pattern matcher (instant)
        start = time.time()
        instant_suggestions = self.pattern_matcher.analyze(prospect_statement)
        latency_instant = (time.time() - start) * 1000

        if instant_suggestions:
            print(f"\n  [INSTANT - {latency_instant:.0f}ms] Pattern Match:")
            for sug in instant_suggestions[:2]:  # Top 2
                self._format_suggestion({
                    "urgency": sug.urgency.value,
                    "category": sug.category.value,
                    "text": sug.text,
                    "framework": sug.framework,
                    "confidence": sug.confidence
                })

        # Use Claude if enabled
        if self.use_claude:
            print(f"\n  [CONTEXT-AWARE] Claude Analysis:")
            print(f"  (Analyzing with pre-call context...)")

            start = time.time()
            context = CallContext(
                pre_call_context=self.pre_call_context,
                recent_transcript=self.transcript[-5:],
                sales_stage=self.call_stage,
                meddic_progress={}
            )

            try:
                claude_suggestions = self.generator.generate_suggestions(
                    context,
                    urgency_filter="high"  # Only show high urgency from Claude (speed)
                )
                latency_claude = (time.time() - start) * 1000

                print(f"  (Generated in {latency_claude:.0f}ms)")

                for sug in claude_suggestions[:2]:  # Top 2
                    self._format_suggestion(sug)

            except Exception as e:
                print(f"  Error: {e}")

    def _format_suggestion(self, sug: dict):
        """Format and display a suggestion"""
        urgency = sug["urgency"].upper()
        category = sug["category"]
        confidence = int(sug["confidence"] * 100)

        # Priority indicators
        urgency_symbol = {
            "high": "!!!",
            "medium": "!! ",
            "low": "!  "
        }.get(sug["urgency"], "   ")

        print(f"\n    {urgency_symbol} [{urgency}] {category.title()} | {sug['framework']} | {confidence}%")
        print(f"    > {sug['text']}")

    def _show_call_summary(self):
        """Show post-call summary"""
        print(f"\n{'='*80}")
        print("CALL SUMMARY")
        print(f"{'='*80}")

        print(f"\nMEDDIC Progress Updated:")
        # In real system, would update based on what was learned
        print("  [X] Metrics - Confirmed ($750k at risk)")
        print("  [X] Economic Buyer - Identified (Michael Chen, CFO)")
        print("  [X] Decision Criteria - Confirmed (ROI, ramp time, win rate)")
        print("  [X] Decision Process - Mapped (demo > CFO approval)")
        print("  [X] Pain - Quantified (20 hrs/week manager time, 6mo ramp)")
        print("  [X] Champion - Strong (Sarah is actively looking)")

        print(f"\nKey Insights:")
        print("  - Urgency: High (Q1 deadline = 2 months)")
        print("  - Budget: $18k/year (affordable vs $750k at risk)")
        print("  - Objection: 'Need to think about it' = timing stall")
        print("  - Next Step: Propose pilot (3 reps, 30 days, clear metrics)")

        print(f"\nRecommended Follow-up:")
        print("  1. Send pilot proposal (3 reps, 30-day timeline, success metrics)")
        print("  2. Include CFO-focused ROI deck (for Michael)")
        print("  3. Propose kickoff date: Nov 1 (allows data before Q1 hires)")
        print("  4. Follow up in 2 days if no response")

        print(f"\n{'='*80}")


def main():
    """Run the demo"""
    # Get the sample context file
    context_file = os.path.expanduser("~/.ares/applications/sales-coach/calls/sample_call_context.yaml")

    if not os.path.exists(context_file):
        print(f"Error: Sample context file not found at {context_file}")
        print("Please ensure the file exists before running the demo.")
        sys.exit(1)

    # Check if Claude API is available
    use_claude = bool(os.getenv("ANTHROPIC_API_KEY"))

    if not use_claude:
        print("\n" + "="*80)
        print("NOTE: ANTHROPIC_API_KEY not set")
        print("Demo will use pattern matching only (instant suggestions).")
        print("To see Claude-powered context-aware suggestions, set ANTHROPIC_API_KEY.")
        print("="*80)
        input("\nPress Enter to continue with pattern matching only...")

    # Run demo
    demo = SalesCoachDemo(context_file, use_claude=use_claude)
    demo.simulate_call()


if __name__ == "__main__":
    main()
