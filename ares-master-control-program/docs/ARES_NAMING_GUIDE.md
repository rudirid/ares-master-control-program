# ARES Naming Guide & Conventions

**Version:** 1.0
**Date:** 2025-10-16
**Status:** PROPOSAL
**Purpose:** Resolve naming confusion across ARES ecosystem

---

## Executive Summary

The ARES ecosystem currently has **critical naming confusion** with:
- 3 directories containing "mcp" in different contexts
- 3 versions of `whatsapp_bridge.py`
- 6+ directories with ARES-related content
- Mixed naming patterns (kebab-case, snake_case, Unix hidden)
- Unclear active vs archived status

This guide establishes **clear, consistent naming conventions** for all ARES components.

---

## Current State Analysis

### Major Problems Identified

#### 1. **Directory Name Collisions**
```
.ares-mcp/                      ← Active runtime (hidden directory)
ares-master-control-program/    ← Git repo / "Master Control Program"
ares-mcp-server/                ← MCP Protocol server (TypeScript)
```
**Problem:** Three directories with "mcp" have completely different purposes:
- `.ares-mcp` = Working runtime directory
- `ares-master-control-program` = Core library & documentation
- `ares-mcp-server` = Model Context Protocol server for Claude Desktop

**User Confusion:** "Which one is the Master Control Program?"

#### 2. **File Duplication**
```
whatsapp_bridge.py exists in:
  1. .ares-mcp/                          (ACTIVE - most evolved)
  2. ares-master-control-program/        (Different version)
  3. ares-whatsapp-bridge/               (Original v1.0)
  4. ares-audit-20251015/                (Archive copy)
  5. ares-snapshot-20251015-stable/      (Snapshot copy)
```
**Problem:** No clear canonical version

#### 3. **Mixed Naming Patterns**
- Directories: `.ares-mcp`, `ares-master-control-program`, `ares-whatsapp-bridge`
- Python files: `ares_daemon.py`, `ares_whatsapp_processor.py`
- Batch files: `start_ares_system.bat`, `auto_start_whatsapp.bat`
- Markdown: `ares-core-directives.md`, `ARES_README.md`

**Problem:** No predictable pattern - hard to know where to find things

#### 4. **Unclear Status**
```
ares-whatsapp-bridge/          ← Active? Archived? Superseded?
ares-snapshot-20251015-stable/ ← Backup or reference?
ares-audit-20251015/           ← Historical or current?
```
**Problem:** Can't tell what's in use vs historical

---

## Proposed Naming Convention

### Core Principles

1. **One Purpose, One Name** - No overlapping names for different purposes
2. **Predictable Patterns** - Consistent naming makes files discoverable
3. **Clear Status** - Active vs Archive is obvious from name/location
4. **Semantic Clarity** - Name describes purpose, not implementation
5. **Future-Proof** - Convention scales as system grows

---

## Directory Naming Standards

### Active System Directories

#### Pattern: `ares-{component-type}`

```
ares-runtime/          ← Active runtime system (was: .ares-mcp)
ares-core/             ← Core Python library (was: ares-master-control-program)
ares-claude-mcp/       ← MCP server for Claude Desktop (was: ares-mcp-server)
ares-integrations/     ← External system integrations
  ├── whatsapp/        ← WhatsApp Cloud API integration
  ├── signal/          ← Signal messenger integration
  └── telegram/        ← Future: Telegram integration
```

**Rules:**
- Use `kebab-case` (lowercase, hyphen-separated)
- Start with `ares-` prefix
- Component type describes **function**, not implementation
- No version numbers in directory names (use git tags/branches)
- No dates in active directory names

**Examples:**
- ✅ `ares-runtime` - Clear it's the active system
- ✅ `ares-core` - Clear it's the core library
- ✅ `ares-claude-mcp` - Clear it's for Claude Desktop MCP integration
- ❌ `ares-mcp-server` - "mcp" could mean multiple things
- ❌ `.ares-mcp` - Hidden directory unclear purpose
- ❌ `ares-master-control-program` - Too long, "master control program" is conceptual not functional

### Archive Directories

#### Pattern: `ares-archive/{category}/`

```
ares-archive/
  ├── snapshots/
  │   ├── 2025-10-15-stable/      ← Dated snapshot
  │   └── v2.3-milestone/         ← Version milestone
  ├── deprecated/
  │   ├── whatsapp-bridge-v1/     ← Old standalone WhatsApp project
  │   └── signal-poc/             ← Proof of concept
  └── audits/
      └── 2025-10-15-security/    ← Security audit package
```

