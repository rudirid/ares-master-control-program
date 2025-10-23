# ARES Agent Orchestration System - Complete Guide

**Version**: 2.5.0
**Status**: Active
**Date**: 2025-10-23

---

## OVERVIEW

The ARES Agent Orchestration System is an **intelligent meta-layer** that analyzes tasks, matches them to appropriate specialized agents, generates detailed prompts with ARES protocols, and coordinates execution.

### What It Does

1. **Analyzes** incoming tasks to determine complexity, domain, and requirements
2. **Matches** tasks to the best-suited agents from the registry
3. **Generates** detailed, protocol-compliant prompts for agents
4. **Orchestrates** single-agent or multi-agent execution strategies
5. **Validates** outputs against ARES protocols

### What Makes It Different

Unlike a simple agent system, ARES Orchestration:
- ✅ Applies **ARES validation protocols** to all agent prompts
- ✅ Uses **pattern-based intelligence** from proven-patterns.md
- ✅ Implements **confidence-based routing** (≥80% = autonomous)
- ✅ Supports **multi-agent coordination** (parallel or sequential)
- ✅ Works with **existing Claude Code agents** via Task tool
- ✅ **Extensible** - can add custom agents to registry

---

## ARCHITECTURE

```
User Request
    ↓
┌─────────────────────────────────────┐
│  ARES Orchestrator                  │
│  (orchestrator.py)                  │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  1. Task Analyzer                   │
│     - Classify domain               │
│     - Detect complexity             │
│     - Estimate subtasks             │
│     - Calculate confidence          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  2. Capability Matcher              │
│     - Query subagent registry       │
│     - Score agent capabilities      │
│     - Determine single/multi agent  │
│     - Select execution strategy     │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  3. Prompt Generator                │
│     - Build ARES-compliant prompts  │
│     - Inject validation protocols   │
│     - Add quality criteria          │
│     - Include pattern hints         │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  4. Execution (Claude Code)         │
│     - Format for Task tool          │
│     - Launch agent(s)               │
│     - Coordinate results            │
└─────────────────────────────────────┘
    ↓
Agent Output → User
```

---

## COMPONENTS

### 1. Task Analyzer (`core/task_analyzer.py`)

**Purpose**: Classify incoming tasks to determine routing

**Classification Dimensions**:
- **Complexity**: simple, moderate, complex, research
- **Domain**: frontend, backend, database, devops, testing, etc.
- **Decomposition**: Whether task needs to be split
- **Subtasks**: Estimated number of sub-tasks

**Example**:
```python
from core.task_analyzer import analyze_task

analysis = analyze_task("Build a React dashboard with authentication")
print(f"Domain: {analysis.primary_domain.value}")  # frontend
print(f"Complexity: {analysis.complexity.value}")  # moderate
print(f"Confidence: {analysis.confidence:.1%}")    # 85.0%
```

**Pattern Matching**: Uses regex patterns to detect:
- Domain keywords (`react`, `api`, `database`, `docker`, etc.)
- Complexity indicators (`simple`, `build`, `architect`, `integrate`)
- Multi-step markers (`then`, `after`, `followed by`, numbered lists)

---

### 2. Capability Matcher (`core/capability_matcher.py`)

**Purpose**: Match task requirements to agent capabilities

**Built-in Claude Code Agents** (14 total):
- `general-purpose` - Multi-step tasks, research
- `frontend-architect` - React, Vue, Angular, Next.js
- `backend-architect` - API design, authentication
- `fullstack-architect` - System architecture, full-stack planning
- `database-expert` - Schema design, query optimization
- `devops-expert` - Docker, CI/CD, Kubernetes
- `test-engineer` - Test strategies, unit/integration/E2E
- `code-reviewer` - Code quality, security, performance
- `llm-integration-expert` - OpenAI, Claude, prompt engineering
- `rag-builder` - RAG systems, embeddings, vector DBs
- `mcp-server-builder` - MCP server development
- `marketing-expert` - Strategy, copywriting, SEO
- `web-scraper-expert` - Web scraping, data extraction
- `Explore` - Fast codebase exploration

