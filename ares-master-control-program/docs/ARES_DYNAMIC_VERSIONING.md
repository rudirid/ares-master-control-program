# ARES Dynamic Versioning System

## Problem Solved

**Old System**: Hardcoded v2.5.0 in CLAUDE.md
- Would break when v3.0 is released
- Required manual updates to CLAUDE.md
- Could load outdated version unknowingly
- Technical debt accumulation

**New System**: Dynamic version detection
- ✅ Automatically finds LATEST version
- ✅ No hardcoded version numbers
- ✅ Future-proof (works for v3.0, v4.0, etc.)
- ✅ Verifies installation completeness
- ✅ Zero manual updates needed

---

## How It Works

### 1. Version Detection Script

**File**: `C:\Users\riord\ares-master-control-program\check_ares_version.py`

**What it does**:
1. Scans all `*ares*` directories in `C:\Users\riord\`
2. Reads version from:
   - `config/ares.yaml` (preferred)
   - `ares-core-directives.md` (fallback)
3. Parses version numbers (e.g., 2.5.0 > 2.1.0)
4. Verifies core files exist (completeness check)
5. Selects HIGHEST version with complete installation
6. Creates marker file with results

**Example Output**:
```
============================================================
ARES DYNAMIC VERSION CHECKER
============================================================

Scanning for Ares installations...

✓ Found LATEST Ares Installation
  Path: C:\Users\riord\ares-master-control-program
  Version: 2.5.0

Installation Check:
  Core Modules:
    ✓ validation.py (10,910 bytes)
    ✓ output.py (8,593 bytes)
    ✓ patterns.py (10,027 bytes)

  Knowledge Base:
    ✓ ares-core-directives.md (27.1 KB)
    ✓ proven-patterns.md (17.8 KB)
    [... more files ...]

============================================================
STATUS: ✓ ARES 2.5.0 READY (LATEST)
============================================================
```

### 2. Version Marker File

**File**: `C:\Users\riord\ares-master-control-program\.ares_latest_version.txt`

**Content**:
```
LATEST_VERSION=2.5.0
LATEST_PATH=C:\Users\riord\ares-master-control-program
VERIFIED=true
```

**Purpose**: Cache the detection results so Claude can quickly read without running Python every time.

### 3. Updated CLAUDE.md (Primary Directive)

**File**: `C:\Users\riord\CLAUDE.md`

**Key Changes**:

❌ **OLD** (Hardcoded):
```markdown
**Current Version**: v2.5.0 (Released 2025-10-15)
**Location**: `C:\Users\riord\ares-master-control-program\`
```

✅ **NEW** (Dynamic):
```markdown
## CRITICAL: DYNAMIC VERSION LOADING

**DO NOT hardcode version numbers in your logic.**

1. Check for version marker file: `.ares_latest_version.txt`
2. If marker doesn't exist, run: `check_ares_version.py`
3. Load from detected LATEST_PATH
4. Confirm LATEST_VERSION on invocation
```

---

## Invocation Flow

When you say "Launch Ares Master Control Program":

```
1. Claude checks: .ares_latest_version.txt exists?

   YES → Read LATEST_VERSION and LATEST_PATH
   NO  → Run check_ares_version.py
         → Creates .ares_latest_version.txt
         → Read LATEST_VERSION and LATEST_PATH

2. Load files from {LATEST_PATH}:
   - ares-core-directives.md
   - config/ares.yaml
   - proven-patterns.md
   - tech-success-matrix.md
   - decision-causality.md
   - core/*.py (if exists)

3. Confirm activation:
   [ARES {LATEST_VERSION} ACTIVATED - LATEST VERIFIED]

   Loaded from: {LATEST_PATH}

   Status: READY - Internal Validation Active
```

---

## Benefits

### 1. Future-Proof
When you release Ares v3.0:
- Update `config/ares.yaml` with `ares_version: "3.0.0"`
- Run `check_ares_version.py`
- System automatically detects v3.0 as latest
- No CLAUDE.md changes needed ✅

