#!/usr/bin/env python3
"""
Sales Coach Extension WebSocket Server

WebSocket server for Chrome extension communication.
Receives transcripts from extension, generates suggestions, sends back to extension.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import aiohttp
from aiohttp import web

# Add core directory to path
core_path = Path(__file__).parent / "core"
sys.path.insert(0, str(core_path))

from realtime_coach import RealtimeCoach, LiveSuggestion
from pattern_matcher import PatternMatcher


class SalesCoachExtensionServer:
    """
    WebSocket server for Chrome extension integration.
    """

    def __init__(self, default_context_file: str = None):
        self.app = web.Application()
        self.default_context_file = default_context_file or self._get_default_context()
        self.coach = None
        self.extension_clients = set()  # WebSocket clients from extension

        # Setup routes
        self.app.router.add_get('/extension', self.extension_handler)
        self.app.router.add_get('/health', self.health_handler)

    def _get_default_context(self):
        """Get default context file path"""
        return os.path.expanduser("~/.ares/applications/sales-coach/calls/sample_call_context.yaml")

    async def health_handler(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "ok",
            "clients": len(self.extension_clients),
            "coach_active": self.coach is not None
        })

    async def extension_handler(self, request):
        """Handle WebSocket connections from Chrome extension"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.extension_clients.add(ws)
        print(f"[Server] Extension connected (total clients: {len(self.extension_clients)})")

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self.process_message(data, ws)
                    except json.JSONDecodeError:
                        print(f"[Server] Invalid JSON received")
                    except Exception as e:
                        print(f"[Server] Error processing message: {e}")

                elif msg.type == aiohttp.WSMsgType.ERROR:
                    print(f'[Server] WebSocket error: {ws.exception()}')

        finally:
            self.extension_clients.discard(ws)
            print(f"[Server] Extension disconnected (total clients: {len(self.extension_clients)})")

        return ws

    async def process_message(self, data: dict, ws):
        """Process incoming message from extension"""
        msg_type = data.get('type')

        if msg_type == 'start_call':
            await self.handle_start_call(data, ws)

        elif msg_type == 'stop_call':
            await self.handle_stop_call(ws)

        elif msg_type == 'transcript':
            await self.handle_transcript(data, ws)

        else:
            print(f"[Server] Unknown message type: {msg_type}")

    async def handle_start_call(self, data: dict, ws):
        """Start a new coaching session"""
        context_file = data.get('context_file', 'sample')

        # Map context file names to actual files
        context_map = {
            'sample': os.path.expanduser("~/.ares/applications/sales-coach/calls/sample_call_context.yaml"),
            'default': self.default_context_file,
            'custom': self.default_context_file  # TODO: Allow custom file selection
        }

        actual_file = context_map.get(context_file, self.default_context_file)

        if not os.path.exists(actual_file):
            print(f"[Server] Context file not found: {actual_file}, using default")
            actual_file = self.default_context_file

        print(f"[Server] Starting coaching with context: {actual_file}")

        # Initialize coach
        try:
            self.coach = RealtimeCoach(
                actual_file,
                on_suggestion=self.broadcast_suggestion,
                use_claude=bool(os.getenv("ANTHROPIC_API_KEY"))
            )

            # Send MEDDIC progress
            meddic_progress = self.coach.get_meddic_progress()
            await self.broadcast_to_clients({
                'type': 'meddic_update',
                'data': meddic_progress
            })

            print(f"[Server] Coach initialized, MEDDIC: {meddic_progress['completed']}/6")

        except Exception as e:
            print(f"[Server] Error initializing coach: {e}")
            await ws.send_json({
                'type': 'error',
                'message': f'Failed to initialize coach: {e}'
            })

    async def handle_stop_call(self, ws):
        """Stop coaching session"""
        print("[Server] Stopping coaching")
        self.coach = None

    async def handle_transcript(self, data: dict, ws):
        """Process transcript from extension"""
        if not self.coach:
            print("[Server] No active coach, ignoring transcript")
            return

        transcript_data = data.get('data', {})
        text = transcript_data.get('text', '')
        is_final = transcript_data.get('is_final', False)
        confidence = transcript_data.get('confidence', 0.0)

        if not is_final:
            return  # Only process final transcripts

        print(f"[Server] Transcript: {text} (confidence: {confidence:.0%})")

        # Create transcript segment
        from realtime_transcriber import TranscriptSegment
        segment = TranscriptSegment(
            speaker="Prospect",  # Assume prospect for now
            text=text,
            confidence=confidence,
            timestamp=datetime.now(),
            is_final=True
        )

        # Process through coach (generates suggestions via callback)
        self.coach.process_transcript(segment)

        # Echo transcript back to extension (for debugging)
        await self.broadcast_to_clients({
            'type': 'transcript_echo',
            'data': {
                'text': text,
                'confidence': confidence
            }
        })

    def broadcast_suggestion(self, suggestion: LiveSuggestion):
        """Callback from coach - broadcast suggestion to all extensions"""
        asyncio.create_task(self.broadcast_to_clients({
            'type': 'suggestion',
            'data': {
                'id': suggestion.id,
                'text': suggestion.text,
                'urgency': suggestion.urgency,
                'category': suggestion.category,
                'confidence': suggestion.confidence,
                'framework': suggestion.framework,
                'trigger_text': suggestion.trigger_text,
                'source': suggestion.source,
                'timestamp': suggestion.timestamp.isoformat()
            }
        }))

    async def broadcast_to_clients(self, message: dict):
        """Send message to all connected extensions"""
        if not self.extension_clients:
            return

        data = json.dumps(message)
        for ws in list(self.extension_clients):
            try:
                await ws.send_str(data)
            except Exception as e:
                print(f"[Server] Error sending to client: {e}")
                self.extension_clients.discard(ws)

    def run(self, host='localhost', port=5001):
        """Start the server"""
        print("=" * 80)
        print("SALES COACH EXTENSION SERVER")
        print("=" * 80)
        print(f"\nServer starting on {host}:{port}")
        print(f"Extension should connect to: ws://{host}:{port}/extension")
        print("\nWaiting for extension connections...")
        print("Press Ctrl+C to stop\n")

        web.run_app(self.app, host=host, port=port, print=lambda *args: None)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="Sales Coach Extension Server")
    parser.add_argument('--context', help="Default context file")
    parser.add_argument('--host', default='localhost', help="Server host")
    parser.add_argument('--port', type=int, default=5001, help="Server port")

    args = parser.parse_args()

    server = SalesCoachExtensionServer(default_context_file=args.context)

    try:
        server.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