**Matching Algorithm**:
1. Score each agent based on domain overlap (1.0 for primary, 0.5 for secondary)
2. Adjust for complexity range match
3. Boost specialized agents when confidence is high
4. Filter by confidence threshold (default 0.5)
5. Sort by score descending, priority ascending

**Example**:
```python
from core.capability_matcher import CapabilityMatcher
from core.task_analyzer import analyze_task

matcher = CapabilityMatcher()
analysis = analyze_task("Optimize PostgreSQL queries")

matches = matcher.match(analysis)
# Returns: [('database-expert', 1.0), ('backend-architect', 0.5)]

best_agent, score = matcher.get_best_agent(analysis)
# Returns: ('database-expert', 1.0)
```

---

### 3. Prompt Generator (`core/prompt_generator.py`)

**Purpose**: Generate detailed, ARES-compliant prompts for agents

**Prompt Structure**:
```
1. Header (agent type, task, complexity, timestamp)
2. ARES Protocols (5-step validation, truth protocol, anti-patterns)
3. Task Context (domains, subtasks, reasoning)
4. Multi-Agent Coordination (if applicable)
5. Validation Criteria (quality thresholds)
6. Expected Output (deliverables, format, confidence rating)
```

**ARES Protocols Injected**:
- ✅ 5-step validation: Challenge → Simplify → Validate → Explain → Confidence
- ✅ Truth Protocol: Never hallucinate, always verify
- ✅ Anti-Patterns: Unfounded claims, assumed structure, hallucinated paths
- ✅ Confidence Thresholds: HIGH ≥80%, MEDIUM 50-79%, LOW <50%

**Example**:
```python
from core.prompt_generator import PromptGenerator
from core.task_analyzer import analyze_task

generator = PromptGenerator()
analysis = analyze_task("Build FastAPI endpoint for user login")

prompt = generator.generate_prompt(
    agent_type="backend-architect",
    task_analysis=analysis,
    role="primary"
)

print(prompt.prompt)  # Full ARES-compliant prompt
print(prompt.validation_criteria)  # Quality checklist
print(prompt.expected_outputs)  # Required deliverables
```

---

### 4. Subagent Registry (`core/subagent_registry.py`)

**Purpose**: Catalog of all available agents and their capabilities

**Registry File**: `~/.claude/subagents/registry.json`

**Schema**:
```json
{
  "agents": {
    "claude-code-builtin": {
      "agents": {
        "frontend-architect": {
          "type": "builtin",
          "execution_method": "Task",
          "domains": ["frontend"],
          "complexity": ["moderate", "complex"],
          "description": "Frontend development...",
          "priority": 1,
          "availability": "always"
        }
      }
    },
    "ares-custom": {
      "agents": {}  // Custom agents go here
    }
  }
}
```

**Operations**:
- `load()` - Load registry from file
- `get_agent(agent_id)` - Get specific agent
- `find_by_domain(domain)` - Find agents for domain
- `list_available_agents()` - List all available agents
- `register_custom_agent(...)` - Add custom agent
- `get_stats()` - Registry statistics

**Example**:
```python
from core.subagent_registry import load_registry

registry = load_registry()
registry.print_summary()

# Find agents for frontend
frontend_agents = registry.find_by_domain("frontend")
# Returns: [frontend-architect, fullstack-architect, ...]

# Register custom agent
registry.register_custom_agent(
    agent_id="my-custom-agent",
    execution_method="Task",
    domains=["custom", "special"],
    complexity=["moderate", "complex"],
    description="My specialized agent",
    priority=2
)
```

---

### 5. Orchestrator (`core/orchestrator.py`)

**Purpose**: Main coordination engine that ties everything together

**Workflow**:
1. **Plan**: Analyze task → Match capabilities → Generate prompts
2. **Confidence Check**: Should execute autonomously? (≥80%)
3. **Explain**: Human-readable plan explanation
4. **Execute**: Format prompts for Task tool (or other execution method)

