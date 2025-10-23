"""
FastAPI Backend for Business Brain
Provides REST API for the dashboard and coordinates all agents
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database
from discovery.workflow_engine import WorkflowDiscoveryEngine
from discovery.automation_suggester import AutomationSuggester
from agents.invoice_agent import InvoiceAgent
from agents.email_response_agent import EmailResponseAgent

app = FastAPI(title="Business Brain API", version="1.0.0")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
db = Database()
workflow_engine = WorkflowDiscoveryEngine()
automation_suggester = AutomationSuggester()
invoice_agent = InvoiceAgent()
email_response_agent = EmailResponseAgent()


# Pydantic models
class EmailData(BaseModel):
    from_address: str
    to_address: str
    subject: str
    body: str
    date: str
    thread_id: Optional[str] = None


class DiscoveryRequest(BaseModel):
    emails: List[EmailData]
    calendar_events: Optional[List[Dict]] = None
    hourly_rate: Optional[float] = 50.0


class InvoiceProcessRequest(BaseModel):
    email: EmailData


class EmailResponseRequest(BaseModel):
    email: EmailData
    context: Optional[Dict] = None


@app.on_event("startup")
async def startup():
    """Initialize database on startup"""
    await db.initialize()


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "operational",
        "service": "Business Brain API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = await db.get_dashboard_stats()
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/workflows")
async def get_workflows(limit: int = 10):
    """Get recently discovered workflows"""
    try:
        workflows = await db.get_recent_workflows(limit)
        return {
            "success": True,
            "data": workflows,
            "count": len(workflows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/discover")
async def discover_workflows(request: DiscoveryRequest, background_tasks: BackgroundTasks):
    """
    Analyze data and discover workflow patterns
    This is the core "magic" - automatic workflow discovery
    """
    try:
        # Convert Pydantic models to dicts
        emails = [e.dict() for e in request.emails]

        # Discover workflows
        discovered = workflow_engine.analyze_email_patterns(emails)

        # Store in database
        workflow_ids = []
        for workflow in discovered:
            workflow_id = await db.add_discovered_workflow(
                workflow_type=workflow["type"],
                description=workflow["description"],
                confidence=workflow["confidence"],
                frequency=workflow["frequency"],
                example_data=workflow.get("pattern_details", {})
            )
            workflow_ids.append(workflow_id)

        # Generate automation suggestions
        suggestions = automation_suggester.generate_suggestions(
            discovered,
            hourly_rate=request.hourly_rate
        )

        # Store suggestions
        for idx, suggestion in enumerate(suggestions):
            await db.add_automation_suggestion(
                workflow_id=workflow_ids[idx] if idx < len(workflow_ids) else workflow_ids[0],
                title=suggestion["title"],
                description=suggestion.get("description_enhanced", suggestion["description"]),
                time_saved=suggestion["roi_data"]["hours_saved_per_year"],
                cost_saved=suggestion["roi_data"]["cost_saved_per_year"],
                complexity=suggestion["implementation_complexity"]
            )

        # Calculate total potential
        total_potential = automation_suggester.calculate_total_potential(suggestions)

        return {
            "success": True,
            "workflows_discovered": len(discovered),
            "suggestions_generated": len(suggestions),
            "workflows": discovered,
            "suggestions": suggestions,
            "total_potential": total_potential,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/invoice/process")
async def process_invoice(request: InvoiceProcessRequest):
    """Process an invoice using the invoice agent"""
    try:
        email_dict = request.email.dict()
        result = await invoice_agent.process_email(email_dict)

        # Log to database if processed
        if result["invoice_detected"]:
            # In production, we'd get agent_id from database
            # For POC, we'll just return the result
            pass

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/email-response/draft")
async def draft_email_response(request: EmailResponseRequest):
    """Draft an email response using the email response agent"""
    try:
        email_dict = request.email.dict()
        result = await email_response_agent.draft_response(
            email_dict,
            context=request.context
        )

        return {
            "success": True,
            "data": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/agents/email-response/learn")
async def learn_from_emails(emails: List[EmailData]):
    """Train email response agent on sent emails"""
    try:
        emails_dict = [e.dict() for e in emails]
        learned_style = await email_response_agent.learn_from_sent_emails(emails_dict)

        return {
            "success": True,
            "learned_style": learned_style,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/agents/stats")
async def get_agent_stats():
    """Get statistics for all agents"""
    try:
        return {
            "success": True,
            "agents": {
                "invoice_agent": invoice_agent.get_stats(),
                "email_response_agent": email_response_agent.get_stats()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