### 2. Multiple Version Support
If you have:
- `C:\Users\riord\ares-v2.5\` (version 2.5.0)
- `C:\Users\riord\ares-v3.0\` (version 3.0.0)

System will:
- Detect both
- Parse versions: 3.0.0 > 2.5.0
- Auto-load v3.0 as latest ✅

### 3. Completeness Verification
Won't load incomplete installations:
- Checks for core modules
- Checks for directives
- Checks for knowledge base
- Only loads if ≥2/3 components exist

### 4. Zero Technical Debt
No hardcoded version numbers to update:
- ❌ No "v2.5.0" in CLAUDE.md
- ❌ No hardcoded paths
- ✅ All dynamic detection
- ✅ Self-maintaining system

---

## Version Comparison Examples

### Example 1: v2.5 vs v2.1
```
Found:
- C:\Users\riord\ares-master-control-program (v2.5.0, complete)
- C:\Users\riord\.ares-mcp (v2.1.0, complete)

Parse versions:
- 2.5.0 → (2, 5, 0)
- 2.1.0 → (2, 1, 0)

Sort descending: (2, 5, 0) > (2, 1, 0)

Result: Load v2.5.0 ✅
```

### Example 2: v3.0 vs v2.5
```
Found:
- C:\Users\riord\ares-v3 (v3.0.0, complete)
- C:\Users\riord\ares-master-control-program (v2.5.0, complete)

Parse versions:
- 3.0.0 → (3, 0, 0)
- 2.5.0 → (2, 5, 0)

Sort descending: (3, 0, 0) > (2, 5, 0)

Result: Load v3.0.0 ✅
```

### Example 3: Incomplete Installation
```
Found:
- C:\Users\riord\ares-beta (v3.0.0-beta, 1/3 complete)
- C:\Users\riord\ares-master-control-program (v2.5.0, 3/3 complete)

Parse versions:
- 3.0.0-beta → (3, 0, 0) [but incomplete]
- 2.5.0 → (2, 5, 0) [complete]

Sort by: (version DESC, completeness DESC)

Result: Load v2.5.0 (most complete) ✅
```

---

## Anti-Patterns Prevented

### ❌ Hardcoded Version Assumptions
**Before**:
```python
# CLAUDE.md
Current Version: v2.5.0
Location: C:\Users\riord\ares-master-control-program\
```

Problem: When v3.0 exists, still loads v2.5.0

**After**:
```python
# CLAUDE.md
Run detection → Load LATEST
```

Solution: Always loads highest version ✅

### ❌ Unfounded "Latest" Claims
**Before**:
```
"Loading latest Ares v2.5.0..."
(without actually checking if it's latest)
```

**After**:
```
Run check_ares_version.py → Verify → Confirm
"Loading LATEST Ares {detected_version} - VERIFIED"
```

Truth Protocol compliant ✅

---

## Testing

### Test 1: Current State
```bash
python C:\Users\riord\ares-master-control-program\check_ares_version.py
```

Expected:
```
STATUS: ✓ ARES 2.5.0 READY (LATEST)
```

### Test 2: Marker File Created
```bash
cat C:\Users\riord\ares-master-control-program\.ares_latest_version.txt
```

Expected:
```
LATEST_VERSION=2.5.0
LATEST_PATH=C:\Users\riord\ares-master-control-program
VERIFIED=true
```

### Test 3: Invocation
Say: "Launch Ares Master Control Program"

Expected response:
```
[ARES 2.5.0 ACTIVATED - LATEST VERIFIED]

Loaded from: C:\Users\riord\ares-master-control-program

[... capabilities listed ...]
```

---

## When You Release v3.0

**Steps**:
1. Create new directory (any name with "ares" in it)
2. Add `config/ares.yaml` with `ares_version: "3.0.0"`
3. Add core files (directives, modules, knowledge base)
4. Run: `python check_ares_version.py`
5. Done! System auto-detects v3.0 as latest

**NO changes needed to**:
- ❌ CLAUDE.md
- ❌ Any invocation commands
- ❌ Any documentation

Everything is **automatic** ✅

---

## Summary

**Old System**:
- Hardcoded v2.5.0 everywhere
- Manual updates required
- Technical debt accumulation
- Could load wrong version

**New System**:
- ✅ Scans all Ares directories
- ✅ Finds highest version number
- ✅ Verifies completeness
- ✅ Caches result in marker file
- ✅ No hardcoded versions
- ✅ Future-proof for v3.0+
- ✅ Truth Protocol compliant
- ✅ Zero maintenance

**You can now confidently invoke Ares knowing it will ALWAYS load the actual latest verified version.**

---

**Created**: 2025-10-22
**System**: Dynamic Version Detection v1.0
**Status**: Active and Verified ✓