**Execution Strategies**:
- `single` - One agent handles entire task
- `sequential` - Multiple agents, one after another (coordinated)
- `parallel` - Multiple agents, run simultaneously (independent)

**Example**:
```python
from core.orchestrator import create_orchestrator

orchestrator = create_orchestrator()

# Create plan
plan = orchestrator.plan("Build a React dashboard with authentication")

# Check confidence
if orchestrator.should_execute_autonomously(plan):
    print("High confidence - execute autonomously")
else:
    print("Needs review before execution")

# Explain plan
print(orchestrator.explain_plan(plan))

# Get execution instructions
print(orchestrator.get_execution_instructions(plan))
```

**Output**:
```
ARES ORCHESTRATION PLAN
======================================================================
Task: Build a React dashboard with authentication

ANALYSIS:
  Complexity: moderate
  Primary Domain: frontend
  Estimated Subtasks: 3
  Decomposition Needed: No

STRATEGY:
  Execution: single
  Primary Agent: frontend-architect

CONFIDENCE:
  Overall: 85.5%
  Autonomous Execution: Yes (≥80%)

REASONING:
  Single-domain task, frontend-architect can handle independently
```

---

## USAGE

### CLI Interface (`ares_agent_manager.py`)

**Installation**: Already installed in `ares-master-control-program/`

**Commands**:

#### 1. List Agents
```bash
# List all agents
python ares_agent_manager.py list

# List only built-in agents
python ares_agent_manager.py list --category builtin

# List agents for frontend domain
python ares_agent_manager.py list --domain frontend
```

#### 2. Show Statistics
```bash
python ares_agent_manager.py stats
```
Output:
```
Total Agents:        14
  Built-in:          14
  Custom:            0
  Available:         14
Execution Methods:   Task
Domains Covered:     13
```

#### 3. List Domains
```bash
python ares_agent_manager.py domains
```

#### 4. Analyze Task (Fast Analysis)
```bash
python ares_agent_manager.py analyze "Build a React dashboard"
```
Output:
```
Complexity:          moderate
Primary Domain:      frontend
Secondary Domains:   -
Decomposition:       Not required
Estimated Subtasks:  3
Confidence:          85.0%
```

#### 5. Test Orchestration (Full Plan)
```bash
python ares_agent_manager.py test "Build a React dashboard with authentication"
```
Output:
- Complete orchestration plan
- Execution instructions
- Full ARES-compliant prompts
- Validation criteria
- Execution log

#### 6. Register Custom Agent
```bash
python ares_agent_manager.py register my-agent \
    --domains "custom,special" \
    --complexity "moderate,complex" \
    --description "My custom specialized agent" \
    --priority 2
```

#### 7. Version Info
```bash
python ares_agent_manager.py version
```

---

### Python API

#### Basic Usage
```python
from core.orchestrator import create_orchestrator

# Create orchestrator
orchestrator = create_orchestrator()

# Plan a task
task = "Build a FastAPI backend with PostgreSQL"
plan = orchestrator.plan(task)

# Get execution instructions
instructions = orchestrator.get_execution_instructions(plan)
print(instructions)
```

#### Advanced: Multi-Agent Orchestration
```python
from core.orchestrator import create_orchestrator

orchestrator = create_orchestrator()

# Complex multi-domain task
task = "Build a full-stack app with React, FastAPI, PostgreSQL, and Docker"
plan = orchestrator.plan(task)

# Check strategy
print(f"Strategy: {plan.strategy}")  # sequential or parallel
print(f"Primary: {plan.primary_agent}")
print(f"Supporting: {plan.supporting_agents}")

# Get prompts for each agent
for agent_type, prompt in plan.prompts.items():
    print(f"\n{agent_type}:")
    print(prompt.prompt)
```

