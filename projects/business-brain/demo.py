"""
Demo Script for Business Brain
Demonstrates workflow discovery and automation suggestions with sample data
"""

import asyncio
import json
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import Database
from discovery.workflow_engine import WorkflowDiscoveryEngine
from discovery.automation_suggester import AutomationSuggester
from agents.invoice_agent import InvoiceAgent
from agents.email_response_agent import EmailResponseAgent


# Sample business data
SAMPLE_EMAILS = [
    # Invoice pattern
    {
        "from": "accounts@acmesupply.com",
        "to": "you@business.com",
        "subject": "Invoice #12345 - Payment Due",
        "body": "Thank you for your business. Please find invoice #12345 attached. Total: $450.00. Due date: 2024-02-15. Payment terms: Net 30.",
        "date": datetime(2024, 2, 1, 10, 0),
        "thread_id": "inv001"
    },
    {
        "from": "billing@acmesupply.com",
        "to": "you@business.com",
        "subject": "Invoice #12389 - Monthly Statement",
        "body": "Monthly office supplies invoice. Amount: $420.00. Payment due: 2024-03-15. Thank you.",
        "date": datetime(2024, 3, 1, 10, 0),
        "thread_id": "inv002"
    },
    {
        "from": "invoices@acmesupply.com",
        "to": "you@business.com",
        "subject": "Invoice #12423 Due",
        "body": "Invoice for April supplies. Total amount: $385.00. Due: 2024-04-15",
        "date": datetime(2024, 4, 1, 10, 0),
        "thread_id": "inv003"
    },
    {
        "from": "accounts@techservices.com",
        "to": "you@business.com",
        "subject": "Monthly SaaS Invoice",
        "body": "Your monthly subscription invoice. Amount due: $299.00. Auto-payment on file.",
        "date": datetime(2024, 3, 15, 9, 0),
        "thread_id": "inv004"
    },

    # Customer inquiry pattern
    {
        "from": "customer@email.com",
        "to": "you@business.com",
        "subject": "Question about your services",
        "body": "Hi, I was wondering if you could help me with pricing information for your services? I'm interested in your consulting packages.",
        "date": datetime(2024, 3, 15, 14, 30),
        "thread_id": "inq001"
    },
    {
        "from": "client@company.com",
        "to": "you@business.com",
        "subject": "Inquiry about availability",
        "body": "Hello, can you let me know your availability for a consultation next week? We're interested in your expertise.",
        "date": datetime(2024, 3, 18, 9, 15),
        "thread_id": "inq002"
    },
    {
        "from": "prospect@business.net",
        "to": "you@business.com",
        "subject": "Quick question",
        "body": "Hi there, just wondering if you offer weekend appointments? Thanks!",
        "date": datetime(2024, 3, 20, 16, 45),
        "thread_id": "inq003"
    },
    {
        "from": "newclient@startup.io",
        "to": "you@business.com",
        "subject": "Help needed",
        "body": "We're looking for someone to help with our project. Can you provide information about your rates and availability?",
        "date": datetime(2024, 3, 22, 11, 0),
        "thread_id": "inq004"
    },

    # Appointment booking pattern
    {
        "from": "patient@health.com",
        "to": "you@business.com",
        "subject": "Appointment Request",
        "body": "I'd like to schedule an appointment for next Tuesday if possible. Morning times work best for me.",
        "date": datetime(2024, 3, 10, 14, 0),
        "thread_id": "apt001"
    },
    {
        "from": "client2@email.com",
        "to": "you@business.com",
        "subject": "Booking a meeting",
        "body": "Can we schedule a meeting to discuss the project? I'm available Monday through Wednesday afternoons.",
        "date": datetime(2024, 3, 12, 10, 30),
        "thread_id": "apt002"
    },
    {
        "from": "customer3@business.com",
        "to": "you@business.com",
        "subject": "Calendar availability?",
        "body": "Looking to book time with you. What does your calendar look like for the next two weeks?",
        "date": datetime(2024, 3, 16, 15, 20),
        "thread_id": "apt003"
    }
]

SAMPLE_SENT_EMAILS = [
    {
        "to": "customer@email.com",
        "subject": "Re: Question about your services",
        "body": "Hi there,\n\nThanks for reaching out! I'd be happy to help with pricing information. Our consulting packages start at $150/hour for basic services, with monthly retainer options available for ongoing work.\n\nWould you like to schedule a quick call to discuss your specific needs?\n\nBest regards,\nYou",
        "date": datetime(2024, 3, 15, 16, 0)
    },
    {
        "to": "client@company.com",
        "subject": "Re: Inquiry about availability",
        "body": "Hello,\n\nI'd be glad to help! I have availability next week on Tuesday afternoon or Thursday morning. Would either of those work for you?\n\nLooking forward to connecting.\n\nBest,\nYou",
        "date": datetime(2024, 3, 18, 11, 30)
    }
]


