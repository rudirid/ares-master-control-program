#!/usr/bin/env python3
"""
Sales Coach - Live System

Orchestrates the full real-time sales coaching system:
1. Audio capture (microphone or virtual cable)
2. Real-time transcription (Deepgram)
3. Tactical suggestion generation (pattern matching + Claude)
4. Web UI display (second screen)

Usage:
    python run_sales_coach.py <context_file> [options]

    Options:
        --device <id>     Audio input device ID (see --list-devices)
        --no-claude       Disable Claude suggestions (pattern matching only)
        --list-devices    List available audio devices and exit
"""

import sys
import os
import asyncio
import argparse
from pathlib import Path
import threading

# Add core directory to path
core_path = Path(__file__).parent / "core"
sys.path.insert(0, str(core_path))

from audio_capture import AudioCapture, AudioConfig
from realtime_transcriber import RealtimeTranscriber, TranscriptSegment
from realtime_coach import RealtimeCoach, LiveSuggestion

# Import UI server functions
sys.path.insert(0, str(Path(__file__).parent))
from ui_server import emit_transcript, emit_suggestion, emit_meddic_update, emit_stage_change, socketio, app


class SalesCoachSystem:
    """
    Main orchestrator for the real-time sales coaching system.
    """

    def __init__(
        self,
        context_file: str,
        audio_device: int = None,
        use_claude: bool = True
    ):
        """
        Initialize the system.

        Args:
            context_file: Path to pre-call context YAML
            audio_device: Audio input device ID
            use_claude: Use Claude for suggestions
        """
        self.context_file = context_file
        self.audio_device = audio_device
        self.use_claude = use_claude

        # Components
        self.audio_capture = None
        self.transcriber = None
        self.coach = None

        # State
        self.is_running = False

    async def start(self):
        """Start the full system"""
        print("\n" + "="*80)
        print("SALES COACH - REAL-TIME SYSTEM")
        print("="*80)

        # 1. Initialize coach (loads pre-call context)
        print("\n[1/4] Initializing sales coach...")
        self.coach = RealtimeCoach(
            self.context_file,
            on_suggestion=self._on_suggestion,
            use_claude=self.use_claude
        )

        # Show MEDDIC progress
        meddic = self.coach.get_meddic_progress()
        emit_meddic_update(meddic)
        print(f"      Pre-call context loaded")
        print(f"      MEDDIC: {meddic['completed']}/{meddic['total']} complete")

        # 2. Initialize transcriber
        print("\n[2/4] Connecting to Deepgram...")
        self.transcriber = RealtimeTranscriber(on_transcript=self._on_transcript)

        success = await self.transcriber.start_streaming()
        if not success:
            print("\n      ERROR: Failed to connect to Deepgram")
            print("      Check your DEEPGRAM_API_KEY environment variable")
            return False

        print("      Connected to Deepgram")

        # 3. Initialize audio capture
        print("\n[3/4] Starting audio capture...")
        self.audio_capture = AudioCapture(
            device=self.audio_device,
            on_audio=self._on_audio
        )

        print(f"      Audio device: {self.audio_device or 'default'}")

        # 4. Start UI server (in background thread)
        print("\n[4/4] Starting UI server...")
        threading.Thread(
            target=lambda: socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True),
            daemon=True
        ).start()

        print("      UI server running at: http://localhost:5000")

        # Start audio capture (this blocks)
        print("\n" + "="*80)
        print("SYSTEM READY")
        print("="*80)
        print("\nOpen UI: http://localhost:5000")
        print("Display on second screen for real-time coaching\n")
        print("Speak into microphone to test...")
        print("Press Ctrl+C to stop\n")

        self.is_running = True

        try:
            await self.audio_capture.start_capture()
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            await self.stop()

    async def stop(self):
        """Stop the system"""
        print("\nShutting down...")

        if self.audio_capture:
            self.audio_capture.stop_capture()

        if self.transcriber:
            await self.transcriber.stop_streaming()

        self.is_running = False
        print("System stopped")

    async def _on_audio(self, audio_bytes: bytes):
        """Handle incoming audio from capture"""
        if self.transcriber and self.transcriber.is_running:
            await self.transcriber.stream_audio(audio_bytes)

    def _on_transcript(self, segment: TranscriptSegment):
        """Handle incoming transcript from transcriber"""
        # Emit to UI
        emit_transcript(segment.speaker, segment.text, segment.is_final)

        # Process through coach
        self.coach.process_transcript(segment)

    def _on_suggestion(self, suggestion: LiveSuggestion):
        """Handle new suggestion from coach"""
        # Convert to dict for JSON
        suggestion_dict = {
            "id": suggestion.id,
            "text": suggestion.text,
            "urgency": suggestion.urgency,
            "category": suggestion.category,
            "confidence": suggestion.confidence,
            "framework": suggestion.framework,
            "timestamp": suggestion.timestamp.isoformat(),
            "trigger_text": suggestion.trigger_text,
            "source": suggestion.source
        }

        # Emit to UI
        emit_suggestion(suggestion_dict)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sales Coach - Real-Time AI Sales Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "context_file",
        nargs="?",
        help="Path to pre-call context YAML file"
    )

    parser.add_argument(
        "--device",
        type=int,
        help="Audio input device ID (use --list-devices to see options)"
    )

    parser.add_argument(
        "--no-claude",
        action="store_true",
        help="Disable Claude suggestions (pattern matching only)"
    )

    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices and exit"
    )

    args = parser.parse_args()

    # List devices mode
    if args.list_devices:
        capture = AudioCapture()
        capture.list_devices()
        sys.exit(0)

    # Check for context file
    if not args.context_file:
        print("Error: context_file required")
        print("\nUsage:")
        print("  python run_sales_coach.py <context_file>")
        print("\nExample:")
        print("  python run_sales_coach.py calls/sample_call_context.yaml")
        print("\nOptions:")
        print("  --list-devices    List available audio devices")
        print("  --device <id>     Select audio input device")
        print("  --no-claude       Use pattern matching only (no Claude API)")
        sys.exit(1)

    # Expand path
    context_file = os.path.expanduser(args.context_file)

    if not os.path.exists(context_file):
        print(f"Error: Context file not found: {context_file}")
        sys.exit(1)

    # Check API keys
    if not os.getenv("DEEPGRAM_API_KEY"):
        print("\nError: DEEPGRAM_API_KEY not set")
        print("\n1. Get your API key at: https://deepgram.com")
        print("2. Set it: export DEEPGRAM_API_KEY=your_key")
        print("\nOr add to ~/.bashrc or ~/.zshrc for persistence\n")
        sys.exit(1)

    if not args.no_claude and not os.getenv("ANTHROPIC_API_KEY"):
        print("\nWarning: ANTHROPIC_API_KEY not set")
        print("Claude suggestions will be disabled (pattern matching only)")
        print("\nTo enable Claude:")
        print("1. Get API key at: https://console.anthropic.com")
        print("2. Set it: export ANTHROPIC_API_KEY=your_key\n")
        args.no_claude = True

    # Create and run system
    system = SalesCoachSystem(
        context_file=context_file,
        audio_device=args.device,
        use_claude=not args.no_claude
    )

    try:
        asyncio.run(system.start())
    except KeyboardInterrupt:
        print("\nInterrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
