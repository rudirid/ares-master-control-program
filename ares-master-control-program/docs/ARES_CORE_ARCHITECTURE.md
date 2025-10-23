# ARES Core Architecture
## Standalone Master Control Program with Modular Database-Driven System

**Version:** 3.0 (Proposed)
**Date:** 2025-10-16
**Status:** ARCHITECTURAL PROPOSAL
**Based On:** ARES v2.1 (Internal Skeptic) + v2.5 (Core Library) + Ultrathink Analysis

---

## EXECUTIVE SUMMARY

This document proposes **ARES 3.0** - a complete architectural redesign that separates ARES Core (the Master Control Program) from all integrations and functions, using a **database-driven modular system** where the Core Program dynamically loads and launches capabilities on demand.

### Key Principles

1. **ARES Core = Pure Intelligence** - Validation, patterns, decision-making only
2. **Database = Module Registry** - All apps, functions, integrations stored in DB
3. **Master Control = Orchestrator** - Launches modules when needed, not before
4. **Zero Coupling** - Core never imports integration code directly
5. **Plugin Architecture** - Add/remove capabilities without touching Core

---

## ANALYSIS: BEST VERSION = ARES-MASTER-CONTROL-PROGRAM

Based on comprehensive analysis of all versions (v1.0 through v2.5), **ares-master-control-program** is the winner:

### What Makes It Best

✅ **v2.1.0 Directives** - Complete Internal Skeptic framework
✅ **v2.5.0 Core Library** - Python implementation of protocols
✅ **5-Step Validation** - Codified in `core/validation.py`
✅ **Proven Patterns** - Codified in `core/patterns.py` (6 patterns, Tier 1-3)
✅ **Show Your Work** - Codified in `core/output.py`
✅ **Ultrathink Mode** - Highest intelligence level for architecture decisions
✅ **Test Suite** - Demonstrates all functionality works
✅ **Configuration** - `config/ares.yaml` system
✅ **Git Repository** - Version controlled, collaboration-ready

### Ultrathink Findings

**Ultrathink** is ARES's highest thinking mode (7-step comprehensive analysis):
1. Scan everything (read all files, not summaries)
2. Cross-reference patterns across projects
3. Historical context (git history for decision reasoning)
4. Dependency mapping (trace imports, calls, data flows)
5. Performance analysis (bottlenecks, optimizations)
6. Internal validation (full skeptical loop)
7. Confidence rating (HIGH/MEDIUM/LOW)

**When to use:** Architecture decisions, major refactoring, tech stack choices, database design

---

## CURRENT STATE PROBLEMS

### Problem 1: Everything Mixed Together

**Current .ares-mcp/ structure:**
```
.ares-mcp/
├── whatsapp_bridge.py          ← Integration
├── whatsapp_poller.py          ← Integration
├── ares_daemon.py              ← Core?
├── browser_automation.py       ← Integration
├── ares_security.py            ← Core?
├── proven-patterns.md          ← Core
├── ares-core-directives.md     ← Core
└── ... (50+ files mixed)
```

**Problem:** Can't tell what's Core vs what's an integration. Everything runs together.

### Problem 2: Hardcoded Integrations

**Current ares_daemon.py:**
```python
from ares_whatsapp_processor import process_task  # Hardcoded dependency
```

**Problem:** Core depends on WhatsApp. Can't use ARES without WhatsApp running.

### Problem 3: No Module Discovery

**Current system:** You must know which Python files to run
- `python whatsapp_bridge.py`
- `python ares_daemon.py`
- `python browser_automation.py`

**Problem:** No way to ask "what capabilities are available?" or "launch sentiment analysis module"

### Problem 4: Duplicate Files Everywhere

**3 versions of whatsapp_bridge.py:**
- `.ares-mcp/whatsapp_bridge.py`
- `ares-master-control-program/whatsapp_bridge.py`
- `ares-whatsapp-bridge/whatsapp_bridge.py`

**Problem:** Which is canonical? How to maintain consistency?

---

## PROPOSED ARCHITECTURE: ARES 3.0

### Vision

```
┌─────────────────────────────────────────────────────────────┐
│                      ARES CORE 3.0                          │
│                   (Master Control Program)                  │
│                                                             │
│  Validation • Patterns • Confidence • Ultrathink • Output   │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ Queries
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    MODULE REGISTRY (SQLite)                 │
│                                                             │
│  modules: id, name, type, version, entry_point, config      │
│  capabilities: module_id, capability, description           │
│  dependencies: module_id, requires, version                 │
│  status: module_id, state, last_run, health                 │
└─────────────────────────────────────────────────────────────┘
                             │
                             │ Launches
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      REGISTERED MODULES                     │
│                                                             │
│  ├─ whatsapp-bridge      (Integration)                      │
│  ├─ browser-automation   (Tool)                             │
│  ├─ sentiment-analysis   (AI Feature)                       │
│  ├─ security-scanner     (Monitor)                          │
│  ├─ signal-bridge        (Integration)                      │
│  └─ custom-module        (User-defined)                     │
└─────────────────────────────────────────────────────────────┘
```

### Core Principles

