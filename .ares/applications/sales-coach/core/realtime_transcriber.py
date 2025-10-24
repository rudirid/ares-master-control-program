"""
Real-Time Transcriber - Deepgram WebSocket Integration

Streams audio to Deepgram and receives real-time transcription with speaker diarization.
Target latency: <500ms from speech to transcript.
"""

import os
import asyncio
import json
from typing import Callable, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions


@dataclass
class TranscriptSegment:
    """A segment of transcribed speech"""
    speaker: str  # "You" or "Prospect" (or Speaker0/Speaker1 before identification)
    text: str
    confidence: float
    timestamp: datetime
    is_final: bool  # True if this is final, False if interim


class RealtimeTranscriber:
    """
    Real-time speech-to-text using Deepgram streaming API.

    Features:
    - WebSocket streaming for low latency
    - Speaker diarization (who's talking)
    - Interim results (show immediately while processing)
    - High accuracy with punctuation
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        on_transcript: Optional[Callable[[TranscriptSegment], None]] = None
    ):
        """
        Initialize transcriber.

        Args:
            api_key: Deepgram API key (or reads from DEEPGRAM_API_KEY env)
            on_transcript: Callback function called when transcript received
        """
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DEEPGRAM_API_KEY not found. Get one at https://deepgram.com\n"
                "Set via: export DEEPGRAM_API_KEY=your_key"
            )

        self.client = DeepgramClient(self.api_key)
        self.connection = None
        self.on_transcript = on_transcript
        self.is_running = False

        # Speaker mapping (after we identify who's who)
        self.speaker_map = {}  # {"0": "You", "1": "Prospect"}

    async def start_streaming(self):
        """Start the Deepgram streaming connection"""

        try:
            # Configure Deepgram options for optimal real-time performance
            options = LiveOptions(
                model="nova-2",  # Latest, most accurate model
                language="en-US",
                smart_format=True,  # Automatic punctuation/formatting
                interim_results=True,  # Get results immediately (before finalized)
                utterance_end_ms=1000,  # Mark utterance end after 1s silence
                vad_events=True,  # Voice activity detection
                diarize=True,  # Speaker diarization (who's talking)
                punctuate=True,
                profanity_filter=False,
                redact=False,
            )

            # Create WebSocket connection
            self.connection = self.client.listen.asyncwebsocket.v("1")

            # Set up event handlers
            self.connection.on(LiveTranscriptionEvents.Open, self._on_open)
            self.connection.on(LiveTranscriptionEvents.Transcript, self._on_transcript)
            self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
            self.connection.on(LiveTranscriptionEvents.Close, self._on_close)

            # Start the connection
            if await self.connection.start(options):
                print("[Deepgram] Connection opened - ready to stream audio")
                self.is_running = True
                return True
            else:
                print("[Deepgram] Failed to start connection")
                return False

        except Exception as e:
            print(f"[Deepgram] Error starting: {e}")
            return False

    async def stream_audio(self, audio_data: bytes):
        """
        Stream audio data to Deepgram.

        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz mono recommended)
        """
        if self.connection and self.is_running:
            try:
                await self.connection.send(audio_data)
            except Exception as e:
                print(f"[Deepgram] Error streaming audio: {e}")

    async def stop_streaming(self):
        """Stop the streaming connection"""
        if self.connection:
            self.is_running = False
            await self.connection.finish()
            print("[Deepgram] Connection closed")

    def _on_open(self, *args, **kwargs):
        """Called when WebSocket connection opens"""
        print("[Deepgram] WebSocket opened")

    def _on_transcript(self, *args, **kwargs):
        """Called when transcript received from Deepgram"""
        result = kwargs.get("result")

        if not result:
            return

        # Extract transcript data
        channel = result.channel
        alternatives = channel.alternatives

        if not alternatives or len(alternatives) == 0:
            return

        # Get best alternative (highest confidence)
        alternative = alternatives[0]
        transcript = alternative.transcript.strip()

        if not transcript:
            return  # Empty transcript, skip

        # Extract speaker info (if diarization enabled)
        speaker_id = "unknown"
        if hasattr(alternative, 'words') and alternative.words:
            # Get speaker from first word (usually consistent across utterance)
            speaker_id = str(getattr(alternative.words[0], 'speaker', 'unknown'))

        # Map speaker ID to human-readable name
        speaker_name = self.speaker_map.get(speaker_id, f"Speaker{speaker_id}")

        # Check if this is final or interim
        is_final = result.is_final if hasattr(result, 'is_final') else True

        # Create transcript segment
        segment = TranscriptSegment(
            speaker=speaker_name,
            text=transcript,
            confidence=alternative.confidence,
            timestamp=datetime.now(),
            is_final=is_final
        )

        # Call the callback
        if self.on_transcript:
            self.on_transcript(segment)

        # Debug output
        finality = "FINAL" if is_final else "interim"
        print(f"[{speaker_name}] ({finality}, {alternative.confidence:.0%}): {transcript}")

    def _on_error(self, *args, **kwargs):
        """Called on error"""
        error = kwargs.get("error")
        print(f"[Deepgram] Error: {error}")

    def _on_close(self, *args, **kwargs):
        """Called when connection closes"""
        print("[Deepgram] Connection closed")
        self.is_running = False

    def set_speaker_mapping(self, speaker_map: Dict[str, str]):
        """
        Set mapping from speaker IDs to names.

        Args:
            speaker_map: {"0": "You", "1": "Prospect"} or similar
        """
        self.speaker_map = speaker_map
        print(f"[Deepgram] Speaker mapping updated: {speaker_map}")


# Example usage / test
if __name__ == "__main__":
    import sys

    if not os.getenv("DEEPGRAM_API_KEY"):
        print("Error: DEEPGRAM_API_KEY not set")
        print("Get your API key at: https://deepgram.com")
        print("Then set it: export DEEPGRAM_API_KEY=your_key")
        sys.exit(1)

    # Test callback
    def on_transcript_received(segment: TranscriptSegment):
        print(f"\n>>> Received transcript:")
        print(f"    Speaker: {segment.speaker}")
        print(f"    Text: {segment.text}")
        print(f"    Confidence: {segment.confidence:.0%}")
        print(f"    Final: {segment.is_final}")

    async def test_transcriber():
        """Test the transcriber with microphone input"""
        print("Testing Deepgram Real-Time Transcriber")
        print("=" * 60)

        transcriber = RealtimeTranscriber(on_transcript=on_transcript_received)

        # Set speaker mapping
        transcriber.set_speaker_mapping({"0": "You", "1": "Prospect"})

        # Start streaming
        success = await transcriber.start_streaming()

        if not success:
            print("Failed to start transcriber")
            return

        print("\nTranscriber ready. Speak into your microphone...")
        print("(This test requires audio input implementation)")
        print("Press Ctrl+C to stop\n")

        try:
            # In real usage, you'd pipe audio here
            # For now, just keep connection alive
            await asyncio.sleep(30)  # Keep alive for 30 seconds
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            await transcriber.stop_streaming()

    # Run test
    asyncio.run(test_transcriber())