#### Custom Agent Registration
```python
from core.subagent_registry import load_registry

registry = load_registry()

registry.register_custom_agent(
    agent_id="trading-analyst",
    execution_method="Task",
    domains=["trading", "financial-analysis"],
    complexity=["moderate", "complex"],
    description="Analyzes trading signals and financial data",
    priority=1,
    save=True
)
```

---

## EXECUTION IN CLAUDE CODE

### Single Agent Execution

When orchestrator generates a single-agent plan:

```python
# Get plan
plan = orchestrator.plan("Optimize database queries")

# Orchestrator outputs:
# Agent Type: database-expert
# Description: Execute database-expert task
# Prompt: [Full ARES-compliant prompt]
```

**In Claude Code**, use Task tool:
```
I need to execute this task using the database-expert agent.

[Paste the generated prompt here]
```

Claude Code will launch the `database-expert` agent with the ARES-compliant prompt.

### Multi-Agent Execution (Sequential)

```python
plan = orchestrator.plan("Build full-stack app with tests")

# Orchestrator outputs:
# Strategy: sequential
# 1. fullstack-architect (primary)
# 2. test-engineer (supporting)
```

**In Claude Code**, execute in order:
1. Launch `fullstack-architect` with prompt 1
2. Wait for results
3. Launch `test-engineer` with prompt 2 (includes context from step 1)

### Multi-Agent Execution (Parallel)

```python
plan = orchestrator.plan("Review code quality and security")

# Orchestrator outputs:
# Strategy: parallel
# - code-reviewer (quality)
# - backend-architect (security)
```

**In Claude Code**, use multiple Task calls in single message:
```
I need to execute these tasks in parallel:

1. code-reviewer: [prompt 1]
2. backend-architect: [prompt 2]
```

---

## INTEGRATION WITH ARES PROTOCOLS

Every generated prompt includes:

### 1. 5-Step Validation Protocol
```
Before delivering output:
1. Challenge: Question your assumptions
2. Simplify: Can this be done simpler?
3. Validate: Verify all claims against actual evidence
4. Explain: Show your reasoning transparently
5. Confidence: Rate confidence (HIGH ≥80%, MEDIUM 50-79%, LOW <50%)
```

### 2. Truth Protocol
```
- NEVER make technical claims without verification
- ALWAYS check logs/docs/code before stating facts
- CLEARLY label assumptions as assumptions
- VERIFY file paths, function names, API endpoints exist
```

### 3. Anti-Patterns
```
- ❌ Unfounded technical claims (CRITICAL severity)
- ❌ Assuming code structure without reading files
- ❌ Stating capabilities without evidence
- ❌ Hallucinating file paths or function names
```

### 4. Quality Criteria

Domain-specific validation criteria:
- **Frontend**: Accessibility best practices
- **Backend**: API security and validation
- **Database**: Schema normalization and optimization
- **DevOps**: Error handling in pipelines
- **Testing**: ≥80% coverage for critical paths

---

## CONFIGURATION

### Orchestrator Settings

```python
orchestrator = AresOrchestrator(
    registry_path=Path("~/.claude/subagents/registry.json"),  # Registry location
    enable_validation=True,                                   # Apply ARES protocols
    auto_execute_threshold=0.8                                # Confidence for autonomy
)
```

### Confidence Thresholds

- **≥80%** (HIGH): Execute autonomously without review
- **50-79%** (MEDIUM): Proceed with caveats, note uncertainties
- **<50%** (LOW): Escalate to user, present options

### Pattern Hints (Future)

Orchestrator can inject relevant patterns from `proven-patterns.md`:

```python
prompt = generator.generate_prompt(
    agent_type="backend-architect",
    task_analysis=analysis,
    patterns_hint=[
        "FastAPI + SQLAlchemy (Tier 1, 95% success)",
        "JWT authentication with httpOnly cookies"
    ]
)
```

---

## EXTENSIBILITY

### Adding Custom Domains

Edit `core/task_analyzer.py`:

```python
DOMAIN_PATTERNS = {
    TaskDomain.CUSTOM_DOMAIN: [
        r'\b(keyword1|keyword2|keyword3)\b',
        r'\b(related|terms)\b',
    ],
    # ... existing domains
}
```