1. **ARES Core never imports module code** - Uses dynamic loading
2. **Database is single source of truth** - All modules registered in DB
3. **Modules are self-contained** - Each has own directory, config, dependencies
4. **Launch on demand** - Core starts modules only when needed
5. **Health monitoring** - Core checks module status, restarts if crashed
6. **Version management** - Multiple versions can coexist, DB tracks which is active

---

## DIRECTORY STRUCTURE

### Proposed Clean Architecture

```
C:\Users\riord\ares\
├── core\                           # ARES Core (Master Control Program)
│   ├── __init__.py                 # Version 3.0.0
│   ├── validation.py               # 5-step validation protocol
│   ├── patterns.py                 # Pattern matcher
│   ├── output.py                   # Output formatter
│   ├── orchestrator.py             # NEW: Master Control Program
│   ├── module_loader.py            # NEW: Dynamic module loading
│   ├── module_registry.py          # NEW: Database interface
│   ├── health_monitor.py           # NEW: Module health checks
│   └── config.py                   # Configuration management
│
├── database\                       # Module Registry Database
│   ├── ares_registry.db            # SQLite database
│   ├── schema.sql                  # Database schema
│   └── migrations\                 # Schema migrations
│       ├── 001_initial.sql
│       └── 002_add_health.sql
│
├── modules\                        # All modules/integrations
│   ├── whatsapp-bridge\
│   │   ├── module.yaml             # Module metadata
│   │   ├── __init__.py
│   │   ├── bridge.py               # Main entry point
│   │   ├── processor.py
│   │   ├── poller.py
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   ├── browser-automation\
│   │   ├── module.yaml
│   │   ├── __init__.py
│   │   ├── automation.py
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   ├── security-scanner\
│   │   ├── module.yaml
│   │   ├── __init__.py
│   │   ├── scanner.py
│   │   ├── requirements.txt
│   │   └── README.md
│   │
│   └── signal-bridge\
│       ├── module.yaml
│       ├── __init__.py
│       ├── bridge.py
│       ├── requirements.txt
│       └── README.md
│
├── knowledge\                      # ARES knowledge base (read-only for Core)
│   ├── proven-patterns.md
│   ├── decision-causality.md
│   ├── tech-success-matrix.md
│   ├── project-evolution.md
│   └── ares-core-directives.md
│
├── config\                         # System configuration
│   ├── ares.yaml                   # Main ARES config
│   ├── modules.yaml                # Module-specific configs
│   └── secrets.env                 # API keys, tokens (gitignored)
│
├── logs\                           # Centralized logging
│   ├── ares-core.log
│   ├── whatsapp-bridge.log
│   ├── browser-automation.log
│   └── orchestrator.log
│
├── bin\                            # Executable scripts
│   ├── ares                        # Main CLI entry point
│   ├── ares-start                  # Start all or specific modules
│   ├── ares-stop                   # Stop modules
│   ├── ares-status                 # Check system status
│   ├── ares-register               # Register new module
│   └── ares-test                   # Run test suite
│
├── tests\                          # Test suite
│   ├── test_core\
│   │   ├── test_validation.py
│   │   ├── test_patterns.py
│   │   └── test_orchestrator.py
│   ├── test_modules\
│   │   └── test_module_loading.py
│   └── integration\
│       └── test_end_to_end.py
│
├── docs\                           # Documentation
│   ├── ARES_README.md              # Main README
│   ├── ARES_ARCHITECTURE.md        # This document
│   ├── ARES_NAMING_GUIDE.md        # Naming conventions
│   ├── MODULE_DEVELOPMENT_GUIDE.md # How to create modules
│   └── API_REFERENCE.md            # Core API docs
│
├── setup.py                        # Python package setup
├── requirements.txt                # Core dependencies only
├── .gitignore
└── README.md                       # Quick start
```

---

## DATABASE SCHEMA

### Module Registry (SQLite)

**Why SQLite?**
- Proven pattern (100% success rate in tech-success-matrix.md)
- Zero configuration
- File-based (easy backup/restore)
- Thread-safe with proper locking
- Perfect for local orchestration