**Rules:**
- All archives under single `ares-archive/` directory
- Categorize by type: snapshots, deprecated, audits, experiments
- Use dates in ISO format: `YYYY-MM-DD` (sortable)
- Include version or purpose in subdirectory name
- Never import/reference code from archive directories

---

## File Naming Standards

### Python Files

#### Pattern: `ares_{component}_{function}.py`

```
Core modules:
  ares_daemon.py              ← Main daemon/orchestrator
  ares_validation.py          ← Internal validation protocols
  ares_patterns.py            ← Pattern matching engine
  ares_config.py              ← Configuration management

Integration modules:
  ares_whatsapp_bridge.py     ← WhatsApp API bridge
  ares_whatsapp_processor.py  ← WhatsApp message processor
  ares_whatsapp_poller.py     ← WhatsApp offline poller
  ares_claude_mcp_server.py   ← MCP server (if rewritten in Python)

Utility modules:
  ares_security.py            ← Security framework
  ares_browser.py             ← Browser automation
  ares_logger.py              ← Logging utilities
```

**Rules:**
- Use `snake_case` (lowercase, underscore-separated)
- Start with `ares_` prefix (identifies as ARES component)
- Format: `ares_{system}_{function}.py` for integrations
- Format: `ares_{function}.py` for core modules
- Be specific: `ares_whatsapp_bridge.py` not `whatsapp_bridge.py`

**Rationale:**
- Prefix prevents naming conflicts in imports
- Easy to grep for all ARES files: `grep -r "ares_" .`
- Clear ownership and purpose

**Examples:**
- ✅ `ares_whatsapp_bridge.py` - Clear it's ARES WhatsApp integration
- ✅ `ares_daemon.py` - Clear it's the main ARES daemon
- ❌ `whatsapp_bridge.py` - Could be any WhatsApp bridge
- ❌ `bridge.py` - Too generic
- ❌ `aresWhatsAppBridge.py` - Wrong case convention for Python

### Configuration Files

#### Pattern: `ares.{type}.{format}` or `.ares-{type}`

```
ares.config.yaml         ← Main ARES configuration
ares.secrets.env         ← Secrets and API keys (gitignored)
ares.logging.yaml        ← Logging configuration
.ares-runtime            ← Runtime state directory
.ares-cache              ← Cache directory
```

**Rules:**
- Use `kebab-case` or `snake_case` depending on format conventions
- Start with `ares.` for files or `.ares-` for directories
- Include type/purpose before extension
- Secrets always use `.env` extension and are gitignored

### Batch/Shell Scripts

#### Pattern: `ares-{action}.{sh|bat}`

```
ares-start.bat           ← Start all ARES services
ares-stop.bat            ← Stop all ARES services
ares-restart.bat         ← Restart services
ares-status.bat          ← Check service status
ares-install.bat         ← Install dependencies
ares-test.bat            ← Run test suite
```

**Rules:**
- Use `kebab-case`
- Start with `ares-` prefix
- Action verb describes what script does
- Keep names short and memorable

**Examples:**
- ✅ `ares-start.bat` - Clear, simple
- ✅ `ares-test.bat` - Obvious purpose
- ❌ `start_ares_system.bat` - Inconsistent with naming pattern
- ❌ `auto_start_whatsapp.bat` - Unclear what "auto" means
- ❌ `setup_autostart.bat` - Missing ares prefix

### Documentation Files

#### Pattern: `ARES_{TOPIC}.md` or `{topic}-guide.md`

```
Documentation (uppercase for visibility):
  ARES_README.md              ← Main project README
  ARES_ARCHITECTURE.md        ← System architecture
  ARES_SECURITY.md            ← Security documentation
  ARES_CHANGELOG.md           ← Version history
  ARES_NAMING_GUIDE.md        ← This document

Guides (lowercase for user docs):
  quick-start-guide.md        ← Getting started
  whatsapp-integration-guide.md
  claude-mcp-setup-guide.md
  developer-guide.md
```

**Rules:**
- System docs: `ARES_{TOPIC}.md` (uppercase for discoverability)
- User guides: `{topic}-guide.md` (lowercase, descriptive)
- Use hyphens for multi-word topics
- One README per directory (ARES_README.md for main)