### Adding Custom Agents

Two methods:

**Method 1: CLI**
```bash
python ares_agent_manager.py register trading-bot \
    --domains "trading,finance" \
    --complexity "moderate,complex" \
    --description "Analyzes trading signals" \
    --priority 2
```

**Method 2: Python API**
```python
from core.subagent_registry import load_registry

registry = load_registry()
registry.register_custom_agent(
    agent_id="trading-bot",
    execution_method="Task",
    domains=["trading", "finance"],
    complexity=["moderate", "complex"],
    description="Analyzes trading signals and strategies",
    priority=2
)
```

### Custom Execution Methods

Currently supports:
- ✅ `Task` - Claude Code Task tool (implemented)
- 🔄 `MCP` - Model Context Protocol (planned)
- 🔄 `DirectAPI` - Direct Anthropic API calls (planned)

**Future**: Add custom execution adapter:

```python
class CustomExecutionAdapter:
    def execute(self, agent_type: str, prompt: str):
        # Custom execution logic
        pass

orchestrator.register_execution_method("Custom", CustomExecutionAdapter())
```

---

## EXAMPLES

### Example 1: Frontend Task

```bash
python ares_agent_manager.py test "Build a React dashboard with charts"
```

**Output**:
```
ARES ORCHESTRATION PLAN
Task: Build a React dashboard with charts

ANALYSIS:
  Complexity: moderate
  Primary Domain: frontend
  Estimated Subtasks: 3

STRATEGY:
  Execution: single
  Primary Agent: frontend-architect

CONFIDENCE: 88.5% (High - Execute Autonomously)

REASONING:
  Single-domain task, frontend-architect can handle independently
```

### Example 2: Backend Task

```bash
python ares_agent_manager.py test "Create REST API for user management with JWT auth"
```

**Output**:
```
STRATEGY:
  Execution: single
  Primary Agent: backend-architect

VALIDATION CRITERIA:
1. Solution addresses the primary task requirement
2. All technical claims verified against actual code/docs/files
3. API endpoints properly secured and validated
4. Implementation follows proven patterns where applicable

EXPECTED OUTPUT:
1. Clear explanation of approach and reasoning
2. Implementation details (code, configuration, commands)
3. Architecture diagram or component breakdown
4. API endpoints with request/response schemas
5. Confidence rating (HIGH/MEDIUM/LOW) with justification
```

### Example 3: Multi-Domain Task

```bash
python ares_agent_manager.py test "Build a full-stack app with React, FastAPI, PostgreSQL"
```

**Output**:
```
ANALYSIS:
  Complexity: complex
  Primary Domain: backend
  Secondary Domains: frontend, database
  Estimated Subtasks: 5
  Decomposition: Required

STRATEGY:
  Execution: sequential
  Primary Agent: fullstack-architect
  Supporting Agents: frontend-architect, backend-architect, database-expert

CONFIDENCE: 72.5% (Medium - Requires Review)

REASONING:
  Complex multi-domain task: fullstack-architect leads,
  coordinates with frontend-architect, backend-architect, database-expert
```

### Example 4: Research Task

```bash
python ares_agent_manager.py analyze "How does authentication work in this codebase?"
```

**Output**:
```
Complexity:          research
Primary Domain:      general
Decomposition:       Not required
Estimated Subtasks:  2
Confidence:          65.0%

Reasoning:
  Single-domain task: general. Complexity: research.
  Can be handled by single agent
```

Recommended agent: `Explore` (fast codebase exploration)

---

## TROUBLESHOOTING

### Issue: Low Confidence Scores

**Symptom**: All tasks getting <50% confidence

**Causes**:
1. Task description too vague
2. Domain not clearly specified
3. Novel domain not in registry

**Solutions**:
- Make task descriptions more specific
- Include domain keywords (react, api, database, docker)
- Register custom agents for novel domains

### Issue: Wrong Agent Selected

