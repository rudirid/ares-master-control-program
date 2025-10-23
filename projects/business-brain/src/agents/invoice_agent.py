"""
Invoice Processing Agent
Automatically reads invoices, extracts data, and creates bookkeeping entries
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from anthropic import Anthropic
import os
import json


class InvoiceAgent:
    """
    Intelligent agent that processes invoices automatically
    - Extracts vendor, amount, due date, line items
    - Categorizes expenses
    - Flags unusual amounts
    - Creates draft bookkeeping entries
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        self.config = config or {}

        # Approval threshold - amounts above this need human review
        self.approval_threshold = self.config.get("approval_threshold", 1000.0)

        # Known vendors for pattern recognition
        self.known_vendors = self.config.get("known_vendors", {})

        # Expense categories
        self.expense_categories = self.config.get("categories", [
            "Office Supplies", "Software/SaaS", "Professional Services",
            "Utilities", "Rent", "Marketing", "Travel", "Other"
        ])

    async def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an email that potentially contains an invoice

        Args:
            email_data: Dict with keys: from, subject, body, attachments

        Returns:
            Processing result with extracted data and actions taken
        """
        result = {
            "invoice_detected": False,
            "processing_time": datetime.now().isoformat(),
            "confidence": 0.0,
            "extracted_data": {},
            "actions_taken": [],
            "requires_review": False,
            "review_reason": None
        }

        # Check if this looks like an invoice
        if not self._is_invoice_email(email_data):
            result["actions_taken"].append("Not an invoice - no processing needed")
            return result

        result["invoice_detected"] = True

        # Extract invoice data using AI
        invoice_data = await self._extract_invoice_data(email_data)

        if not invoice_data:
            result["actions_taken"].append("Failed to extract invoice data")
            result["requires_review"] = True
            result["review_reason"] = "Data extraction failed"
            return result

        result["extracted_data"] = invoice_data
        result["confidence"] = invoice_data.get("confidence", 0.0)

        # Check if requires review
        amount = invoice_data.get("total_amount", 0)
        if amount > self.approval_threshold:
            result["requires_review"] = True
            result["review_reason"] = f"Amount ${amount:.2f} exceeds threshold ${self.approval_threshold:.2f}"
            result["actions_taken"].append("Flagged for review - high amount")
        elif invoice_data.get("unusual_pattern"):
            result["requires_review"] = True
            result["review_reason"] = "Unusual pattern detected"
            result["actions_taken"].append("Flagged for review - unusual pattern")
        else:
            # Auto-process
            bookkeeping_entry = self._create_bookkeeping_entry(invoice_data)
            result["bookkeeping_entry"] = bookkeeping_entry
            result["actions_taken"].append("Created bookkeeping entry")
            result["actions_taken"].append("Ready for auto-posting to accounting software")

        return result

    def _is_invoice_email(self, email_data: Dict) -> bool:
        """Quick check if email contains an invoice"""
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body", "").lower()
        text = subject + " " + body

        invoice_indicators = [
            "invoice", "bill", "payment due", "amount due",
            "receipt", "statement", "payment required"
        ]

        return any(indicator in text for indicator in invoice_indicators)

    async def _extract_invoice_data(self, email_data: Dict) -> Optional[Dict[str, Any]]:
        """Use AI to extract structured data from invoice email"""
        if not self.client:
            # Fallback: simple regex extraction
            return self._fallback_extraction(email_data)

        # Prepare email content for AI
        email_text = f"""
From: {email_data.get('from', '')}
Subject: {email_data.get('subject', '')}

{email_data.get('body', '')}
"""

        prompt = f"""Extract invoice data from this email. Be precise and only extract data you're confident about.

{email_text}

Return a JSON object with this structure:
{{
  "vendor_name": "company name",
  "vendor_email": "email",
  "invoice_number": "invoice #",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "total_amount": 123.45,
  "currency": "USD",
  "line_items": [
    {{"description": "item", "amount": 123.45}}
  ],
  "suggested_category": "Office Supplies|Software/SaaS|Professional Services|etc",
  "confidence": 0.0-1.0,
  "unusual_pattern": false,
  "notes": "any relevant notes"
}}

If you cannot extract a field confidently, use null.
Set unusual_pattern to true if this invoice seems unusual (first time vendor, unusual amount, etc).
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            # Extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                invoice_data = json.loads(content[json_start:json_end])
                return invoice_data

        except Exception as e:
            print(f"AI extraction error: {e}")

        return None

    def _fallback_extraction(self, email_data: Dict) -> Optional[Dict[str, Any]]:
        """Simple regex-based extraction when AI is not available"""
        body = email_data.get("body", "")
        subject = email_data.get("subject", "")

        # Extract amount
        amount_match = re.search(r'\$?\s*(\d+[,.]?\d*\.?\d+)', body)
        amount = float(amount_match.group(1).replace(',', '')) if amount_match else 0.0

        # Extract invoice number
        invoice_match = re.search(r'invoice\s*#?\s*:?\s*(\w+)', body + subject, re.IGNORECASE)
        invoice_number = invoice_match.group(1) if invoice_match else "unknown"

        return {
            "vendor_name": email_data.get("from", "").split('@')[0],
            "vendor_email": email_data.get("from", ""),
            "invoice_number": invoice_number,
            "total_amount": amount,
            "currency": "USD",
            "confidence": 0.6,
            "unusual_pattern": False
        }

    def _create_bookkeeping_entry(self, invoice_data: Dict) -> Dict[str, Any]:
        """Create a bookkeeping entry ready for accounting software"""
        return {
            "entry_type": "bill",
            "vendor": invoice_data.get("vendor_name"),
            "date": invoice_data.get("invoice_date") or datetime.now().strftime("%Y-%m-%d"),
            "due_date": invoice_data.get("due_date"),
            "reference": invoice_data.get("invoice_number"),
            "amount": invoice_data.get("total_amount"),
            "category": invoice_data.get("suggested_category", "Other"),
            "description": f"Invoice from {invoice_data.get('vendor_name')}",
            "line_items": invoice_data.get("line_items", []),
            "status": "draft",
            "notes": invoice_data.get("notes", "")
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return agent statistics"""
        return {
            "agent_type": "invoice_processor",
            "approval_threshold": self.approval_threshold,
            "known_vendors_count": len(self.known_vendors),
            "categories_available": len(self.expense_categories)
        }