---

## Component Organization

### Recommended Directory Structure

```
C:\Users\riord\
├── ares-runtime/                    # Active ARES runtime (was: .ares-mcp)
│   ├── bin/                         # Executable scripts
│   │   ├── ares-start.bat
│   │   ├── ares-stop.bat
│   │   └── ares-status.bat
│   ├── config/                      # Configuration files
│   │   ├── ares.config.yaml
│   │   ├── ares.secrets.env         # Gitignored
│   │   └── ares.logging.yaml
│   ├── data/                        # Runtime data
│   │   ├── task-queue.json
│   │   ├── processed-tasks.json
│   │   └── response-log.json
│   ├── logs/                        # Log files
│   │   ├── ares-daemon.log
│   │   └── whatsapp-bridge.log
│   ├── modules/                     # Python modules
│   │   ├── ares_daemon.py
│   │   ├── ares_validation.py
│   │   ├── ares_patterns.py
│   │   └── integrations/
│   │       ├── ares_whatsapp_bridge.py
│   │       ├── ares_whatsapp_processor.py
│   │       └── ares_whatsapp_poller.py
│   └── ARES_README.md
│
├── ares-core/                       # Core library (was: ares-master-control-program)
│   ├── core/                        # Core Python library
│   │   ├── __init__.py
│   │   ├── validation.py
│   │   ├── patterns.py
│   │   └── output.py
│   ├── docs/                        # Documentation
│   │   ├── ARES_ARCHITECTURE.md
│   │   ├── ARES_PROTOCOLS.md
│   │   └── proven-patterns.md
│   ├── tests/                       # Test suite
│   │   ├── test_validation.py
│   │   ├── test_patterns.py
│   │   └── test_integration.py
│   ├── config/
│   │   └── ares.yaml
│   ├── setup.py                     # Python package setup
│   └── ARES_README.md
│
├── ares-claude-mcp/                 # MCP server (was: ares-mcp-server)
│   ├── src/
│   │   ├── index.ts
│   │   ├── tools/
│   │   └── resources/
│   ├── dist/                        # Compiled output
│   ├── package.json
│   ├── tsconfig.json
│   └── ARES_MCP_README.md
│
├── ares-integrations/               # Integration projects
│   ├── whatsapp/                    # WhatsApp integration
│   │   ├── bridge.py                # Bridge service
│   │   ├── processor.py             # Message processor
│   │   ├── poller.py                # Offline poller
│   │   └── README.md
│   ├── signal/                      # Signal integration
│   │   └── (future)
│   └── telegram/                    # Telegram integration
│       └── (future)
│
└── ares-archive/                    # Historical/deprecated
    ├── snapshots/
    │   ├── 2025-10-15-stable/       # v2.3 milestone
    │   └── 2025-09-01-v2.1/
    ├── deprecated/
    │   ├── whatsapp-bridge-v1/      # Old standalone project
    │   └── signal-poc/
    └── audits/
        └── 2025-10-15-security/     # Security audit package
```

---

## Migration Plan

### Phase 1: Immediate Fixes (No Breaking Changes)

**Goal:** Reduce confusion without breaking current system

1. **Create `ares-archive/` and move old versions**
   ```bash
   mkdir ares-archive\snapshots
   mkdir ares-archive\deprecated
   mkdir ares-archive\audits

   move ares-snapshot-20251015-stable ares-archive\snapshots\2025-10-15-stable
   move ares-audit-20251015 ares-archive\audits\2025-10-15-security
   move ares-whatsapp-bridge ares-archive\deprecated\whatsapp-bridge-v1
   ```

2. **Add status indicators to active directories**
   Create `STATUS.txt` in each directory:
   ```
   .ares-mcp/STATUS.txt:
     "ACTIVE - Main runtime directory - DO NOT DELETE"

   ares-master-control-program/STATUS.txt:
     "ACTIVE - Core library and git repository"

   ares-mcp-server/STATUS.txt:
     "ACTIVE - MCP server for Claude Desktop"
   ```