```sql
-- modules table: All registered modules
CREATE TABLE modules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,              -- e.g., 'whatsapp-bridge'
    display_name TEXT NOT NULL,             -- e.g., 'WhatsApp Cloud API Bridge'
    type TEXT NOT NULL,                     -- 'integration', 'tool', 'monitor', 'ai-feature'
    version TEXT NOT NULL,                  -- Semantic version: '1.0.0'
    entry_point TEXT NOT NULL,              -- Path to main module: 'modules/whatsapp-bridge/bridge.py'
    main_function TEXT,                     -- Function to call: 'start_bridge'
    config_path TEXT,                       -- Path to module.yaml
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    enabled BOOLEAN DEFAULT 1,              -- Can be disabled without unregistering
    auto_start BOOLEAN DEFAULT 0,           -- Start automatically with ARES
    description TEXT,
    author TEXT,
    license TEXT
);

-- capabilities table: What each module can do
CREATE TABLE capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    capability TEXT NOT NULL,               -- e.g., 'send_whatsapp_message'
    description TEXT,
    input_schema TEXT,                      -- JSON schema for inputs
    output_schema TEXT,                     -- JSON schema for outputs
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

-- dependencies table: Module requirements
CREATE TABLE dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    dependency_type TEXT NOT NULL,          -- 'python', 'system', 'module', 'api'
    dependency_name TEXT NOT NULL,          -- Package name or module name
    version_constraint TEXT,                -- e.g., '>=1.0.0', '==2.5.1'
    required BOOLEAN DEFAULT 1,             -- Required or optional
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

-- status table: Runtime status of modules
CREATE TABLE status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    state TEXT NOT NULL,                    -- 'stopped', 'starting', 'running', 'error', 'crashed'
    process_id INTEGER,                     -- PID if running as process
    started_at TIMESTAMP,
    stopped_at TIMESTAMP,
    last_health_check TIMESTAMP,
    health_status TEXT,                     -- 'healthy', 'degraded', 'unhealthy'
    error_message TEXT,
    restart_count INTEGER DEFAULT 0,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

-- events table: Audit log of all module events
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER,
    event_type TEXT NOT NULL,               -- 'registered', 'started', 'stopped', 'crashed', 'health_check'
    event_data TEXT,                        -- JSON with event details
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE SET NULL
);

-- configurations table: Module-specific configs (overrides)
CREATE TABLE configurations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,                    -- JSON value
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE,
    UNIQUE(module_id, key)
);

-- Create indexes for performance
CREATE INDEX idx_modules_name ON modules(name);
CREATE INDEX idx_modules_type ON modules(type);
CREATE INDEX idx_modules_enabled ON modules(enabled);
CREATE INDEX idx_capabilities_module ON capabilities(module_id);
CREATE INDEX idx_dependencies_module ON dependencies(module_id);
CREATE INDEX idx_status_module ON status(module_id);
CREATE INDEX idx_status_state ON status(state);
CREATE INDEX idx_events_module ON events(module_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp);
```

---

## CORE COMPONENTS

### 1. Master Control Program (orchestrator.py)

**Purpose:** Main entry point, orchestrates all modules

```python
"""
ARES Core - Master Control Program
Orchestrates all modules based on database registry
"""

import logging
from typing import List, Optional, Dict
from core.module_registry import ModuleRegistry
from core.module_loader import ModuleLoader
from core.health_monitor import HealthMonitor
from core.validation import AresValidation

class AresMasterControl:
    """
    Master Control Program
    - Queries module registry
    - Launches modules on demand
    - Monitors health
    - Applies ARES validation protocols
    """

    def __init__(self, db_path: str = "database/ares_registry.db"):
        self.registry = ModuleRegistry(db_path)
        self.loader = ModuleLoader(self.registry)
        self.monitor = HealthMonitor(self.registry)
        self.validator = AresValidation()
        self.running_modules: Dict[str, object] = {}

    def start(self):
        """Start Master Control Program"""
        logging.info("🚀 ARES Master Control Program v3.0")

        # Start auto-start modules
        auto_modules = self.registry.get_auto_start_modules()
        for module in auto_modules:
            self.start_module(module['name'])

        # Start health monitoring
        self.monitor.start()

    def start_module(self, module_name: str) -> bool:
        """
        Start a specific module

        Args:
            module_name: Name of module to start (e.g., 'whatsapp-bridge')

        Returns:
            bool: True if started successfully
        """
        # Get module metadata from registry
        module = self.registry.get_module(module_name)
        if not module:
            logging.error(f"Module '{module_name}' not found in registry")
            return False

        if not module['enabled']:
            logging.warning(f"Module '{module_name}' is disabled")
            return False

        # Check dependencies
        if not self._check_dependencies(module['id']):
            logging.error(f"Dependencies not met for '{module_name}'")
            return False

        # Load and start module
        try:
            instance = self.loader.load_module(module)
            self.running_modules[module_name] = instance

            # Update status in DB
            self.registry.update_status(
                module['id'],
                state='running',
                process_id=instance.process_id if hasattr(instance, 'process_id') else None
            )

            logging.info(f"✅ Started: {module['display_name']}")
            return True

        except Exception as e:
            logging.error(f"Failed to start '{module_name}': {e}")
            self.registry.update_status(
                module['id'],
                state='error',
                error_message=str(e)
            )
            return False

    def stop_module(self, module_name: str) -> bool:
        """Stop a running module"""
        if module_name not in self.running_modules:
            logging.warning(f"Module '{module_name}' is not running")
            return False

        instance = self.running_modules[module_name]

        try:
            # Call stop method if exists
            if hasattr(instance, 'stop'):
                instance.stop()

            # Remove from running modules
            del self.running_modules[module_name]

            # Update status
            module = self.registry.get_module(module_name)
            self.registry.update_status(module['id'], state='stopped')

            logging.info(f"🛑 Stopped: {module_name}")
            return True

        except Exception as e:
            logging.error(f"Error stopping '{module_name}': {e}")
            return False

    def list_modules(self, type_filter: Optional[str] = None) -> List[Dict]:
        """
        List all registered modules

        Args:
            type_filter: Filter by type ('integration', 'tool', etc.)

        Returns:
            List of module dictionaries
        """
        return self.registry.list_modules(type_filter=type_filter)

    def get_capabilities(self, capability_name: str) -> List[Dict]:
        """
        Find all modules that provide a specific capability

        Args:
            capability_name: e.g., 'send_message', 'analyze_sentiment'

        Returns:
            List of modules with that capability
        """
        return self.registry.get_modules_by_capability(capability_name)

    def invoke_capability(self, capability_name: str, **kwargs):
        """
        Invoke a capability (starts module if needed)

        Args:
            capability_name: Capability to invoke
            **kwargs: Arguments to pass to capability

        Returns:
            Result from capability invocation
        """
        # Find module with this capability
        modules = self.get_capabilities(capability_name)
        if not modules:
            raise ValueError(f"No module provides capability '{capability_name}'")

        # Use first available module (or implement prioritization)
        module = modules[0]

        # Start module if not running
        if module['name'] not in self.running_modules:
            self.start_module(module['name'])

        # Invoke capability
        instance = self.running_modules[module['name']]
        if not hasattr(instance, capability_name):
            raise AttributeError(f"Module '{module['name']}' doesn't have method '{capability_name}'")

        method = getattr(instance, capability_name)
        return method(**kwargs)

    def _check_dependencies(self, module_id: int) -> bool:
        """Check if all dependencies are satisfied"""
        dependencies = self.registry.get_dependencies(module_id)

        for dep in dependencies:
            if dep['required']:
                # Check based on dependency type
                if dep['dependency_type'] == 'python':
                    if not self._check_python_package(dep['dependency_name'], dep['version_constraint']):
                        logging.error(f"Missing Python package: {dep['dependency_name']}")
                        return False

                elif dep['dependency_type'] == 'module':
                    # Check if other module is registered and enabled
                    other_module = self.registry.get_module(dep['dependency_name'])
                    if not other_module or not other_module['enabled']:
                        logging.error(f"Required module not available: {dep['dependency_name']}")
                        return False

        return True

    def _check_python_package(self, package: str, version_constraint: Optional[str]) -> bool:
        """Check if Python package is installed"""
        try:
            import importlib
            importlib.import_module(package)
            # TODO: Check version constraint
            return True
        except ImportError:
            return False

    def status(self) -> Dict:
        """Get overall system status"""
        modules = self.registry.list_modules()

        total = len(modules)
        running = sum(1 for m in modules if self.registry.get_status(m['id'])['state'] == 'running')
        stopped = sum(1 for m in modules if self.registry.get_status(m['id'])['state'] == 'stopped')
        error = sum(1 for m in modules if self.registry.get_status(m['id'])['state'] == 'error')

        return {
            'total_modules': total,
            'running': running,
            'stopped': stopped,
            'error': error,
            'modules': modules
        }
```