async def run_demo():
    """Run complete demo of Business Brain"""
    print("=" * 80)
    print("BUSINESS BRAIN - Proof of Concept Demo")
    print("=" * 80)
    print()

    # Initialize
    print("[*] Initializing system...")
    db = Database()
    await db.initialize()
    print("✓ Database initialized")

    workflow_engine = WorkflowDiscoveryEngine()
    print("✓ Workflow discovery engine ready")

    automation_suggester = AutomationSuggester()
    print("✓ Automation suggester ready")

    invoice_agent = InvoiceAgent()
    print("✓ Invoice agent ready")

    email_agent = EmailResponseAgent()
    print("✓ Email response agent ready")
    print()

    # Step 1: Discover workflows
    print("-" * 80)
    print("STEP 1: DISCOVERING WORKFLOW PATTERNS")
    print("-" * 80)
    print(f"Analyzing {len(SAMPLE_EMAILS)} business emails...")
    print()

    discovered = workflow_engine.analyze_email_patterns(SAMPLE_EMAILS)

    print(f"✓ Discovered {len(discovered)} workflow patterns:\n")
    for i, workflow in enumerate(discovered, 1):
        print(f"  {i}. {workflow['description']}")
        print(f"     Type: {workflow['type']}")
        print(f"     Frequency: {workflow['frequency']}")
        print(f"     Confidence: {workflow['confidence']*100:.0f}%")
        print()

    # Step 2: Generate automation suggestions
    print("-" * 80)
    print("STEP 2: GENERATING AUTOMATION SUGGESTIONS")
    print("-" * 80)
    print("Calculating ROI and creating implementation plans...")
    print()

    suggestions = automation_suggester.generate_suggestions(
        discovered,
        hourly_rate=75.0
    )

    for i, suggestion in enumerate(suggestions, 1):
        print(f"  {i}. {suggestion['title']}")
        print(f"     {suggestion['description'][:100]}...")
        print(f"     Complexity: {suggestion['implementation_complexity'].upper()}")
        roi = suggestion['roi_data']
        print(f"     ROI: {roi['hours_saved_per_week']:.1f}h/week = ${roi['cost_saved_per_year']:.0f}/year")
        print()

    # Calculate total potential
    total = automation_suggester.calculate_total_potential(suggestions)
    print(f"📈 TOTAL POTENTIAL:")
    print(f"   • {total['total_hours_per_week']:.1f} hours saved per week")
    print(f"   • {total['total_hours_per_year']:.0f} hours saved per year")
    print(f"   • ${total['total_cost_per_year']:.0f} annual savings")
    print(f"   • Equivalent to {total['equivalent_full_time_employees']:.2f} FTE")
    print()

    # Step 3: Demo invoice agent
    print("-" * 80)
    print("STEP 3: INVOICE PROCESSING AGENT DEMO")
    print("-" * 80)
    invoice_email = SAMPLE_EMAILS[0]  # First invoice
    print(f"Processing email from {invoice_email['from']}...")
    print(f"Subject: {invoice_email['subject']}")
    print()

    result = await invoice_agent.process_email(invoice_email)

    if result['invoice_detected']:
        print("✓ Invoice detected and processed!")
        print(f"  Confidence: {result['confidence']*100:.0f}%")
        if result['extracted_data']:
            data = result['extracted_data']
            print(f"  Vendor: {data.get('vendor_name', 'N/A')}")
            print(f"  Amount: ${data.get('total_amount', 0):.2f}")
            print(f"  Invoice #: {data.get('invoice_number', 'N/A')}")

        if result.get('bookkeeping_entry'):
            print("  ✓ Bookkeeping entry created (ready for Xero/QuickBooks)")

        if result['requires_review']:
            print(f"  ⚠️  Flagged for review: {result['review_reason']}")
    print()

    # Step 4: Demo email response agent
    print("-" * 80)
    print("STEP 4: EMAIL RESPONSE AGENT DEMO")
    print("-" * 80)

    # First, learn from sent emails
    print("Training agent on your communication style...")
    learned = await email_agent.learn_from_sent_emails(SAMPLE_SENT_EMAILS)
    print(f"✓ Learned style: {learned.get('tone', 'professional')}")
    print()

    # Draft a response
    inquiry_email = SAMPLE_EMAILS[4]  # Customer inquiry
    print(f"Drafting response to: {inquiry_email['subject']}")
    print(f"From: {inquiry_email['from']}")
    print()

    draft_result = await email_agent.draft_response(inquiry_email)

    if draft_result['draft_created']:
        print("✓ Draft created!")
        print(f"  Confidence: {draft_result['confidence']*100:.0f}%")
        print(f"\n  Draft Subject: {draft_result['draft_subject']}")
        print(f"\n  Draft Body:\n{draft_result['draft_body']}")
        print(f"\n  Status: {draft_result['review_reason']}")
    print()

    # Step 5: Store results in database
    print("-" * 80)
    print("STEP 5: STORING RESULTS IN DATABASE")
    print("-" * 80)

    for workflow in discovered:
        workflow_id = await db.add_discovered_workflow(
            workflow_type=workflow['type'],
            description=workflow['description'],
            confidence=workflow['confidence'],
            frequency=workflow['frequency'],
            example_data=workflow.get('pattern_details', {})
        )
        print(f"✓ Stored workflow: {workflow['type']} (ID: {workflow_id})")

    for suggestion in suggestions:
        await db.add_automation_suggestion(
            workflow_id=1,  # Simplified for demo
            title=suggestion['title'],
            description=suggestion['description'],
            time_saved=suggestion['roi_data']['hours_saved_per_year'],
            cost_saved=suggestion['roi_data']['cost_saved_per_year'],
            complexity=suggestion['implementation_complexity']
        )
        print(f"✓ Stored suggestion: {suggestion['title']}")

    print()

    # Final stats
    print("=" * 80)
    print("✅ DEMO COMPLETE - SYSTEM READY")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Start the API server: python src/api/main.py")
    print("  2. Open the dashboard: src/dashboard/index.html")
    print("  3. Connect your actual email/calendar accounts")
    print()
    print("Database location:", db.db_path)
    print()


if __name__ == "__main__":
    asyncio.run(run_demo())
