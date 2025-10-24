"""
Sales Coach UI Server

Flask + SocketIO server for real-time suggestion display.
Runs on second screen/device showing suggestions as they arrive.
"""

from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from datetime import datetime
from dataclasses import asdict


app = Flask(__name__)
app.config['SECRET_KEY'] = 'sales-coach-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
current_call = {
    "active": False,
    "start_time": None,
    "transcript": [],
    "suggestions": [],
    "meddic_progress": {},
    "call_stage": "discovery"
}


@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('coach_ui.html')


@app.route('/api/status')
def status():
    """Get current call status"""
    return jsonify({
        "active": current_call["active"],
        "start_time": current_call["start_time"].isoformat() if current_call["start_time"] else None,
        "transcript_count": len(current_call["transcript"]),
        "suggestion_count": len(current_call["suggestions"]),
        "call_stage": current_call["call_stage"]
    })


@app.route('/api/call_data')
def call_data():
    """Get full call data"""
    return jsonify(current_call)


@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print("[UI Server] Client connected")
    emit('status', {'connected': True})


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print("[UI Server] Client disconnected")


@socketio.on('start_call')
def handle_start_call(data):
    """Start a new call"""
    current_call["active"] = True
    current_call["start_time"] = datetime.now()
    current_call["transcript"] = []
    current_call["suggestions"] = []
    current_call["call_stage"] = data.get("stage", "discovery")

    print("[UI Server] Call started")
    socketio.emit('call_started', current_call)


@socketio.on('end_call')
def handle_end_call():
    """End the current call"""
    current_call["active"] = False
    print("[UI Server] Call ended")
    socketio.emit('call_ended', {})


def emit_transcript(speaker: str, text: str, is_final: bool = True):
    """Emit new transcript segment to UI"""
    segment = {
        "speaker": speaker,
        "text": text,
        "is_final": is_final,
        "timestamp": datetime.now().isoformat()
    }

    if is_final:
        current_call["transcript"].append(segment)

    socketio.emit('transcript', segment)


def emit_suggestion(suggestion_dict: dict):
    """Emit new suggestion to UI"""
    current_call["suggestions"].append(suggestion_dict)
    socketio.emit('suggestion', suggestion_dict)


def emit_meddic_update(meddic_progress: dict):
    """Emit MEDDIC progress update"""
    current_call["meddic_progress"] = meddic_progress
    socketio.emit('meddic_update', meddic_progress)


def emit_stage_change(new_stage: str):
    """Emit call stage change"""
    current_call["call_stage"] = new_stage
    socketio.emit('stage_change', {"stage": new_stage})


if __name__ == '__main__':
    print("=" * 80)
    print("SALES COACH UI SERVER")
    print("=" * 80)
    print("\nStarting server...")
    print("Open in browser: http://localhost:5000")
    print("\nDisplay on second screen for real-time coaching")
    print("Press Ctrl+C to stop\n")

    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