### 2. Module Registry (module_registry.py)

**Purpose:** Database interface for module registration

```python
"""
Module Registry - Database interface for ARES modules
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
import logging

class ModuleRegistry:
    """Interface to ARES module registry database"""

    def __init__(self, db_path: str = "database/ares_registry.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        self._ensure_schema()

    def _ensure_schema(self):
        """Create tables if they don't exist"""
        # Read schema.sql and execute
        try:
            with open("database/schema.sql") as f:
                self.conn.executescript(f.read())
        except FileNotFoundError:
            logging.warning("schema.sql not found, tables may not exist")

    def register_module(self, module_data: Dict) -> int:
        """
        Register a new module

        Args:
            module_data: Dict with module metadata

        Returns:
            module_id: ID of registered module
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            INSERT INTO modules (
                name, display_name, type, version, entry_point,
                main_function, config_path, enabled, auto_start,
                description, author, license
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            module_data['name'],
            module_data.get('display_name', module_data['name']),
            module_data['type'],
            module_data['version'],
            module_data['entry_point'],
            module_data.get('main_function'),
            module_data.get('config_path'),
            module_data.get('enabled', True),
            module_data.get('auto_start', False),
            module_data.get('description'),
            module_data.get('author'),
            module_data.get('license')
        ))

        module_id = cursor.lastrowid
        self.conn.commit()

        # Log event
        self._log_event(module_id, 'registered', module_data)

        logging.info(f"Registered module: {module_data['name']} (ID: {module_id})")
        return module_id

    def get_module(self, name: str) -> Optional[Dict]:
        """Get module by name"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM modules WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_modules(self, type_filter: Optional[str] = None) -> List[Dict]:
        """List all modules, optionally filtered by type"""
        cursor = self.conn.cursor()

        if type_filter:
            cursor.execute("SELECT * FROM modules WHERE type = ? ORDER BY name", (type_filter,))
        else:
            cursor.execute("SELECT * FROM modules ORDER BY name")

        return [dict(row) for row in cursor.fetchall()]

    def get_auto_start_modules(self) -> List[Dict]:
        """Get all modules marked for auto-start"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM modules WHERE auto_start = 1 AND enabled = 1")
        return [dict(row) for row in cursor.fetchall()]

    def register_capability(self, module_id: int, capability: str, description: str,
                          input_schema: Optional[Dict] = None,
                          output_schema: Optional[Dict] = None):
        """Register a capability for a module"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO capabilities (module_id, capability, description, input_schema, output_schema)
            VALUES (?, ?, ?, ?, ?)
        """, (
            module_id,
            capability,
            description,
            json.dumps(input_schema) if input_schema else None,
            json.dumps(output_schema) if output_schema else None
        ))
        self.conn.commit()

    def get_modules_by_capability(self, capability: str) -> List[Dict]:
        """Find all modules that provide a specific capability"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT m.* FROM modules m
            JOIN capabilities c ON m.id = c.module_id
            WHERE c.capability = ? AND m.enabled = 1
        """, (capability,))
        return [dict(row) for row in cursor.fetchall()]

    def add_dependency(self, module_id: int, dep_type: str, dep_name: str,
                      version_constraint: Optional[str] = None, required: bool = True):
        """Add a dependency for a module"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO dependencies (module_id, dependency_type, dependency_name, version_constraint, required)
            VALUES (?, ?, ?, ?, ?)
        """, (module_id, dep_type, dep_name, version_constraint, required))
        self.conn.commit()

    def get_dependencies(self, module_id: int) -> List[Dict]:
        """Get all dependencies for a module"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM dependencies WHERE module_id = ?", (module_id,))
        return [dict(row) for row in cursor.fetchall()]

    def update_status(self, module_id: int, state: str, process_id: Optional[int] = None,
                     health_status: Optional[str] = None, error_message: Optional[str] = None):
        """Update runtime status of a module"""
        cursor = self.conn.cursor()

        # Check if status exists
        cursor.execute("SELECT id FROM status WHERE module_id = ?", (module_id,))
        existing = cursor.fetchone()

        if existing:
            # Update existing status
            cursor.execute("""
                UPDATE status SET
                    state = ?,
                    process_id = ?,
                    health_status = ?,
                    error_message = ?,
                    last_health_check = CURRENT_TIMESTAMP,
                    started_at = CASE WHEN ? = 'running' THEN CURRENT_TIMESTAMP ELSE started_at END,
                    stopped_at = CASE WHEN ? IN ('stopped', 'error', 'crashed') THEN CURRENT_TIMESTAMP ELSE stopped_at END,
                    restart_count = CASE WHEN ? = 'running' AND state != 'running' THEN restart_count + 1 ELSE restart_count END
                WHERE module_id = ?
            """, (state, process_id, health_status, error_message, state, state, state, module_id))
        else:
            # Insert new status
            cursor.execute("""
                INSERT INTO status (module_id, state, process_id, health_status, error_message, started_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (module_id, state, process_id, health_status, error_message))

        self.conn.commit()

        # Log event
        self._log_event(module_id, state, {'process_id': process_id, 'error': error_message})

    def get_status(self, module_id: int) -> Dict:
        """Get current status of a module"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM status WHERE module_id = ?", (module_id,))
        row = cursor.fetchone()
        return dict(row) if row else {'state': 'unknown'}

    def _log_event(self, module_id: Optional[int], event_type: str, event_data: Dict):
        """Log an event to audit log"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO events (module_id, event_type, event_data)
            VALUES (?, ?, ?)
        """, (module_id, event_type, json.dumps(event_data)))
        self.conn.commit()
```

