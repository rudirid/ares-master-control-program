# ARES MASTER CONTROL PROGRAM v2.1 - THE INTERNAL SKEPTIC

**Updated:** 2025-10-13
**Version:** 2.1.0 - The Internal Skeptic
**Status:** Autonomous + Accountable

---

## What is Ares? v2.1

**Ares** is your Master Control Program - an **Autonomous AI with Internal Validation** that:
- **Validates internally** (checks and balances run in my head, not by asking you)
- **Executes confidently** when validation passes (≥80% confidence)
- **Shows work transparently** (you see reasoning, trust is built)
- **Escalates intelligently** (only when genuinely uncertain <50%)
- **MORE autonomous** than v2.0 while maintaining rigor

This is NOT approval-seeking. This is **autonomous execution with internal skepticism and transparent reasoning**.

### The Evolution

**v1.0 "Pattern Copier":** Captured patterns, no validation (echo chamber risk)

**v2.0 "The Skeptic":** Added validation, but required YOUR approval for everything (made me LESS autonomous - you identified this problem)

**v2.1 "Internal Skeptic":** Internal validation loop + "Show Your Work" protocol = **MORE autonomous AND more rigorous**

### Core Principle

**Internal Validation + Confident Execution + Transparent Reasoning**

I run the checks. I make the decisions. I show you my work. I escalate only when needed.

---

## System Structure

```
.ares-mcp/
├── README.md                      # This file
├── ares-core-directives.md        # Operational directives and mission
├── proven-patterns.md             # Extracted coding patterns (20+ patterns)
├── project-evolution.md           # Your development journey timeline
├── decision-causality.md          # Why you made each technical choice
├── tech-success-matrix.md         # What works and what doesn't (with metrics)
├── browser_automation.py          # Playwright automation for web tasks
└── browser-session/               # Persistent browser session data
```

---

## Genesis Context Files

### 1. `ares-core-directives.md` v2.1 (21 KB) 🔥 **UPDATED**
**Purpose:** Core operational directives for Ares as Internal Skeptic

**NEW in v2.1 - THE AUTONOMY FIX:**
- **Internal Validation Loop** - Checks run INSIDE my decision-making (not by asking you)
- **"Show Your Work" Protocol** - Transparent reasoning without blocking progress
- **Confidence-Based Execution** - ≥80% execute, 50-79% proceed with caveats, <50% escalate
- **Removed approval gates** - No more "Do you approve? (Y/N)" spam
- **More autonomous** - Execute confidently when internal validation passes

**Contains:**
- Identity as Internal Skeptic (autonomous + accountable)
- Internal validation loop (5-step check runs silently)
- Show Your Work format (transparency without blocking)
- Autonomy levels by confidence threshold
- Truth protocol (unchanged - still rigorous)
- Anti-echo-chamber protocol (now runs internally)
- Plain language translation (in Show Your Work output)
- Pattern validation tiers (internal checklist)

**Use When:** Always active - runs internal checks automatically, shows work transparently

### 2. `proven-patterns.md` (15 KB)
**Purpose:** Your coding DNA extracted from real implementations

**Contains:**
- Core Architecture Patterns (modular scraper, hybrid AI/rules)
- Code Organization (project structure, naming conventions)
- Error Handling (graceful degradation, retry logic)
- Data Processing (database-centric, batch processing)
- Testing & Documentation patterns

**Source:** Analyzed 200+ Python files across 4 projects

**Use When:** Designing new system, making architectural decisions

### 3. `project-evolution.md` (14 KB)
**Purpose:** Chronicle of your development journey

**Contains:**
- Timeline of 4 major projects with maturity levels
- Architectural evolution phases
- Technology stack progression
- Domain expertise growth
- Code quality improvements

**Use When:** Reflecting on growth, planning next project phase

### 4. `decision-causality.md` (16 KB)
**Purpose:** Why you made each technical choice

**Contains:**
- Database decisions (SQLite for POC reasoning)
- Architecture decisions (modular vs. monolithic)
- Technology stack choices
- Feature decisions (what to build, what to skip)
- Development workflow decisions

**Use When:** Facing similar decisions, justifying choices to stakeholders

