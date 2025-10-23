# Riordan Butler - Development Directory

**Master workspace for all projects, tools, and AI systems**

---

## Directory Structure

```
C:\Users\riord\
│
├── /projects/                          # Active business & development projects
│   ├── ai-consulting-business/         # Customer acquisition system for AI consulting
│   ├── asx-trading-ai/                 # (Currently in use - will move when available)
│   ├── business-brain/                 # AI workflow discovery & automation POC
│   ├── focusguard-ai/                  # AI phone answering service
│   └── xero-integration/               # Xero MCP integration
│
├── /fireflies-mvp/                     # Voice-first AI business OS (Joint IP: Rio/Anthony/Dan)
│
├── /ares-master-control-program/       # ARES v3.0 Master Control Program
│   ├── /core/                          # Core validation, orchestration, protocols
│   ├── /config/                        # Configuration files
│   ├── /commands/                      # Slash commands
│   └── /docs/                          # ARES documentation (moved from root)
│
├── /ares-integrations/                 # ARES-related MCP servers & bridges
│   ├── ares-mcp-server/                # ARES patterns as MCP tools
│   ├── ares-whatsapp-bridge/           # WhatsApp automation integration
│   └── gemini-research-mcp/            # Research capabilities MCP server
│
├── /archives/                          # Old snapshots & deprecated projects
│   ├── ares-audit-20251015/
│   ├── ares-snapshot-20251015-stable/
│   └── simple-rest-api/                # Basic Express tutorial (no unique value)
│
├── /tools/                             # Utilities & standalone tools
│   ├── ngrok.exe
│   └── ngrok.zip
│
├── /docs/                              # Standalone documentation
│   ├── PLAYWRIGHT_CHROME_SETUP_GUIDE.md
│   ├── POWERSHELL_AUTO_START_GUIDE.md
│   ├── whatsapp-bridge-documentation.md
│   └── ares-mindmap.html
│
├── CLAUDE.md                           # Primary directive for Claude Code
└── README.md                           # This file
```

---

## Organization Philosophy

### Reference vs Operational

**Reference Folders** (change infrequently):
- `/ares-master-control-program/` - Core system, proven patterns
- `/docs/` - Setup guides, documentation
- `/tools/` - Utilities

**Operational Folders** (change frequently):
- `/projects/` - Active development work
- `/ares-integrations/` - Active integrations in use

**Archived Folders** (historical):
- `/archives/` - Old snapshots, completed/deprecated projects

### Separation of Concerns

- **ARES Core** → Own directory with versioned documentation
- **Projects** → Business applications, POCs, active work
- **Integrations** → MCP servers, bridges, extensions
- **Fireflies** → Separate (joint IP with Anthony/Dan)

---

## Active Projects

### AI Consulting Business
**Location:** `projects/ai-consulting-business/`
**Status:** Active - Customer acquisition system complete
**Purpose:** Full framework for acquiring home services AI consulting clients
**Tech:** Adaptive frameworks, discovery call scripts, pipeline tracking

### ASX Trading AI
**Location:** `asx-trading-ai/` (root - will move when available)
**Status:** Active - Live trading system
**Purpose:** Automated stock trading with AI-driven analysis
**Tech:** Python, yfinance, FastAPI, real-time data processing

### Business Brain
**Location:** `projects/business-brain/`
**Status:** POC - ~1,300 lines Python
**Purpose:** AI workflow discovery & automation for small businesses
**Tech:** Python, FastAPI, SQLite, AI agents (invoice, email)
**Note:** Potential future integration into ARES

### FocusGuard AI
**Location:** `projects/focusguard-ai/`
**Status:** Pre-sales validation (Week 1)
**Purpose:** AI phone answering service for small businesses
**Target:** 3 founding customers, $10K/month revenue
**Tech:** Twilio, Bland.ai, Python, FastAPI

### Xero Integration
**Location:** `projects/xero-integration/`
**Status:** Active
**Purpose:** Xero accounting integration via MCP
**Tech:** Official @xeroapi/xero-mcp-server

---

## ARES Ecosystem

### Master Control Program
**Location:** `ares-master-control-program/`
**Version:** 3.0.0
**Purpose:** AI assistant with internal validation protocols
**Features:**
- 5-step internal validation loop
- Confidence-based execution (≥80% autonomous)
- Agent orchestration (14 specialized agents)
- Application orchestration (standalone app management)
- Adaptive learning (riord_learning_patterns.md)

### ARES Integrations

**ARES MCP Server** (`ares-integrations/ares-mcp-server/`)
- Exposes ARES proven patterns as MCP tools
- Tech success matrix, validation protocols
- Pattern recommendations for Claude Desktop

**WhatsApp Bridge** (`ares-integrations/ares-whatsapp-bridge/`)
- WhatsApp automation integration
- Message handling, notifications

**Gemini Research MCP** (`ares-integrations/gemini-research-mcp/`)
- Research capabilities (Google Scholar, YouTube, Gemini)
- Weighted decision-making with confidence scores
- Deep research synthesis

---

## Fireflies MVP (Joint IP)

**Location:** `/fireflies-mvp/` (separate for IP purposes)
**Partners:** Riordan, Anthony, Dan
**Status:** Low priority until partners + equity tracking in place
**Purpose:** Voice-first AI business OS
**Tech:** Node.js, Express, Anthropic Claude, Web Speech API

**Note:** Business Brain may amalgamate into this in future

---

## Archived Projects

- **ares-audit-20251015** - Security audit snapshot
- **ares-snapshot-20251015-stable** - Stable v2.3 snapshot
- **simple-rest-api** - Basic Express tutorial (no unique value)

---

## Tools & Utilities

- **ngrok** - Secure tunneling for local development
- **Documentation** - Setup guides, integration docs, visual maps

---

## Git Repository

**Branch:** `backup-clean`
**Remote:** https://github.com/rudirid/ares-master-control-program

**Tracked:**
- ARES v3.0 system
- AI consulting business
- All projects and integrations

---

## Quick Navigation

**Start ARES:**
```
Load Ares Master Control Program
```

**AI Consulting Help:**
```
Load customer acquisition agent
File: C:\Users\riord\projects\ai-consulting-business\customer-acquisition\customer-acquisition-agent.md
```

**Check Project Status:**
```
cd projects/[project-name]
cat README.md
```

---

## Notes

- **asx-trading-ai** currently at root (in use, will move when available)
- **Fireflies** kept separate for IP/equity tracking purposes
- **Business Brain** POC - functional, potential ARES integration
- **All ARES docs** now consolidated in `ares-master-control-program/docs/`

---

**Last Updated:** 2025-10-24 (Full directory reorganization)
**ARES Version:** 3.0.0
**Active Projects:** 5
**ARES Integrations:** 3
