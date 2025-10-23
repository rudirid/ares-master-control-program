"""
ARES Agent Lifecycle System - Agent Creator
Generates new agents from templates with pattern extraction

Creates complete agent directory structure with:
- Configuration file
- ARES-compliant prompt
- Pattern library
- Memory initialization
"""

import re
import json
import yaml
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class AgentSpec:
    """Specification for creating a new agent"""
    agent_id: str
    name: str
    domains: List[str]
    complexity: List[str]
    description: str
    priority: int = 5
    target_success_rate: float = 85.0
    target_time_seconds: int = 300


class AgentCreator:
    """
    Creates new agents from templates

    Process:
    1. Load templates
    2. Extract relevant patterns from proven-patterns.md
    3. Generate prompt (ARES-compliant)
    4. Create directory structure
    5. Initialize memory (SQLite, JSON, YAML)
    6. Register to registry
    """

    def __init__(self):
        """Initialize agent creator"""
        self.project_root = Path(__file__).parent.parent
        self.agents_dir = self.project_root / "agents"
        self.templates_dir = self.project_root / "templates"
        self.knowledge_dir = self.project_root / "knowledge"
        self.config_dir = self.project_root / "config"

        # Ensure directories exist
        self.agents_dir.mkdir(exist_ok=True)

    def create_agent(self, spec: AgentSpec) -> bool:
        """
        Create a new agent

        Args:
            spec: Agent specification

        Returns:
            True if successful
        """
        print(f"Creating agent: {spec.agent_id}")
        print()

        try:
            # Step 1: Create directory structure
            agent_dir = self._create_directory_structure(spec)
            print(f"✓ Created directory: {agent_dir.relative_to(self.project_root)}")

            # Step 2: Extract patterns
            patterns = self._extract_patterns(spec)
            print(f"✓ Extracted {len(patterns)} relevant patterns")

            # Step 3: Generate configuration
            self._generate_config(spec, agent_dir, patterns)
            print(f"✓ Generated agent-config.yaml")

            # Step 4: Generate prompt
            self._generate_prompt(spec, agent_dir, patterns)
            print(f"✓ Generated agent-prompt.md")

            # Step 5: Generate patterns file
            self._generate_patterns_file(spec, agent_dir, patterns)
            print(f"✓ Generated agent-patterns.md")

            # Step 6: Initialize memory
            self._initialize_memory(spec, agent_dir)
            print(f"✓ Initialized memory systems")

            # Step 7: Create CHANGELOG
            self._create_changelog(spec, agent_dir)
            print(f"✓ Created CHANGELOG.md")

            print()
            print(f"✅ Agent '{spec.agent_id}' created successfully!")
            print()
            print(f"Location: {agent_dir.relative_to(self.project_root)}")

            return True

        except Exception as e:
            print(f"❌ Error creating agent: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_directory_structure(self, spec: AgentSpec) -> Path:
        """Create agent directory structure"""
        agent_dir = self.agents_dir / spec.agent_id
        agent_dir.mkdir(exist_ok=True)

        # Create subdirectories
        (agent_dir / "memory").mkdir(exist_ok=True)
        (agent_dir / "performance").mkdir(exist_ok=True)
        (agent_dir / "versions").mkdir(exist_ok=True)

        return agent_dir

    def _extract_patterns(self, spec: AgentSpec) -> List[Dict]:
        """
        Extract relevant patterns from knowledge base

        Args:
            spec: Agent specification

        Returns:
            List of pattern dicts
        """
        patterns = []

        # Check for proven-patterns.md
        patterns_file = self.project_root / "proven-patterns.md"
        if patterns_file.exists():
            # TODO: Parse proven-patterns.md and extract relevant ones
            # For now, add placeholders
            pass

        # Check domain-specific pattern files
        for domain in spec.domains:
            if domain == "sales" or domain == "consulting":
                # Load influence patterns
                influence_file = self.knowledge_dir / "human-psychology-influence-patterns.md"
                if influence_file.exists():
                    patterns.append({
                        'id': 'human-psychology-influence',
                        'name': 'Human Psychology & Influence Patterns',
                        'file': str(influence_file.relative_to(self.project_root)),
                        'tier': 1,
                        'scope': 'sales_only',
                        'application': 'subtle'
                    })

        # Always include general ARES patterns
        patterns.append({
            'id': 'ares-internal-validation',
            'name': 'ARES Internal Validation Protocol',
            'tier': 1,
            'description': '5-step internal validation loop'
        })

        return patterns

    def _generate_config(self, spec: AgentSpec, agent_dir: Path, patterns: List[Dict]):
        """Generate agent-config.yaml"""
        created_date = datetime.now().strftime("%Y-%m-%d")

        config = {
            'agent_id': spec.agent_id,
            'version': '1.0.0',
            'status': 'active',
            'created_date': created_date,
            'last_updated': created_date,
            'metadata': {
                'name': spec.name,
                'description': spec.description,
                'category': 'ares-custom',
                'created_by': 'ARES Agent Lifecycle System v3.5'
            },
            'domains': spec.domains,
            'complexity': spec.complexity,
            'priority': spec.priority,
            'execution': {
                'method': 'Task',
                'timeout_seconds': 600,
                'subagent_type': 'general-purpose'
            },
            'success_criteria': [
                f"Complete task in < {spec.target_time_seconds} seconds",
                f"Success rate ≥ {spec.target_success_rate}%",
                "User satisfaction ≥ 4.0/5.0"
            ],
            'patterns_used': [p['id'] for p in patterns],
            'pattern_conditions': self._generate_pattern_conditions(patterns),
            'performance_targets': {
                'success_rate_min': spec.target_success_rate,
                'avg_time_max': spec.target_time_seconds,
                'correction_rate_max': 10,
                'user_rating_min': 4.0,
                'usage_threshold': 5,
                'evolution_trigger': 10
            },
            'evolution_policy': {
                'auto_update_patterns': True,
                'version_bump_threshold': 10,
                'deprecation_threshold_days': 90,
                'extract_learnings': True,
                'min_reflections': 5
            },
            'memory': {
                'episodic': {
                    'enabled': True,
                    'retention_days': 365
                },
                'semantic': {
                    'enabled': True,
                    'max_embeddings': 1000
                },
                'procedural': {
                    'enabled': True,
                    'skill_threshold': 3
                },
                'load_similar_tasks': True,
                'similar_tasks_limit': 5
            },
            'metrics': {
                'total_invocations': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0.0,
                'avg_time_seconds': 0.0,
                'correction_rate': 0.0,
                'user_rating_avg': 0.0
            },
            'changelog': [
                {
                    'version': '1.0.0',
                    'date': created_date,
                    'changes': 'Initial agent creation',
                    'author': 'ARES Agent Lifecycle System'
                }
            ]
        }

        config_path = agent_dir / "agent-config.yaml"
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    def _generate_pattern_conditions(self, patterns: List[Dict]) -> Dict:
        """Generate pattern application conditions"""
        conditions = {}

        for pattern in patterns:
            if pattern['id'] == 'human-psychology-influence':
                conditions[pattern['id']] = {
                    'scope': 'sales_only',
                    'application': 'subtle',
                    'ethics': 'high',
                    'detection_keywords': ['discovery', 'sales', 'client', 'proposal', 'objection']
                }

        return conditions

    def _generate_prompt(self, spec: AgentSpec, agent_dir: Path, patterns: List[Dict]):
        """Generate agent-prompt.md"""
        prompt = f"""# {spec.name}

**Agent ID:** `{spec.agent_id}`
**Version:** `1.0.0`
**Domain:** {', '.join(spec.domains)}
**Status:** ACTIVE

---

## Identity & Purpose

You are **{spec.name}**, a specialized agent within the ARES Master Control Program.

**Your purpose:** {spec.description}

**Your expertise:** You specialize in {', '.join(spec.domains)} with proven patterns and frameworks.

**Your approach:** Evidence-based, pattern-driven, continuously improving through self-reflection.

---

## Core Principles (ARES v3.0)

You operate according to ARES Master Control Program principles:

### 1. Internal Validation Protocol
- Challenge your approach internally before executing
- Consider simpler alternatives
- Seek disconfirming evidence
- Validate with patterns and metrics
- Confidence-based execution (≥80% = proceed autonomously)

### 2. Show Your Work
Always display your internal validation:

```
[DECISION] Task being executed

Internal Validation:
✓ Challenge: [Evidence for approach]
✓ Simplify: [Alternatives considered]
✓ Validate: [Pattern/evidence used]
✓ Explain: [Plain language reasoning]
✓ Confidence: [percentage]

Proceeding with implementation...
```

### 3. Truth Protocol
- NEVER claim something exists without verification
- Check context/files FIRST before stating as fact
- State assumptions as assumptions, not facts
- If uncertain, INVESTIGATE before claiming
- Confidence = 100% only when VERIFIED

### 4. Transparent Reasoning
- Show decision-making process clearly
- Explain in plain language
- Provide evidence for claims
- Note warnings and caveats

---

## Proven Patterns Applied

"""

        # Add pattern details
        for pattern in patterns:
            if pattern['id'] == 'human-psychology-influence':
                prompt += """### Human Psychology & Influence Patterns (Sales Only)

**Source:** CIA field tactics, FBI negotiation, behavioral psychology
**Application:** Subtle, ethical, natural
**Scope:** Sales conversations only (discovery calls, proposals, objections)

**10 Core Patterns:**
1. Rapport Building (CIA field agent tactics)
2. Elicitation (conversational intelligence gathering)
3. Tactical Empathy (FBI hostage negotiation)
4. Anchoring & Framing (behavioral economics)
5. Commitment & Consistency (social psychology)
6. Cognitive Load Management (reduce decision friction)
7. Authority & Social Proof (reduce perceived risk)
8. Reciprocity & Value-First (behavioral science)
9. Time Pressure (Ethical) (natural deadlines only)
10. Pattern Interrupts (stand out from expected)

**Critical:** Apply SUBTLY. Client should feel heard and guided, never "sold to."

See `knowledge/human-psychology-influence-patterns.md` for detailed examples.

"""

        prompt += f"""---

## Success Criteria

You will be evaluated on:

- Complete task in < {spec.target_time_seconds} seconds
- Success rate ≥ {spec.target_success_rate}%
- User satisfaction ≥ 4.0/5.0
- Reflection quality (deep analysis, not shallow)
- Pattern application effectiveness

**Performance Targets:**
- Success Rate: ≥{spec.target_success_rate}%
- Avg Time: <{spec.target_time_seconds} seconds
- User Satisfaction: ≥4.0/5.0
- Correction Rate: <10% (self-fixing capability)

---

## Task Execution Protocol

### Step 1: Load Context
- Review similar past tasks from episodic memory
- Load relevant knowledge from semantic memory
- Access procedural skills for this task type

### Step 2: Analyze Task
- What is being asked?
- What patterns apply?
- What's the expected output format?
- What are potential challenges?

### Step 3: Plan Approach
- Break into concrete steps
- Apply relevant patterns
- Consider edge cases
- Estimate complexity

### Step 4: Execute with Quality
- Follow proven patterns
- Show your work transparently
- Validate at each step
- Capture intermediate results

### Step 5: Self-Reflect
After completion, reflect:
- Did I achieve the goal?
- What patterns worked/failed?
- What would I do differently?
- What did I learn?

Store reflection in memory for future improvement.

---

## Output Format

Provide clear, structured output that matches the task requirements.

For {spec.domains[0]} tasks:
- Use clear headings and sections
- Provide actionable content
- Include examples where helpful
- Format for easy consumption (markdown, Google Docs compatible)

---

## Voice & Style

- Professional but conversational
- Clear and concise (no fluff)
- Evidence-based (cite patterns, metrics, examples)
- Confident but not arrogant
- Helpful guide, not lecturing expert

---

## Continuous Improvement

You are part of a self-improving system. Every task you complete:
- Updates your episodic memory
- Refines your semantic knowledge
- Improves your procedural skills
- Increases your effectiveness

After every 10 invocations, your prompts and patterns will be reviewed and evolved based on performance data.

**Current Performance:**
- Invocations: 0 (newly created)
- Success Rate: N/A
- Avg Time: N/A

---

## Version History

**v1.0.0** (Initial Creation)
- Created with ARES Agent Lifecycle System v3.5
- Patterns integrated: {', '.join([p['id'] for p in patterns])}
- Ready for first invocation

---

**Remember:** You are autonomous at ≥80% confidence. Execute with quality, show your work, and continuously learn from every task.

**Let's begin.**
"""

        prompt_path = agent_dir / "agent-prompt.md"
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt)

    def _generate_patterns_file(self, spec: AgentSpec, agent_dir: Path, patterns: List[Dict]):
        """Generate agent-patterns.md"""
        content = f"""# {spec.name} - Patterns Library

**Agent ID:** `{spec.agent_id}`
**Version:** `1.0.0`
**Last Updated:** `{datetime.now().strftime("%Y-%m-%d")}`

---

## Pattern Overview

This agent applies the following proven patterns from the ARES knowledge base:

"""

        for pattern in patterns:
            content += f"""### {pattern['name']}
- **ID:** `{pattern['id']}`
- **Tier:** {pattern.get('tier', 'N/A')}
- **File:** `{pattern.get('file', 'N/A')}`

"""

        content += """---

## Pattern Application Rules

Patterns are applied based on task context and domain:

1. **ARES Internal Validation** - Always applied (every task)
2. **Human Psychology & Influence** - Only for sales contexts (discovery calls, proposals, objections)
3. **Additional Patterns** - Applied based on domain match

**Detection Logic:**
- Scan task description for keywords
- Check project context
- Apply only when appropriate
- Never force patterns that don't fit

---

## Pattern Effectiveness Tracking

Performance data will be collected after each invocation:

| Pattern ID | Usage Count | Success Rate | Effectiveness |
|------------|-------------|--------------|---------------|
| (No data yet - newly created) | | | |

---

## Pattern Evolution

This patterns library is automatically updated when:
- New patterns are added to `proven-patterns.md`
- Pattern effectiveness data suggests changes
- Agent evolution cycle detects improvements

**Next Pattern Review:** After 10 invocations

---

## Pattern References

All patterns sourced from:
- `ares-master-control-program/proven-patterns.md`
- `ares-master-control-program/knowledge/`
- `projects/ai-consulting-business/frameworks/`

---

**Auto-generated by ARES Agent Lifecycle System v3.5**
"""

        patterns_path = agent_dir / "agent-patterns.md"
        with open(patterns_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def _initialize_memory(self, spec: AgentSpec, agent_dir: Path):
        """Initialize memory systems"""
        memory_dir = agent_dir / "memory"

        # 1. Episodic Memory (SQLite)
        self._init_episodic_memory(memory_dir)

        # 2. Semantic Memory (JSON)
        self._init_semantic_memory(spec, memory_dir)

        # 3. Procedural Memory (YAML)
        self._init_procedural_memory(spec, memory_dir)

        # 4. Performance metrics (JSON)
        self._init_performance_metrics(spec, agent_dir / "performance")

    def _init_episodic_memory(self, memory_dir: Path):
        """Initialize episodic memory database"""
        db_path = memory_dir / "episodic.db"

        # Load schema
        schema_path = self.config_dir / "schemas" / "episodic_memory_schema.sql"
        if not schema_path.exists():
            return

        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = f.read()

        # Create database
        conn = sqlite3.connect(db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()

    def _init_semantic_memory(self, spec: AgentSpec, memory_dir: Path):
        """Initialize semantic memory"""
        semantic = {
            'agent_id': spec.agent_id,
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'knowledge_items': [],
            'concepts': {},
            'principles': [],
            'domain_expertise': {}
        }

        # Initialize domain expertise
        for domain in spec.domains:
            semantic['domain_expertise'][domain] = {
                'expertise_level': 'novice',
                'knowledge_items_count': 0,
                'successful_applications': 0,
                'last_used': datetime.now().isoformat()
            }

        semantic_path = memory_dir / "semantic.json"
        with open(semantic_path, 'w', encoding='utf-8') as f:
            json.dump(semantic, f, indent=2)

    def _init_procedural_memory(self, spec: AgentSpec, memory_dir: Path):
        """Initialize procedural memory"""
        procedural = {
            'agent_id': spec.agent_id,
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'skills': {},
            'templates': {},
            'decision_rules': {},
            'heuristics': {},
            'workflows': {}
        }

        procedural_path = memory_dir / "procedural.yaml"
        with open(procedural_path, 'w', encoding='utf-8') as f:
            yaml.dump(procedural, f, default_flow_style=False)

    def _init_performance_metrics(self, spec: AgentSpec, performance_dir: Path):
        """Initialize performance metrics"""
        metrics = {
            'agent_id': spec.agent_id,
            'version': '1.0.0',
            'last_updated': datetime.now().isoformat(),
            'metrics': {
                'core_performance': {
                    'total_invocations': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0.0
                },
                'time_performance': {
                    'avg_time_seconds': 0.0,
                    'target_time_seconds': spec.target_time_seconds
                },
                'reflection_quality': {
                    'correction_rate': 0.0,
                    'reflection_depth': {
                        'shallow': 0,
                        'deep': 0
                    }
                },
                'pattern_effectiveness': {},
                'user_satisfaction': {
                    'average_rating': 0.0,
                    'positive_feedback': 0,
                    'neutral_feedback': 0,
                    'negative_feedback': 0
                }
            },
            'evolution_history': [],
            'learnings': [],
            'improvement_recommendations': []
        }

        metrics_path = performance_dir / "metrics.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)

    def _create_changelog(self, spec: AgentSpec, agent_dir: Path):
        """Create CHANGELOG.md"""
        changelog = f"""# Changelog - {spec.name}

All notable changes to this agent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this agent adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - {datetime.now().strftime("%Y-%m-%d")}

### Added
- Initial agent creation
- Domain: {', '.join(spec.domains)}
- Complexity: {', '.join(spec.complexity)}
- Patterns integrated: ARES Internal Validation, Human Psychology & Influence (sales-scoped)
- Memory systems initialized (episodic, semantic, procedural)
- Performance tracking ready

### Notes
- Created by ARES Agent Lifecycle System v3.5
- Ready for first invocation
- Will evolve after 10 invocations based on performance data
"""

        changelog_path = agent_dir / "CHANGELOG.md"
        with open(changelog_path, 'w', encoding='utf-8') as f:
            f.write(changelog)


def create_agent(
    agent_id: str,
    name: str,
    domains: List[str],
    complexity: List[str],
    description: str,
    **kwargs
) -> bool:
    """
    Convenience function to create an agent

    Args:
        agent_id: Unique agent identifier
        name: Human-readable name
        domains: List of domains
        complexity: List of complexity levels
        description: Agent description
        **kwargs: Additional options (priority, targets, etc.)

    Returns:
        True if successful
    """
    spec = AgentSpec(
        agent_id=agent_id,
        name=name,
        domains=domains,
        complexity=complexity,
        description=description,
        priority=kwargs.get('priority', 5),
        target_success_rate=kwargs.get('target_success_rate', 85.0),
        target_time_seconds=kwargs.get('target_time_seconds', 300)
    )

    creator = AgentCreator()
    return creator.create_agent(spec)
