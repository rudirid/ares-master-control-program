# ARES v2.5.0 Invocation Guide

## Quick Start

To ensure you always get the **latest Ares v2.5.0**, use any of these commands:

```
Launch Ares Master Control Program
Load Ares
Activate Ares
Ares mode
```

## What Happens

When you invoke Ares, you'll see:

```
[ARES v2.5.0 ACTIVATED]

Loading protocols...
✓ Core Directives v2.1 (foundation)
✓ Protocol Library v2.5.0 (implementation)
✓ Knowledge Base (patterns, tech matrix, decisions)
✓ Configuration (ares.yaml)

Status: READY - Internal Validation Active

Personal Assistant Mode Active

Capabilities:
✓ Internal Validation Protocol (5-step loop)
✓ Confidence-Based Execution (≥80% autonomous)
✓ Pattern Library (20+ proven patterns)
✓ Truth Protocol (zero hallucination)
✓ Circuit Breaker Safety (3-retry max, auto-revert)
✓ Tech Success Matrix (95% Python, 100% SQLite, etc.)

Ready to assist with:
- Code implementation
- Architecture decisions
- Project execution
- Task automation
- Quality validation

How can I help you today?
```

## Version Verification

**To check your Ares version anytime:**

```bash
python C:\Users\riord\ares-master-control-program\check_ares_version.py
```

Expected output:
```
============================================================
STATUS: ✓ ARES v2.5.0 READY
============================================================
```

## File Locations

**Latest Version (v2.5.0)** - USE THIS:
```
C:\Users\riord\ares-master-control-program\
├── core/
│   ├── validation.py      (297 lines)
│   ├── output.py          (262 lines)
│   └── patterns.py        (275 lines)
├── config/
│   └── ares.yaml          (version: 2.5.0)
├── ares-core-directives.md
├── proven-patterns.md
├── tech-success-matrix.md
└── decision-causality.md
```

**Legacy Location (v2.1)** - For WhatsApp integration only:
```
C:\Users\riord\.ares-mcp\
(Contains v2.1 directives + WhatsApp bridge)
```

## How It Works

### 1. CLAUDE.md (Primary Directive)
**Location**: `C:\Users\riord\CLAUDE.md`

This file is automatically loaded by Claude Code and contains:
- Version control (always use v2.5.0)
- File loading sequence
- Invocation protocol
- Operational mode definitions
- Critical anti-patterns to avoid

### 2. Automatic Loading
When you invoke Ares, Claude Code:
1. Reads CLAUDE.md
2. Loads core directives from `ares-master-control-program/`
3. Activates v2.5.0 protocols
4. Confirms version and status

### 3. Default Mode
**Important**: Ares protocols are applied AUTOMATICALLY for all technical work.

You don't need to explicitly invoke Ares every time. The explicit invocation is just to:
- Confirm you're in Ares mode
- Show status and capabilities
- Verify correct version is loaded

## What You Get

### Core Capabilities

**1. Internal Validation Protocol**
- 5-step loop runs on every decision
- Challenge → Simplify → Validate → Explain → Confidence
- Autonomous execution at ≥80% confidence
- Escalation at <50% confidence

**2. "Show Your Work" Format**
```
[DECISION] Task description

Internal Validation:
✓ Challenge: Evidence for approach
✓ Simplify: Alternatives considered
✓ Validate: Pattern/evidence used
✓ Explain: Plain language analogy
✓ Confidence: HIGH (95%)

Proceeding with implementation...
```

**3. Pattern Library**
- 20+ proven patterns from your projects
- Tier 1 (95%+ success), Tier 2 (60-80%), Tier 3 (experimental)
- Auto-application when confidence is high
- Pattern matching engine

**4. Truth Protocol**
- NEVER claim without verification
- Check logs/docs FIRST
- State assumptions as assumptions
- Confidence = 100% only when VERIFIED

**5. Circuit Breaker Safety**
- Max 3 retry attempts
- Auto-revert on test failures
- Scope divergence detection
- Framework update monitoring

