#!/usr/bin/env python3
"""
ARES Agent Lifecycle Management System - CLI
Version: 3.5.0
Created: 2025-10-24

CLI for managing the complete agent lifecycle:
- Evaluate: Should we create an agent?
- Create: Generate new agent from template
- Execute: Run agent with memory context
- Evolve: Improve agent based on performance
- Curate: Audit and optimize agent portfolio
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Version
VERSION = "3.5.0"


class AresAgentLifecycle:
    """
    Main class for ARES Agent Lifecycle Management System
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the lifecycle management system

        Args:
            config_path: Path to agent_lifecycle.yaml
        """
        self.config_path = config_path or PROJECT_ROOT / "config" / "agent_lifecycle.yaml"
        self.agents_dir = PROJECT_ROOT / "agents"
        self.templates_dir = PROJECT_ROOT / "templates"
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        # TODO: Implement YAML loading
        # For now, return empty dict
        return {}

    # ========================================================================
    # PHASE 0: Foundation (Complete)
    # ========================================================================

    def version_info(self):
        """Display version information"""
        print("=" * 70)
        print("ARES AGENT LIFECYCLE MANAGEMENT SYSTEM")
        print("=" * 70)
        print()
        print(f"Version:     {VERSION}")
        print(f"Component:   Agent Lifecycle Layer")
        print(f"Status:      Phase 3 Complete - Analytics + Stats Ready")
        print()
        print("Capabilities:")
        print("  ✓ Configuration system")
        print("  ✓ Agent templates")
        print("  ✓ Memory schemas (episodic, semantic, procedural)")
        print("  ✓ Performance tracking schemas")
        print("  ✓ Agent evaluator (ROI + frequency + capability gap)")
        print("  ✓ Agent creator (pattern extraction + memory init)")
        print("  ✓ Memory manager (episodic + semantic + procedural)")
        print("  ✓ Agent executor (execution + reflection + metrics)")
        print("  ✓ Performance analytics (stats, trends, health)")
        print()
        print("Next Phase: Agent Evolution + Hypothesis Testing")
        print("=" * 70)

    def list_agents(self, status: Optional[str] = None):
        """
        List all agents

        Args:
            status: Filter by status (active, deprecated, archived)
        """
        print("=" * 70)
        print("ARES AGENTS")
        print("=" * 70)
        print()

        if not self.agents_dir.exists():
            print("No agents directory found.")
            print(f"Expected: {self.agents_dir}")
            return

        agent_dirs = [d for d in self.agents_dir.iterdir() if d.is_dir()]

        if not agent_dirs:
            print("No agents created yet.")
            print()
            print("To create your first agent:")
            print(f"  python {Path(__file__).name} evaluate \"Your task description\"")
            return

        # TODO: Implement agent listing from config files
        print(f"Found {len(agent_dirs)} agent(s)")
        for agent_dir in agent_dirs:
            print(f"  - {agent_dir.name}")

        print("=" * 70)

    # ========================================================================
    # PHASE 1: Agent Evaluator + Creator (TODO)
    # ========================================================================

    def evaluate(self, task_description: str):
        """
        Evaluate if a new agent should be created for this task

        Args:
            task_description: Description of the task
        """
        from core.agent_evaluator import AgentEvaluator

        print("=" * 70)
        print("AGENT EVALUATION")
        print("=" * 70)
        print()
        print(f"Task: {task_description}")
        print()

        evaluator = AgentEvaluator()
        result = evaluator.evaluate(task_description)

        print("Analysis:")
        print("-" * 70)
        for reason in result.reasoning:
            print(f"  • {reason}")
        print()

        print("Result:")
        print("-" * 70)
        print(f"  Decision:          {result.decision}")
        print(f"  Confidence:        {result.confidence:.1f}%")
        if result.existing_agent:
            print(f"  Existing Agent:    {result.existing_agent}")
        print(f"  Capability Gap:    {result.capability_gap:.0f}%")
        print(f"  Estimated ROI:     {result.estimated_roi:.1f}x")
        print(f"  Task Frequency:    {result.task_frequency_per_month:.1f}/month")
        print()

        # Recommendation
        if result.decision == "CREATE" and result.confidence >= 80:
            print("✓ RECOMMENDATION: Create new agent")
            print()
            print("Next step:")
            print(f"  python {Path(__file__).name} create [agent-id] \\")
            print(f"      --domains \"...\" \\")
            print(f"      --complexity \"...\" \\")
            print(f"      --description \"...\"")
        elif result.decision == "USE_EXISTING":
            print(f"✓ RECOMMENDATION: Use existing agent '{result.existing_agent}'")
        elif result.decision == "ENHANCE":
            print(f"✓ RECOMMENDATION: Enhance existing agent '{result.existing_agent}'")
        elif result.decision == "DIRECT":
            print("✓ RECOMMENDATION: Handle directly (no agent needed)")
            print()
            print("Reasons:")
            print("  - Low frequency or low ROI")
            print("  - More efficient to handle case-by-case")

        print("=" * 70)

    def create(
        self,
        agent_id: str,
        domains: List[str],
        complexity: List[str],
        description: str
    ):
        """
        Create a new agent

        Args:
            agent_id: Unique agent identifier
            domains: List of domains
            complexity: List of complexity levels
            description: Agent description
        """
        from core.agent_creator import create_agent

        print("=" * 70)
        print("AGENT CREATION")
        print("=" * 70)
        print()
        print(f"Agent ID: {agent_id}")
        print(f"Name: {agent_id.replace('-', ' ').title()}")
        print(f"Domains: {', '.join(domains)}")
        print(f"Complexity: {', '.join(complexity)}")
        print(f"Description: {description}")
        print()

        # Create the agent
        name = agent_id.replace('-', ' ').title()
        success = create_agent(
            agent_id=agent_id,
            name=name,
            domains=domains,
            complexity=complexity,
            description=description
        )

        if success:
            print()
            print("Next steps:")
            print(f"  1. Review agent files in: agents/{agent_id}/")
            print(f"  2. Test agent execution (Phase 2 - coming soon)")
            print(f"  3. Monitor performance after 10 invocations")
        else:
            print()
            print("❌ Agent creation failed. See errors above.")

        print("=" * 70)

    # ========================================================================
    # PHASE 2: Agent Executor + Memory (COMPLETE)
    # ========================================================================

    def execute(self, agent_id: str, task: str):
        """
        Execute an agent

        Args:
            agent_id: Agent to execute
            task: Task description
        """
        from core.agent_executor import AgentExecutor

        print("=" * 70)
        print("AGENT EXECUTION")
        print("=" * 70)
        print()

        # Check agent exists
        agent_dir = self.agents_dir / agent_id
        if not agent_dir.exists():
            print(f"❌ Error: Agent '{agent_id}' not found")
            print()
            print("Available agents:")
            for d in self.agents_dir.iterdir():
                if d.is_dir():
                    print(f"  - {d.name}")
            print("=" * 70)
            return

        # Execute
        executor = AgentExecutor(agent_id)
        result = executor.execute(task)

        # Display result
        print("=" * 70)
        print("EXECUTION RESULT")
        print("=" * 70)
        print()
        print(f"Task ID: {result.task_id}")
        print(f"Success: {result.success}")
        print(f"Time: {result.execution_time_seconds:.1f}s")
        print(f"Patterns Used: {', '.join(result.patterns_used)}")
        print()
        print("Output:")
        print("-" * 70)
        print(result.output)
        print("-" * 70)
        print()

        if result.reflection:
            print("Reflection:")
            print("-" * 70)
            print(result.reflection)
            print("-" * 70)
            print()

        if result.error_message:
            print(f"Error: {result.error_message}")
            print()

        print("✓ Execution stored to episodic memory")
        print("✓ Performance metrics updated")
        print("=" * 70)

    # ========================================================================
    # PHASE 3: Performance Analytics (COMPLETE)
    # ========================================================================

    def stats(self, agent_id: str, detailed: bool = False):
        """
        Show agent performance statistics

        Args:
            agent_id: Agent to show stats for
            detailed: Show detailed pattern analysis
        """
        from core.performance_analytics import PerformanceAnalytics

        # Check agent exists
        agent_dir = self.agents_dir / agent_id
        if not agent_dir.exists():
            print("=" * 70)
            print(f"AGENT STATS: {agent_id}")
            print("=" * 70)
            print()
            print(f"❌ Error: Agent '{agent_id}' not found")
            print()
            print("Available agents:")
            for d in self.agents_dir.iterdir():
                if d.is_dir():
                    print(f"  - {d.name}")
            print("=" * 70)
            return

        # Generate and display report
        try:
            analytics = PerformanceAnalytics(agent_id)
            report = analytics.generate_report(detailed=detailed)
            print(report)
        except FileNotFoundError:
            print("=" * 70)
            print(f"AGENT STATS: {agent_id}")
            print("=" * 70)
            print()
            print(f"❌ Error: No performance data found for {agent_id}")
            print()
            print("Agent has not been executed yet. Run:")
            print(f"  python {Path(__file__).name} execute {agent_id} --task \"Your task\"")
            print("=" * 70)
        except Exception as e:
            print("=" * 70)
            print(f"AGENT STATS: {agent_id}")
            print("=" * 70)
            print()
            print(f"❌ Error: {e}")
            print("=" * 70)

    # ========================================================================
    # PHASE 4: Agent Evolver (TODO)
    # ========================================================================

    def evolve(self, agent_id: str):
        """
        Evolve an agent based on performance data

        Args:
            agent_id: Agent to evolve
        """
        print("=" * 70)
        print(f"AGENT EVOLUTION: {agent_id}")
        print("=" * 70)
        print()
        print("Status: NOT IMPLEMENTED YET")
        print()
        print("Phase 4 will implement:")
        print("  - Performance analysis")
        print("  - Learning extraction")
        print("  - Hypothesis generation")
        print("  - Prompt updating")
        print("  - Version control (semantic versioning)")
        print("=" * 70)

    # ========================================================================
    # PHASE 5: Agent Curator (TODO)
    # ========================================================================

    def curate(self, report: bool = False):
        """
        Curate agent portfolio

        Args:
            report: Generate report only (no changes)
        """
        print("=" * 70)
        print("AGENT PORTFOLIO CURATION")
        print("=" * 70)
        print()
        print("Status: NOT IMPLEMENTED YET")
        print()
        print("Phase 5 will implement:")
        print("  - Portfolio analysis")
        print("  - Redundancy detection")
        print("  - Performance auditing")
        print("  - State-of-the-art updates")
        print("  - Human-in-the-loop recommendations")
        print("=" * 70)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ARES Agent Lifecycle Management System v3.5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show version info
  python ares_agent_lifecycle.py version

  # List all agents
  python ares_agent_lifecycle.py list

  # Evaluate if agent needed
  python ares_agent_lifecycle.py evaluate "Prepare discovery call for client"

  # Create new agent
  python ares_agent_lifecycle.py create discovery-call-specialist \\
      --domains "sales,consulting" \\
      --complexity "moderate" \\
      --description "Specialized agent for discovery call preparation"

  # Execute agent
  python ares_agent_lifecycle.py execute discovery-call-specialist \\
      --task "Prepare discovery call for Daren (HVAC)"

  # Show agent stats
  python ares_agent_lifecycle.py stats discovery-call-specialist

  # Evolve agent
  python ares_agent_lifecycle.py evolve discovery-call-specialist

  # Curate portfolio
  python ares_agent_lifecycle.py curate --report

Current Status:
  Phase 0: ✓ Complete (Foundation)
  Phase 1: ✓ Complete (Evaluator + Creator)
  Phase 2: ✓ Complete (Executor + Memory)
  Phase 3: ✓ Complete (Performance Analytics)
  Phase 4: ⏳ Next (Evolution)
  Phase 5: ⏳ Pending (Curation)
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Version command
    subparsers.add_parser('version', help='Show version information')

    # List command
    list_parser = subparsers.add_parser('list', help='List all agents')
    list_parser.add_argument(
        '--status',
        choices=['active', 'deprecated', 'archived'],
        help='Filter by status'
    )

    # Evaluate command (Phase 1)
    evaluate_parser = subparsers.add_parser(
        'evaluate',
        help='Evaluate if new agent needed for task'
    )
    evaluate_parser.add_argument('task', help='Task description')

    # Create command (Phase 1)
    create_parser = subparsers.add_parser('create', help='Create new agent')
    create_parser.add_argument('agent_id', help='Unique agent identifier')
    create_parser.add_argument(
        '--domains',
        required=True,
        help='Comma-separated domains'
    )
    create_parser.add_argument(
        '--complexity',
        required=True,
        help='Comma-separated complexity levels'
    )
    create_parser.add_argument(
        '--description',
        required=True,
        help='Agent description'
    )

    # Execute command (Phase 2)
    execute_parser = subparsers.add_parser('execute', help='Execute agent')
    execute_parser.add_argument('agent_id', help='Agent to execute')
    execute_parser.add_argument('--task', required=True, help='Task description')

    # Stats command (Phase 3)
    stats_parser = subparsers.add_parser('stats', help='Show agent statistics')
    stats_parser.add_argument('agent_id', help='Agent ID')
    stats_parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed pattern analysis'
    )

    # Evolve command (Phase 4)
    evolve_parser = subparsers.add_parser('evolve', help='Evolve agent')
    evolve_parser.add_argument('agent_id', help='Agent to evolve')

    # Curate command (Phase 5)
    curate_parser = subparsers.add_parser('curate', help='Curate agent portfolio')
    curate_parser.add_argument(
        '--report',
        action='store_true',
        help='Generate report only (no changes)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize system
    system = AresAgentLifecycle()

    # Execute command
    if args.command == 'version':
        system.version_info()
    elif args.command == 'list':
        system.list_agents(args.status if hasattr(args, 'status') else None)
    elif args.command == 'evaluate':
        system.evaluate(args.task)
    elif args.command == 'create':
        domains = [d.strip() for d in args.domains.split(',')]
        complexity = [c.strip() for c in args.complexity.split(',')]
        system.create(args.agent_id, domains, complexity, args.description)
    elif args.command == 'execute':
        system.execute(args.agent_id, args.task)
    elif args.command == 'stats':
        system.stats(args.agent_id, detailed=args.detailed if hasattr(args, 'detailed') else False)
    elif args.command == 'evolve':
        system.evolve(args.agent_id)
    elif args.command == 'curate':
        system.curate(args.report if hasattr(args, 'report') else False)


if __name__ == "__main__":
    main()
