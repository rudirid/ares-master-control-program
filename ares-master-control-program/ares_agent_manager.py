#!/usr/bin/env python3
"""
ARES Agent Manager - CLI for Managing Subagents
Provides commands to list, test, version, and deploy subagents
"""

import sys
import json
from pathlib import Path
from typing import Optional
import argparse
from datetime import datetime

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.subagent_registry import SubagentRegistry
from core.orchestrator import AresOrchestrator
from core.task_analyzer import analyze_task


class AresAgentManager:
    """CLI manager for ARES agents"""

    def __init__(self):
        self.registry = SubagentRegistry()
        self.orchestrator = AresOrchestrator()

    def list_agents(self, category: Optional[str] = None, domain: Optional[str] = None):
        """
        List available agents

        Args:
            category: Filter by category (builtin, custom)
            domain: Filter by domain
        """
        print("=" * 70)
        print("ARES AVAILABLE AGENTS")
        print("=" * 70)
        print()

        agents = list(self.registry.agents.values())

        # Apply filters
        if category:
            category_map = {
                'builtin': 'claude-code-builtin',
                'custom': 'ares-custom'
            }
            filter_cat = category_map.get(category, category)
            agents = [a for a in agents if a.category == filter_cat]

        if domain:
            agents = [a for a in agents if domain in a.domains]

        # Sort by priority
        agents.sort(key=lambda a: a.priority)

        if not agents:
            print("No agents found matching criteria")
            return

        for agent in agents:
            print(f"┌─ {agent.agent_id}")
            print(f"│  Category: {agent.category}")
            print(f"│  Type: {agent.agent_type}")
            print(f"│  Execution: {agent.execution_method}")
            print(f"│  Domains: {', '.join(agent.domains)}")
            print(f"│  Complexity: {', '.join(agent.complexity)}")
            print(f"│  Priority: {agent.priority} (1=highest)")
            print(f"│  Availability: {agent.availability}")
            print(f"│  Description: {agent.description}")
            print("└─")
            print()

        print(f"Total: {len(agents)} agent(s)")
        print("=" * 70)

    def list_domains(self):
        """List all available domains"""
        stats = self.registry.get_stats()
        print("=" * 70)
        print("ARES DOMAIN COVERAGE")
        print("=" * 70)
        print()

        domains = sorted(stats['domains_covered'])
        for domain in domains:
            agents = self.registry.find_by_domain(domain)
            print(f"{domain:20} ({len(agents)} agent(s))")

        print()
        print(f"Total: {len(domains)} domain(s)")
        print("=" * 70)

    def stats(self):
        """Show registry statistics"""
        stats = self.registry.get_stats()
        print("=" * 70)
        print("ARES AGENT REGISTRY STATISTICS")
        print("=" * 70)
        print()
        print(f"Total Agents:        {stats['total_agents']}")
        print(f"  Built-in:          {stats['builtin_agents']}")
        print(f"  Custom:            {stats['custom_agents']}")
        print(f"  Available:         {stats['available_agents']}")
        print()
        print(f"Execution Methods:   {', '.join(stats['execution_methods'])}")
        print(f"Domains Covered:     {len(stats['domains_covered'])}")
        print()
        print("=" * 70)

    def test_task(self, task_description: str):
        """
        Test orchestration for a task description

        Args:
            task_description: Task to test
        """
        print("=" * 70)
        print("ARES ORCHESTRATION TEST")
        print("=" * 70)
        print()
        print(f"Task: {task_description}")
        print()

        # Create plan
        plan = self.orchestrator.plan(task_description)

        # Show plan
        print(self.orchestrator.explain_plan(plan))

        # Show what would be executed
        print()
        print(self.orchestrator.get_execution_instructions(plan))

        # Show execution log
        print()
        print("EXECUTION LOG:")
        print("-" * 70)
        for entry in self.orchestrator.execution_log:
            print(f"  {entry}")
        print("=" * 70)

    def analyze_task(self, task_description: str):
        """
        Analyze a task without creating full plan

        Args:
            task_description: Task to analyze
        """
        print("=" * 70)
        print("ARES TASK ANALYSIS")
        print("=" * 70)
        print()

        analysis = analyze_task(task_description)

        print(f"Task: {task_description}")
        print()
        print(f"Complexity:          {analysis.complexity.value}")
        print(f"Primary Domain:      {analysis.primary_domain.value}")

        if analysis.secondary_domains:
            domains = ", ".join(d.value for d in analysis.secondary_domains)
            print(f"Secondary Domains:   {domains}")

        print(f"Decomposition:       {'Required' if analysis.requires_decomposition else 'Not required'}")
        print(f"Estimated Subtasks:  {analysis.estimated_subtasks}")
        print(f"Confidence:          {analysis.confidence:.1%}")
        print()
        print("Reasoning:")
        print(f"  {analysis.reasoning}")
        print()
        print("=" * 70)

    def register_custom_agent(
        self,
        agent_id: str,
        domains: str,
        complexity: str,
        description: str,
        priority: int = 5
    ):
        """
        Register a new custom agent

        Args:
            agent_id: Unique agent identifier
            domains: Comma-separated domains
            complexity: Comma-separated complexity levels
            description: Agent description
            priority: Priority (1-10)
        """
        domains_list = [d.strip() for d in domains.split(',')]
        complexity_list = [c.strip() for c in complexity.split(',')]

        success = self.registry.register_custom_agent(
            agent_id=agent_id,
            execution_method="Task",  # Default to Task tool
            domains=domains_list,
            complexity=complexity_list,
            description=description,
            priority=priority,
            save=True
        )

        if success:
            print(f"✓ Successfully registered custom agent: {agent_id}")
            print(f"  Domains: {', '.join(domains_list)}")
            print(f"  Complexity: {', '.join(complexity_list)}")
            print(f"  Priority: {priority}")
        else:
            print(f"✗ Failed to register agent: {agent_id}")
            print("  (Agent may already exist)")

    def version_info(self):
        """Show version information"""
        print("=" * 70)
        print("ARES AGENT ORCHESTRATION SYSTEM")
        print("=" * 70)
        print()
        print("Version:     2.5.0")
        print("Component:   Agent Orchestration Layer")
        print("Status:      Active")
        print()
        print("Components:")
        print("  ✓ Task Analyzer")
        print("  ✓ Capability Matcher")
        print("  ✓ Prompt Generator")
        print("  ✓ Subagent Registry")
        print("  ✓ Orchestrator")
        print()
        print("Registry Location:")
        print(f"  {self.registry.registry_path}")
        print()
        print("=" * 70)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ARES Agent Manager - Manage and orchestrate subagents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all agents
  python ares_agent_manager.py list

  # List only custom agents
  python ares_agent_manager.py list --category custom

  # List agents for frontend domain
  python ares_agent_manager.py list --domain frontend

  # Show all domains
  python ares_agent_manager.py domains

  # Show statistics
  python ares_agent_manager.py stats

  # Test orchestration for a task
  python ares_agent_manager.py test "Build a React dashboard with authentication"

  # Analyze a task
  python ares_agent_manager.py analyze "Optimize database queries for user table"

  # Register custom agent
  python ares_agent_manager.py register my-agent \\
      --domains "custom,special" \\
      --complexity "moderate,complex" \\
      --description "My custom specialized agent" \\
      --priority 2

  # Show version
  python ares_agent_manager.py version
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List available agents')
    list_parser.add_argument('--category', choices=['builtin', 'custom'], help='Filter by category')
    list_parser.add_argument('--domain', help='Filter by domain')

    # Domains command
    subparsers.add_parser('domains', help='List all available domains')

    # Stats command
    subparsers.add_parser('stats', help='Show registry statistics')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test orchestration for a task')
    test_parser.add_argument('task', help='Task description to test')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a task')
    analyze_parser.add_argument('task', help='Task description to analyze')

    # Register command
    register_parser = subparsers.add_parser('register', help='Register a custom agent')
    register_parser.add_argument('agent_id', help='Unique agent identifier')
    register_parser.add_argument('--domains', required=True, help='Comma-separated domains')
    register_parser.add_argument('--complexity', required=True, help='Comma-separated complexity levels')
    register_parser.add_argument('--description', required=True, help='Agent description')
    register_parser.add_argument('--priority', type=int, default=5, help='Priority (1-10, default 5)')

    # Version command
    subparsers.add_parser('version', help='Show version information')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = AresAgentManager()

    # Execute command
    if args.command == 'list':
        manager.list_agents(args.category, args.domain)
    elif args.command == 'domains':
        manager.list_domains()
    elif args.command == 'stats':
        manager.stats()
    elif args.command == 'test':
        manager.test_task(args.task)
    elif args.command == 'analyze':
        manager.analyze_task(args.task)
    elif args.command == 'register':
        manager.register_custom_agent(
            args.agent_id,
            args.domains,
            args.complexity,
            args.description,
            args.priority
        )
    elif args.command == 'version':
        manager.version_info()


if __name__ == "__main__":
    main()
