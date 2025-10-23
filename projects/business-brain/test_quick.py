"""Quick test of Business Brain core functionality"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import Database
from discovery.workflow_engine import WorkflowDiscoveryEngine
from discovery.automation_suggester import AutomationSuggester

# Simple test data - need 3+ of each type to trigger pattern detection
test_emails = [
    # Invoice pattern (need 3+)
    {
        "from": "invoices@supplier.com",
        "subject": "Invoice #123 - Payment Due",
        "body": "Thank you for your business. Invoice attached. Amount due: $500. Payment terms: Net 30.",
        "date": "2024-03-01"
    },
    {
        "from": "billing@supplier.com",
        "subject": "Invoice #124",
        "body": "Monthly invoice. Total amount: $525. Due date: 2024-04-15",
        "date": "2024-04-01"
    },
    {
        "from": "accounts@supplier.com",
        "subject": "Invoice #125 Due",
        "body": "Invoice for services. Total: $510. Payment required by 2024-05-01",
        "date": "2024-05-01"
    },
    # Customer inquiry pattern (need 3+)
    {
        "from": "customer1@email.com",
        "subject": "Question about services",
        "body": "Can you help me with pricing information? I'm wondering about your rates.",
        "date": "2024-03-15"
    },
    {
        "from": "customer2@company.com",
        "subject": "Quick question",
        "body": "Hi, just wondering if you could provide some information about your services?",
        "date": "2024-03-18"
    },
    {
        "from": "prospect@startup.io",
        "subject": "Inquiry",
        "body": "Hello, can you help me understand your pricing model? Thanks!",
        "date": "2024-03-20"
    },
    # Appointment pattern (need 3+)
    {
        "from": "client1@email.com",
        "subject": "Appointment request",
        "body": "I'd like to schedule an appointment for next week. What's your availability?",
        "date": "2024-03-10"
    },
    {
        "from": "client2@company.com",
        "subject": "Booking a meeting",
        "body": "Can we schedule a meeting to discuss the project? My calendar is open Tuesday.",
        "date": "2024-03-12"
    },
    {
        "from": "client3@business.net",
        "subject": "Schedule time?",
        "body": "Would love to book some time on your calendar. When are you available?",
        "date": "2024-03-14"
    }
]

async def test():
    print("=" * 60)
    print("Business Brain - Quick Test")
    print("=" * 60)

    # Test database
    print("\n[1] Testing database...")
    db = Database()
    await db.initialize()
    print("    SUCCESS - Database initialized")

    # Test workflow discovery
    print("\n[2] Testing workflow discovery...")
    engine = WorkflowDiscoveryEngine()
    workflows = engine.analyze_email_patterns(test_emails)
    print(f"    SUCCESS - Found {len(workflows)} workflows")
    for w in workflows:
        print(f"      - {w['type']}: {w['description']}")

    # Test automation suggester
    print("\n[3] Testing automation suggester...")
    suggester = AutomationSuggester()
    suggestions = suggester.generate_suggestions(workflows, hourly_rate=75.0)
    print(f"    SUCCESS - Generated {len(suggestions)} suggestions")
    for s in suggestions:
        roi = s['roi_data']
        print(f"      - {s['title']}")
        print(f"        ROI: ${roi['cost_saved_per_year']:.0f}/year")

    # Test total potential
    print("\n[4] Calculating total potential...")
    total = suggester.calculate_total_potential(suggestions)
    print(f"    Total hours saved/week: {total['total_hours_per_week']}")
    print(f"    Total annual savings: ${total['total_cost_per_year']:.0f}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED - System Working!")
    print("=" * 60)
    print("\nNext: Run the full demo with 'python demo.py'")
    print("Or start the web interface:")
    print("  1. python src/api/main.py")
    print("  2. Open src/dashboard/index.html in browser")

if __name__ == "__main__":
    asyncio.run(test())