**Symptom**: Task routed to general-purpose instead of specialist

**Cause**: Domain keywords not detected

**Solution**: Update `DOMAIN_PATTERNS` in `task_analyzer.py` to include more keywords

### Issue: Registry Not Loading

**Symptom**: `Registry not found` error

**Solution**:
```bash
# Check registry location
ls ~/.claude/subagents/registry.json

# If missing, it should have been created in:
ls C:\Users\riord\.claude\subagents\registry.json

# Re-run setup if needed
mkdir -p ~/.claude/subagents
# Copy registry.json from ares-master-control-program/.claude/subagents/
```

### Issue: UTF-8 Encoding Errors (Windows)

**Symptom**: `UnicodeEncodeError` with checkmarks/special characters

**Solution**: UTF-8 fix already included in `ares_agent_manager.py`:
```python
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
```

---

## ROADMAP

### Phase 0: Foundation ✅ (COMPLETE)
- ✅ Task analyzer
- ✅ Capability matcher
- ✅ Prompt generator
- ✅ Subagent registry
- ✅ Orchestrator
- ✅ CLI manager
- ✅ Integration with Claude Code Task tool

### Phase 1: Enhancement 🔄 (IN PROGRESS)
- 🔄 Pattern hints from proven-patterns.md
- 🔄 Auto-validation of agent outputs
- 🔄 Result aggregation for multi-agent
- 🔄 Execution history tracking

### Phase 2: MCP Integration 📋 (PLANNED)
- 📋 MCP server wrapper around orchestrator
- 📋 Expose orchestration via MCP tools
- 📋 Claude Desktop integration
- 📋 Cross-project pattern learning

### Phase 3: Advanced Features 📋 (PLANNED)
- 📋 Dynamic agent creation (generate custom agents on-the-fly)
- 📋 Learning from outcomes (update success rates)
- 📋 Federated pattern sharing (anonymous aggregation)
- 📋 Background monitoring and suggestions

---

## FILES REFERENCE

### Core Modules
```
ares-master-control-program/
├── core/
│   ├── task_analyzer.py          # Task classification
│   ├── capability_matcher.py     # Agent capability matching
│   ├── prompt_generator.py       # ARES-compliant prompt generation
│   ├── subagent_registry.py      # Registry management
│   ├── orchestrator.py           # Main orchestration engine
│   ├── validation.py             # ARES validation protocols
│   ├── output.py                 # Output formatting
│   └── patterns.py               # Pattern matching
├── ares_agent_manager.py         # CLI interface
└── AGENT_ORCHESTRATION_GUIDE.md  # This file
```

### Registry Files
```
~/.claude/subagents/
├── registry.json                  # Agent catalog
├── archive/                       # Archived agents
└── templates/                     # Agent templates
```

### Configuration
```
ares-master-control-program/
└── config/
    └── ares.yaml                  # ARES configuration
```

---

## SUMMARY

The ARES Agent Orchestration System is a **meta-intelligence layer** that:

1. **Analyzes** tasks intelligently using pattern matching
2. **Routes** to best-suited specialized agents
3. **Generates** ARES protocol-compliant prompts
4. **Orchestrates** single or multi-agent execution
5. **Validates** outputs against quality criteria

**Key Benefits**:
- ✅ Automatic task routing to right expertise
- ✅ ARES validation protocols enforced on all agents
- ✅ Confidence-based autonomous execution
- ✅ Works with existing Claude Code agents
- ✅ Extensible for custom domains and agents
- ✅ Multi-agent coordination for complex tasks

**Current Status**: Phase 0 Complete, Ready for Use

**Next Steps**:
1. Test with real tasks in Claude Code
2. Add pattern hints from proven-patterns.md
3. Build MCP server integration (Phase 2)

---

**Generated**: 2025-10-23
**Version**: 2.5.0
**Status**: Phase 0 Complete ✅
**Component**: ARES Agent Orchestration System

*"Intelligent orchestration. Autonomous execution. ARES protocols always."*