### 3. Module Loader (module_loader.py)

**Purpose:** Dynamically load and instantiate modules

```python
"""
Dynamic Module Loader
Loads modules from filesystem based on registry metadata
"""

import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any
import logging

class ModuleLoader:
    """Dynamically loads modules without hardcoded imports"""

    def __init__(self, registry):
        self.registry = registry

    def load_module(self, module_metadata: Dict) -> Any:
        """
        Load a module from filesystem

        Args:
            module_metadata: Module metadata from registry

        Returns:
            Instantiated module object
        """
        entry_point = module_metadata['entry_point']
        main_function = module_metadata.get('main_function', 'start')

        # Load Python module dynamically
        module = self._import_from_path(entry_point)

        # Get main function
        if hasattr(module, main_function):
            func = getattr(module, main_function)
            return func()  # Call function to get instance
        else:
            # If no main function, return module itself
            return module

    def _import_from_path(self, file_path: str):
        """Import a Python module from file path"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Module file not found: {file_path}")

        # Create module name from path
        module_name = path.stem

        # Load module spec
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load module from {file_path}")

        # Create module from spec
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module
```

---

## MODULE STRUCTURE

### Module Metadata (module.yaml)

Every module has a `module.yaml` file describing it:

```yaml
# modules/whatsapp-bridge/module.yaml

name: whatsapp-bridge
display_name: WhatsApp Cloud API Bridge
version: 2.0.0
type: integration
author: Riord ARES Team
license: MIT

description: |
  WhatsApp Cloud API integration for ARES.
  Provides webhook server, message processing, and offline polling.

entry_point: modules/whatsapp-bridge/bridge.py
main_function: start_bridge

auto_start: true
enabled: true

capabilities:
  - name: send_message
    description: Send WhatsApp message to authorized number
    input:
      phone: string
      message: string
    output:
      message_id: string
      status: string

  - name: receive_messages
    description: Receive incoming WhatsApp messages via webhook
    input:
      webhook_url: string
    output:
      messages: array

dependencies:
  python:
    - flask>=2.0.0
    - requests>=2.28.0

  system:
    - ngrok

  modules:
    - ares-core>=3.0.0

  apis:
    - name: Meta WhatsApp Cloud API
      endpoint: https://graph.facebook.com/v18.0
      auth: bearer_token

configuration:
  phone_number_id: "810808242121215"
  authorized_number: "+61432154351"
  webhook_port: 5000
  verify_token: "ares_webhook_verify_2024"
  polling_interval: 30
```

