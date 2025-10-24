"""
Audio Capture - System Audio or Microphone

Captures audio from system (Google Meet) or microphone and streams to transcriber.
Supports virtual audio cable routing for Google Meet.
"""

import os
import asyncio
import queue
import numpy as np
import sounddevice as sd
from typing import Optional, Callable
from dataclasses import dataclass


@dataclass
class AudioConfig:
    """Audio configuration"""
    sample_rate: int = 16000  # Deepgram optimized for 16kHz
    channels: int = 1  # Mono (simplifies processing)
    dtype: str = 'int16'  # 16-bit PCM
    blocksize: int = 8000  # 0.5 seconds at 16kHz (low latency)


class AudioCapture:
    """
    Capture audio from system or microphone and stream to callback.

    Supports:
    - Microphone input (for testing)
    - Virtual audio cable input (for Google Meet capture)
    - Low latency buffering
    """

    def __init__(
        self,
        config: Optional[AudioConfig] = None,
        on_audio: Optional[Callable[[bytes], None]] = None,
        device: Optional[int] = None
    ):
        """
        Initialize audio capture.

        Args:
            config: Audio configuration (defaults to 16kHz mono)
            on_audio: Callback function called with audio bytes
            device: Audio device index (None = default, see list_devices())
        """
        self.config = config or AudioConfig()
        self.on_audio = on_audio
        self.device = device
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.stream = None

    def list_devices(self):
        """List available audio devices"""
        print("\nAvailable Audio Devices:")
        print("=" * 80)
        devices = sd.query_devices()

        for i, device in enumerate(devices):
            device_type = []
            if device['max_input_channels'] > 0:
                device_type.append("INPUT")
            if device['max_output_channels'] > 0:
                device_type.append("OUTPUT")

            type_str = "/".join(device_type) if device_type else "N/A"
            default = " [DEFAULT]" if i == sd.default.device[0] else ""

            print(f"{i:2d}. {device['name']}")
            print(f"    Type: {type_str}{default}")
            print(f"    Channels: In={device['max_input_channels']}, Out={device['max_output_channels']}")
            print(f"    Sample Rate: {device['default_samplerate']} Hz")
            print()

        print("=" * 80)
        print("\nFor Google Meet capture:")
        print("1. Install Virtual Audio Cable (VB-CABLE or BlackHole)")
        print("2. Route Google Meet audio to virtual cable")
        print("3. Select virtual cable as input device")
        print()

    def _audio_callback(self, indata, frames, time_info, status):
        """Called when audio data is available"""
        if status:
            print(f"[Audio] Status: {status}")

        # Convert to bytes and add to queue
        audio_bytes = indata.tobytes()
        self.audio_queue.put(audio_bytes)

    async def start_capture(self):
        """Start capturing audio"""
        print(f"[Audio] Starting capture from device {self.device or 'default'}...")

        try:
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.config.channels,
                samplerate=self.config.sample_rate,
                dtype=self.config.dtype,
                blocksize=self.config.blocksize,
                callback=self._audio_callback
            )

            self.stream.start()
            self.is_running = True

            print(f"[Audio] Capture started")
            print(f"[Audio] Config: {self.config.sample_rate}Hz, {self.config.channels}ch, {self.config.dtype}")

            # Process audio queue asynchronously
            await self._process_queue()

        except Exception as e:
            print(f"[Audio] Error starting capture: {e}")
            print("\nTroubleshooting:")
            print("1. Run list_devices() to see available devices")
            print("2. Check if device is in use by another application")
            print("3. Verify virtual audio cable is installed (if using)")

    async def _process_queue(self):
        """Process audio from queue and call callback"""
        while self.is_running:
            try:
                # Get audio from queue (non-blocking with timeout)
                audio_bytes = self.audio_queue.get(timeout=0.1)

                # Call the callback
                if self.on_audio:
                    # If callback is async, await it
                    if asyncio.iscoroutinefunction(self.on_audio):
                        await self.on_audio(audio_bytes)
                    else:
                        self.on_audio(audio_bytes)

            except queue.Empty:
                await asyncio.sleep(0.01)  # Small sleep to prevent busy waiting
            except Exception as e:
                print(f"[Audio] Error processing queue: {e}")

    def stop_capture(self):
        """Stop capturing audio"""
        self.is_running = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("[Audio] Capture stopped")

    def get_volume_level(self) -> float:
        """
        Get current audio volume level (0-100).
        Useful for debugging and visualizing audio input.
        """
        if self.audio_queue.empty():
            return 0.0

        # Peek at latest audio without removing from queue
        try:
            audio_bytes = self.audio_queue.queue[-1]
            audio_data = np.frombuffer(audio_bytes, dtype=np.int16)

            # Calculate RMS volume
            rms = np.sqrt(np.mean(audio_data**2))
            max_amplitude = 32768  # Max for 16-bit audio

            # Convert to percentage
            volume = min(100, (rms / max_amplitude) * 100)
            return volume

        except Exception:
            return 0.0


# Test/Example Usage
if __name__ == "__main__":
    import sys

    def print_help():
        print("Audio Capture Test")
        print("=" * 80)
        print("\nUsage:")
        print("  python audio_capture.py list       - List available devices")
        print("  python audio_capture.py test       - Test default microphone")
        print("  python audio_capture.py test <id>  - Test specific device")
        print()

    async def test_capture(device_id: Optional[int] = None):
        """Test audio capture"""
        print(f"Testing audio capture (device={device_id or 'default'})")
        print("Speak into your microphone...")
        print("Press Ctrl+C to stop\n")

        # Callback to show audio is being captured
        def on_audio_received(audio_bytes):
            # Just print length to show it's working
            print(f"[Audio] Captured {len(audio_bytes)} bytes", end='\r')

        capture = AudioCapture(device=device_id, on_audio=on_audio_received)

        try:
            await capture.start_capture()
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            capture.stop_capture()

    # Parse command line
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        capture = AudioCapture()
        capture.list_devices()

    elif command == "test":
        device_id = None
        if len(sys.argv) > 2:
            device_id = int(sys.argv[2])

        asyncio.run(test_capture(device_id))

    else:
        print_help()