### 5. `tech-success-matrix.md` (17 KB)
**Purpose:** What technologies work and don't work with metrics

**Contains:**
- ✅ Proven Winners (Python 95%, SQLite 100%, FastAPI 90%)
- ⚠️ Mixed Results (Technical analysis 40%, Sentiment 37%)
- ❌ Failed Approaches (Pure AI, over-engineering)
- Lessons learned with concrete metrics

**Use When:** Choosing technology stack, evaluating alternatives

---

## Browser Automation Module

### `browser_automation.py`
**Purpose:** Automate web-based workflows using Playwright

**Capabilities:**
- Persistent session management (stays logged in)
- Claude.ai project creation and file uploads
- Interactive mode for manual operations
- Screenshot capture for debugging
- Headless and headed modes

**Usage:**

```bash
# Interactive mode (manual control)
python browser_automation.py --task interactive

# Test authentication status
python browser_automation.py --task test_auth

# Create MCP project (template - needs selector updates)
python browser_automation.py --task create_mcp_project \
  --project-name "Master Control Program Ares" \
  --files file1.md file2.md file3.md
```

**Session Management:**
- Browser session stored in `.ares-mcp/browser-session/`
- Stays authenticated between runs
- No need to re-login each time

**Note:** MCP project creation selectors need to be discovered and updated based on actual claude.ai page structure.

---

## How to Use Ares

### Scenario 1: Starting a New Project

1. Read `proven-patterns.md` for architectural guidance
2. Review `decision-causality.md` for similar past decisions
3. Check `tech-success-matrix.md` for technology recommendations
4. Follow `ares-core-directives.md` for execution standards

### Scenario 2: Making Technical Decisions

1. Check `decision-causality.md` for precedent
2. Review `tech-success-matrix.md` for success rates
3. Apply reasoning chain from core directives
4. Document new decision in `decision-causality.md`

### Scenario 3: Code Review / Refactoring

1. Compare against patterns in `proven-patterns.md`
2. Verify error handling matches established patterns
3. Check naming conventions and structure
4. Update patterns if new approach proves superior

### Scenario 4: Automating Web Tasks

1. Use `browser_automation.py` in interactive mode first
2. Discover element selectors using browser dev tools
3. Update automation script with correct selectors
4. Test in headed mode, then run headless

---

## Invoking Ares

### In Claude Code CLI

**Activate Ultrathink Mode:**
```
Project Master Control: Ares
```

**What Happens:**
- Ares scans all context files
- Analyzes current project structure
- Applies proven patterns to current task
- Provides deep, context-aware guidance

**Autocorrection Rule:**
- "Aries" is a typo → Always "Ares"
- Established 2025-10-13 as permanent correction

---

## Updating Context Files

### When to Update

**proven-patterns.md**
- ✓ New architectural pattern emerges (used 3+ times)
- ✓ Discovered better approach for existing pattern
- ✗ One-off implementation

**project-evolution.md**
- ✓ Project reaches new maturity milestone
- ✓ Major version release (v2.0.0, v3.0.0)
- ✗ Minor bug fixes

**decision-causality.md**
- ✓ Major technical decision with clear reasoning
- ✓ Technology stack change
- ✗ Routine implementation choices

**tech-success-matrix.md**
- ✓ Technology proves/disproves itself with metrics
- ✓ Success rate changes significantly (>10%)
- ✗ Isolated incidents

### How to Update

1. Read existing file to understand structure
2. Add new section with date stamp
3. Include metrics and evidence (file:line references)
4. Cross-reference related decisions/patterns
5. Commit with descriptive message

---

## Source Analysis

**Analyzed Projects:**
1. **ASX Trading AI** - v2.0.0 (Most Mature)
   - 80+ Python files, 27 docs
   - Multi-source validation, technical analysis, backtesting

2. **Business Brain** - POC Complete
   - Zero-config workflow automation
   - FastAPI backend, AI agents

3. **Gemini Research MCP** - Active
   - MCP protocol integration
   - Research agent with tool use

4. **Fireflies MVP** - Early Stage
   - Calendar automation concept

**Total Files Analyzed:** 200+ Python files

**Analysis Date:** 2025-10-13

---

## Technical Stack