### Module Entry Point (bridge.py)

```python
# modules/whatsapp-bridge/bridge.py

"""
WhatsApp Cloud API Bridge
Entry point for WhatsApp integration module
"""

import logging
from flask import Flask, request, jsonify
from .processor import WhatsAppProcessor
from .poller import WhatsAppPoller

class WhatsAppBridge:
    """WhatsApp integration module for ARES"""

    def __init__(self, config: dict):
        self.config = config
        self.app = Flask(__name__)
        self.processor = WhatsAppProcessor(config)
        self.poller = WhatsAppPoller(config)
        self.process_id = None

        # Register routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route('/webhook', methods=['GET', 'POST'])
        def webhook():
            if request.method == 'GET':
                # Verification
                return self._verify_webhook(request)
            else:
                # Process message
                return self._handle_message(request)

    def start(self):
        """Start WhatsApp bridge"""
        logging.info("Starting WhatsApp Bridge")

        # Start poller in background
        self.poller.start()

        # Start Flask server
        self.app.run(
            host='0.0.0.0',
            port=self.config.get('webhook_port', 5000)
        )

    def stop(self):
        """Stop WhatsApp bridge"""
        logging.info("Stopping WhatsApp Bridge")
        self.poller.stop()
        # Flask shutdown handled by process termination

    def send_message(self, phone: str, message: str) -> dict:
        """
        Capability: send_message
        Send WhatsApp message
        """
        return self.processor.send_message(phone, message)

    def receive_messages(self, webhook_url: str) -> list:
        """
        Capability: receive_messages
        Get received messages
        """
        return self.processor.get_received_messages()

def start_bridge():
    """
    Main entry point called by ModuleLoader
    Returns instantiated WhatsAppBridge
    """
    # Load config from ARES
    # (ModuleLoader passes config from module.yaml + overrides)
    config = {
        'phone_number_id': '810808242121215',
        'authorized_number': '+61432154351',
        'webhook_port': 5000,
        # ... other config
    }

    return WhatsAppBridge(config)
```

---

## CLI INTERFACE

### bin/ares (Main CLI)

```python
#!/usr/bin/env python3
"""
ARES CLI - Main entry point
"""

import click
from core.orchestrator import AresMasterControl

@click.group()
def cli():
    """ARES Master Control Program CLI"""
    pass

@cli.command()
def start():
    """Start ARES Master Control Program"""
    mcp = AresMasterControl()
    mcp.start()

@cli.command()
@click.argument('module_name')
def start_module(module_name):
    """Start a specific module"""
    mcp = AresMasterControl()
    if mcp.start_module(module_name):
        click.echo(f"✅ Started {module_name}")
    else:
        click.echo(f"❌ Failed to start {module_name}", err=True)

@cli.command()
@click.argument('module_name')
def stop_module(module_name):
    """Stop a specific module"""
    mcp = AresMasterControl()
    if mcp.stop_module(module_name):
        click.echo(f"🛑 Stopped {module_name}")
    else:
        click.echo(f"❌ Failed to stop {module_name}", err=True)

@cli.command()
@click.option('--type', help='Filter by module type')
def list(type):
    """List all registered modules"""
    mcp = AresMasterControl()
    modules = mcp.list_modules(type_filter=type)

    for mod in modules:
        status = mcp.registry.get_status(mod['id'])
        click.echo(f"{mod['name']:30} {mod['version']:10} {status['state']:15}")

@cli.command()
def status():
    """Show system status"""
    mcp = AresMasterControl()
    stat = mcp.status()

    click.echo(f"\n{'='*60}")
    click.echo(f"ARES Master Control Program - System Status")
    click.echo(f"{'='*60}")
    click.echo(f"Total Modules: {stat['total_modules']}")
    click.echo(f"Running:       {stat['running']}")
    click.echo(f"Stopped:       {stat['stopped']}")
    click.echo(f"Error:         {stat['error']}")
    click.echo(f"{'='*60}\n")

@cli.command()
@click.argument('module_path')
def register(module_path):
    """Register a new module from module.yaml"""
    import yaml
    from pathlib import Path

    yaml_path = Path(module_path) / "module.yaml"

    if not yaml_path.exists():
        click.echo(f"❌ module.yaml not found in {module_path}", err=True)
        return

    with open(yaml_path) as f:
        module_data = yaml.safe_load(f)

    mcp = AresMasterControl()
    module_id = mcp.registry.register_module(module_data)

    # Register capabilities
    for cap in module_data.get('capabilities', []):
        mcp.registry.register_capability(
            module_id,
            cap['name'],
            cap['description'],
            input_schema=cap.get('input'),
            output_schema=cap.get('output')
        )

    # Register dependencies
    for dep_type, deps in module_data.get('dependencies', {}).items():
        if isinstance(deps, list):
            for dep in deps:
                mcp.registry.add_dependency(module_id, 'python', dep)
        elif isinstance(deps, dict):
            for dep_name, details in deps.items():
                mcp.registry.add_dependency(
                    module_id,
                    dep_type,
                    dep_name,
                    version_constraint=details.get('version')
                )

    click.echo(f"✅ Registered {module_data['name']} (ID: {module_id})")

if __name__ == '__main__':
    cli()
```

