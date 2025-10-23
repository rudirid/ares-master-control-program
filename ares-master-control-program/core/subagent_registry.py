"""
ARES Subagent Registry - Catalog and Management of Available Agents
Loads, queries, and manages the subagent registry
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentRegistryEntry:
    """Single agent entry from registry"""
    agent_id: str
    agent_type: str  # builtin or custom
    execution_method: str
    domains: List[str]
    complexity: List[str]
    description: str
    priority: int
    availability: str
    category: str  # claude-code-builtin or ares-custom


class SubagentRegistry:
    """
    Manages the subagent registry
    Provides query and management capabilities
    """

    DEFAULT_REGISTRY_PATH = Path.home() / ".claude" / "subagents" / "registry.json"

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize registry

        Args:
            registry_path: Path to registry.json (uses default if None)
        """
        self.registry_path = registry_path or self.DEFAULT_REGISTRY_PATH
        self.registry_data = {}
        self.agents = {}
        self.load()

    def load(self) -> bool:
        """
        Load registry from file

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.registry_path.exists():
            print(f"Warning: Registry not found at {self.registry_path}")
            return False

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry_data = json.load(f)

            # Parse agents into AgentRegistryEntry objects
            self._parse_agents()
            return True

        except Exception as e:
            print(f"Error loading registry: {e}")
            return False

    def _parse_agents(self):
        """Parse registry data into AgentRegistryEntry objects"""
        self.agents = {}

        for category_key, category_data in self.registry_data.get('agents', {}).items():
            for agent_id, agent_data in category_data.get('agents', {}).items():
                entry = AgentRegistryEntry(
                    agent_id=agent_id,
                    agent_type=agent_data.get('type', 'unknown'),
                    execution_method=agent_data.get('execution_method', 'unknown'),
                    domains=agent_data.get('domains', []),
                    complexity=agent_data.get('complexity', []),
                    description=agent_data.get('description', ''),
                    priority=agent_data.get('priority', 5),
                    availability=agent_data.get('availability', 'unknown'),
                    category=category_key
                )
                self.agents[agent_id] = entry

    def get_agent(self, agent_id: str) -> Optional[AgentRegistryEntry]:
        """Get agent by ID"""
        return self.agents.get(agent_id)

    def find_by_domain(self, domain: str) -> List[AgentRegistryEntry]:
        """Find all agents that support a domain"""
        return [
            agent for agent in self.agents.values()
            if domain in agent.domains
        ]

    def find_by_complexity(self, complexity: str) -> List[AgentRegistryEntry]:
        """Find all agents that support a complexity level"""
        return [
            agent for agent in self.agents.values()
            if complexity in agent.complexity
        ]

    def find_by_execution_method(self, method: str) -> List[AgentRegistryEntry]:
        """Find all agents with specific execution method"""
        return [
            agent for agent in self.agents.values()
            if agent.execution_method == method
        ]

    def list_all_agents(self) -> List[AgentRegistryEntry]:
        """List all agents sorted by priority"""
        return sorted(self.agents.values(), key=lambda a: a.priority)

    def list_available_agents(self) -> List[AgentRegistryEntry]:
        """List only available agents"""
        return [
            agent for agent in self.agents.values()
            if agent.availability == "always"
        ]

    def get_builtin_agents(self) -> List[AgentRegistryEntry]:
        """Get all built-in Claude Code agents"""
        return [
            agent for agent in self.agents.values()
            if agent.category == "claude-code-builtin"
        ]

    def get_custom_agents(self) -> List[AgentRegistryEntry]:
        """Get all custom Ares agents"""
        return [
            agent for agent in self.agents.values()
            if agent.category == "ares-custom"
        ]

    def register_custom_agent(
        self,
        agent_id: str,
        execution_method: str,
        domains: List[str],
        complexity: List[str],
        description: str,
        priority: int = 5,
        save: bool = True
    ) -> bool:
        """
        Register a new custom agent

        Args:
            agent_id: Unique identifier
            execution_method: How to execute (Task, MCP, DirectAPI)
            domains: List of domain strings
            complexity: List of complexity levels
            description: Description of agent
            priority: Priority (1=highest, 10=lowest)
            save: Whether to save registry to file

        Returns:
            True if registered successfully
        """
        # Check if already exists
        if agent_id in self.agents:
            print(f"Warning: Agent {agent_id} already exists")
            return False

        # Add to in-memory registry
        entry = AgentRegistryEntry(
            agent_id=agent_id,
            agent_type="custom",
            execution_method=execution_method,
            domains=domains,
            complexity=complexity,
            description=description,
            priority=priority,
            availability="always",
            category="ares-custom"
        )
        self.agents[agent_id] = entry

        if save:
            return self._save_registry()

        return True

    def _save_registry(self) -> bool:
        """Save registry to file"""
        try:
            # Update custom agents section in registry data
            custom_agents = {}
            for agent_id, agent in self.agents.items():
                if agent.category == "ares-custom":
                    custom_agents[agent_id] = {
                        "type": agent.agent_type,
                        "execution_method": agent.execution_method,
                        "domains": agent.domains,
                        "complexity": agent.complexity,
                        "description": agent.description,
                        "priority": agent.priority,
                        "availability": agent.availability
                    }

            self.registry_data['agents']['ares-custom']['agents'] = custom_agents
            self.registry_data['last_updated'] = datetime.now().strftime("%Y-%m-%d")

            # Update metadata
            total_agents = len(self.agents)
            custom_count = len(custom_agents)
            builtin_count = total_agents - custom_count

            self.registry_data['metadata'].update({
                'total_agents': total_agents,
                'builtin_agents': builtin_count,
                'custom_agents': custom_count
            })

            # Write to file
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving registry: {e}")
            return False

    def get_stats(self) -> Dict[str, any]:
        """Get registry statistics"""
        return {
            'total_agents': len(self.agents),
            'builtin_agents': len(self.get_builtin_agents()),
            'custom_agents': len(self.get_custom_agents()),
            'available_agents': len(self.list_available_agents()),
            'execution_methods': list(set(a.execution_method for a in self.agents.values())),
            'domains_covered': list(set(d for a in self.agents.values() for d in a.domains)),
        }

    def print_summary(self):
        """Print registry summary"""
        stats = self.get_stats()
        print("=" * 60)
        print("ARES SUBAGENT REGISTRY SUMMARY")
        print("=" * 60)
        print(f"Total Agents: {stats['total_agents']}")
        print(f"  Built-in (Claude Code): {stats['builtin_agents']}")
        print(f"  Custom (Ares): {stats['custom_agents']}")
        print(f"  Available: {stats['available_agents']}")
        print(f"\nExecution Methods: {', '.join(stats['execution_methods'])}")
        print(f"\nDomains Covered ({len(stats['domains_covered'])}):")
        for domain in sorted(stats['domains_covered']):
            print(f"  - {domain}")
        print("=" * 60)

    def print_agents(self, category: Optional[str] = None):
        """
        Print agent list

        Args:
            category: Filter by category (claude-code-builtin, ares-custom)
        """
        agents = self.agents.values()
        if category:
            agents = [a for a in agents if a.category == category]

        agents = sorted(agents, key=lambda a: a.priority)

        for agent in agents:
            print(f"\n{agent.agent_id}")
            print(f"  Type: {agent.agent_type}")
            print(f"  Domains: {', '.join(agent.domains)}")
            print(f"  Complexity: {', '.join(agent.complexity)}")
            print(f"  Priority: {agent.priority}")
            print(f"  Description: {agent.description}")


# Convenience function
def load_registry(path: Optional[Path] = None) -> SubagentRegistry:
    """Load the subagent registry"""
    return SubagentRegistry(path)