3. **Consolidate batch files in .ares-mcp/**
   ```
   Keep:    start_ares_system.bat → Rename to: ares-start.bat
   Keep:    start_whatsapp_bridge.bat → Rename to: ares-start-bridge-only.bat
   Archive: All other batch files to ares-archive/deprecated/scripts/
   ```

4. **Document canonical file locations**
   Create `.ares-mcp/CANONICAL_FILES.md`:
   ```markdown
   # Canonical File Locations

   **whatsapp_bridge.py**
   - Canonical: C:\Users\riord\.ares-mcp\whatsapp_bridge.py
   - Archived versions:
     - ares-archive/deprecated/whatsapp-bridge-v1/whatsapp_bridge.py
     - ares-master-control-program/whatsapp_bridge.py (outdated)

   **ares_task_processor.py**
   - Canonical: C:\Users\riord\ares-master-control-program\ares_task_processor.py
   - Note: Should be moved to .ares-mcp/ in Phase 2
   ```

### Phase 2: Structural Reorganization (Breaking Changes)

**Goal:** Implement full naming convention (requires updates to imports/paths)

1. **Rename directories**
   ```bash
   # Stop all services first
   ares-stop.bat

   # Rename directories
   ren .ares-mcp ares-runtime
   ren ares-master-control-program ares-core
   ren ares-mcp-server ares-claude-mcp
   ```

2. **Reorganize ares-runtime/**
   ```bash
   cd ares-runtime
   mkdir bin config data logs modules
   move *.bat bin\
   move *.json data\
   move *.log logs\
   move ares_*.py modules\
   ```

3. **Update imports in Python files**
   Change:
   ```python
   # Old
   from ares_whatsapp_processor import process_task

   # New
   from modules.integrations.ares_whatsapp_processor import process_task
   ```

4. **Update batch file paths**
   Update `ares-start.bat` (formerly `start_ares_system.bat`):
   ```batch
   # Old
   python C:\Users\riord\.ares-mcp\whatsapp_bridge.py

   # New
   python C:\Users\riord\ares-runtime\modules\integrations\ares_whatsapp_bridge.py
   ```

5. **Update Claude Desktop config**
   Edit `%APPDATA%\Claude\claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "ares": {
         "command": "C:\\Program Files\\nodejs\\node.exe",
         "args": ["C:\\Users\\riord\\ares-claude-mcp\\dist\\index.js"]
       }
     }
   }
   ```

### Phase 3: Establish New Conventions (Future)

1. **Create ares-integrations/** for external systems
2. **Move WhatsApp code** from ares-runtime to ares-integrations/whatsapp
3. **Publish ares-core** as Python package
4. **Version all components** with semantic versioning

---

## Naming Quick Reference

### Directories

| Type | Pattern | Example | Notes |
|------|---------|---------|-------|
| Active component | `ares-{component}` | `ares-runtime` | Kebab-case, descriptive |
| Archive snapshot | `ares-archive/snapshots/{date}-{name}` | `snapshots/2025-10-15-stable` | ISO date format |
| Archive deprecated | `ares-archive/deprecated/{name}` | `deprecated/whatsapp-v1` | Descriptive name |
| Integration | `ares-integrations/{system}` | `integrations/whatsapp` | Lowercase system name |

### Files

| Type | Pattern | Example | Notes |
|------|---------|---------|-------|
| Python module | `ares_{component}.py` | `ares_daemon.py` | Snake_case, ares_ prefix |
| Integration module | `ares_{system}_{function}.py` | `ares_whatsapp_bridge.py` | Specific, descriptive |
| Batch script | `ares-{action}.bat` | `ares-start.bat` | Kebab-case, verb action |
| Config file | `ares.{type}.{ext}` | `ares.config.yaml` | Dot-separated |
| System doc | `ARES_{TOPIC}.md` | `ARES_README.md` | Uppercase for visibility |
| User guide | `{topic}-guide.md` | `quick-start-guide.md` | Lowercase, readable |

---

## Decision Matrix

**When naming a new component, ask:**

1. **Is it active or archived?**
   - Active → Use standard pattern
   - Archived → Move to `ares-archive/{category}/`

2. **What is its scope?**
   - System-wide → Top-level `ares-{component}/`
   - Integration → `ares-integrations/{system}/`
   - Utility → Inside relevant component directory

3. **What language/tech?**
   - Python → `ares_{name}.py` (snake_case)
   - TypeScript/JS → `ares-{name}.ts` (kebab-case)
   - Batch/Shell → `ares-{action}.bat` (kebab-case)
   - Config → `ares.{type}.{ext}` (dot-separated)

4. **Is it user-facing or system-facing?**
   - System → `ARES_{TOPIC}.md` (uppercase)
   - User → `{topic}-guide.md` (lowercase)

---

## FAQ

### Q: Why not keep `.ares-mcp` as hidden directory?

**A:** Hidden directories are useful for user config (like `.git`, `.vscode`), but `.ares-mcp` is the PRIMARY active system directory. Hiding it makes it:
- Hard to discover for new developers
- Unclear that it's the main runtime
- Inconsistent with other ARES directories

Better: `ares-runtime` is clear and discoverable.

### Q: Why prefix Python files with `ares_`?

**A:** Prevents naming conflicts and makes ownership clear:
```python
# Without prefix - could be any whatsapp bridge
from whatsapp_bridge import send_message

# With prefix - clearly ARES component
from ares_whatsapp_bridge import send_message
```

Also makes grepping easier:
```bash
# Find all ARES Python files
ls ares_*.py

# Find all ARES imports
grep -r "from ares_" .
```

### Q: What about version numbers?

**A:**
- **Directories:** NO version numbers (use git tags/branches)
- **Files:** NO version numbers (use git commits)
- **Archives:** YES, include version in archive directory name

Examples:
- ✅ `ares-runtime/` (active, version tracked in git)
- ✅ `ares-archive/snapshots/v2.3-milestone/` (snapshot, version in name)
- ❌ `ares-runtime-v2.5/` (version will change, require renaming)

### Q: How to handle multiple versions of same file during migration?

**A:**
1. Identify canonical version (usually most recent/evolved)
2. Move canonical to proper location
3. Archive all other versions
4. Document in `CANONICAL_FILES.md`

Example:
```
Canonical: ares-runtime/modules/integrations/ares_whatsapp_bridge.py
Archives:
  - ares-archive/deprecated/whatsapp-v1/whatsapp_bridge.py
  - ares-archive/snapshots/2025-10-15/ares-core/whatsapp_bridge.py
```

### Q: What if I need a temporary/experimental directory?

**A:** Use `ares-experiments/` with date or purpose:
```
ares-experiments/
  ├── 2025-10-signal-poc/       ← Dated experiment
  ├── llm-integration-test/     ← Purpose-named
  └── scratch/                  ← Temporary work
```

Then either:
- Promote to active component (move to ares-{component})
- Archive (move to ares-archive/deprecated/)
- Delete if truly temporary

---

## Checklist for New Components

When creating a new ARES component:

- [ ] Choose appropriate directory based on scope
- [ ] Follow naming pattern for component type
- [ ] Create `README.md` documenting purpose
- [ ] Add to main `ARES_README.md` if user-facing
- [ ] Use consistent file naming within component
- [ ] Add to `.gitignore` if contains secrets
- [ ] Document dependencies in `requirements.txt` or `package.json`
- [ ] Create startup script in `ares-runtime/bin/` if needed
- [ ] Update main `ares-start.bat` if part of core system
- [ ] Add tests in `tests/` directory

---

## Summary

**Current State:**
- 6+ directories, 3 naming patterns, unclear ownership

**Target State:**
- 4 active directories with clear purposes
- 1 archive directory with categorized historical versions
- Consistent naming patterns across all files
- Clear canonical locations documented

**Key Changes:**
1. Rename `.ares-mcp` → `ares-runtime`
2. Rename `ares-master-control-program` → `ares-core`
3. Rename `ares-mcp-server` → `ares-claude-mcp`
4. Consolidate archives into `ares-archive/`
5. Standardize file prefixes (`ares_` for Python, `ares-` for scripts)

**Benefits:**
- **Discoverability:** Easy to find components by name
- **Clarity:** Purpose obvious from name
- **Consistency:** Predictable patterns
- **Scalability:** Convention supports growth
- **Maintainability:** Clear ownership and canonical locations

---

## Next Steps

1. **Review this proposal** - Identify any issues or concerns
2. **Test Phase 1 changes** - Archive old directories (non-breaking)
3. **Plan Phase 2 migration** - Identify all import/path updates needed
4. **Create migration scripts** - Automate renaming and path updates
5. **Execute migration** - Apply changes with rollback plan
6. **Update documentation** - Reflect new structure in all docs
7. **Enforce going forward** - Use this guide for all new components

---

**Document Status:** PROPOSAL
**Author:** Claude (ARES Analysis)
**Review Required:** Yes
**Breaking Changes:** Phase 2 and 3 only
**Rollback Plan:** Git revert + manual directory rename