---

## USAGE EXAMPLES

### Example 1: Start ARES with Auto-Start Modules

```bash
$ ares start

🚀 ARES Master Control Program v3.0
✅ Started: WhatsApp Cloud API Bridge
✅ Started: Security Scanner
🏃 Health monitoring active
📊 Status: 2 modules running
```

### Example 2: Register a New Module

```bash
$ ares register modules/telegram-bridge

✅ Registered telegram-bridge (ID: 5)
```

### Example 3: List All Modules

```bash
$ ares list

whatsapp-bridge               2.0.0      running
browser-automation            1.5.0      stopped
security-scanner              1.0.0      running
signal-bridge                 1.0.0      stopped
sentiment-analysis            0.9.0      error
```

### Example 4: Start Specific Module

```bash
$ ares start-module browser-automation

Checking dependencies... ✅
Loading module... ✅
Starting browser-automation... ✅
✅ Started browser-automation
```

### Example 5: Check System Status

```bash
$ ares status

============================================================
ARES Master Control Program - System Status
============================================================
Total Modules: 5
Running:       3
Stopped:       1
Error:         1
============================================================
```

### Example 6: Invoke Capability from Python

```python
from core.orchestrator import AresMasterControl

# Initialize Master Control
mcp = AresMasterControl()

# Send WhatsApp message (automatically starts whatsapp-bridge if needed)
result = mcp.invoke_capability(
    'send_message',
    phone='+61432154351',
    message='Hello from ARES 3.0!'
)

print(f"Message sent: {result['message_id']}")
```

---

## MIGRATION PLAN: FROM CURRENT STATE TO ARES 3.0

### Phase 1: Preparation (Non-Breaking)

1. **Create new directory structure**
   ```bash
   mkdir -p C:\Users\riord\ares\{core,database,modules,knowledge,config,logs,bin,tests,docs}
   ```

2. **Copy ARES Core v2.5 library**
   ```bash
   cp -r ares-master-control-program/core/* ares/core/
   ```

3. **Copy knowledge base**
   ```bash
   cp ares-master-control-program/*.md ares/knowledge/
   ```

4. **Copy configuration**
   ```bash
   cp ares-master-control-program/config/ares.yaml ares/config/
   ```

5. **Create database schema**
   ```bash
   # Create schema.sql from specification above
   sqlite3 ares/database/ares_registry.db < database/schema.sql
   ```

### Phase 2: Implement Core Components

1. **Implement orchestrator.py** (Master Control Program)
2. **Implement module_registry.py** (Database interface)
3. **Implement module_loader.py** (Dynamic loading)
4. **Implement health_monitor.py** (Health checks)
5. **Create CLI** (bin/ares)

### Phase 3: Convert Existing Integrations to Modules

1. **WhatsApp Bridge**
   ```bash
   mkdir -p ares/modules/whatsapp-bridge
   # Create module.yaml
   # Refactor whatsapp_bridge.py to follow module structure
   # Register: ares register modules/whatsapp-bridge
   ```

2. **Browser Automation**
   ```bash
   mkdir -p ares/modules/browser-automation
   # Create module.yaml
   # Refactor browser_automation.py
   # Register: ares register modules/browser-automation
   ```

3. **Security Scanner**
   ```bash
   mkdir -p ares/modules/security-scanner
   # Create module.yaml
   # Refactor ares_security.py
   # Register: ares register modules/security-scanner
   ```

### Phase 4: Testing & Validation

1. **Run test suite**
   ```bash
   python -m pytest tests/
   ```

2. **Test module registration**
   ```bash
   ares list
   ```

3. **Test module lifecycle**
   ```bash
   ares start-module whatsapp-bridge
   ares status
   ares stop-module whatsapp-bridge
   ```

4. **Test capability invocation**
   ```python
   mcp = AresMasterControl()
   result = mcp.invoke_capability('send_message', phone='+61...', message='Test')
   ```

### Phase 5: Archive Old System

1. **Stop current system**
   ```bash
   # Stop all running .ares-mcp services
   ```

2. **Archive old directories**
   ```bash
   mkdir -p ares-archive/pre-v3.0
   mv .ares-mcp ares-archive/pre-v3.0/
   mv ares-whatsapp-bridge ares-archive/pre-v3.0/
   mv ares-snapshot-20251015-stable ares-archive/pre-v3.0/
   mv ares-audit-20251015 ares-archive/pre-v3.0/
   ```

3. **Keep ares-master-control-program as development repo**
   ```bash
   # Keep this for git history and reference
   # But active system is now in ares/
   ```

---

## BENEFITS OF ARES 3.0 ARCHITECTURE

### 1. **Clean Separation of Concerns**
- ✅ ARES Core = Pure intelligence (validation, patterns, orchestration)
- ✅ Modules = Specific functionality (WhatsApp, browser, security)
- ✅ Database = Single source of truth for what's available

### 2. **Zero Coupling**
- ✅ Core never imports module code directly
- ✅ Can add/remove modules without touching Core
- ✅ Modules can be developed independently

### 3. **Dynamic & Extensible**
- ✅ Register new modules with `ares register`
- ✅ Start/stop modules on demand
- ✅ Query capabilities: "What can send messages?"

