"""
ARES Agent Lifecycle System - Agent Executor
Executes agents with memory context and reflection

Responsibilities:
- Load agent prompt and configuration
- Inject memory context into prompt
- Execute agent task
- Capture output and intermediate steps
- Store execution to episodic memory
- Trigger immediate reflection
- Update performance metrics
"""

import json
import yaml
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

from core.memory_manager import MemoryManager, MemoryContext


@dataclass
class ExecutionResult:
    """Result of agent execution"""
    task_id: str
    success: bool
    output: str
    execution_time_seconds: float
    patterns_used: List[str]
    intermediate_steps: List[Dict[str, Any]]
    reflection: Optional[str] = None
    reflection_depth: str = 'shallow'
    correction_made: bool = False
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'task_id': self.task_id,
            'success': self.success,
            'output': self.output,
            'execution_time_seconds': self.execution_time_seconds,
            'patterns_used': self.patterns_used,
            'intermediate_steps': self.intermediate_steps,
            'reflection': self.reflection,
            'reflection_depth': self.reflection_depth,
            'correction_made': self.correction_made,
            'error_message': self.error_message
        }


class AgentExecutor:
    """
    Executes agents with full ARES protocols

    Execution Flow:
    1. Load agent prompt + config
    2. Load memory context (episodic + semantic + procedural)
    3. Inject memory into prompt
    4. Execute agent task
    5. Capture output + intermediate steps
    6. Store to episodic memory
    7. Trigger immediate reflection
    8. Update performance metrics
    """

    def __init__(
        self,
        agent_id: str,
        agents_dir: Optional[Path] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize agent executor

        Args:
            agent_id: Agent identifier
            agents_dir: Path to agents directory
            config_path: Path to agent_lifecycle.yaml
        """
        self.agent_id = agent_id
        self.project_root = Path(__file__).parent.parent
        self.agents_dir = agents_dir or self.project_root / "agents"
        self.agent_dir = self.agents_dir / agent_id

        # Config
        self.config_path = config_path or self.project_root / "config" / "agent_lifecycle.yaml"
        self.config = self._load_config()

        # Agent files
        self.agent_config_file = self.agent_dir / "agent-config.yaml"
        self.agent_prompt_file = self.agent_dir / "agent-prompt.md"
        self.performance_file = self.agent_dir / "performance" / "metrics.json"

        # Memory manager
        self.memory_manager = MemoryManager(agent_id, agents_dir)

    def _load_config(self) -> Dict:
        """Load system configuration"""
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
            'execution': {
                'timeout_seconds': 600,
                'load_episodic_memories': True,
                'episodic_memory_limit': 5,
                'load_semantic_knowledge': True,
                'semantic_retrieval_limit': 10,
                'load_procedural_skills': True,
                'immediate_reflection': True,
                'memory_context_max_tokens': 2000
            },
            'performance': {
                'track_intermediate_steps': True,
                'store_full_context': True,
                'capture_user_feedback': False
            }
        }

    def execute(
        self,
        task_description: str,
        context: Optional[Dict] = None
    ) -> ExecutionResult:
        """
        Execute agent on a task

        Args:
            task_description: Task to execute
            context: Optional additional context

        Returns:
            ExecutionResult with output and metadata
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = datetime.now()

        print(f"[EXECUTOR] Starting task {task_id}")
        print(f"[EXECUTOR] Agent: {self.agent_id}")
        print(f"[EXECUTOR] Task: {task_description}")
        print()

        try:
            # Step 1: Load agent configuration
            agent_config = self._load_agent_config()
            print(f"✓ Loaded agent config (v{agent_config['version']})")

            # Step 2: Load agent prompt
            agent_prompt = self._load_agent_prompt()
            print(f"✓ Loaded agent prompt ({len(agent_prompt)} chars)")

            # Step 3: Load memory context
            memory_context = self._load_memory_context(task_description)
            print(f"✓ Loaded memory context:")
            print(f"  - {len(memory_context.episodic_memories)} episodic memories")
            print(f"  - {len(memory_context.semantic_knowledge)} knowledge items")
            print(f"  - {len(memory_context.procedural_skills)} procedural skills")
            print()

            # Step 4: Inject memory into prompt
            full_prompt = self._inject_memory(agent_prompt, memory_context, task_description)
            print(f"✓ Generated execution prompt ({len(full_prompt)} chars)")
            print()

            # Step 5: Execute agent
            # Note: For Phase 2, we simulate execution
            # Phase 3 will add actual Task tool integration
            output, intermediate_steps, success = self._execute_agent(
                full_prompt,
                task_description,
                agent_config
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            print()
            print(f"✓ Execution complete ({execution_time:.1f}s)")
            print(f"  Success: {success}")
            print()

            # Step 6: Extract patterns used
            patterns_used = self._extract_patterns_used(agent_config, intermediate_steps)

            # Step 7: Generate reflection
            reflection, reflection_depth, correction_made = self._generate_reflection(
                task_description,
                output,
                success,
                intermediate_steps
            )

            print(f"✓ Generated reflection (depth: {reflection_depth})")
            if correction_made:
                print(f"  ⚠ Self-correction detected")
            print()

            # Step 8: Store to episodic memory
            self._store_execution(
                task_id=task_id,
                task_description=task_description,
                execution_time_seconds=execution_time,
                success=success,
                patterns_used=patterns_used,
                reflection_text=reflection,
                reflection_depth=reflection_depth,
                correction_made=correction_made,
                intermediate_steps=intermediate_steps
            )

            print(f"✓ Stored to episodic memory (task_id: {task_id})")
            print()

            # Step 9: Update performance metrics
            self._update_performance_metrics(
                success=success,
                execution_time_seconds=execution_time,
                reflection_depth=reflection_depth,
                correction_made=correction_made,
                patterns_used=patterns_used
            )

            print(f"✓ Updated performance metrics")
            print()

            return ExecutionResult(
                task_id=task_id,
                success=success,
                output=output,
                execution_time_seconds=execution_time,
                patterns_used=patterns_used,
                intermediate_steps=intermediate_steps,
                reflection=reflection,
                reflection_depth=reflection_depth,
                correction_made=correction_made
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            print()
            print(f"✗ Execution failed: {e}")
            print()

            return ExecutionResult(
                task_id=task_id,
                success=False,
                output="",
                execution_time_seconds=execution_time,
                patterns_used=[],
                intermediate_steps=[],
                error_message=str(e)
            )

    def _load_agent_config(self) -> Dict:
        """Load agent configuration"""
        if not self.agent_config_file.exists():
            raise FileNotFoundError(f"Agent config not found: {self.agent_config_file}")

        with open(self.agent_config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_agent_prompt(self) -> str:
        """Load agent prompt"""
        if not self.agent_prompt_file.exists():
            raise FileNotFoundError(f"Agent prompt not found: {self.agent_prompt_file}")

        with open(self.agent_prompt_file, 'r', encoding='utf-8') as f:
            return f.read()

    def _load_memory_context(self, task_description: str) -> MemoryContext:
        """Load memory context for task"""
        exec_config = self.config.get('execution', {})

        episodic_limit = exec_config.get('episodic_memory_limit', 5)
        semantic_limit = exec_config.get('semantic_retrieval_limit', 10)
        max_tokens = exec_config.get('memory_context_max_tokens', 2000)

        return self.memory_manager.load_context(
            task_description=task_description,
            episodic_limit=episodic_limit,
            semantic_limit=semantic_limit,
            max_context_tokens=max_tokens
        )

    def _inject_memory(
        self,
        agent_prompt: str,
        memory_context: MemoryContext,
        task_description: str
    ) -> str:
        """
        Inject memory context into agent prompt

        Args:
            agent_prompt: Base agent prompt
            memory_context: Loaded memory
            task_description: Current task

        Returns:
            Full prompt with memory injected
        """
        memory_text = memory_context.to_prompt_text(
            max_tokens=self.config.get('execution', {}).get('memory_context_max_tokens', 2000)
        )

        # Inject memory before task
        full_prompt = f"""
{agent_prompt}

---

# MEMORY CONTEXT

{memory_text}

---

# CURRENT TASK

{task_description}

Please execute this task using the proven patterns from your configuration and learnings from past experience shown above.

Apply ARES v3.0 internal validation:
1. Challenge approach internally
2. Consider simpler alternatives
3. Validate with patterns and evidence
4. Execute with confidence
5. Show your work
"""

        return full_prompt

    def _execute_agent(
        self,
        prompt: str,
        task_description: str,
        agent_config: Dict
    ) -> Tuple[str, List[Dict], bool]:
        """
        Execute agent task

        For Phase 2: Simulated execution (returns mock output)
        For Phase 3+: Will integrate with actual Task tool

        Args:
            prompt: Full execution prompt
            task_description: Task description
            agent_config: Agent configuration

        Returns:
            (output, intermediate_steps, success)
        """
        print("[EXECUTOR] Simulating agent execution (Phase 2)")
        print(f"[EXECUTOR] Prompt length: {len(prompt)} chars")
        print()

        # Simulated output for Phase 2
        output = f"""
Task: {task_description}

[SIMULATED EXECUTION]

This is a Phase 2 simulated execution. The agent would:

1. Load the full prompt with memory context
2. Apply ARES v3.0 internal validation
3. Execute using proven patterns:
   {', '.join([p['id'] for p in agent_config.get('proven_patterns', [])])}
4. Generate output based on the task
5. Self-reflect on execution

In Phase 3, this will be replaced with actual Task tool invocation
that executes the agent with the full prompt and captures real output.

Status: SUCCESS (simulated)
"""

        intermediate_steps = [
            {
                'step_number': 1,
                'description': 'Load prompt and memory context',
                'output': 'Loaded successfully',
                'success': True
            },
            {
                'step_number': 2,
                'description': 'Apply ARES validation',
                'output': 'Validation passed (confidence: 85%)',
                'success': True
            },
            {
                'step_number': 3,
                'description': 'Execute task',
                'output': 'Task completed (simulated)',
                'success': True
            }
        ]

        success = True

        return output, intermediate_steps, success

    def _extract_patterns_used(
        self,
        agent_config: Dict,
        intermediate_steps: List[Dict]
    ) -> List[str]:
        """Extract which patterns were used during execution"""
        # For Phase 2, return configured patterns
        # Phase 3+ can extract from actual execution logs
        patterns = agent_config.get('proven_patterns', [])
        return [p['id'] for p in patterns]

    def _generate_reflection(
        self,
        task_description: str,
        output: str,
        success: bool,
        intermediate_steps: List[Dict]
    ) -> Tuple[str, str, bool]:
        """
        Generate post-task reflection

        Args:
            task_description: Task description
            output: Execution output
            success: Whether execution succeeded
            intermediate_steps: Execution steps

        Returns:
            (reflection_text, reflection_depth, correction_made)
        """
        # Analyze execution for quality
        total_steps = len(intermediate_steps)
        successful_steps = sum(1 for s in intermediate_steps if s.get('success', True))
        step_success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 100.0

        # Determine reflection depth
        # Deep reflection if: low success rate, or high complexity
        if not success or step_success_rate < 80:
            reflection_depth = 'deep'
        else:
            reflection_depth = 'shallow'

        # Detect self-correction
        # Check if any step output mentions "correcting", "fixing", "retry", etc.
        correction_keywords = ['correct', 'fix', 'retry', 'error', 'mistake', 'revise']
        correction_made = any(
            any(kw in step.get('output', '').lower() for kw in correction_keywords)
            for step in intermediate_steps
        )

        # Generate reflection text
        reflection_lines = [
            f"Task: {task_description}",
            f"Outcome: {'Success' if success else 'Failed'}",
            f"Steps: {successful_steps}/{total_steps} successful ({step_success_rate:.0f}%)",
            ""
        ]

        if reflection_depth == 'deep':
            reflection_lines.extend([
                "Deep Reflection:",
                "",
                "What went well:",
                "- " + (intermediate_steps[0].get('output', 'N/A') if intermediate_steps else 'N/A'),
                "",
                "What could improve:",
                "- " + ("Analyze failure points and patterns" if not success else "N/A"),
                "",
                "Learnings:",
                "- " + ("Pattern effectiveness needs validation" if not success else "Approach validated"),
            ])
        else:
            reflection_lines.extend([
                "Shallow Reflection:",
                "Execution successful using established patterns. No major issues detected."
            ])

        if correction_made:
            reflection_lines.extend([
                "",
                "Self-Correction:",
                "Agent detected and corrected issue during execution."
            ])

        reflection_text = "\n".join(reflection_lines)

        return reflection_text, reflection_depth, correction_made

    def _store_execution(
        self,
        task_id: str,
        task_description: str,
        execution_time_seconds: float,
        success: bool,
        patterns_used: List[str],
        reflection_text: str,
        reflection_depth: str,
        correction_made: bool,
        intermediate_steps: List[Dict]
    ):
        """Store execution to episodic memory"""
        self.memory_manager.store_task_execution(
            task_id=task_id,
            task_description=task_description,
            execution_time_seconds=execution_time_seconds,
            success=success,
            patterns_used=patterns_used,
            reflection_text=reflection_text,
            reflection_depth=reflection_depth,
            correction_made=correction_made,
            intermediate_steps=intermediate_steps
        )

    def _update_performance_metrics(
        self,
        success: bool,
        execution_time_seconds: float,
        reflection_depth: str,
        correction_made: bool,
        patterns_used: List[str]
    ):
        """Update agent performance metrics"""
        if not self.performance_file.exists():
            # Initialize metrics if not exists
            self._initialize_performance_metrics()

        try:
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                metrics = json.load(f)

            # Update core performance
            core = metrics['metrics']['core_performance']
            core['total_invocations'] += 1
            if success:
                core['successful'] += 1
            else:
                core['failed'] += 1
            core['success_rate'] = (core['successful'] / core['total_invocations'] * 100)

            # Update time performance
            time_perf = metrics['metrics'].get('time_performance', {})
            if 'avg_time_seconds' not in time_perf or 'min_time_seconds' not in time_perf:
                # Initialize or fix incomplete time_performance
                time_perf['avg_time_seconds'] = execution_time_seconds
                time_perf['min_time_seconds'] = execution_time_seconds
                time_perf['max_time_seconds'] = execution_time_seconds
            else:
                # Update average
                total = core['total_invocations']
                time_perf['avg_time_seconds'] = (
                    (time_perf['avg_time_seconds'] * (total - 1) + execution_time_seconds) / total
                )
                time_perf['min_time_seconds'] = min(time_perf.get('min_time_seconds', execution_time_seconds), execution_time_seconds)
                time_perf['max_time_seconds'] = max(time_perf.get('max_time_seconds', execution_time_seconds), execution_time_seconds)

            metrics['metrics']['time_performance'] = time_perf

            # Update reflection quality
            reflection = metrics['metrics'].get('reflection_quality', {
                'correction_rate': 0.0,
                'reflection_depth': {'shallow': 0, 'deep': 0},
                'self_corrections': 0
            })

            # Ensure all fields exist (handle legacy metrics files)
            if 'self_corrections' not in reflection:
                reflection['self_corrections'] = 0
            if 'reflection_depth' not in reflection:
                reflection['reflection_depth'] = {'shallow': 0, 'deep': 0}

            if reflection_depth == 'deep':
                reflection['reflection_depth']['deep'] += 1
            else:
                reflection['reflection_depth']['shallow'] += 1

            if correction_made:
                reflection['self_corrections'] += 1

            reflection['correction_rate'] = (
                reflection['self_corrections'] / core['total_invocations'] * 100
            )

            metrics['metrics']['reflection_quality'] = reflection

            # Update pattern effectiveness
            pattern_eff = metrics['metrics'].get('pattern_effectiveness', {})
            for pattern_id in patterns_used:
                if pattern_id not in pattern_eff:
                    pattern_eff[pattern_id] = {'usage': 0, 'success': 0, 'effectiveness': 0.0}

                pattern_eff[pattern_id]['usage'] += 1
                if success:
                    pattern_eff[pattern_id]['success'] += 1
                pattern_eff[pattern_id]['effectiveness'] = (
                    pattern_eff[pattern_id]['success'] / pattern_eff[pattern_id]['usage'] * 100
                )

            metrics['metrics']['pattern_effectiveness'] = pattern_eff

            # Update last_updated
            metrics['last_updated'] = datetime.now().isoformat()

            # Save
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Warning: Could not update performance metrics: {e}")

    def _initialize_performance_metrics(self):
        """Initialize performance metrics file"""
        metrics = {
            'agent_id': self.agent_id,
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'metrics': {
                'core_performance': {
                    'total_invocations': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0.0
                },
                'time_performance': {},
                'reflection_quality': {
                    'correction_rate': 0.0,
                    'reflection_depth': {'shallow': 0, 'deep': 0},
                    'self_corrections': 0
                },
                'pattern_effectiveness': {}
            }
        }

        self.performance_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.performance_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)


def execute_agent(agent_id: str, task_description: str, context: Optional[Dict] = None) -> ExecutionResult:
    """
    Convenience function to execute an agent

    Args:
        agent_id: Agent identifier
        task_description: Task to execute
        context: Optional context

    Returns:
        ExecutionResult
    """
    executor = AgentExecutor(agent_id)
    return executor.execute(task_description, context)
