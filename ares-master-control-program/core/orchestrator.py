"""
ARES Orchestrator - Main Coordination and Execution Engine
Ties together task analysis, capability matching, prompt generation, and execution
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys

# Import ARES core modules
from .task_analyzer import TaskAnalyzer, TaskAnalysis, TaskComplexity
from .capability_matcher import CapabilityMatcher
from .prompt_generator import PromptGenerator, GeneratedPrompt
from .subagent_registry import SubagentRegistry
from .validation import ConfidenceLevel


@dataclass
class OrchestrationPlan:
    """Plan for executing a task"""
    task_description: str
    task_analysis: TaskAnalysis
    strategy: str  # 'single', 'parallel', 'sequential'
    primary_agent: str
    supporting_agents: List[str]
    prompts: Dict[str, GeneratedPrompt]
    confidence: float
    reasoning: str


@dataclass
class OrchestrationResult:
    """Result of orchestrated task execution"""
    success: bool
    plan: OrchestrationPlan
    outputs: Dict[str, str]  # agent_type -> output
    validation_results: Dict[str, any]
    final_confidence: ConfidenceLevel
    execution_log: List[str]


class AresOrchestrator:
    """
    Main orchestration engine for ARES

    Workflow:
    1. Analyze task (classify, detect complexity)
    2. Match capabilities (find best agents)
    3. Generate prompts (create detailed instructions)
    4. Execute (coordinate agents)
    5. Validate (apply ARES protocols)
    6. Return results
    """

    def __init__(
        self,
        registry_path: Optional[Path] = None,
        enable_validation: bool = True,
        auto_execute_threshold: float = 0.8,
        knowledge_base_path: Optional[Path] = None,
        enable_rag: bool = True
    ):
        """
        Initialize orchestrator

        Args:
            registry_path: Path to subagent registry
            enable_validation: Whether to apply ARES validation protocols
            auto_execute_threshold: Confidence threshold for autonomous execution (0-1)
            knowledge_base_path: Path to ARES knowledge base (for RAG)
            enable_rag: Whether to enable RAG retrieval (default: True)
        """
        self.task_analyzer = TaskAnalyzer()
        self.capability_matcher = CapabilityMatcher()
        self.prompt_generator = PromptGenerator(
            knowledge_base_path=knowledge_base_path,
            enable_rag=enable_rag
        )
        self.registry = SubagentRegistry(registry_path)
        self.enable_validation = enable_validation
        self.auto_execute_threshold = auto_execute_threshold
        self.enable_rag = enable_rag

        self.execution_log = []

    def plan(self, task_description: str) -> OrchestrationPlan:
        """
        Create orchestration plan for a task

        Args:
            task_description: Natural language task description

        Returns:
            OrchestrationPlan with execution strategy
        """
        self.execution_log = [f"Planning task: {task_description}"]

        # Step 1: Analyze task
        task_analysis = self.task_analyzer.analyze(task_description)
        self.execution_log.append(
            f"Task analysis: {task_analysis.complexity.value} complexity, "
            f"{task_analysis.primary_domain.value} domain, "
            f"confidence {task_analysis.confidence:.2f}"
        )

        # Step 2: Match capabilities
        multi_agent_strategy = self.capability_matcher.get_multi_agent_strategy(task_analysis)
        self.execution_log.append(
            f"Capability matching: {multi_agent_strategy['execution_strategy']} strategy"
        )

        # Step 3: Generate prompts
        prompts = {}

        # Primary agent prompt
        primary_agent = multi_agent_strategy['primary_agent']
        supporting_agents = multi_agent_strategy.get('supporting_agents', [])

        primary_prompt = self.prompt_generator.generate_prompt(
            agent_type=primary_agent,
            task_analysis=task_analysis,
            role="primary",
            other_agents=supporting_agents if supporting_agents else None,
            coordination_strategy=multi_agent_strategy['execution_strategy']
        )
        prompts[primary_agent] = primary_prompt

        # Supporting agent prompts
        for agent_type in supporting_agents:
            supporting_prompt = self.prompt_generator.generate_prompt(
                agent_type=agent_type,
                task_analysis=task_analysis,
                role="supporting",
                other_agents=[primary_agent] + [a for a in supporting_agents if a != agent_type],
                coordination_strategy=multi_agent_strategy['execution_strategy']
            )
            prompts[agent_type] = supporting_prompt

        self.execution_log.append(f"Generated {len(prompts)} agent prompts")

        # Step 4: Calculate overall confidence
        plan_confidence = self._calculate_plan_confidence(task_analysis, multi_agent_strategy)

        # Create plan
        plan = OrchestrationPlan(
            task_description=task_description,
            task_analysis=task_analysis,
            strategy=multi_agent_strategy['execution_strategy'],
            primary_agent=primary_agent,
            supporting_agents=supporting_agents,
            prompts=prompts,
            confidence=plan_confidence,
            reasoning=multi_agent_strategy['reasoning']
        )

        self.execution_log.append(f"Plan complete: {plan.confidence:.2f} confidence")

        return plan

    def should_execute_autonomously(self, plan: OrchestrationPlan) -> bool:
        """
        Determine if plan should execute autonomously

        Args:
            plan: OrchestrationPlan

        Returns:
            True if confidence meets threshold
        """
        return plan.confidence >= self.auto_execute_threshold

    def _calculate_plan_confidence(
        self,
        task_analysis: TaskAnalysis,
        multi_agent_strategy: Dict[str, any]
    ) -> float:
        """Calculate confidence in orchestration plan"""
        # Start with task analysis confidence
        confidence = task_analysis.confidence

        # Adjust based on strategy
        if multi_agent_strategy['use_multi_agent']:
            # Multi-agent adds coordination complexity
            if multi_agent_strategy['execution_strategy'] == 'sequential':
                confidence *= 0.95  # Slight reduction for coordination
            else:  # parallel
                confidence *= 0.90  # More reduction for parallel coordination
        else:
            # Single agent is simpler
            confidence *= 1.0  # No reduction

        # Adjust for complexity
        complexity_adjustments = {
            TaskComplexity.SIMPLE: 1.1,  # Boost simple tasks
            TaskComplexity.RESEARCH: 1.0,
            TaskComplexity.MODERATE: 1.0,
            TaskComplexity.COMPLEX: 0.9,  # Reduce complex tasks
        }
        confidence *= complexity_adjustments.get(task_analysis.complexity, 1.0)

        return max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

    def explain_plan(self, plan: OrchestrationPlan) -> str:
        """
        Generate human-readable explanation of plan

        Args:
            plan: OrchestrationPlan

        Returns:
            Formatted explanation string
        """
        lines = [
            "=" * 70,
            "ARES ORCHESTRATION PLAN",
            "=" * 70,
            "",
            f"Task: {plan.task_description}",
            "",
            "ANALYSIS:",
            f"  Complexity: {plan.task_analysis.complexity.value}",
            f"  Primary Domain: {plan.task_analysis.primary_domain.value}",
        ]

        if plan.task_analysis.secondary_domains:
            domains_str = ", ".join(d.value for d in plan.task_analysis.secondary_domains)
            lines.append(f"  Secondary Domains: {domains_str}")

        lines.extend([
            f"  Estimated Subtasks: {plan.task_analysis.estimated_subtasks}",
            f"  Decomposition Needed: {'Yes' if plan.task_analysis.requires_decomposition else 'No'}",
            "",
            "STRATEGY:",
            f"  Execution: {plan.strategy}",
            f"  Primary Agent: {plan.primary_agent}",
        ])

        if plan.supporting_agents:
            agents_str = ", ".join(plan.supporting_agents)
            lines.append(f"  Supporting Agents: {agents_str}")

        lines.extend([
            "",
            "CONFIDENCE:",
            f"  Overall: {plan.confidence:.1%}",
            f"  Autonomous Execution: {'Yes (≥80%)' if self.should_execute_autonomously(plan) else 'No - Requires Review'}",
            "",
            "REASONING:",
            f"  {plan.reasoning}",
            "",
            "=" * 70
        ])

        return "\n".join(lines)

    def format_prompt_for_task_tool(self, prompt: GeneratedPrompt) -> Tuple[str, str]:
        """
        Format a GeneratedPrompt for Claude Code Task tool

        Args:
            prompt: GeneratedPrompt object

        Returns:
            Tuple of (description, full_prompt) suitable for Task tool
        """
        # Description: 3-5 words
        description = f"Execute {prompt.agent_type} task"

        # Full prompt includes all sections
        full_prompt = prompt.prompt

        return (description, full_prompt)

    def get_execution_instructions(self, plan: OrchestrationPlan) -> str:
        """
        Get instructions for executing the plan

        Args:
            plan: OrchestrationPlan

        Returns:
            Formatted execution instructions for Claude Code
        """
        lines = [
            "EXECUTION INSTRUCTIONS",
            "=" * 70,
            "",
            f"Strategy: {plan.strategy}",
            f"Agents: {len(plan.prompts)}",
            "",
        ]

        if plan.strategy == "single":
            # Single agent execution
            desc, full_prompt = self.format_prompt_for_task_tool(
                plan.prompts[plan.primary_agent]
            )
            lines.extend([
                "Execute this using Task tool:",
                "",
                f"Agent Type: {plan.primary_agent}",
                f"Description: {desc}",
                "",
                "Prompt:",
                "```",
                full_prompt,
                "```",
            ])

        elif plan.strategy == "sequential":
            # Sequential execution
            lines.append("Execute agents in this order:")
            for i, agent_type in enumerate([plan.primary_agent] + plan.supporting_agents, 1):
                if agent_type in plan.prompts:
                    desc, full_prompt = self.format_prompt_for_task_tool(plan.prompts[agent_type])
                    lines.extend([
                        "",
                        f"{i}. {agent_type}",
                        f"   Description: {desc}",
                        f"   Prompt: (see below)",
                    ])

            lines.append("")
            lines.append("Full prompts:")
            for agent_type in [plan.primary_agent] + plan.supporting_agents:
                if agent_type in plan.prompts:
                    _, full_prompt = self.format_prompt_for_task_tool(plan.prompts[agent_type])
                    lines.extend([
                        "",
                        f"--- {agent_type} ---",
                        "```",
                        full_prompt,
                        "```",
                    ])

        elif plan.strategy == "parallel":
            # Parallel execution
            lines.append("Execute these agents in parallel (single message with multiple Task calls):")
            for agent_type in [plan.primary_agent] + plan.supporting_agents:
                if agent_type in plan.prompts:
                    desc, _ = self.format_prompt_for_task_tool(plan.prompts[agent_type])
                    lines.append(f"  - {agent_type}: {desc}")

            lines.append("")
            lines.append("Full prompts:")
            for agent_type in [plan.primary_agent] + plan.supporting_agents:
                if agent_type in plan.prompts:
                    _, full_prompt = self.format_prompt_for_task_tool(plan.prompts[agent_type])
                    lines.extend([
                        "",
                        f"--- {agent_type} ---",
                        "```",
                        full_prompt,
                        "```",
                    ])

        lines.extend([
            "",
            "=" * 70
        ])

        return "\n".join(lines)


# Convenience function
def create_orchestrator(
    registry_path: Optional[Path] = None,
    enable_validation: bool = True,
    knowledge_base_path: Optional[Path] = None,
    enable_rag: bool = True
) -> AresOrchestrator:
    """
    Create an ARES orchestrator instance

    Args:
        registry_path: Path to subagent registry
        enable_validation: Whether to apply ARES validation protocols
        knowledge_base_path: Path to ARES knowledge base
        enable_rag: Whether to enable RAG retrieval (2025 enhancement)

    Returns:
        AresOrchestrator instance
    """
    return AresOrchestrator(
        registry_path=registry_path,
        enable_validation=enable_validation,
        knowledge_base_path=knowledge_base_path,
        enable_rag=enable_rag
    )


# CLI entry point
def main():
    """CLI interface for testing orchestration"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py '<task description>'")
        sys.exit(1)

    task_description = " ".join(sys.argv[1:])

    orchestrator = create_orchestrator()
    plan = orchestrator.plan(task_description)

    print(orchestrator.explain_plan(plan))
    print()
    print(orchestrator.get_execution_instructions(plan))


if __name__ == "__main__":
    main()
