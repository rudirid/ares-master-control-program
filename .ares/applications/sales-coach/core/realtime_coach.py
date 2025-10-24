"""
Real-Time Sales Coach Engine

Processes live transcripts and generates tactical suggestions in real-time.
Combines instant pattern matching with context-aware Claude suggestions.
"""

import os
import asyncio
import yaml
from typing import Optional, Callable, List, Dict
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass, asdict

from pattern_matcher import PatternMatcher, Suggestion as PatternSuggestion
from suggestion_generator import SuggestionGenerator, CallContext
from realtime_transcriber import TranscriptSegment


@dataclass
class LiveSuggestion:
    """A suggestion to display to the user"""
    id: str
    text: str
    urgency: str  # high, medium, low
    category: str
    confidence: float
    framework: str
    timestamp: datetime
    trigger_text: str  # What prospect said
    source: str  # "pattern" or "claude"
    shown: bool = False
    dismissed: bool = False


class RealtimeCoach:
    """
    Real-time sales coaching engine.

    Processes transcripts as they arrive and generates suggestions instantly.
    """

    def __init__(
        self,
        pre_call_context_file: str,
        on_suggestion: Optional[Callable[[LiveSuggestion], None]] = None,
        use_claude: bool = True
    ):
        """
        Initialize coach.

        Args:
            pre_call_context_file: Path to pre-call context YAML
            on_suggestion: Callback when new suggestion generated
            use_claude: Use Claude for context-aware suggestions (requires API key)
        """
        self.on_suggestion = on_suggestion
        self.use_claude = use_claude

        # Load pre-call context
        with open(pre_call_context_file) as f:
            self.pre_call_context = yaml.safe_load(f)

        # Initialize pattern matcher (always used)
        self.pattern_matcher = PatternMatcher()

        # Initialize Claude generator (optional)
        if use_claude and os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.suggestion_generator = SuggestionGenerator()
                print("[Coach] Claude suggestions enabled")
            except Exception as e:
                print(f"[Coach] Claude unavailable: {e}")
                self.use_claude = False
        else:
            self.use_claude = False
            print("[Coach] Using pattern matching only (no Claude API key)")

        # State tracking
        self.transcript_history = deque(maxlen=50)  # Last 50 statements
        self.suggestions_shown = []
        self.call_stage = "discovery"
        self.last_suggestion_time = {}  # Prevent duplicate suggestions

        # Suggestion cache (prevent showing same suggestion twice)
        self.suggestion_cache = set()

    def process_transcript(self, segment: TranscriptSegment):
        """
        Process a new transcript segment and generate suggestions.

        Args:
            segment: Transcript segment from transcriber
        """
        # Only process prospect's speech (not our own)
        # In real usage, you'd identify speakers properly
        if segment.speaker == "You":
            self.transcript_history.append(segment.text)
            return

        # Add to history
        self.transcript_history.append(segment.text)

        # Only generate suggestions on final transcripts (not interim)
        if not segment.is_final:
            return

        print(f"\n[Coach] Processing: {segment.speaker}: {segment.text}")

        # Generate suggestions
        asyncio.create_task(self._generate_suggestions(segment))

    async def _generate_suggestions(self, segment: TranscriptSegment):
        """Generate suggestions for a transcript segment"""

        # 1. INSTANT: Pattern matching (<100ms)
        pattern_suggestions = self._get_pattern_suggestions(segment.text)

        for sug in pattern_suggestions:
            await self._emit_suggestion(sug, segment.text, source="pattern")

        # 2. CONTEXT-AWARE: Claude analysis (~1-2s)
        if self.use_claude:
            try:
                claude_suggestions = await self._get_claude_suggestions(segment.text)

                for sug in claude_suggestions:
                    await self._emit_suggestion(sug, segment.text, source="claude")

            except Exception as e:
                print(f"[Coach] Claude error: {e}")

    def _get_pattern_suggestions(self, text: str) -> List[Dict]:
        """Get instant pattern-matched suggestions"""
        suggestions = self.pattern_matcher.analyze(text)

        # Convert to dicts
        return [
            {
                "text": sug.text,
                "urgency": sug.urgency.value,
                "category": sug.category.value,
                "confidence": sug.confidence,
                "framework": sug.framework
            }
            for sug in suggestions
        ]

    async def _get_claude_suggestions(self, text: str) -> List[Dict]:
        """Get context-aware Claude suggestions"""

        # Build context
        context = CallContext(
            pre_call_context=self.pre_call_context,
            recent_transcript=list(self.transcript_history)[-10:],  # Last 10 statements
            sales_stage=self.call_stage,
            meddic_progress={}
        )

        # Generate suggestions (run in thread pool to not block)
        loop = asyncio.get_event_loop()
        suggestions = await loop.run_in_executor(
            None,
            self.suggestion_generator.generate_suggestions,
            context,
            "high"  # Only high urgency for speed
        )

        return suggestions

    async def _emit_suggestion(self, suggestion_dict: Dict, trigger_text: str, source: str):
        """Emit a suggestion to the UI"""

        # Create cache key to prevent duplicates
        cache_key = f"{suggestion_dict['text'][:50]}_{source}"

        # Check if we've shown this recently (within 60 seconds)
        if cache_key in self.last_suggestion_time:
            last_time = self.last_suggestion_time[cache_key]
            if datetime.now() - last_time < timedelta(seconds=60):
                return  # Skip duplicate

        # Create live suggestion
        suggestion = LiveSuggestion(
            id=f"{source}_{datetime.now().timestamp()}",
            text=suggestion_dict["text"],
            urgency=suggestion_dict["urgency"],
            category=suggestion_dict["category"],
            confidence=suggestion_dict["confidence"],
            framework=suggestion_dict["framework"],
            timestamp=datetime.now(),
            trigger_text=trigger_text,
            source=source
        )

        # Update cache
        self.last_suggestion_time[cache_key] = datetime.now()
        self.suggestions_shown.append(suggestion)

        # Call callback
        if self.on_suggestion:
            self.on_suggestion(suggestion)

        # Log
        urgency_symbol = {"high": "!!!", "medium": "!! ", "low": "!  "}.get(suggestion.urgency, "   ")
        print(f"  {urgency_symbol} [{suggestion.urgency.upper()}] {suggestion.framework}")
        print(f"  > {suggestion.text[:100]}...")

    def update_call_stage(self, stage: str):
        """Update current sales stage (discovery, demo, negotiation, close)"""
        self.call_stage = stage
        print(f"[Coach] Stage updated: {stage}")

    def get_meddic_progress(self) -> Dict:
        """Get MEDDIC completion status"""
        meddic = self.pre_call_context.get("meddic", {})

        components = {
            "Metrics": bool(meddic.get("metrics", {}).get("current_problem_cost")),
            "Economic Buyer": bool(meddic.get("economic_buyer", {}).get("name")),
            "Decision Criteria": bool(meddic.get("decision_criteria", {}).get("must_haves")),
            "Decision Process": bool(meddic.get("decision_process", {}).get("steps")),
            "Pain": bool(meddic.get("pain", {}).get("identified_pains")),
            "Champion": bool(meddic.get("champion", {}).get("name"))
        }

        completed = sum(components.values())
        total = len(components)

        return {
            "components": components,
            "completed": completed,
            "total": total,
            "percentage": int(completed / total * 100)
        }

    def get_call_summary(self) -> Dict:
        """Generate call summary"""
        return {
            "transcript_segments": len(self.transcript_history),
            "suggestions_shown": len(self.suggestions_shown),
            "meddic_progress": self.get_meddic_progress(),
            "call_stage": self.call_stage,
            "duration": "N/A"  # Would track actual duration
        }


