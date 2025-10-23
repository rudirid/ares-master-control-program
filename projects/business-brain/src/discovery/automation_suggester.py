"""
Intelligent Automation Suggestion System
Analyzes discovered workflows and suggests specific automations with ROI estimates
"""

from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import os
import json


class AutomationSuggester:
    """
    Takes discovered workflows and suggests practical automations
    Includes ROI calculations and implementation complexity estimates
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

        # Rule-based suggestions (fast, no AI needed)
        self.suggestion_rules = {
            "invoice_processing": {
                "title": "Automated Invoice Processing",
                "description": "AI agent reads invoices, extracts data (amount, due date, vendor), creates bookkeeping entries, and flags unusual amounts for review.",
                "time_saved_per_occurrence": 10,  # minutes
                "implementation_complexity": "medium",
                "confidence": 0.92
            },
            "customer_inquiry": {
                "title": "Smart Email Response Assistant",
                "description": "AI learns your response style and drafts replies to common questions. You review and send. Handles 70-80% of routine inquiries.",
                "time_saved_per_occurrence": 8,
                "implementation_complexity": "low",
                "confidence": 0.88
            },
            "appointment_booking": {
                "title": "Automated Appointment Scheduler",
                "description": "AI reads appointment requests, checks your calendar, suggests times, and sends booking confirmations automatically.",
                "time_saved_per_occurrence": 12,
                "implementation_complexity": "medium",
                "confidence": 0.85
            },
            "recurring_meetings": {
                "title": "Meeting Preparation Assistant",
                "description": "Before recurring meetings, AI compiles relevant updates, creates agenda drafts, and sends reminders to attendees.",
                "time_saved_per_occurrence": 15,
                "implementation_complexity": "low",
                "confidence": 0.80
            },
            "regular_client_meetings": {
                "title": "Client Meeting Automation",
                "description": "Sends pre-meeting prep materials, creates meeting notes from calendar, and drafts follow-up emails with action items.",
                "time_saved_per_occurrence": 20,
                "implementation_complexity": "medium",
                "confidence": 0.78
            }
        }

    def generate_suggestions(self, workflows: List[Dict[str, Any]],
                            hourly_rate: float = 50.0) -> List[Dict[str, Any]]:
        """
        Generate automation suggestions for discovered workflows

        Args:
            workflows: List of discovered workflow patterns
            hourly_rate: Business owner's hourly rate for ROI calculation

        Returns:
            List of automation suggestions with ROI data
        """
        suggestions = []

        for workflow in workflows:
            workflow_type = workflow.get("type")
            frequency = workflow.get("frequency", "weekly")
            confidence = workflow.get("confidence", 0.5)

            # Get base suggestion from rules
            if workflow_type in self.suggestion_rules:
                rule = self.suggestion_rules[workflow_type]

                # Calculate ROI
                occurrences_per_week = self._frequency_to_weekly(frequency)
                time_saved_minutes_per_week = (
                    rule["time_saved_per_occurrence"] * occurrences_per_week
                )
                time_saved_hours_per_week = time_saved_minutes_per_week / 60.0
                cost_saved_per_week = time_saved_hours_per_week * hourly_rate

                # Annual projections
                annual_hours_saved = time_saved_hours_per_week * 52
                annual_cost_saved = cost_saved_per_week * 52

                suggestion = {
                    "workflow_type": workflow_type,
                    "title": rule["title"],
                    "description": rule["description"],
                    "confidence": rule["confidence"] * confidence,
                    "implementation_complexity": rule["implementation_complexity"],
                    "roi_data": {
                        "time_saved_per_occurrence_minutes": rule["time_saved_per_occurrence"],
                        "occurrences_per_week": round(occurrences_per_week, 1),
                        "hours_saved_per_week": round(time_saved_hours_per_week, 2),
                        "hours_saved_per_year": round(annual_hours_saved, 0),
                        "cost_saved_per_week": round(cost_saved_per_week, 2),
                        "cost_saved_per_year": round(annual_cost_saved, 2),
                        "hourly_rate_used": hourly_rate
                    },
                    "implementation_steps": self._get_implementation_steps(workflow_type),
                    "example_workflow": workflow.get("pattern_details", {})
                }

                suggestions.append(suggestion)

        # Use AI to enhance suggestions with specific business context
        if self.client and len(workflows) > 0:
            enhanced = self._ai_enhance_suggestions(suggestions, workflows)
            return enhanced

        return suggestions

    def _frequency_to_weekly(self, frequency: str) -> float:
        """Convert frequency string to occurrences per week"""
        frequency_map = {
            "daily": 5.0,  # Assuming business days
            "weekly": 1.0,
            "monthly": 0.25,
            "occasional": 0.1
        }
        return frequency_map.get(frequency.lower(), 1.0)

    def _get_implementation_steps(self, workflow_type: str) -> List[str]:
        """Get implementation steps for a workflow type"""
        steps_map = {
            "invoice_processing": [
                "Connect email account for invoice monitoring",
                "Train AI on your invoice format (2-3 examples)",
                "Set up approval thresholds (auto-process under $X)",
                "Connect to accounting software (Xero/QuickBooks)",
                "Review and approve first 5 processed invoices",
                "Enable full automation"
            ],
            "customer_inquiry": [
                "Connect email account",
                "AI analyzes your past responses (learns tone/style)",
                "Set up draft notification system",
                "Review AI drafts for first 10 emails",
                "Adjust style preferences as needed",
                "Enable auto-draft for all similar inquiries"
            ],
            "appointment_booking": [
                "Connect calendar system",
                "Set availability preferences",
                "Define booking rules (buffer times, max per day)",
                "Create confirmation email templates",
                "Test with trial bookings",
                "Enable public booking links"
            ],
            "recurring_meetings": [
                "Connect calendar to identify recurring meetings",
                "Set prep time preferences (e.g., 1 day before)",
                "Define agenda template",
                "Connect data sources for updates (email, project tools)",
                "Review first 3 automated preps",
                "Enable for all recurring meetings"
            ],
            "regular_client_meetings": [
                "Identify client meeting patterns",
                "Create meeting note templates",
                "Set up follow-up email templates",
                "Connect project management tools",
                "Review automated outputs for first 2 meetings",
                "Roll out to all client meetings"
            ]
        }
        return steps_map.get(workflow_type, ["Contact support for custom setup"])

    def _ai_enhance_suggestions(self, suggestions: List[Dict],
                                workflows: List[Dict]) -> List[Dict]:
        """Use AI to add specific, contextual details to suggestions"""
        if not self.client or not suggestions:
            return suggestions

        # Create context summary
        context = {
            "workflows": workflows[:5],  # Sample
            "suggestions": suggestions
        }

        prompt = f"""You're helping a business owner understand how automation can help their specific business.

