"""
Workflow Discovery Engine
Analyzes email patterns, calendar events, and communication to discover repetitive workflows
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import json
from anthropic import Anthropic
import os


class WorkflowDiscoveryEngine:
    """
    Analyzes business data to automatically discover repetitive workflows
    Uses AI to identify patterns that humans might miss
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    def analyze_email_patterns(self, emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze emails to discover workflow patterns

        Args:
            emails: List of email dicts with keys: from, to, subject, body, date, thread_id

        Returns:
            List of discovered workflow patterns
        """
        workflows = []

        # Group emails by sender domain
        domain_groups = defaultdict(list)
        for email in emails:
            sender = email.get("from", "")
            domain = self._extract_domain(sender)
            domain_groups[domain].append(email)

        # Analyze each domain group
        for domain, domain_emails in domain_groups.items():
            if len(domain_emails) < 3:  # Need at least 3 emails to establish pattern
                continue

            # Analyze subject patterns
            subjects = [e.get("subject", "") for e in domain_emails]
            subject_pattern = self._find_common_pattern(subjects)

            # Check for invoice patterns
            if self._is_invoice_pattern(domain_emails):
                workflows.append({
                    "type": "invoice_processing",
                    "domain": domain,
                    "description": f"Regular invoices from {domain}",
                    "confidence": 0.9,
                    "frequency": self._calculate_frequency(domain_emails),
                    "example_count": len(domain_emails),
                    "pattern_details": {
                        "subject_pattern": subject_pattern,
                        "typical_day": self._find_typical_day(domain_emails)
                    }
                })

            # Check for customer inquiry patterns
            elif self._is_inquiry_pattern(domain_emails):
                workflows.append({
                    "type": "customer_inquiry",
                    "domain": domain,
                    "description": f"Customer questions from {domain}",
                    "confidence": 0.85,
                    "frequency": self._calculate_frequency(domain_emails),
                    "example_count": len(domain_emails),
                    "pattern_details": {
                        "subject_pattern": subject_pattern,
                        "avg_response_needed": True
                    }
                })

            # Check for appointment/booking patterns
            elif self._is_appointment_pattern(domain_emails):
                workflows.append({
                    "type": "appointment_booking",
                    "domain": domain,
                    "description": f"Appointment requests from {domain}",
                    "confidence": 0.88,
                    "frequency": self._calculate_frequency(domain_emails),
                    "example_count": len(domain_emails),
                    "pattern_details": {
                        "subject_pattern": subject_pattern
                    }
                })

        # Use AI to find patterns we might have missed
        if self.client and len(emails) > 0:
            ai_patterns = self._ai_discover_patterns(emails[:50])  # Analyze sample
            workflows.extend(ai_patterns)

        return workflows

    def analyze_calendar_patterns(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze calendar events to discover workflow patterns

        Args:
            events: List of calendar events with keys: title, start, end, attendees, recurrence

        Returns:
            List of discovered workflow patterns
        """
        workflows = []

        # Find recurring meeting patterns
        recurring_events = [e for e in events if e.get("recurrence")]
        if recurring_events:
            workflows.append({
                "type": "recurring_meetings",
                "description": f"{len(recurring_events)} recurring meetings requiring prep",
                "confidence": 0.95,
                "frequency": "weekly",
                "pattern_details": {
                    "meetings": [e.get("title") for e in recurring_events[:5]]
                }
            })

        # Find one-off meetings with similar attendees (client check-ins?)
        attendee_groups = defaultdict(list)
        for event in events:
            attendees = tuple(sorted(event.get("attendees", [])))
            if len(attendees) > 0:
                attendee_groups[attendees].append(event)

        for attendees, group_events in attendee_groups.items():
            if len(group_events) >= 3:
                workflows.append({
                    "type": "regular_client_meetings",
                    "description": f"Regular meetings with {len(attendees)} people",
                    "confidence": 0.82,
                    "frequency": self._calculate_frequency(group_events),
                    "pattern_details": {
                        "attendee_count": len(attendees)
                    }
                })

        return workflows

    def _extract_domain(self, email: str) -> str:
        """Extract domain from email address"""
        match = re.search(r'@([\w.-]+)', email)
        return match.group(1) if match else "unknown"

    def _find_common_pattern(self, texts: List[str]) -> str:
        """Find common pattern in text list"""
        if not texts:
            return ""

        # Simple approach: find most common words
        all_words = []
        for text in texts:
            words = re.findall(r'\w+', text.lower())
            all_words.extend(words)

        common = Counter(all_words).most_common(3)
        return " ".join([word for word, count in common if count > len(texts) * 0.3])

    def _is_invoice_pattern(self, emails: List[Dict]) -> bool:
        """Detect if emails are likely invoices"""
        invoice_keywords = ['invoice', 'payment', 'bill', 'due', 'amount', 'total', 'receipt']

        keyword_count = 0
        for email in emails:
            subject = email.get("subject", "").lower()
            body = email.get("body", "").lower()
            text = subject + " " + body

            if any(keyword in text for keyword in invoice_keywords):
                keyword_count += 1

        return keyword_count / len(emails) > 0.6

    def _is_inquiry_pattern(self, emails: List[Dict]) -> bool:
        """Detect if emails are customer inquiries"""
        inquiry_keywords = ['question', 'help', 'inquiry', 'wondering', 'can you', 'would you', 'how to']

        keyword_count = 0
        for email in emails:
            subject = email.get("subject", "").lower()
            body = email.get("body", "").lower()
            text = subject + " " + body

            if any(keyword in text for keyword in inquiry_keywords):
                keyword_count += 1

        return keyword_count / len(emails) > 0.5

    def _is_appointment_pattern(self, emails: List[Dict]) -> bool:
        """Detect if emails are appointment requests"""
        appointment_keywords = ['appointment', 'booking', 'schedule', 'meeting', 'available', 'time', 'calendar']

        keyword_count = 0
        for email in emails:
            subject = email.get("subject", "").lower()
            body = email.get("body", "").lower()
            text = subject + " " + body

            if any(keyword in text for keyword in appointment_keywords):
                keyword_count += 1

        return keyword_count / len(emails) > 0.6

    def _calculate_frequency(self, items: List[Dict]) -> str:
        """Calculate frequency of pattern (daily, weekly, monthly)"""
        if len(items) < 2:
            return "occasional"

        dates = [item.get("date") or item.get("start") for item in items]
        dates = [d for d in dates if d]  # Filter None

        if len(dates) < 2:
            return "occasional"

        # Simple calculation: items per week
        date_objects = []
        for d in dates:
            if isinstance(d, str):
                try:
                    date_objects.append(datetime.fromisoformat(d.replace('Z', '+00:00')))
                except:
                    continue
            elif isinstance(d, datetime):
                date_objects.append(d)

        if len(date_objects) < 2:
            return "occasional"

        date_objects.sort()
        time_span = (date_objects[-1] - date_objects[0]).days

        if time_span == 0:
            return "daily"

        items_per_week = len(items) / (time_span / 7.0)

        if items_per_week > 4:
            return "daily"
        elif items_per_week > 0.8:
            return "weekly"
        elif items_per_week > 0.2:
            return "monthly"
        else:
            return "occasional"

    def _find_typical_day(self, emails: List[Dict]) -> str:
        """Find most common day of week for emails"""
        days = []
        for email in emails:
            date = email.get("date")
            if date:
                if isinstance(date, str):
                    try:
                        dt = datetime.fromisoformat(date.replace('Z', '+00:00'))
                        days.append(dt.strftime('%A'))
                    except:
                        continue
                elif isinstance(date, datetime):
                    days.append(date.strftime('%A'))

        if days:
            most_common = Counter(days).most_common(1)[0][0]
            return most_common
        return "unknown"

    def _ai_discover_patterns(self, emails: List[Dict]) -> List[Dict[str, Any]]:
        """Use AI to discover patterns that rule-based system might miss"""
        if not self.client:
            return []

        # Prepare email summary for AI
        email_summaries = []
        for email in emails[:30]:  # Limit to save tokens
            email_summaries.append({
                "from": email.get("from", ""),
                "subject": email.get("subject", ""),
                "date": str(email.get("date", ""))
            })

        prompt = f"""Analyze these business emails and identify any repetitive workflow patterns that could be automated:

{json.dumps(email_summaries, indent=2)}

Look for:
1. Regular report requests
2. Data entry patterns
3. Follow-up sequences
4. Approval workflows
5. Any other repetitive tasks

Return ONLY a JSON array of patterns found, with this structure:
[
  {{
    "type": "workflow_type",
    "description": "clear description",
    "confidence": 0.0-1.0,
    "frequency": "daily/weekly/monthly",
    "automation_potential": "high/medium/low"
  }}
]

If no clear patterns found, return empty array: []
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                patterns = json.loads(json_match.group(0))
                return patterns
        except Exception as e:
            print(f"AI pattern discovery error: {e}")

        return []