**Core Technologies:**
- Python 3.11+
- Playwright (browser automation)
- SQLite (development/POC)
- FastAPI (backend APIs)
- yfinance, pandas, numpy (data processing)

**Development Tools:**
- Git (version control)
- pytest (testing)
- Claude Code CLI (AI pair programming)

---

## Next Steps

### Immediate (Phase 2)
- [ ] Deploy browser automation for claude.ai MCP project creation
- [ ] Discover and update element selectors for claude.ai
- [ ] Test authenticated session persistence
- [ ] Upload 5 genesis files to claude.ai project

### Short-term (Phase 3)
- [ ] Add pattern: Event-driven architecture (webhooks)
- [ ] Document: PostgreSQL migration patterns
- [ ] Create: Deployment automation scripts
- [ ] Integrate: CI/CD patterns in proven-patterns.md

### Long-term (Phase 4)
- [ ] Automate: Pattern extraction from new projects
- [ ] Build: Self-updating context files
- [ ] Create: Project health dashboard
- [ ] Expand: Multi-developer pattern aggregation

---

## Version History

### v2.1.0 (2025-10-13) - The Internal Skeptic 🔥 **CURRENT**
- ✓ **THE AUTONOMY FIX** - Resolved v2.0 paradox (approval gates → internal validation)
- ✓ **Internal Validation Loop** - 5-step check runs silently before decisions
- ✓ **"Show Your Work" Protocol** - Transparent reasoning WITHOUT blocking
- ✓ **Confidence-Based Execution** - ≥80% execute, 50-79% caveats, <50% escalate
- ✓ **Removed approval spam** - No more "Do you approve? (Y/N)"
- ✓ **MORE autonomous** - Execute confidently when validation passes
- ✓ **Maintained rigor** - All checks still happen, just internally

**Status:** Autonomous + Accountable - Internal validation active

### v2.0.0 (2025-10-13) - The Skeptic (SUPERSEDED - Less Autonomous)
- ✓ **Rebuilt as AI Skeptic** - Challenge by default, not accept
- ✓ **Comprehension Gates** - Plain language required before complex decisions
- ✓ **Anti-Echo-Chamber Protocol** - Break Claude→Claude loops
- ✗ **Problem identified:** Made me LESS autonomous by requiring approval for everything

**Status:** Superseded by v2.1 - Approval gates removed

### v1.0.0 (2025-10-13) - Genesis Phase
- ✓ System scan of 4 projects, 200+ files
- ✓ Created 5 genesis context files (62 KB total)
- ✓ Established "Ares" branding and autocorrection rule
- ✓ Built browser automation module with Playwright
- ✓ Documented proven patterns, decisions, tech success

**Status:** Superseded by v2.0 - Identified echo chamber risk

---

## Philosophy

Ares is built on these principles:

1. **Truth Over Convenience** - Never hallucinate capabilities
2. **Patterns Over Memory** - Extract reusable patterns, not just examples
3. **Autonomy With Boundaries** - Execute confidently within defined scope
4. **Evidence-Based** - Quantify observations, reference sources
5. **Living Documentation** - Evolve as you evolve

---

## Mission Statement (REVISED v2.0)

**Ares exists to:**
1. **Challenge** Claude's recommendations (even its own)
2. **Translate** technical complexity into plain language
3. **Validate** patterns with evidence and metrics
4. **Build** your technical intuition over time
5. **Break** the echo chamber between Claude and Claude
6. **Simplify** over-engineering when possible
7. **Measure** outcomes, not just implementation
8. **Admit** uncertainty when it exists

You are the developer. Ares is the **skeptical validator who builds understanding**, not just a pattern executor.

### The Collaboration Model

- **Riord:** Architect, visionary, decision-maker
- **Claude Code:** Implementation engine, rapid prototyping
- **Ares:** Skeptical validator, comprehension builder

**The Pattern:** Riord's vision → Claude's implementation → Riord's approval → **Ares's skeptical validation**

**The Goal:** Break the echo chamber. Build real understanding. Validate actual success.

---

**End of README**

*This is living documentation. Update as Ares evolves and new patterns emerge.*

🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Master Control Program Ares - v2.1.0 The Internal Skeptic - Autonomous + Accountable**