# Test
if __name__ == "__main__":
    import sys

    # Check for context file
    context_file = os.path.expanduser("~/.ares/applications/sales-coach/calls/sample_call_context.yaml")

    if not os.path.exists(context_file):
        print(f"Error: Context file not found: {context_file}")
        sys.exit(1)

    print("Real-Time Coach Test")
    print("=" * 80)

    # Test callback
    def on_suggestion_received(suggestion: LiveSuggestion):
        print(f"\n>>> SUGGESTION")
        print(f"    {suggestion.urgency.upper()} | {suggestion.framework}")
        print(f"    {suggestion.text}")

    # Create coach
    coach = RealtimeCoach(
        context_file,
        on_suggestion=on_suggestion_received,
        use_claude=False  # Pattern matching only for test
    )

    # Simulate transcript segments
    test_segments = [
        TranscriptSegment("Prospect", "How much does this cost?", 0.9, datetime.now(), True),
        TranscriptSegment("You", "Great question. What budget are you working with?", 0.9, datetime.now(), True),
        TranscriptSegment("Prospect", "We're already using Gong for this", 0.9, datetime.now(), True),
        TranscriptSegment("You", "What's working well with Gong?", 0.9, datetime.now(), True),
        TranscriptSegment("Prospect", "That sounds interesting. How long does implementation take?", 0.9, datetime.now(), True),
    ]

    print("\nProcessing simulated transcript...\n")

    for segment in test_segments:
        print(f"[{segment.speaker}]: {segment.text}")
        coach.process_transcript(segment)

    print("\n" + "=" * 80)
    print("MEDDIC Progress:")
    progress = coach.get_meddic_progress()
    for component, status in progress["components"].items():
        print(f"  [{'X' if status else ' '}] {component}")
    print(f"\nCompleted: {progress['completed']}/{progress['total']} ({progress['percentage']}%)")
