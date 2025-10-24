"""
ARES Prompt Generator - Dynamic Agent Prompt Creation
Generates detailed, context-rich prompts for agents based on task analysis
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from .task_analyzer import TaskAnalysis
from .knowledge_base_rag import KnowledgeBaseRAG, create_rag


@dataclass
class GeneratedPrompt:
    """Generated prompt for an agent"""
    agent_type: str
    prompt: str
    context: Dict[str, any]
    validation_criteria: List[str]
    expected_outputs: List[str]


class PromptGenerator:
    """
    Generates prompts for agents incorporating:
    - Task context and requirements
    - Ares validation protocols
    - Expected outputs and quality criteria
    - Relevant patterns from knowledge base (via RAG)

    2025 Enhancement: Integrated Knowledge Base RAG for context engineering
    """

    def __init__(self, knowledge_base_path: Optional[Path] = None, enable_rag: bool = True):
        """
        Initialize prompt generator

        Args:
            knowledge_base_path: Path to ARES knowledge base
            enable_rag: Whether to enable RAG retrieval (default: True)
        """
        self.enable_rag = enable_rag
        self.rag: Optional[KnowledgeBaseRAG] = None

        if enable_rag:
            try:
                self.rag = create_rag(knowledge_base_path)
            except Exception as e:
                print(f"Warning: Could not initialize RAG system: {e}")
                self.enable_rag = False

    # Template components
    PROMPT_HEADER = """You are a specialized agent working as part of the ARES Master Control Program orchestration system.

**Agent Type**: {agent_type}
**Task**: {task_description}
**Complexity**: {complexity}
**Timestamp**: {timestamp}

"""

    ARES_PROTOCOLS = """
## ARES PROTOCOLS (Apply These)

### 1. Internal Validation Protocol
Before delivering output:
1. **Challenge**: Question your assumptions
2. **Simplify**: Can this be done simpler?
3. **Validate**: Verify all claims against actual evidence
4. **Explain**: Show your reasoning transparently
5. **Confidence**: Rate confidence (HIGH ≥80%, MEDIUM 50-79%, LOW <50%)

### 2. Truth Protocol
- **NEVER** make technical claims without verification
- **ALWAYS** check logs/docs/code before stating facts
- **CLEARLY** label assumptions as assumptions
- **VERIFY** file paths, function names, API endpoints exist before referencing

### 3. Anti-Patterns to Avoid
- ❌ Unfounded technical claims (CRITICAL severity)
- ❌ Assuming code structure without reading files
- ❌ Stating capabilities without evidence
- ❌ Hallucinating file paths or function names

"""

    TASK_CONTEXT_TEMPLATE = """
## TASK CONTEXT

**Primary Domain**: {primary_domain}
{secondary_domains_section}
**Estimated Subtasks**: {estimated_subtasks}
**Requires Decomposition**: {requires_decomposition}

**Task Analysis Reasoning**:
{reasoning}

"""

    VALIDATION_CRITERIA_TEMPLATE = """
## VALIDATION CRITERIA

Your output will be validated against these criteria:

{criteria_list}

**Quality Threshold**: Must meet ≥80% confidence for autonomous execution

"""

    EXPECTED_OUTPUT_TEMPLATE = """
## EXPECTED OUTPUT

Please provide:

{output_list}

**Output Format**:
- Use markdown for clarity
- Include code examples where relevant
- Show your validation process
- State confidence level at the end

"""

    MULTI_AGENT_COORDINATION = """
## MULTI-AGENT COORDINATION

You are part of a multi-agent team:
- **Your Role**: {role}
- **Other Agents**: {other_agents}
- **Coordination**: {coordination_strategy}

**Important**: Focus on your domain expertise. The orchestrator will coordinate outputs.

