# ARES MCP Server v2.5

**Master Control Program exposing proven patterns as MCP tools**

Transform your Claude Desktop with Riord's battle-tested development patterns, internal validation protocols, and tech success metrics.

---

## What This Does

ARES MCP Server gives Claude Desktop access to:

- **Proven Patterns** from 200+ analyzed files across 4 projects
- **Internal Validation Protocol** (5-step confidence-based execution)
- **Tech Success Matrix** (what works, what doesn't, with metrics)
- **Pattern Recommendations** (best approach for your task)

---

## Quick Start

### 1. Build the Server

```bash
cd ares-mcp-server
npm install
npm run build
```

### 2. Configure Claude Desktop

Add to your Claude Desktop MCP settings (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ares": {
      "command": "node",
      "args": ["C:\\Users\\riord\\ares-mcp-server\\dist\\index.js"]
    }
  }
}
```

### 3. Restart Claude Desktop

The ARES MCP tools will now be available in Claude Desktop.

---

## Available Tools

### `get_proven_patterns`

Retrieve Riord's proven coding patterns by tier.

**Parameters:**
- `tier` (optional): Filter by tier (1=validated, 2=working, 3=experimental)
- `category` (optional): Filter by category (architecture, data, ai, interface, reliability)

**Example:**
```
Get all Tier 1 (validated & proven) patterns
```

**Response:**
```json
[
  {
    "name": "Modular Scraper Architecture",
    "tier": 1,
    "description": "Unified coordinator with specialized scrapers",
    "successRate": "95%",
    "usageCount": 12,
    "evidence": ["ASX Trading AI: 5+ scrapers", "Business Brain: 3+ agents"],
    "tradeOffs": "More files vs easier maintenance (acceptable)"
  },
  ...
]
```

---

### `validate_approach`

Run Ares internal validation protocol on a proposed approach.

**Parameters:**
- `task` (required): What needs to be done
- `proposed_approach` (required): How you plan to do it

**Example:**
```
Task: Build a web scraping system for multiple data sources
Approach: Create a modular architecture with separate scrapers and a central coordinator
```

**Response:**
```markdown
## ARES Validation Result

**Confidence:** HIGH (90%)
**Patterns Matched:** Modular Scraper Architecture
**Decision:** EXECUTE - Show work and proceed autonomously

### Recommended Patterns:
- Modular Scraper Architecture (Tier 1): Unified coordinator with specialized scrapers
  Success Rate: 95%
```

---

### `recommend_pattern`

Get the best proven pattern recommendation for a specific task.

**Parameters:**
- `task` (required): Description of what you want to build

**Example:**
```
I need to build an AI system that works without internet
```

**Response:**
```markdown
## Recommended Pattern: "I need to build an AI system that works without internet"

**Rule-Based + AI Hybrid** (Tier 1)

Rules catch 80%, AI enhances edge cases

**Success Rate:** 90%
**Used:** 8 times

**Evidence:**
- Business Brain: Works without API key
- ASX Trading: Sentiment analysis with fallback
- 90% success rate

**Trade-offs:**
Works offline, explainable, but AI accuracy limited
```

---

### `query_tech_success`

Get success rates and evidence for specific technologies.

**Parameters:**
- `technology` (required): Technology name (e.g., 'python', 'sqlite', 'fastapi')

**Example:**
```
Query tech success for "sqlite"
```

**Response:**
```markdown
## Tech Success: SQLITE

**Success Rate:** 100%
**Usage:** All Python projects

**What Works:**
- File-based storage: No server setup
- Zero configuration
- 10MB database = 100K+ records

**When to Use:**
- POC/MVP development
- Single-user applications
- <1M rows

**When NOT to Use:**
- Multi-user concurrent writes (use PostgreSQL)
- >1M rows with complex queries (use PostgreSQL)
```

---

## How It Works

ARES MCP Server implements the **Internal Validation Protocol** from Ares v2.1:

1. **Challenge:** Is this the best approach? (Evidence check)
2. **Simplify:** Is there a simpler alternative? (Complexity audit)
3. **Validate:** Do we have proven patterns? (Success rate lookup)
4. **Explain:** Can we explain in plain language? (Understanding check)
5. **Confidence:** How certain are we? (≥80% execute, <50% escalate)

**Result:** Confidence-based recommendations with evidence.

---

## Pattern Tier System

- **Tier 1 (⭐⭐⭐):** Validated & Proven (5+ uses, metrics prove success)
- **Tier 2 (⭐⭐):** Working, Needs More Validation (2-4 uses)
- **Tier 3 (⭐):** Experimental (1 use or less)

---

## What Makes This Different

**Not Generic Copilot Suggestions** — These are YOUR proven patterns from YOUR codebase.

**Not Theoretical Best Practices** — These are battle-tested approaches with actual success rates.

**Not One-Size-Fits-All** — Patterns are contextualized to your tech stack, constraints, and preferences.

---

## Example Workflow

1. **You ask Claude:** "Help me build a database-centric workflow automation system"

2. **Claude uses ARES MCP:**
   - Calls `recommend_pattern` → Gets "Database-Centric Architecture" (Tier 1, 100% success)
   - Calls `validate_approach` → Confirms high confidence (90%)
   - Calls `query_tech_success("sqlite")` → Gets SQLite best practices

3. **Claude responds** with YOUR proven patterns, not generic advice

---

## Roadmap

### Phase 0: Foundation ✅ (Complete)
- Core protocols codified (Python library)
- MCP server built (TypeScript)
- Basic tools working

### Phase 1: Simple Meta-Agent (Next - Weeks 2-3)
- Add `decompose_task` tool
- Simple task list generation (not full DAG yet)
- References proven patterns for each subtask

### Phase 2: Orchestration (Weeks 5-8)
- Add LangGraph for parallel execution
- Task graphs (DAGs) for complex workflows
- Validator nodes for quality control

### Phase 3: Self-Improvement (Weeks 9-12)
- Pattern extraction from successful executions
- Auto-promotion (3+ successful uses → Tier 2 → Tier 1)
- Continuous learning

### Phase 4: Replication (Months 3-4)
- Containerization
- Deploy to other users' machines
- Learn THEIR patterns

### Phase 5: SaaS (Months 4-6)
- Multi-tenancy
- Federated learning (privacy-preserving)
- 1000s of users, each with personalized ARES

---

## Development

```bash
# Build
npm run build

# Watch mode (development)
npm run dev

# Start server
npm start
```

---

## Troubleshooting

**ARES tools not showing in Claude Desktop:**
1. Check `claude_desktop_config.json` has correct path
2. Restart Claude Desktop
3. Check logs: `%APPDATA%\Claude\logs\mcp.log`

**Server crashes on startup:**
1. Ensure paths to proven-patterns.md are correct
2. Check `dist/index.js` exists (run `npm run build`)
3. Verify Node.js version (requires Node 18+)

---

## License

MIT

---

**Built with Claude Code** — ARES v2.5 "The Foundation"

*Next: Meta-agent capabilities*
