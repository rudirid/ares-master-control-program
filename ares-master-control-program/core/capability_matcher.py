"""
ARES Capability Matcher - Maps Tasks to Agent Capabilities
Intelligently routes tasks to appropriate agents based on capability matching
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from .task_analyzer import TaskAnalysis, TaskDomain, TaskComplexity


@dataclass
class AgentCapability:
    """Definition of an agent's capabilities"""
    agent_type: str
    domains: List[TaskDomain]
    complexity_range: Tuple[TaskComplexity, TaskComplexity]  # (min, max)
    description: str
    confidence_threshold: float = 0.5  # Minimum confidence to route here
    priority: int = 5  # 1=highest priority, 10=lowest


class CapabilityMatcher:
    """
    Matches task requirements to agent capabilities
    Supports both Claude Code built-in agents and custom Ares agents
    """

    # Claude Code built-in agents (from Task tool documentation)
    CLAUDE_CODE_AGENTS = {
        "general-purpose": AgentCapability(
            agent_type="general-purpose",
            domains=[TaskDomain.GENERAL],
            complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.COMPLEX),
            description="General-purpose agent for complex multi-step tasks, research, and code search",
            priority=7,  # Lower priority (use specialized when possible)
        ),
        "frontend-architect": AgentCapability(
            agent_type="frontend-architect",
            domains=[TaskDomain.FRONTEND],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Frontend development: React, Vue, Angular, Next.js, component architecture, state management",
            priority=1,
        ),
        "backend-architect": AgentCapability(
            agent_type="backend-architect",
            domains=[TaskDomain.BACKEND],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Backend development: API design (REST, GraphQL, tRPC), database architecture, authentication",
            priority=1,
        ),
        "fullstack-architect": AgentCapability(
            agent_type="fullstack-architect",
            domains=[TaskDomain.ARCHITECTURE, TaskDomain.FRONTEND, TaskDomain.BACKEND],
            complexity_range=(TaskComplexity.COMPLEX, TaskComplexity.COMPLEX),
            description="High-level system architecture design, technical decisions, full-stack application planning",
            priority=2,
        ),
        "database-expert": AgentCapability(
            agent_type="database-expert",
            domains=[TaskDomain.DATABASE],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Database design, schema modeling, query optimization, migrations, PostgreSQL, MongoDB, Redis, Prisma",
            priority=1,
        ),
        "devops-expert": AgentCapability(
            agent_type="devops-expert",
            domains=[TaskDomain.DEVOPS],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="DevOps: Docker, CI/CD pipelines, Kubernetes, deployment strategies, infrastructure as code",
            priority=1,
        ),
        "test-engineer": AgentCapability(
            agent_type="test-engineer",
            domains=[TaskDomain.TESTING],
            complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.COMPLEX),
            description="Test strategies, unit tests, integration tests, E2E tests, testing best practices",
            priority=1,
        ),
        "code-reviewer": AgentCapability(
            agent_type="code-reviewer",
            domains=[TaskDomain.CODE_REVIEW],
            complexity_range=(TaskComplexity.SIMPLE, TaskComplexity.COMPLEX),
            description="Code review for quality, security, performance, and best practices",
            priority=2,
        ),
        "llm-integration-expert": AgentCapability(
            agent_type="llm-integration-expert",
            domains=[TaskDomain.LLM_INTEGRATION],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Integrating LLMs (OpenAI, Claude, open-source), prompt engineering, function calling, embeddings",
            priority=1,
        ),
        "rag-builder": AgentCapability(
            agent_type="rag-builder",
            domains=[TaskDomain.RAG_SYSTEM],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Building RAG systems: document processing, chunking, embeddings, vector databases, semantic search",
            priority=1,
        ),
        "mcp-server-builder": AgentCapability(
            agent_type="mcp-server-builder",
            domains=[TaskDomain.MCP_SERVER],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Building MCP servers and tools for LLM applications",
            priority=1,
        ),
        "marketing-expert": AgentCapability(
            agent_type="marketing-expert",
            domains=[TaskDomain.MARKETING],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Marketing strategy, copywriting, SEO, growth tactics",
            priority=3,
        ),
        "web-scraper-expert": AgentCapability(
            agent_type="web-scraper-expert",
            domains=[TaskDomain.WEB_SCRAPING],
            complexity_range=(TaskComplexity.MODERATE, TaskComplexity.COMPLEX),
            description="Web scraping, crawling, data extraction from websites",
            priority=2,
        ),
        "Explore": AgentCapability(
            agent_type="Explore",
            domains=[TaskDomain.GENERAL],
            complexity_range=(TaskComplexity.RESEARCH, TaskComplexity.RESEARCH),
            description="Fast exploration of codebases, file pattern searches, keyword searches",
            priority=3,
            confidence_threshold=0.3,
        ),
    }

    def __init__(self, custom_agents: Optional[Dict[str, AgentCapability]] = None):
        """
        Initialize capability matcher

        Args:
            custom_agents: Optional dict of custom agent capabilities to register
        """
        self.agents = self.CLAUDE_CODE_AGENTS.copy()

        if custom_agents:
            self.agents.update(custom_agents)

    def match(self, task_analysis: TaskAnalysis) -> List[Tuple[str, float]]:
        """
        Match task to appropriate agents

        Args:
            task_analysis: Result from TaskAnalyzer

        Returns:
            List of (agent_type, match_score) tuples sorted by score descending
        """
        matches = []

        for agent_type, capability in self.agents.items():
            score = self._calculate_match_score(task_analysis, capability)

            if score >= capability.confidence_threshold:
                matches.append((agent_type, score))

        # Sort by score descending, then by priority ascending
        matches.sort(key=lambda x: (-x[1], self.agents[x[0]].priority))

        return matches

    def get_best_agent(self, task_analysis: TaskAnalysis) -> Optional[Tuple[str, float]]:
        """
        Get single best agent for task

        Args:
            task_analysis: Result from TaskAnalyzer

        Returns:
            (agent_type, match_score) or None if no match
        """
        matches = self.match(task_analysis)
        return matches[0] if matches else None

    def get_multi_agent_strategy(self, task_analysis: TaskAnalysis) -> Dict[str, any]:
        """
        Determine if task should be split across multiple agents

        Args:
            task_analysis: Result from TaskAnalyzer

        Returns:
            Dict with strategy information:
            {
                'use_multi_agent': bool,
                'primary_agent': str,
                'supporting_agents': List[str],
                'execution_strategy': 'parallel' | 'sequential',
                'reasoning': str
            }
        """
        matches = self.match(task_analysis)

        if not matches:
            return {
                'use_multi_agent': False,
                'primary_agent': 'general-purpose',
                'supporting_agents': [],
                'execution_strategy': 'single',
                'reasoning': 'No specific domain match, using general-purpose agent'
            }

        primary_agent = matches[0][0]
        primary_score = matches[0][1]

        # Check if multiple domains need multiple agents
        use_multi_agent = (
            task_analysis.requires_decomposition and
            len(task_analysis.secondary_domains) >= 1 and
            len(matches) >= 2
        )

        if use_multi_agent:
            # Get agents for secondary domains
            supporting_agents = [
                agent for agent, score in matches[1:3]  # Top 2 supporting agents
                if score >= 0.5  # Only if good match
            ]

            # Determine execution strategy
            if task_analysis.complexity == TaskComplexity.COMPLEX:
                execution_strategy = 'sequential'  # Complex tasks need coordination
                reasoning = (
                    f"Complex multi-domain task: {primary_agent} leads, "
                    f"coordinates with {', '.join(supporting_agents)}"
                )
            else:
                execution_strategy = 'parallel'  # Can run in parallel
                reasoning = (
                    f"Multi-domain task: {primary_agent} handles primary domain, "
                    f"{', '.join(supporting_agents)} handle secondary aspects in parallel"
                )

            return {
                'use_multi_agent': True,
                'primary_agent': primary_agent,
                'supporting_agents': supporting_agents,
                'execution_strategy': execution_strategy,
                'reasoning': reasoning
            }
        else:
            return {
                'use_multi_agent': False,
                'primary_agent': primary_agent,
                'supporting_agents': [],
                'execution_strategy': 'single',
                'reasoning': f"Single-domain task, {primary_agent} can handle independently (match score: {primary_score:.2f})"
            }

    def _calculate_match_score(self, task_analysis: TaskAnalysis, capability: AgentCapability) -> float:
        """Calculate how well an agent matches task requirements"""
        score = 0.0

        # Domain matching (primary = 1.0, secondary = 0.5)
        if task_analysis.primary_domain in capability.domains:
            score += 1.0
        else:
            # Check secondary domains
            secondary_matches = sum(
                1 for domain in task_analysis.secondary_domains
                if domain in capability.domains
            )
            if secondary_matches > 0:
                score += 0.5 * (secondary_matches / max(1, len(task_analysis.secondary_domains)))

        # Complexity matching
        complexity_match = self._check_complexity_match(
            task_analysis.complexity,
            capability.complexity_range
        )
        score += 0.3 * complexity_match

        # Boost for specialized agents when domain is clear
        if task_analysis.confidence >= 0.7 and score >= 0.8:
            if capability.agent_type != "general-purpose":
                score += 0.2  # Prefer specialized

        return min(1.0, score)  # Cap at 1.0

    def _check_complexity_match(
        self,
        task_complexity: TaskComplexity,
        capability_range: Tuple[TaskComplexity, TaskComplexity]
    ) -> float:
        """Check if task complexity is in agent's capability range"""
        complexity_order = [
            TaskComplexity.SIMPLE,
            TaskComplexity.RESEARCH,
            TaskComplexity.MODERATE,
            TaskComplexity.COMPLEX
        ]

        task_idx = complexity_order.index(task_complexity)
        min_idx = complexity_order.index(capability_range[0])
        max_idx = complexity_order.index(capability_range[1])

        if min_idx <= task_idx <= max_idx:
            return 1.0  # Perfect match
        elif abs(task_idx - min_idx) == 1 or abs(task_idx - max_idx) == 1:
            return 0.5  # Close match
        else:
            return 0.0  # No match

    def register_custom_agent(self, agent_type: str, capability: AgentCapability):
        """Register a custom agent capability"""
        self.agents[agent_type] = capability

    def list_available_agents(self) -> List[Dict[str, any]]:
        """List all available agents with their capabilities"""
        return [
            {
                'agent_type': agent_type,
                'domains': [d.value for d in cap.domains],
                'complexity_range': [c.value for c in cap.complexity_range],
                'description': cap.description,
                'priority': cap.priority
            }
            for agent_type, cap in sorted(
                self.agents.items(),
                key=lambda x: x[1].priority
            )
        ]
