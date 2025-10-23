#!/usr/bin/env python3
"""
ARES Version Checker - Dynamic Latest Version Detection
Finds and verifies the LATEST Ares version automatically
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Optional, Dict, Tuple

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse_version(version_str: str) -> Tuple[int, int, int]:
    """Parse version string like '2.5.0' into tuple (2, 5, 0)"""
    try:
        parts = version_str.strip().split('.')
        return tuple(int(p) for p in parts[:3])
    except:
        return (0, 0, 0)

def find_latest_ares_version() -> Optional[Dict]:
    """
    Dynamically find the LATEST Ares version by checking all possible locations
    Returns dict with path, version, and verification status
    """

    candidates = []
    base_dir = Path("C:/Users/riord")

    # Search for all potential Ares locations
    potential_locations = [
        base_dir / "ares-master-control-program",
        base_dir / ".ares-mcp",
        base_dir / "ares-mcp-server",
    ]

    # Also check for versioned directories
    for item in base_dir.iterdir():
        if item.is_dir() and 'ares' in item.name.lower():
            potential_locations.append(item)

    # Check each location for valid Ares installation
    for location in potential_locations:
        if not location.exists():
            continue

        # Try to read version from config
        config_path = location / "config" / "ares.yaml"
        version = None

        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    version = config.get('ares_version')
            except:
                pass

        # Fallback: check directives file for version
        if not version:
            directives_path = location / "ares-core-directives.md"
            if directives_path.exists():
                try:
                    with open(directives_path, 'r', encoding='utf-8') as f:
                        first_lines = f.read(500)
                        if 'v2.5' in first_lines or 'v2.1' in first_lines:
                            # Extract version from markdown header
                            for line in first_lines.split('\n'):
                                if 'v2.' in line.lower():
                                    # Simple extraction
                                    if 'v2.5' in line:
                                        version = '2.5.0'
                                    elif 'v2.1' in line:
                                        version = '2.1.0'
                                    break
                except:
                    pass

        if version:
            # Verify core files exist
            has_core_modules = (location / "core" / "validation.py").exists()
            has_directives = (location / "ares-core-directives.md").exists()
            has_patterns = (location / "proven-patterns.md").exists()

            completeness = sum([has_core_modules, has_directives, has_patterns])

            candidates.append({
                'path': location,
                'version': version,
                'version_tuple': parse_version(version),
                'has_core_modules': has_core_modules,
                'has_directives': has_directives,
                'has_patterns': has_patterns,
                'completeness': completeness
            })

    if not candidates:
        return None

    # Sort by version (descending), then by completeness
    candidates.sort(key=lambda x: (x['version_tuple'], x['completeness']), reverse=True)

    return candidates[0]

def check_ares_version():
    """Check which version of Ares is loaded and find the latest"""

    print("=" * 60)
    print("ARES DYNAMIC VERSION CHECKER")
    print("=" * 60)
    print()

    print("Scanning for Ares installations...")
    print()

    latest = find_latest_ares_version()

    if not latest:
        print("✗ NO ARES INSTALLATIONS FOUND")
        print()
        print("Expected locations:")
        print("  - C:/Users/riord/ares-master-control-program")
        print("  - C:/Users/riord/.ares-mcp")
        print()
        print("=" * 60)
        print("STATUS: ✗ ARES NOT FOUND")
        print("=" * 60)
        return None

    # Found the latest version
    print(f"✓ Found LATEST Ares Installation")
    print(f"  Path: {latest['path']}")
    print(f"  Version: {latest['version']}")
    print()

    # Verify completeness
    print("Installation Check:")

    if latest['has_core_modules']:
        core_path = latest['path'] / "core"
        modules = ['validation.py', 'output.py', 'patterns.py']

        print("  Core Modules:")
        for module in modules:
            module_path = core_path / module
            if module_path.exists():
                size = module_path.stat().st_size
                print(f"    ✓ {module} ({size:,} bytes)")
            else:
                print(f"    ✗ {module} (MISSING)")
    else:
        print("  ✗ Core modules not found")

    print()

    if latest['has_directives'] or latest['has_patterns']:
        knowledge_files = [
            'ares-core-directives.md',
            'proven-patterns.md',
            'tech-success-matrix.md',
            'decision-causality.md',
            'project-evolution.md'
        ]

        print("  Knowledge Base:")
        for kfile in knowledge_files:
            kpath = latest['path'] / kfile
            if kpath.exists():
                size = kpath.stat().st_size / 1024  # KB
                print(f"    ✓ {kfile} ({size:.1f} KB)")

    print()

    # Overall status
    if latest['completeness'] >= 2:
        print("=" * 60)
        print(f"STATUS: ✓ ARES {latest['version']} READY (LATEST)")
        print("=" * 60)
        print()
        print("This is the LATEST verified version.")
        print()
        print("You can invoke with:")
        print('  "Launch Ares Master Control Program"')
        print('  "Load Ares"')
        print('  "Activate Ares"')
        print()

        # Write latest version info to a file for Claude to read
        version_info_path = latest['path'] / ".ares_latest_version.txt"
        try:
            with open(version_info_path, 'w', encoding='utf-8') as f:
                f.write(f"LATEST_VERSION={latest['version']}\n")
                f.write(f"LATEST_PATH={latest['path']}\n")
                f.write(f"VERIFIED=true\n")
        except:
            pass

        return latest
    else:
        print("=" * 60)
        print("STATUS: ⚠ INCOMPLETE INSTALLATION")
        print("=" * 60)
        return None

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("Installing PyYAML...")
        os.system("pip install pyyaml")
        import yaml

    check_ares_version()
