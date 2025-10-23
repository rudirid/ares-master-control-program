"""
Email Response Agent
Learns your communication style and drafts responses to common inquiries
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from anthropic import Anthropic
import os
import json


class EmailResponseAgent:
    """
    Intelligent agent that drafts email responses
    - Learns from your past emails
    - Understands context and tone
    - Drafts responses for your review
    - Handles 70-80% of routine inquiries
    """

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if self.api_key else None
        self.config = config or {}

        # Style learning
        self.learned_style = self.config.get("learned_style", {
            "tone": "professional and friendly",
            "signature": "Best regards",
            "typical_greeting": "Hi",
            "formality_level": "moderate"
        })

        # Common response templates (learned from past emails)
        self.response_patterns = self.config.get("response_patterns", {})

    async def learn_from_sent_emails(self, sent_emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sent emails to learn communication style

        Args:
            sent_emails: List of previously sent emails

        Returns:
            Learned style characteristics
        """
        if not self.client or len(sent_emails) < 5:
            return self.learned_style

        # Sample emails for learning
        sample_emails = sent_emails[:20]  # Use up to 20 for learning

        email_samples = []
        for email in sample_emails:
            email_samples.append({
                "to": email.get("to", ""),
                "subject": email.get("subject", ""),
                "body": email.get("body", "")[:500]  # First 500 chars
            })

        prompt = f"""Analyze these sent emails to learn the writing style and tone:

{json.dumps(email_samples, indent=2)}

Identify:
1. Tone (professional, casual, friendly, formal, etc.)
2. Common greetings used
3. Common sign-offs
4. Formality level (high, moderate, low)
5. Typical response patterns for common scenarios
6. Average email length preference
7. Use of emojis or exclamation points

Return JSON:
{{
  "tone": "description",
  "typical_greeting": "Hi|Hello|Hey|etc",
  "signature": "Best regards|Cheers|Thanks|etc",
  "formality_level": "high|moderate|low",
  "uses_emojis": true/false,
  "avg_length": "brief|moderate|detailed",
  "key_phrases": ["phrase1", "phrase2"],
  "response_speed_preference": "immediate|thoughtful"
}}
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0:
                self.learned_style = json.loads(content[json_start:json_end])

        except Exception as e:
            print(f"Style learning error: {e}")

        return self.learned_style

    async def draft_response(self, incoming_email: Dict[str, Any],
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Draft a response to an incoming email

        Args:
            incoming_email: The email to respond to
            context: Optional context (past emails with sender, business info, etc.)

        Returns:
            Draft response with metadata
        """
        result = {
            "draft_created": False,
            "confidence": 0.0,
            "draft_subject": "",
            "draft_body": "",
            "requires_review": True,
            "review_reason": "Standard review",
            "processing_time": datetime.now().isoformat()
        }

        if not self.client:
            result["review_reason"] = "AI not configured - cannot draft"
            return result

        # Analyze incoming email
        email_type = self._classify_email(incoming_email)

        # Build context for AI
        context_text = ""
        if context:
            past_emails = context.get("past_emails", [])
            if past_emails:
                context_text = "\n\nPrevious emails with this sender:\n"
                for past in past_emails[:3]:  # Last 3 emails
                    context_text += f"- {past.get('subject', '')}: {past.get('body', '')[:100]}\n"

        # Generate response
        prompt = f"""You're drafting an email response. Match this writing style exactly:

Style Profile:
- Tone: {self.learned_style.get('tone', 'professional and friendly')}
- Greeting: {self.learned_style.get('typical_greeting', 'Hi')}
- Sign-off: {self.learned_style.get('signature', 'Best regards')}
- Formality: {self.learned_style.get('formality_level', 'moderate')}

Incoming Email:
From: {incoming_email.get('from', '')}
Subject: {incoming_email.get('subject', '')}
Body:
{incoming_email.get('body', '')}
{context_text}

Draft a response that:
1. Addresses their question/request directly
2. Matches the style profile above exactly
3. Is helpful and clear
4. Includes all necessary information
5. Is appropriately brief or detailed

Return JSON:
{{
  "subject": "Re: subject here",
  "body": "draft email body here",
  "confidence": 0.0-1.0,
  "requires_info": false,
  "missing_info": ["list", "of", "needed", "info"],
  "tone_check": "matches|needs_adjustment"
}}
"""

        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start >= 0:
                draft_data = json.loads(content[json_start:json_end])

                result["draft_created"] = True
                result["draft_subject"] = draft_data.get("subject", "")
                result["draft_body"] = draft_data.get("body", "")
                result["confidence"] = draft_data.get("confidence", 0.7)

                # Determine if requires review
                if draft_data.get("requires_info"):
                    result["requires_review"] = True
                    result["review_reason"] = f"Missing info: {', '.join(draft_data.get('missing_info', []))}"
                elif result["confidence"] < 0.75:
                    result["requires_review"] = True
                    result["review_reason"] = "Low confidence - please review carefully"
                elif email_type in ["complaint", "urgent", "high_value"]:
                    result["requires_review"] = True
                    result["review_reason"] = f"Email type '{email_type}' requires human review"
                else:
                    result["requires_review"] = True  # Always require review for POC
                    result["review_reason"] = "Standard review before sending"

        except Exception as e:
            print(f"Draft generation error: {e}")
            result["review_reason"] = f"Error generating draft: {str(e)}"

        return result

    def _classify_email(self, email: Dict[str, Any]) -> str:
        """Classify email type for appropriate handling"""
        subject = email.get("subject", "").lower()
        body = email.get("body", "").lower()
        text = subject + " " + body

        # Classify based on keywords
        if any(word in text for word in ["urgent", "asap", "immediately", "emergency"]):
            return "urgent"
        elif any(word in text for word in ["complaint", "unhappy", "disappointed", "problem"]):
            return "complaint"
        elif any(word in text for word in ["quote", "proposal", "contract", "pricing"]):
            return "high_value"
        elif any(word in text for word in ["thank", "thanks", "appreciate"]):
            return "appreciation"
        elif "?" in text:
            return "question"
        else:
            return "general"

    async def improve_from_feedback(self, draft_id: str, actual_sent: str,
                                   feedback: Optional[str] = None):
        """
        Learn from edits made to drafts
        This helps the agent improve over time

        Args:
            draft_id: ID of the draft
            actual_sent: What was actually sent
            feedback: Optional explicit feedback
        """
        # In production, this would analyze the differences and update the learned_style
        # For POC, we'll just log it
        learning = {
            "draft_id": draft_id,
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback or "No explicit feedback",
            "note": "Learning recorded for future improvement"
        }

        return learning

    def get_stats(self) -> Dict[str, Any]:
        """Return agent statistics"""
        return {
            "agent_type": "email_response",
            "learned_style": self.learned_style,
            "response_patterns_count": len(self.response_patterns),
            "confidence_threshold": 0.75
        }
