#!/usr/bin/env python3
"""
ARES Application Manager - CLI for Managing Standalone Applications
Manage, launch, monitor, and stop applications in the ARES ecosystem
"""

import sys
import json
from pathlib import Path
from typing import Optional
import argparse

# Fix UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.app_orchestrator import ApplicationOrchestrator, AppStatus


class AresApplicationManager:
    """CLI manager for ARES applications"""

    def __init__(self):
        self.orchestrator = ApplicationOrchestrator()

    def list_apps(self, app_type: Optional[str] = None, show_details: bool = False):
        """
        List registered applications

        Args:
            app_type: Filter by type
            show_details: Show detailed information
        """
        print("=" * 70)
        print("ARES REGISTERED APPLICATIONS")
        print("=" * 70)
        print()

        apps = self.orchestrator.list_applications(app_type)

        if not apps:
            print("No applications registered")
            return

        for app in apps:
            # Get current status
            status = self.orchestrator.get_status(app.app_id)
            status_icon = {
                AppStatus.RUNNING: "✓",
                AppStatus.STOPPED: "○",
                AppStatus.ERROR: "✗",
                AppStatus.UNKNOWN: "?",
                AppStatus.NOT_REGISTERED: "⚠"
            }.get(status, "?")

            print(f"{status_icon} {app.name} ({app.app_id})")
            print(f"   Status: {status.value}")
            print(f"   Type: {app.app_type}")
            print(f"   Version: {app.version}")

            if show_details:
                print(f"   Description: {app.description}")
                if app.path:
                    print(f"   Path: {app.path}")
                if app.capabilities:
                    print(f"   Capabilities: {', '.join(app.capabilities)}")
                print(f"   Launch Method: {app.launch_config.get('method', 'unknown')}")

            print()

        print(f"Total: {len(apps)} application(s)")
        print("=" * 70)

    def status(self, app_id: Optional[str] = None):
        """
        Show application status

        Args:
            app_id: Specific application ID, or None for all
        """
        print("=" * 70)
        print("ARES APPLICATION STATUS")
        print("=" * 70)
        print()

        if app_id:
            # Single app status
            app = self.orchestrator.get_application(app_id)
            if not app:
                print(f"Application '{app_id}' not found")
                return

            status = self.orchestrator.get_status(app_id)
            status_icon = {
                AppStatus.RUNNING: "✓",
                AppStatus.STOPPED: "○",
                AppStatus.ERROR: "✗",
                AppStatus.UNKNOWN: "?"
            }.get(status, "?")

            print(f"{status_icon} {app.name}")
            print(f"   ID: {app_id}")
            print(f"   Status: {status.value}")
            print(f"   Type: {app.app_type}")
            print(f"   Version: {app.version}")
            print(f"   Description: {app.description}")

            if app.path:
                print(f"   Path: {app.path}")

            # Monitoring info
            health_check = app.monitoring_config.get('health_check', {})
            if health_check:
                health_type = health_check.get('type', 'none')
                print(f"   Health Check: {health_type}")

            # Capabilities
            if app.capabilities:
                print(f"   Capabilities: {', '.join(app.capabilities)}")

        else:
            # All apps status
            status_all = self.orchestrator.get_status_all()

            for app_id, status in sorted(status_all.items()):
                app = self.orchestrator.get_application(app_id)
                status_icon = {
                    AppStatus.RUNNING: "✓",
                    AppStatus.STOPPED: "○",
                    AppStatus.ERROR: "✗",
                    AppStatus.UNKNOWN: "?"
                }.get(status, "?")

                print(f"{status_icon} {app.name:30} {status.value:12} ({app_id})")

        print()
        print("=" * 70)

    def launch(self, app_id: str, wait: bool = False):
        """
        Launch an application

        Args:
            app_id: Application identifier
            wait: Wait for completion (blocking)
        """
        app = self.orchestrator.get_application(app_id)
        if not app:
            print(f"✗ Application '{app_id}' not found")
            return

        print(f"Launching {app.name}...")

        # Check if requires approval
        requires_approval = app.launch_config.get('requires_approval', False)
        if requires_approval:
            print(f"⚠ This application requires approval to launch")
            print(f"   {app.description}")
            response = input("Proceed? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Launch cancelled")
                return

        success, message = self.orchestrator.launch(app_id, wait=wait)

        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")

    def stop(self, app_id: str, force: bool = False):
        """
        Stop a running application

        Args:
            app_id: Application identifier
            force: Force kill
        """
        app = self.orchestrator.get_application(app_id)
        if not app:
            print(f"✗ Application '{app_id}' not found")
            return

        action = "Force-stopping" if force else "Stopping"
        print(f"{action} {app.name}...")

        success, message = self.orchestrator.stop(app_id, force=force)

        if success:
            print(f"✓ {message}")
        else:
            print(f"✗ {message}")

    def capabilities(self, app_id: Optional[str] = None):
        """
        Show application capabilities

        Args:
            app_id: Specific application, or None for all
        """
        print("=" * 70)
        print("ARES APPLICATION CAPABILITIES")
        print("=" * 70)
        print()

        if app_id:
            # Single app
            app = self.orchestrator.get_application(app_id)
            if not app:
                print(f"Application '{app_id}' not found")
                return

            print(f"{app.name}:")
            if app.capabilities:
                for cap in app.capabilities:
                    print(f"  - {cap}")
            else:
                print("  (No capabilities listed)")
        else:
            # All apps
            for app_id, app in self.orchestrator.applications.items():
                if app.capabilities:
                    print(f"{app.name}:")
                    for cap in app.capabilities:
                        print(f"  - {cap}")
                    print()

        print("=" * 70)

    def find_capability(self, capability: str):
        """
        Find applications with a capability

        Args:
            capability: Capability to search for
        """
        print(f"Searching for capability: {capability}")
        print()

        app_ids = self.orchestrator.find_by_capability(capability)

        if not app_ids:
            print(f"No applications found with capability '{capability}'")
            return

        print(f"Found {len(app_ids)} application(s):")
        for app_id in app_ids:
            app = self.orchestrator.get_application(app_id)
            status = self.orchestrator.get_status(app_id)
            print(f"  - {app.name} ({app_id}) [{status.value}]")

    def register(
        self,
        app_id: str,
        name: str,
        path: str,
        app_type: str,
        description: str,
        launch_method: str,
        launch_command: str
    ):
        """Register a new application"""

        launch_config = {
            "method": launch_method,
            "command": launch_command,
            "working_dir": path,
            "auto_start": False,
            "requires_approval": True
        }

        success = self.orchestrator.register_application(
            app_id=app_id,
            name=name,
            path=path,
            app_type=app_type,
            description=description,
            launch_config=launch_config,
            save=True
        )

        if success:
            print(f"✓ Successfully registered application: {name} ({app_id})")
            print(f"   Type: {app_type}")
            print(f"   Path: {path}")
            print(f"   Launch: {launch_method}")
        else:
            print(f"✗ Failed to register application: {app_id}")

    def summary(self):
        """Show summary of all applications"""
        self.orchestrator.print_summary()

    def info(self, app_id: str):
        """Show detailed info about an application"""
        app = self.orchestrator.get_application(app_id)
        if not app:
            print(f"Application '{app_id}' not found")
            return

        print("=" * 70)
        print(f"APPLICATION: {app.name}")
        print("=" * 70)
        print()

        print(f"ID: {app_id}")
        print(f"Name: {app.name}")
        print(f"Type: {app.app_type}")
        print(f"Version: {app.version}")
        print(f"Status: {app.status}")
        print()

        print(f"Description:")
        print(f"  {app.description}")
        print()

        if app.path:
            print(f"Path: {app.path}")
            print()

        print("Launch Configuration:")
        for key, value in app.launch_config.items():
            print(f"  {key}: {value}")
        print()

        if app.monitoring_config:
            print("Monitoring Configuration:")
            for key, value in app.monitoring_config.items():
                print(f"  {key}: {value}")
            print()

        if app.capabilities:
            print("Capabilities:")
            for cap in app.capabilities:
                print(f"  - {cap}")
            print()

        if app.dependencies:
            print("Dependencies:")
            for dep_type, deps in app.dependencies.items():
                if isinstance(deps, list):
                    print(f"  {dep_type}: {', '.join(deps)}")
                else:
                    print(f"  {dep_type}: {deps}")
            print()

        print("Metadata:")
        for key, value in app.metadata.items():
            print(f"  {key}: {value}")

        print("=" * 70)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ARES Application Manager - Manage standalone applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all applications
  python ares_app_manager.py list

  # List with details
  python ares_app_manager.py list --details

  # Show status of all apps
  python ares_app_manager.py status

  # Show status of specific app
  python ares_app_manager.py status asx-trading

  # Launch an application
  python ares_app_manager.py launch asx-trading

  # Launch and wait for completion
  python ares_app_manager.py launch asx-trading --wait

  # Stop an application
  python ares_app_manager.py stop asx-trading

  # Force stop
  python ares_app_manager.py stop asx-trading --force

  # Show capabilities
  python ares_app_manager.py capabilities

  # Find apps by capability
  python ares_app_manager.py find live_trading

  # Register new application
  python ares_app_manager.py register my-app \\
      --name "My Application" \\
      --path "C:\\path\\to\\app" \\
      --type python_service \\
      --description "My custom app" \\
      --launch-method batch \\
      --launch-command run.bat

  # Show detailed info
  python ares_app_manager.py info asx-trading

  # Summary
  python ares_app_manager.py summary
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # List command
    list_parser = subparsers.add_parser('list', help='List registered applications')
    list_parser.add_argument('--type', help='Filter by type')
    list_parser.add_argument('--details', action='store_true', help='Show detailed information')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show application status')
    status_parser.add_argument('app_id', nargs='?', help='Application ID (optional)')

    # Launch command
    launch_parser = subparsers.add_parser('launch', help='Launch an application')
    launch_parser.add_argument('app_id', help='Application ID')
    launch_parser.add_argument('--wait', action='store_true', help='Wait for completion')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop an application')
    stop_parser.add_argument('app_id', help='Application ID')
    stop_parser.add_argument('--force', action='store_true', help='Force kill')

    # Capabilities command
    cap_parser = subparsers.add_parser('capabilities', help='Show capabilities')
    cap_parser.add_argument('app_id', nargs='?', help='Application ID (optional)')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find apps by capability')
    find_parser.add_argument('capability', help='Capability to search for')

    # Register command
    register_parser = subparsers.add_parser('register', help='Register new application')
    register_parser.add_argument('app_id', help='Unique application ID')
    register_parser.add_argument('--name', required=True, help='Application name')
    register_parser.add_argument('--path', required=True, help='Application path')
    register_parser.add_argument('--type', required=True, help='Application type')
    register_parser.add_argument('--description', required=True, help='Description')
    register_parser.add_argument('--launch-method', required=True, help='Launch method (batch, subprocess, etc.)')
    register_parser.add_argument('--launch-command', required=True, help='Launch command')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show detailed application info')
    info_parser.add_argument('app_id', help='Application ID')

    # Summary command
    subparsers.add_parser('summary', help='Show application summary')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = AresApplicationManager()

    # Execute command
    try:
        if args.command == 'list':
            manager.list_apps(args.type, args.details)
        elif args.command == 'status':
            manager.status(args.app_id)
        elif args.command == 'launch':
            manager.launch(args.app_id, args.wait)
        elif args.command == 'stop':
            manager.stop(args.app_id, args.force)
        elif args.command == 'capabilities':
            manager.capabilities(args.app_id)
        elif args.command == 'find':
            manager.find_capability(args.capability)
        elif args.command == 'register':
            manager.register(
                args.app_id,
                args.name,
                args.path,
                args.type,
                args.description,
                args.launch_method,
                args.launch_command
            )
        elif args.command == 'info':
            manager.info(args.app_id)
        elif args.command == 'summary':
            manager.summary()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