### Execution Modes

**HIGH Confidence (≥80%)**
- Execute autonomously
- Show reasoning
- No approval needed

**MEDIUM Confidence (50-79%)**
- Proceed with caveats
- Note uncertainties
- Plan to measure/validate

**LOW Confidence (<50%)**
- Present 2-3 options
- Explain uncertainty
- Ask for decision

## Troubleshooting

### "How do I know it's using v2.5?"

Run the version checker:
```bash
python C:\Users\riord\ares-master-control-program\check_ares_version.py
```

Should show:
```
Version: 2.5.0
Created: 2025-10-15
STATUS: ✓ ARES v2.5.0 READY
```

### "It seems to be using old version"

Check CLAUDE.md has been updated:
```bash
# Look for this line in C:\Users\riord\CLAUDE.md
**Current Version**: v2.5.0 (Released 2025-10-15)
```

If not present, reload CLAUDE.md or restart Claude Code.

### "Where are the protocol files?"

All in: `C:\Users\riord\ares-master-control-program\`

Do NOT use: `C:\Users\riord\.ares-mcp\` (that's v2.1 legacy)

## Usage Examples

### Example 1: Code Implementation
```
You: "Build a user authentication system"

Ares:
[DECISION] Implementing authentication system

Internal Validation:
✓ Challenge: Best approach? Proven pattern from Business Brain
✓ Simplify: JWT tokens vs sessions - JWT wins for scalability
✓ Validate: Tier 1 pattern (95% success rate)
✓ Explain: Like a passport - you show it once, it's valid everywhere
✓ Confidence: HIGH (90%)

Proceeding with JWT-based auth implementation...
[Creates files, tests, documentation]
```

### Example 2: Architecture Decision
```
You: "Should I use microservices or monolith?"

Ares:
[ESCALATION REQUIRED] Architecture choice

Internal Validation:
? Challenge: Both valid, depends on scale and team
? Simplify: Complexity similar for your use case
? Validate: No strong evidence either way in your patterns
? Confidence: LOW (40%)

Options:
A. Monolith (simpler now, harder to scale later)
B. Microservices (flexible, but complex deployment)

Need input: What's your priority - simplicity now or flexibility later?
```

### Example 3: Pattern Application
```
You: "Create a web scraper for stock data"

Ares:
[EXECUTING] Modular scraper architecture

Internal Validation:
✓ Challenge: Proven pattern - used 5+ times successfully
✓ Simplify: Considered monolithic, but modular wins
✓ Validate: Tier 1 pattern from ASX Trading AI
✓ Explain: LEGO blocks vs glued parts - easier to maintain
✓ Confidence: HIGH (95%)

Creating:
- scrapers/base.py
- scrapers/stock_data.py
- scrapers/coordinator.py
[Implementation proceeds]
```

## Configuration

**Default Settings** (from config/ares.yaml):
- Confidence threshold: 80%
- Validation enabled: true
- Show work: true (always)
- Truth protocol: true
- Internal skeptic: true

**User Preferences**:
- Language: Python
- Database: SQLite (POC), PostgreSQL (scale)
- API Framework: FastAPI
- Testing: Always enabled
- Documentation: Comprehensive
- Platform: Windows-first

## Updates

When new versions are released:

1. Update `ares_version` in `config/ares.yaml`
2. Update CLAUDE.md to reference new version
3. Run version checker to verify
4. Commit changes to git

**Current**: v2.5.0 (2025-10-15)
**Next**: v3.0 (MCP server implementation)

---

## Summary

**To use latest Ares:**

1. ✓ CLAUDE.md is updated (automatically loaded)
2. ✓ Files are in `ares-master-control-program/`
3. ✓ Version checker shows v2.5.0
4. ✓ Invoke with "Launch Ares" or "Load Ares"
5. ✓ Confirm activation message shows v2.5.0

**You're now guaranteed to get Ares v2.5.0 with full protocol capabilities!**

---

*Created: 2025-10-22*
*Ares Version: 2.5.0*