### 4. **Organized & Discoverable**
- ✅ All modules in `modules/` directory
- ✅ Each module self-contained with metadata
- ✅ Database query: `ares list --type integration`

### 5. **Health Monitoring**
- ✅ Track module status (running, stopped, error)
- ✅ Automatic restart on crash
- ✅ Health checks for degradation

### 6. **Version Management**
- ✅ Multiple versions can coexist
- ✅ Database tracks active version
- ✅ Easy rollback: update DB to different version

### 7. **Audit Trail**
- ✅ All events logged (registered, started, stopped, crashed)
- ✅ Timestamps for all state changes
- ✅ Error messages captured

### 8. **Configuration Hierarchy**
- ✅ System config in `ares.yaml`
- ✅ Module config in `module.yaml`
- ✅ Runtime overrides in database

### 9. **Follows Proven Patterns**
- ✅ Database-centric architecture (100% success rate)
- ✅ Modular architecture (95% success rate)
- ✅ SQLite for orchestration (100% success rate)
- ✅ Plugin system (proven pattern)

### 10. **Future-Proof**
- ✅ Easy to add new integration types
- ✅ Can build GUI on top of Core
- ✅ Can expose as API
- ✅ Can distribute modules separately

---

## COMPARISON: CURRENT vs ARES 3.0

| Aspect | Current (.ares-mcp) | ARES 3.0 |
|--------|---------------------|----------|
| **Architecture** | Monolithic, mixed | Modular, layered |
| **Core Definition** | Unclear (mixed with integrations) | Clear (core/ directory) |
| **Module Discovery** | Manual (know which .py to run) | Automatic (database query) |
| **Dependencies** | Hardcoded imports | Database registry |
| **Adding Feature** | Edit existing files | Register new module |
| **Configuration** | Scattered across files | Centralized (DB + YAML) |
| **Status Tracking** | Manual/logs | Database with status table |
| **Health Monitoring** | None | Automated with restarts |
| **Version Management** | Git only | DB tracks active version |
| **Audit Trail** | Logs only | Database events table |
| **Module Isolation** | None (all in one dir) | Each in own directory |
| **Capability Discovery** | Know what exists | Query: "what can do X?" |
| **Testing** | Test entire system | Test core + modules separately |
| **Documentation** | Mixed with code | Separate docs/ directory |

---

## NEXT STEPS

### Immediate Actions

1. **Review this proposal**
   - Validate architecture aligns with vision
   - Identify any concerns or requirements

2. **Approve/modify naming convention**
   - Directory structure
   - File naming patterns
   - Database schema

3. **Prioritize modules to migrate**
   - Which integrations are essential?
   - What can wait?

4. **Decide on implementation timeline**
   - Phase 1: Setup (1 day)
   - Phase 2: Core implementation (2-3 days)
   - Phase 3: Module migration (1-2 days per module)
   - Phase 4: Testing (1-2 days)

### Long-Term Vision

**ARES as a Platform:**
- Core = Master Control Program
- Modules = Ecosystem of capabilities
- Database = Central nervous system
- CLI = User interface
- API = External integration
- GUI = Visual dashboard (future)

**Module Marketplace:**
- Community-contributed modules
- Module versioning and compatibility
- Module discovery and installation

**Meta-Agent Capabilities:**
- ARES can spawn sub-agents for specific tasks
- Each sub-agent is a module
- Database tracks agent delegation

---

## QUESTIONS FOR CONSIDERATION

1. **Should modules run as separate processes or in-process?**
   - Separate: Better isolation, crash doesn't affect Core
   - In-process: Simpler, faster communication
   - Hybrid: Critical modules separate, lightweight in-process

2. **How to handle module authentication/authorization?**
   - API keys per module?
   - OAuth for external services?
   - Centralized secrets management?

3. **Should modules communicate with each other?**
   - Direct: Module A calls Module B
   - Through Core: Module A → Core → Module B
   - Event bus: Publish/subscribe pattern

4. **What about module updates?**
   - Auto-update from git?
   - Manual update with version checking?
   - Rollback mechanism?

5. **How to distribute modules?**
   - Git submodules?
   - Package registry (PyPI-style)?
   - Docker containers?

---

## SUMMARY

**Recommendation:** Implement **ARES 3.0** as described

**Foundation:** `ares-master-control-program` (contains best v2.1 + v2.5 protocols)

**Architecture:** Standalone Core + Database-driven modular system

**Migration:** Phased approach (5 phases, estimated 7-10 days total)

**Benefits:**
- Clean separation (Core vs modules)
- Dynamic discovery (database registry)
- Zero coupling (no hardcoded imports)
- Organized structure (everything in its place)
- Extensible (add modules without touching Core)
- Future-proof (platform for ecosystem)

**Alignment with Vision:**
- ✅ ARES Core = Standalone program
- ✅ Functions/apps = In database
- ✅ Master Control = Pulls and launches on demand
- ✅ Everything organized and smooth

**Ready for approval and implementation.**

---

**Document Status:** ARCHITECTURAL PROPOSAL
**Author:** Claude + Ultrathink Analysis
**Review Required:** Yes
**Implementation Estimate:** 7-10 days
**Breaking Changes:** Yes (but phased migration minimizes disruption)
