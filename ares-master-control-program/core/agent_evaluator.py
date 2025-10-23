"""
ARES Agent Lifecycle System - Agent Evaluator
Determines whether a new agent should be created for a given task

Uses ARES v3.0 internal validation to make evidence-based decisions
"""

import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class EvaluationResult:
    """Result of agent evaluation"""
    decision: str  # CREATE, ENHANCE, USE_EXISTING, DIRECT
    confidence: float  # 0-100
    reasoning: List[str]  # Step-by-step reasoning
    existing_agent: Optional[str] = None
    estimated_roi: float = 0.0
    task_frequency_per_month: float = 0.0
    capability_gap: float = 0.0  # 0-100%

    def to_dict(self) -> Dict:
        return {
            'decision': self.decision,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'existing_agent': self.existing_agent,
            'estimated_roi': self.estimated_roi,
            'task_frequency_per_month': self.task_frequency_per_month,
            'capability_gap': self.capability_gap
        }


class AgentEvaluator:
    """
    Evaluates whether a new agent should be created

    Process:
    1. Analyze task (domain, complexity, frequency)
    2. Check existing agents for capability overlap
    3. Calculate ROI (time saved vs. creation cost)
    4. Make ARES-validated decision (≥80% confidence)
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize evaluator

        Args:
            config_path: Path to agent_lifecycle.yaml
        """
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "agent_lifecycle.yaml"
        self.agents_dir = self.project_root / "agents"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration"""
        if not self.config_path.exists():
            return self._default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load config: {e}")
            return self._default_config()

    def _default_config(self) -> Dict:
        """Default configuration"""
        return {
            'agent_creation': {
                'evidence_threshold': 3,
                'min_frequency_per_month': 5,
                'min_roi': 2.0,
                'confidence_threshold': 80
            }
        }

    def evaluate(self, task_description: str, context: Optional[Dict] = None) -> EvaluationResult:
        """
        Evaluate if a new agent should be created

        Args:
            task_description: Description of the task
            context: Optional context (project, domain hints, etc.)

        Returns:
            EvaluationResult with decision and reasoning
        """
        context = context or {}
        reasoning = []

        # Step 1: Analyze task
        task_analysis = self._analyze_task(task_description, context)
        reasoning.append(f"Task Domain: {task_analysis['domain']}")
        reasoning.append(f"Task Complexity: {task_analysis['complexity']}")

        # Step 2: Estimate frequency
        frequency = self._estimate_frequency(task_description, task_analysis)
        reasoning.append(f"Estimated Frequency: {frequency:.1f}/month")

        # Step 3: Check existing agents
        existing_match = self._check_existing_agents(task_analysis)
        if existing_match:
            reasoning.append(f"Found existing agent: {existing_match['agent_id']} (match: {existing_match['match_score']:.0f}%)")
        else:
            reasoning.append("No existing agent found for this domain")

        # Step 4: Calculate capability gap
        capability_gap = self._calculate_capability_gap(task_analysis, existing_match)
        reasoning.append(f"Capability Gap: {capability_gap:.0f}%")

        # Step 5: Calculate ROI
        roi = self._calculate_roi(frequency, task_analysis, capability_gap)
        reasoning.append(f"Estimated ROI: {roi:.1f}x")

        # Step 6: Make decision (ARES validation)
        decision, confidence = self._make_decision(
            task_analysis,
            frequency,
            existing_match,
            capability_gap,
            roi,
            reasoning
        )

        return EvaluationResult(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            existing_agent=existing_match['agent_id'] if existing_match else None,
            estimated_roi=roi,
            task_frequency_per_month=frequency,
            capability_gap=capability_gap
        )

    def _analyze_task(self, task_description: str, context: Dict) -> Dict:
        """
        Analyze task to extract domain, complexity, keywords

        Args:
            task_description: Task description
            context: Additional context

        Returns:
            Dict with analysis results
        """
        task_lower = task_description.lower()

        # Domain detection keywords
        domain_keywords = {
            'sales': ['discovery call', 'sales', 'prospect', 'client', 'lead', 'pitch', 'close'],
            'consulting': ['consulting', 'consultation', 'advisory', 'strategy'],
            'proposal': ['proposal', 'quote', 'bid', 'rfp'],
            'follow-up': ['follow-up', 'follow up', 'check-in', 'nurture'],
            'technical': ['code', 'debug', 'implement', 'refactor', 'api', 'database'],
            'documentation': ['document', 'documentation', 'readme', 'guide'],
            'analysis': ['analyze', 'analysis', 'review', 'audit', 'assess'],
        }

        # Detect domains
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(kw in task_lower for kw in keywords):
                detected_domains.append(domain)

        if not detected_domains:
            detected_domains = ['general']

        # Complexity detection
        complexity = self._estimate_complexity(task_description, context)

        # Extract key phrases
        key_phrases = self._extract_key_phrases(task_description)

        return {
            'domain': detected_domains[0],  # Primary domain
            'all_domains': detected_domains,
            'complexity': complexity,
            'key_phrases': key_phrases,
            'task_type': self._classify_task_type(task_description)
        }

    def _estimate_complexity(self, task_description: str, context: Dict) -> str:
        """
        Estimate task complexity

        Returns: 'simple', 'moderate', or 'complex'
        """
        task_lower = task_description.lower()

        # Simple indicators
        simple_indicators = ['list', 'show', 'display', 'simple', 'basic', 'quick']
        # Complex indicators
        complex_indicators = ['integrate', 'system', 'architecture', 'multi-step', 'comprehensive', 'full']

        simple_score = sum(1 for ind in simple_indicators if ind in task_lower)
        complex_score = sum(1 for ind in complex_indicators if ind in task_lower)

        # Length-based heuristic
        if len(task_description) > 100:
            complex_score += 1

        if complex_score > simple_score:
            return 'complex'
        elif simple_score > 0:
            return 'simple'
        else:
            return 'moderate'

    def _extract_key_phrases(self, task_description: str) -> List[str]:
        """Extract key phrases for similarity matching"""
        # Simple extraction - split on common words
        words = re.findall(r'\b\w+\b', task_description.lower())
        # Filter stopwords
        stopwords = {'the', 'a', 'an', 'for', 'to', 'of', 'in', 'on', 'with', 'and', 'or'}
        return [w for w in words if w not in stopwords and len(w) > 3]

    def _classify_task_type(self, task_description: str) -> str:
        """Classify the type of task"""
        task_lower = task_description.lower()

        if 'discovery call' in task_lower or 'prepare' in task_lower and 'call' in task_lower:
            return 'discovery-call'
        elif 'proposal' in task_lower:
            return 'proposal'
        elif 'follow' in task_lower:
            return 'follow-up'
        elif 'analyze' in task_lower or 'analysis' in task_lower:
            return 'analysis'
        else:
            return 'general'

    def _estimate_frequency(self, task_description: str, task_analysis: Dict) -> float:
        """
        Estimate how often this task occurs per month

        Uses heuristics based on task type and historical data (if available)

        Returns: Estimated frequency per month
        """
        task_type = task_analysis['task_type']

        # Heuristics based on task type
        frequency_estimates = {
            'discovery-call': 4.0,  # ~1 per week for consulting business
            'proposal': 3.0,
            'follow-up': 8.0,  # More frequent
            'analysis': 2.0,
            'general': 1.0
        }

        estimated = frequency_estimates.get(task_type, 1.0)

        # TODO Phase 2: Check episodic memory for actual frequency
        # For now, use heuristics

        return estimated

    def _check_existing_agents(self, task_analysis: Dict) -> Optional[Dict]:
        """
        Check if existing agents can handle this task

        Args:
            task_analysis: Task analysis dict

        Returns:
            Dict with agent_id and match_score, or None if no match
        """
        if not self.agents_dir.exists():
            return None

        agent_dirs = [d for d in self.agents_dir.iterdir() if d.is_dir()]
        if not agent_dirs:
            return None

        best_match = None
        best_score = 0.0

        for agent_dir in agent_dirs:
            config_path = agent_dir / "agent-config.yaml"
            if not config_path.exists():
                continue

            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    agent_config = yaml.safe_load(f)

                # Calculate match score
                score = self._calculate_match_score(task_analysis, agent_config)

                if score > best_score:
                    best_score = score
                    best_match = {
                        'agent_id': agent_config.get('agent_id', agent_dir.name),
                        'match_score': score,
                        'domains': agent_config.get('domains', [])
                    }
            except Exception as e:
                continue

        # Return match if score is significant (>50%)
        if best_match and best_score > 50:
            return best_match

        return None

    def _calculate_match_score(self, task_analysis: Dict, agent_config: Dict) -> float:
        """
        Calculate how well an agent matches the task

        Returns: Match score 0-100
        """
        score = 0.0

        # Domain match (70% weight)
        agent_domains = agent_config.get('domains', [])
        if task_analysis['domain'] in agent_domains:
            score += 70.0
        elif any(d in agent_domains for d in task_analysis['all_domains']):
            score += 40.0

        # Complexity match (20% weight)
        agent_complexity = agent_config.get('complexity', [])
        if task_analysis['complexity'] in agent_complexity:
            score += 20.0

        # Status check (10% weight)
        if agent_config.get('status') == 'active':
            score += 10.0

        return score

    def _calculate_capability_gap(self, task_analysis: Dict, existing_match: Optional[Dict]) -> float:
        """
        Calculate the capability gap (0-100%)

        0% = existing agent fully capable
        100% = no agent can handle this

        Returns: Capability gap percentage
        """
        if not existing_match:
            return 100.0  # Full gap if no existing agent

        match_score = existing_match['match_score']

        # Gap is inverse of match
        gap = 100.0 - match_score

        return gap

    def _calculate_roi(
        self,
        frequency: float,
        task_analysis: Dict,
        capability_gap: float
    ) -> float:
        """
        Calculate estimated ROI for creating new agent

        ROI = (time_saved_per_month * value_per_hour) / creation_cost

        Returns: ROI multiplier (e.g., 3.0 = 3x return)
        """
        # Time estimates based on complexity
        time_per_task = {
            'simple': 5,      # 5 minutes
            'moderate': 15,   # 15 minutes
            'complex': 30     # 30 minutes
        }

        minutes_per_task = time_per_task.get(task_analysis['complexity'], 15)

        # Agent reduces time by capability gap percentage
        # If gap is 80%, agent saves 80% of time
        time_saved_per_task = minutes_per_task * (capability_gap / 100.0)

        # Monthly time saved
        time_saved_per_month = time_saved_per_task * frequency

        # Value of time (assume $100/hour for consulting work)
        value_per_hour = 100.0
        value_saved_per_month = (time_saved_per_month / 60.0) * value_per_hour

        # Creation cost (assume 4 hours to build + maintain agent)
        creation_cost_hours = 4.0
        creation_cost = creation_cost_hours * value_per_hour  # $400

        # ROI over 3 months (reasonable payback period)
        value_over_3_months = value_saved_per_month * 3
        roi = value_over_3_months / creation_cost

        return roi

    def _make_decision(
        self,
        task_analysis: Dict,
        frequency: float,
        existing_match: Optional[Dict],
        capability_gap: float,
        roi: float,
        reasoning: List[str]
    ) -> Tuple[str, float]:
        """
        Make final decision using ARES validation

        Returns: (decision, confidence)
        """
        config = self.config.get('agent_creation', {})

        min_frequency = config.get('min_frequency_per_month', 5)
        min_roi = config.get('min_roi', 2.0)
        confidence_threshold = config.get('confidence_threshold', 80)

        # Decision logic with confidence scoring
        confidence = 0.0
        decision = "DIRECT"

        # Check 1: Frequency threshold
        if frequency < min_frequency:
            decision = "DIRECT"
            confidence = 90.0
            reasoning.append(f"Decision: DIRECT (frequency {frequency:.1f} < threshold {min_frequency})")
            return decision, confidence

        confidence += 20.0  # Passes frequency check

        # Check 2: ROI threshold
        if roi < min_roi:
            decision = "DIRECT"
            confidence = 85.0
            reasoning.append(f"Decision: DIRECT (ROI {roi:.1f}x < threshold {min_roi}x)")
            return decision, confidence

        confidence += 30.0  # Passes ROI check

        # Check 3: Existing agent capability
        if existing_match and capability_gap < 30.0:
            decision = "USE_EXISTING"
            confidence = 90.0
            reasoning.append(f"Decision: USE_EXISTING (gap {capability_gap:.0f}% < 30%)")
            return decision, confidence

        if existing_match and capability_gap < 60.0:
            decision = "ENHANCE"
            confidence = 85.0
            reasoning.append(f"Decision: ENHANCE existing agent (gap {capability_gap:.0f}%)")
            return decision, confidence

        # Check 4: Create new agent
        decision = "CREATE"
        confidence += 30.0  # Base confidence for creation

        # Boost confidence based on strength of signals
        if roi > min_roi * 2:
            confidence += 10.0
            reasoning.append(f"Strong ROI signal: {roi:.1f}x (>{min_roi*2}x)")

        if frequency > min_frequency * 2:
            confidence += 10.0
            reasoning.append(f"High frequency signal: {frequency:.1f}/month (>{min_frequency*2})")

        reasoning.append(f"Decision: CREATE (confidence {confidence:.0f}%)")

        return decision, min(confidence, 95.0)  # Cap at 95% (never 100% certain)


def evaluate_task(task_description: str, context: Optional[Dict] = None) -> EvaluationResult:
    """
    Convenience function to evaluate a task

    Args:
        task_description: Task description
        context: Optional context dict

    Returns:
        EvaluationResult
    """
    evaluator = AgentEvaluator()
    return evaluator.evaluate(task_description, context)
