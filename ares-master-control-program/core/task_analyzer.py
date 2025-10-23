"""
ARES Task Analyzer - Intelligent Task Classification
Analyzes tasks to determine required capabilities and routing strategy
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re


class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"  # Single-domain, straightforward
    MODERATE = "moderate"  # Multi-step, single domain
    COMPLEX = "complex"  # Multi-domain, requires coordination
    RESEARCH = "research"  # Primarily information gathering


class TaskDomain(Enum):
    """Primary task domains"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    DEVOPS = "devops"
    TESTING = "testing"
    CODE_REVIEW = "code_review"
    ARCHITECTURE = "architecture"
    MARKETING = "marketing"
    LLM_INTEGRATION = "llm_integration"
    RAG_SYSTEM = "rag_system"
    MCP_SERVER = "mcp_server"
    WEB_SCRAPING = "web_scraping"
    GENERAL = "general"


@dataclass
class TaskAnalysis:
    """Result of task analysis"""
    task_description: str
    complexity: TaskComplexity
    primary_domain: TaskDomain
    secondary_domains: List[TaskDomain]
    requires_decomposition: bool
    estimated_subtasks: int
    confidence: float  # 0.0-1.0
    reasoning: str


class TaskAnalyzer:
    """
    Analyzes tasks to determine classification and routing strategy
    Uses pattern matching and keyword analysis
    """

    # Domain detection patterns
    DOMAIN_PATTERNS = {
        TaskDomain.FRONTEND: [
            r'\b(react|vue|angular|next\.?js|component|ui|frontend|spa|ssr)\b',
            r'\b(css|html|tailwind|styled-components|responsive)\b',
            r'\b(state management|redux|zustand|routing)\b',
        ],
        TaskDomain.BACKEND: [
            r'\b(api|endpoint|rest|graphql|trpc|server|backend)\b',
            r'\b(express|fastapi|flask|django|node\.?js)\b',
            r'\b(authentication|auth|jwt|oauth|session)\b',
            r'\b(microservices|service|middleware)\b',
        ],
        TaskDomain.DATABASE: [
            r'\b(database|db|sql|nosql|query|schema)\b',
            r'\b(postgres|mysql|mongodb|redis|sqlite)\b',
            r'\b(prisma|drizzle|orm|migration|index)\b',
            r'\b(optimization|performance|indexing)\b',
        ],
        TaskDomain.DEVOPS: [
            r'\b(docker|kubernetes|k8s|container|deployment)\b',
            r'\b(ci/cd|pipeline|github actions|gitlab ci)\b',
            r'\b(infrastructure|terraform|ansible|cloud)\b',
            r'\b(aws|azure|gcp|nginx|load balancer)\b',
        ],
        TaskDomain.TESTING: [
            r'\b(test|testing|unit test|integration test|e2e)\b',
            r'\b(jest|pytest|vitest|cypress|playwright)\b',
            r'\b(coverage|tdd|bdd|test suite)\b',
        ],
        TaskDomain.CODE_REVIEW: [
            r'\b(review|code quality|refactor|optimize)\b',
            r'\b(security|vulnerability|best practice)\b',
            r'\b(performance|bug|issue|fix)\b',
        ],
        TaskDomain.ARCHITECTURE: [
            r'\b(architecture|design|system design|pattern)\b',
            r'\b(scalability|high-level|blueprint|planning)\b',
            r'\b(technical decision|trade-?off|approach)\b',
        ],
        TaskDomain.MARKETING: [
            r'\b(marketing|seo|copywriting|growth|strategy)\b',
            r'\b(landing page|conversion|analytics|campaign)\b',
        ],
        TaskDomain.LLM_INTEGRATION: [
            r'\b(llm|openai|anthropic|claude|gpt|ai integration)\b',
            r'\b(prompt|embedding|function calling|streaming)\b',
        ],
        TaskDomain.RAG_SYSTEM: [
            r'\b(rag|retrieval|vector|semantic search|embedding)\b',
            r'\b(knowledge base|document|chunking|pinecone|weaviate)\b',
        ],
        TaskDomain.MCP_SERVER: [
            r'\b(mcp|model context protocol|mcp server|mcp tool)\b',
        ],
        TaskDomain.WEB_SCRAPING: [
            r'\b(scrap|crawl|extract|web data|beautifulsoup|selenium)\b',
        ],
    }

    # Complexity indicators
    COMPLEXITY_INDICATORS = {
        TaskComplexity.SIMPLE: [
            r'\b(add|create|fix|update|change)\s+\w+\s+(to|in|for)\b',
            r'\b(single|one|simple|quick|small)\b',
        ],
        TaskComplexity.MODERATE: [
            r'\b(implement|build|develop|integrate)\b',
            r'\b(feature|functionality|system)\b',
            r'\b(multiple|several|various)\b',
        ],
        TaskComplexity.COMPLEX: [
            r'\b(architect|design|plan|orchestrate|coordinate)\b',
            r'\b(full[- ]?stack|end[- ]?to[- ]?end|complete system)\b',
            r'\b(across|between|integrate multiple)\b',
        ],
        TaskComplexity.RESEARCH: [
            r'\b(research|investigate|explore|analyze|understand)\b',
            r'\b(what|how|why|where|find|search|look)\b',
            r'\b(explain|document|learn|study)\b',
        ],
    }

    def analyze(self, task_description: str) -> TaskAnalysis:
        """
        Analyze a task description and classify it

        Args:
            task_description: Natural language task description

        Returns:
            TaskAnalysis with classification and routing info
        """
        task_lower = task_description.lower()

        # Detect domains
        domain_scores = self._score_domains(task_lower)
        primary_domain = max(domain_scores, key=domain_scores.get)

        # Secondary domains (score > 0.3)
        secondary_domains = [
            domain for domain, score in domain_scores.items()
            if score > 0.3 and domain != primary_domain
        ]

        # Detect complexity
        complexity = self._detect_complexity(task_lower, len(secondary_domains))

        # Determine if decomposition needed
        requires_decomposition = (
            complexity == TaskComplexity.COMPLEX or
            len(secondary_domains) >= 2 or
            self._has_multi_step_indicators(task_lower)
        )

        # Estimate subtasks
        estimated_subtasks = self._estimate_subtasks(
            complexity, len(secondary_domains), task_lower
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            domain_scores[primary_domain],
            complexity,
            task_description
        )

        # Generate reasoning
        reasoning = self._generate_reasoning(
            primary_domain, secondary_domains, complexity,
            requires_decomposition, estimated_subtasks
        )

        return TaskAnalysis(
            task_description=task_description,
            complexity=complexity,
            primary_domain=primary_domain,
            secondary_domains=secondary_domains,
            requires_decomposition=requires_decomposition,
            estimated_subtasks=estimated_subtasks,
            confidence=confidence,
            reasoning=reasoning
        )

    def _score_domains(self, task_text: str) -> Dict[TaskDomain, float]:
        """Score each domain based on pattern matches"""
        scores = {domain: 0.0 for domain in TaskDomain}

        for domain, patterns in self.DOMAIN_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, task_text, re.IGNORECASE):
                    matches += 1
            # Normalize by pattern count
            scores[domain] = matches / len(patterns) if patterns else 0.0

        # If no domain matches, default to GENERAL
        if max(scores.values()) == 0.0:
            scores[TaskDomain.GENERAL] = 1.0

        return scores

    def _detect_complexity(self, task_text: str, secondary_domain_count: int) -> TaskComplexity:
        """Detect task complexity"""
        complexity_scores = {comp: 0 for comp in TaskComplexity}

        for complexity, patterns in self.COMPLEXITY_INDICATORS.items():
            for pattern in patterns:
                if re.search(pattern, task_text, re.IGNORECASE):
                    complexity_scores[complexity] += 1

        # Check for multi-domain complexity
        if secondary_domain_count >= 2:
            complexity_scores[TaskComplexity.COMPLEX] += 2

        # Return highest scoring complexity, default to MODERATE
        if sum(complexity_scores.values()) == 0:
            return TaskComplexity.MODERATE

        return max(complexity_scores, key=complexity_scores.get)

    def _has_multi_step_indicators(self, task_text: str) -> bool:
        """Check if task has multi-step indicators"""
        multi_step_patterns = [
            r'\b(then|after|once|next|finally|first|second|third)\b',
            r'\b(and then|followed by|as well as)\b',
            r'\d+\.\s+',  # Numbered lists
        ]
        return any(re.search(p, task_text, re.IGNORECASE) for p in multi_step_patterns)

    def _estimate_subtasks(self, complexity: TaskComplexity, secondary_count: int, task_text: str) -> int:
        """Estimate number of subtasks"""
        base_subtasks = {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MODERATE: 3,
            TaskComplexity.COMPLEX: 5,
            TaskComplexity.RESEARCH: 2,
        }

        subtasks = base_subtasks[complexity]

        # Add subtasks for secondary domains
        subtasks += secondary_count

        # Check for explicit lists
        numbered_items = len(re.findall(r'\d+\.\s+', task_text))
        if numbered_items > 0:
            subtasks = max(subtasks, numbered_items)

        return max(1, subtasks)

    def _calculate_confidence(self, primary_score: float, complexity: TaskComplexity, task_text: str) -> float:
        """Calculate confidence in classification"""
        confidence = primary_score

        # Boost confidence for clear task descriptions
        if len(task_text.split()) >= 10:  # Detailed description
            confidence += 0.1

        # Reduce confidence for very short descriptions
        if len(task_text.split()) < 5:
            confidence -= 0.2

        # Adjust for complexity uncertainty
        if complexity == TaskComplexity.MODERATE:
            confidence -= 0.1  # Moderate is often ambiguous

        return max(0.0, min(1.0, confidence))

    def _generate_reasoning(
        self,
        primary_domain: TaskDomain,
        secondary_domains: List[TaskDomain],
        complexity: TaskComplexity,
        requires_decomposition: bool,
        estimated_subtasks: int
    ) -> str:
        """Generate human-readable reasoning"""
        parts = []

        # Domain analysis
        if secondary_domains:
            domains_str = ", ".join(d.value for d in secondary_domains)
            parts.append(
                f"Primary domain: {primary_domain.value} "
                f"with secondary domains: {domains_str}"
            )
        else:
            parts.append(f"Single-domain task: {primary_domain.value}")

        # Complexity
        parts.append(f"Complexity: {complexity.value}")

        # Decomposition
        if requires_decomposition:
            parts.append(
                f"Requires decomposition into ~{estimated_subtasks} subtasks "
                f"for parallel execution"
            )
        else:
            parts.append("Can be handled by single agent")

        return ". ".join(parts)


# Convenience function
def analyze_task(task_description: str) -> TaskAnalysis:
    """Analyze a task description"""
    analyzer = TaskAnalyzer()
    return analyzer.analyze(task_description)