Discovered workflows:
{json.dumps(context['workflows'], indent=2)}

Generic suggestions:
{json.dumps([{
    'title': s['title'],
    'description': s['description'],
    'type': s['workflow_type']
} for s in suggestions], indent=2)}

Enhance ONLY the descriptions to be more specific to this business's actual workflows.
Make them compelling but accurate. Keep it under 200 chars per description.

Return a JSON object with keys matching workflow_type and values being the enhanced description:
{{
  "invoice_processing": "enhanced description here",
  "customer_inquiry": "enhanced description here"
}}
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            # Extract JSON
            json_match = content[content.find('{'):content.rfind('}')+1]
            enhanced_descriptions = json.loads(json_match)

            # Update suggestions with enhanced descriptions
            for suggestion in suggestions:
                workflow_type = suggestion["workflow_type"]
                if workflow_type in enhanced_descriptions:
                    suggestion["description_enhanced"] = enhanced_descriptions[workflow_type]

        except Exception as e:
            print(f"AI enhancement error: {e}")

        return suggestions

    def calculate_total_potential(self, suggestions: List[Dict]) -> Dict[str, float]:
        """Calculate total potential savings across all suggestions"""
        total_hours_week = 0
        total_hours_year = 0
        total_cost_year = 0

        for suggestion in suggestions:
            roi = suggestion.get("roi_data", {})
            total_hours_week += roi.get("hours_saved_per_week", 0)
            total_hours_year += roi.get("hours_saved_per_year", 0)
            total_cost_year += roi.get("cost_saved_per_year", 0)

        return {
            "total_hours_per_week": round(total_hours_week, 1),
            "total_hours_per_year": round(total_hours_year, 0),
            "total_cost_per_year": round(total_cost_year, 2),
            "equivalent_full_time_employees": round(total_hours_year / 2080, 2)  # 2080 = full-time hours/year
        }