"""

    def generate_prompt(
        self,
        agent_type: str,
        task_analysis: TaskAnalysis,
        role: str = "primary",
        other_agents: Optional[List[str]] = None,
        coordination_strategy: str = "sequential",
        patterns_hint: Optional[List[str]] = None
    ) -> GeneratedPrompt:
        """
        Generate a complete prompt for an agent

        Args:
            agent_type: Type of agent to generate prompt for
            task_analysis: Analysis of the task
            role: Agent's role (primary, supporting)
            other_agents: Other agents in multi-agent setup
            coordination_strategy: How agents coordinate (sequential, parallel)
            patterns_hint: Relevant patterns from knowledge base

        Returns:
            GeneratedPrompt with full prompt and metadata
        """
        # Build prompt sections
        header = self._build_header(agent_type, task_analysis)
        protocols = self.ARES_PROTOCOLS
        context = self._build_context(task_analysis, patterns_hint)
        validation_criteria = self._build_validation_criteria(task_analysis)
        expected_output = self._build_expected_output(task_analysis, agent_type)

        # Add multi-agent coordination if needed
        coordination = ""
        if other_agents:
            coordination = self._build_coordination_section(
                role, other_agents, coordination_strategy
            )

        # Combine all sections
        full_prompt = (
            header +
            protocols +
            context +
            (coordination if coordination else "") +
            validation_criteria +
            expected_output
        )

        # Extract validation criteria and expected outputs for metadata
        criteria_list = self._extract_validation_criteria(task_analysis)
        output_list = self._extract_expected_outputs(task_analysis, agent_type)

        return GeneratedPrompt(
            agent_type=agent_type,
            prompt=full_prompt,
            context={
                'task_description': task_analysis.task_description,
                'complexity': task_analysis.complexity.value,
                'primary_domain': task_analysis.primary_domain.value,
                'role': role,
                'other_agents': other_agents or [],
            },
            validation_criteria=criteria_list,
            expected_outputs=output_list
        )

    def _build_header(self, agent_type: str, task_analysis: TaskAnalysis) -> str:
        """Build prompt header"""
        return self.PROMPT_HEADER.format(
            agent_type=agent_type,
            task_description=task_analysis.task_description,
            complexity=task_analysis.complexity.value,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

    def _build_context(self, task_analysis: TaskAnalysis, patterns_hint: Optional[List[str]]) -> str:
        """
        Build task context section with RAG-enhanced knowledge retrieval

        2025 Enhancement: Automatically retrieves relevant patterns from knowledge base
        """
        # Secondary domains section
        if task_analysis.secondary_domains:
            domains_list = "\n".join(
                f"  - {domain.value}" for domain in task_analysis.secondary_domains
            )
            secondary_section = f"**Secondary Domains**:\n{domains_list}\n"
        else:
            secondary_section = ""

        context = self.TASK_CONTEXT_TEMPLATE.format(
            primary_domain=task_analysis.primary_domain.value,
            secondary_domains_section=secondary_section,
            estimated_subtasks=task_analysis.estimated_subtasks,
            requires_decomposition="Yes" if task_analysis.requires_decomposition else "No",
            reasoning=task_analysis.reasoning
        )

        # NEW: RAG-based pattern retrieval (2025 best practice)
        if self.enable_rag and self.rag:
            try:
                rag_context = self.rag.get_comprehensive_context(
                    domain=task_analysis.primary_domain.value,
                    query=task_analysis.task_description,
                    include_patterns=2,  # Top 2 patterns
                    include_tech=1,  # 1 tech recommendation
                    include_decisions=1,  # 1 past decision
                    include_anti_patterns=1  # 1 anti-pattern to avoid
                )
                if rag_context:
                    context += "\n" + rag_context + "\n"
            except Exception as e:
                print(f"Warning: RAG retrieval failed: {e}")

        # Add manual patterns hint if provided (backwards compatibility)
        if patterns_hint:
            patterns_section = "\n## ADDITIONAL PATTERNS\n\n"
            patterns_section += "\n".join(f"- {pattern}" for pattern in patterns_hint)
            patterns_section += "\n\nConsider these patterns when designing your solution.\n"
            context += patterns_section

        return context

    def _build_coordination_section(
        self,
        role: str,
        other_agents: List[str],
        coordination_strategy: str
    ) -> str:
        """Build multi-agent coordination section"""
        other_agents_list = ", ".join(other_agents)

        return self.MULTI_AGENT_COORDINATION.format(
            role=role,
            other_agents=other_agents_list,
            coordination_strategy=coordination_strategy
        )

    def _build_validation_criteria(self, task_analysis: TaskAnalysis) -> str:
        """Build validation criteria section"""
        criteria = self._extract_validation_criteria(task_analysis)
        criteria_list = "\n".join(f"{i+1}. {criterion}" for i, criterion in enumerate(criteria))

        return self.VALIDATION_CRITERIA_TEMPLATE.format(criteria_list=criteria_list)

    def _extract_validation_criteria(self, task_analysis: TaskAnalysis) -> List[str]:
        """Extract validation criteria based on task"""
        criteria = [
            "Solution addresses the primary task requirement",
            "All technical claims verified against actual code/docs/files",
            "No assumed file paths, function names, or APIs without verification",
            "Implementation follows proven patterns where applicable",
        ]

        # Add complexity-specific criteria
        if task_analysis.complexity.value == "complex":
            criteria.append("Architecture is scalable and maintainable")
            criteria.append("All components properly integrated")

        if task_analysis.requires_decomposition:
            criteria.append("Subtasks properly identified and sequenced")

        # Add domain-specific criteria
        domain_criteria = {
            "frontend": "UI components follow accessibility best practices",
            "backend": "API endpoints properly secured and validated",
            "database": "Schema normalized and optimized for queries",
            "devops": "Deployment pipeline includes proper error handling",
            "testing": "Test coverage ≥80% for critical paths",
        }

        domain_value = task_analysis.primary_domain.value
        if domain_value in domain_criteria:
            criteria.append(domain_criteria[domain_value])

        return criteria

    def _build_expected_output(self, task_analysis: TaskAnalysis, agent_type: str) -> str:
        """Build expected output section"""
        outputs = self._extract_expected_outputs(task_analysis, agent_type)
        output_list = "\n".join(f"{i+1}. {output}" for i, output in enumerate(outputs))

        return self.EXPECTED_OUTPUT_TEMPLATE.format(output_list=output_list)

    def _extract_expected_outputs(self, task_analysis: TaskAnalysis, agent_type: str) -> List[str]:
        """Extract expected outputs based on task and agent type"""
        outputs = [
            "Clear explanation of approach and reasoning",
            "Implementation details (code, configuration, commands)",
        ]

        # Add complexity-specific outputs
        if task_analysis.complexity.value in ["complex", "moderate"]:
            outputs.append("Architecture diagram or component breakdown")

        if task_analysis.requires_decomposition:
            outputs.append("Subtask breakdown with dependencies")

        # Add agent-specific outputs
        agent_outputs = {
            "code-reviewer": "List of issues found with severity ratings",
            "test-engineer": "Test cases with coverage metrics",
            "database-expert": "Schema design with indexing strategy",
            "devops-expert": "Deployment steps with rollback plan",
            "frontend-architect": "Component hierarchy and state management plan",
            "backend-architect": "API endpoints with request/response schemas",
        }

        if agent_type in agent_outputs:
            outputs.append(agent_outputs[agent_type])

        # Always add confidence rating
        outputs.append("**Confidence rating** (HIGH/MEDIUM/LOW) with justification")

        return outputs

    def generate_validation_prompt(self, original_task: str, agent_output: str) -> str:
        """
        Generate a validation prompt for reviewing agent output

        Args:
            original_task: Original task description
            agent_output: Output from the agent

        Returns:
            Validation prompt string
        """
        return f"""You are the ARES validation layer reviewing agent output.

## ORIGINAL TASK
{original_task}

## AGENT OUTPUT
{agent_output}

## VALIDATION CHECKLIST

Review the output against ARES protocols:

1. **Truth Protocol Compliance**:
   - Are all technical claims verified?
   - Are assumptions clearly labeled?
   - Are file paths/functions/APIs real (not hallucinated)?

2. **Completeness**:
   - Does it fully address the original task?
   - Are all required components included?
   - Is the explanation clear?

3. **Quality**:
   - Does it follow best practices?
   - Is it maintainable and scalable?
   - Are there obvious issues or improvements?

4. **Confidence Assessment**:
   - Is the stated confidence level justified?
   - Should this be executed autonomously (≥80%) or require review?

## YOUR OUTPUT

Provide:
1. **Validation Result**: PASS / NEEDS_REVISION / FAIL
2. **Issues Found**: List any problems (or "None")
3. **Confidence in Agent Output**: HIGH / MEDIUM / LOW
4. **Recommendation**: Execute autonomously / Request user review / Revise and resubmit
5. **Reasoning**: Brief explanation of your assessment
"""
