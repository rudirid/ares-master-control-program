"""
FocusGuard AI - Main FastAPI Server
Entry point for the AI phone answering service
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="FocusGuard AI", version="0.1.0")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "FocusGuard AI",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "api": "up",
            "database": "pending",  # TODO: Add DB health check
            "twilio": "pending",    # TODO: Add Twilio health check
            "voice_ai": "pending"   # TODO: Add voice AI health check
        }
    }


# TODO: Add these endpoints in Week 2
# @app.post("/webhook/twilio")  # Receives calls from Twilio
# @app.post("/webhook/voice-ai")  # Receives AI responses
# @app.get("/calls")  # List all calls
# @app.get("/calls/{call_id}")  # Get specific call details
# @app.post("/customers")  # Add new customer
# @app.get("/customers/{customer_id}/calls")  # Get customer call history


if __name__ == "__main__":
    print("🚀 Starting FocusGuard AI server...")
    print("📍 Server will be at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload during development
    )
