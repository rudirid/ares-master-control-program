"""
ARES Application Orchestrator - Layer 3: Application Management
Manages standalone applications (trading, WhatsApp, etc.)
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import psutil
import requests


class AppStatus(Enum):
    """Application status"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"
    NOT_REGISTERED = "not_registered"


class LaunchMethod(Enum):
    """How to launch an application"""
    BATCH = "batch"  # Windows batch file
    SUBPROCESS = "subprocess"  # Python subprocess
    MCP = "mcp"  # MCP server
    DOCKER = "docker"  # Docker container
    AUTOMATIC = "automatic"  # Auto-launched (ARES core)


@dataclass
class ApplicationInfo:
    """Application metadata"""
    app_id: str
    name: str
    path: Optional[str]
    app_type: str
    description: str
    status: str
    version: str
    launch_config: Dict
    monitoring_config: Dict
    dependencies: Dict
    capabilities: List[str]
    metadata: Dict


class ApplicationOrchestrator:
    """
    ARES Layer 3: Application Orchestration

    Manages lifecycle of standalone applications:
    - Launch applications
    - Monitor health
    - Stop applications
    - Query status
    - Register new applications
    """

    DEFAULT_REGISTRY_PATH = Path.home() / ".ares" / "applications" / "registry.json"

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize application orchestrator

        Args:
            registry_path: Path to application registry
        """
        self.registry_path = registry_path or self.DEFAULT_REGISTRY_PATH
        self.registry_data = {}
        self.applications = {}
        self.running_processes = {}  # app_id -> process handle

        self.load_registry()

    def load_registry(self) -> bool:
        """Load application registry from file"""
        if not self.registry_path.exists():
            print(f"Warning: Registry not found at {self.registry_path}")
            return False

        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                self.registry_data = json.load(f)

            # Parse applications
            self._parse_applications()
            return True

        except Exception as e:
            print(f"Error loading registry: {e}")
            return False

    def _parse_applications(self):
        """Parse registry data into ApplicationInfo objects"""
        self.applications = {}

        for app_id, app_data in self.registry_data.get('applications', {}).items():
            app_info = ApplicationInfo(
                app_id=app_id,
                name=app_data.get('name', app_id),
                path=app_data.get('path'),
                app_type=app_data.get('type', 'unknown'),
                description=app_data.get('description', ''),
                status=app_data.get('status', 'registered'),
                version=app_data.get('version', '0.0.0'),
                launch_config=app_data.get('launch', {}),
                monitoring_config=app_data.get('monitoring', {}),
                dependencies=app_data.get('dependencies', {}),
                capabilities=app_data.get('capabilities', []),
                metadata=app_data.get('metadata', {})
            )
            self.applications[app_id] = app_info

    def get_application(self, app_id: str) -> Optional[ApplicationInfo]:
        """Get application info by ID"""
        return self.applications.get(app_id)

    def list_applications(self, app_type: Optional[str] = None) -> List[ApplicationInfo]:
        """
        List all registered applications

        Args:
            app_type: Filter by type (python_service, automation, mcp_server, etc.)

        Returns:
            List of ApplicationInfo objects
        """
        apps = list(self.applications.values())

        if app_type:
            apps = [a for a in apps if a.app_type == app_type]

        return sorted(apps, key=lambda a: a.name)

    def launch(self, app_id: str, wait: bool = False) -> Tuple[bool, str]:
        """
        Launch an application

        Args:
            app_id: Application identifier
            wait: Wait for process to complete (blocking)

        Returns:
            (success: bool, message: str)
        """
        app = self.get_application(app_id)
        if not app:
            return False, f"Application '{app_id}' not registered"

        # Check if already running
        status = self.get_status(app_id)
        if status == AppStatus.RUNNING:
            return False, f"Application '{app.name}' is already running"

        # Get launch configuration
        launch_config = app.launch_config
        method = launch_config.get('method')

        try:
            if method == 'batch':
                return self._launch_batch(app, wait)
            elif method == 'subprocess':
                return self._launch_subprocess(app, wait)
            elif method == 'mcp':
                return self._launch_mcp(app)
            elif method == 'automatic':
                return False, f"{app.name} launches automatically (core system)"
            else:
                return False, f"Unknown launch method: {method}"

        except Exception as e:
            return False, f"Launch failed: {str(e)}"

    def _launch_batch(self, app: ApplicationInfo, wait: bool) -> Tuple[bool, str]:
        """Launch via Windows batch file"""
        working_dir = app.launch_config.get('working_dir', app.path)
        command = app.launch_config.get('command')

        if not working_dir or not command:
            return False, "Missing working_dir or command in launch config"

        # Build full command path
        cmd_path = Path(working_dir) / command

        if not cmd_path.exists():
            return False, f"Batch file not found: {cmd_path}"

        # Launch process
        if wait:
            # Blocking - wait for completion
            result = subprocess.run(
                str(cmd_path),
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            success = result.returncode == 0
            message = f"Completed with code {result.returncode}"
            if result.stdout:
                message += f"\n{result.stdout}"
            return success, message
        else:
            # Non-blocking - start and detach
            process = subprocess.Popen(
                str(cmd_path),
                cwd=working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.running_processes[app.app_id] = process
            return True, f"Launched {app.name} (PID: {process.pid})"

    def _launch_subprocess(self, app: ApplicationInfo, wait: bool) -> Tuple[bool, str]:
        """Launch via Python subprocess"""
        command = app.launch_config.get('command')
        working_dir = app.launch_config.get('working_dir', app.path)

        if not command:
            return False, "Missing command in launch config"

        # Parse command
        cmd_parts = command.split()

        process = subprocess.Popen(
            cmd_parts,
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if wait:
            stdout, stderr = process.communicate()
            success = process.returncode == 0
            message = f"Completed with code {process.returncode}"
            return success, message
        else:
            self.running_processes[app.app_id] = process
            return True, f"Launched {app.name} (PID: {process.pid})"

    def _launch_mcp(self, app: ApplicationInfo) -> Tuple[bool, str]:
        """Launch MCP server (placeholder - MCP handles this)"""
        mcp_name = app.launch_config.get('mcp_server_name')
        return True, f"MCP server '{mcp_name}' managed by MCP system"

    def stop(self, app_id: str, force: bool = False) -> Tuple[bool, str]:
        """
        Stop a running application

        Args:
            app_id: Application identifier
            force: Force kill (SIGKILL) instead of graceful shutdown

        Returns:
            (success: bool, message: str)
        """
        app = self.get_application(app_id)
        if not app:
            return False, f"Application '{app_id}' not registered"

        # Check if we have process handle
        if app_id in self.running_processes:
            process = self.running_processes[app_id]
            try:
                if force:
                    process.kill()
                else:
                    process.terminate()

                # Wait for termination
                process.wait(timeout=10)
                del self.running_processes[app_id]
                return True, f"Stopped {app.name}"

            except subprocess.TimeoutExpired:
                process.kill()
                del self.running_processes[app_id]
                return True, f"Force-killed {app.name} (timeout)"

            except Exception as e:
                return False, f"Stop failed: {str(e)}"
        else:
            return False, f"{app.name} not tracked (may be running independently)"

    def get_status(self, app_id: str) -> AppStatus:
        """
        Get current status of an application

        Args:
            app_id: Application identifier

        Returns:
            AppStatus enum value
        """
        app = self.get_application(app_id)
        if not app:
            return AppStatus.NOT_REGISTERED

        # Check if we're tracking the process
        if app_id in self.running_processes:
            process = self.running_processes[app_id]
            if process.poll() is None:
                return AppStatus.RUNNING
            else:
                # Process ended
                del self.running_processes[app_id]
                return AppStatus.STOPPED

        # Try health check
        health_config = app.monitoring_config.get('health_check', {})
        health_type = health_config.get('type')

        if health_type == 'http':
            return self._check_http_health(health_config)
        elif health_type == 'process':
            return self._check_process_health(health_config)
        elif health_type == 'internal':
            return AppStatus.RUNNING  # Core systems always running
        else:
            return AppStatus.UNKNOWN

    def _check_http_health(self, config: Dict) -> AppStatus:
        """Check health via HTTP endpoint"""
        url = config.get('url')
        if not url:
            return AppStatus.UNKNOWN

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return AppStatus.RUNNING
            else:
                return AppStatus.ERROR
        except requests.RequestException:
            return AppStatus.STOPPED

    def _check_process_health(self, config: Dict) -> AppStatus:
        """Check health via process name"""
        process_name = config.get('process_name')
        if not process_name:
            return AppStatus.UNKNOWN

        # Check if process is running
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return AppStatus.RUNNING

        return AppStatus.STOPPED

    def get_status_all(self) -> Dict[str, AppStatus]:
        """Get status of all applications"""
        return {
            app_id: self.get_status(app_id)
            for app_id in self.applications.keys()
        }

    def register_application(
        self,
        app_id: str,
        name: str,
        path: str,
        app_type: str,
        description: str,
        launch_config: Dict,
        monitoring_config: Optional[Dict] = None,
        capabilities: Optional[List[str]] = None,
        save: bool = True
    ) -> bool:
        """
        Register a new application

        Args:
            app_id: Unique identifier
            name: Human-readable name
            path: Filesystem path to application
            app_type: Type (python_service, automation, etc.)
            description: Description
            launch_config: Launch configuration dict
            monitoring_config: Monitoring configuration dict
            capabilities: List of capabilities
            save: Save registry to file

        Returns:
            True if registered successfully
        """
        if app_id in self.applications:
            print(f"Warning: Application {app_id} already registered")
            return False

        app_data = {
            "name": name,
            "path": path,
            "type": app_type,
            "description": description,
            "status": "registered",
            "version": "1.0.0",
            "launch": launch_config,
            "monitoring": monitoring_config or {},
            "dependencies": {},
            "capabilities": capabilities or [],
            "metadata": {
                "created": datetime.now().strftime("%Y-%m-%d"),
                "owner": "riord",
                "category": "custom"
            }
        }

        # Add to registry data
        self.registry_data['applications'][app_id] = app_data

        # Update metadata
        self.registry_data['metadata']['total_applications'] = len(self.registry_data['applications'])
        self.registry_data['last_updated'] = datetime.now().strftime("%Y-%m-%d")

        # Reload
        self._parse_applications()

        if save:
            return self._save_registry()

        return True

    def _save_registry(self) -> bool:
        """Save registry to file"""
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving registry: {e}")
            return False

    def get_capabilities(self, app_id: str) -> List[str]:
        """Get application capabilities"""
        app = self.get_application(app_id)
        return app.capabilities if app else []

    def find_by_capability(self, capability: str) -> List[str]:
        """Find applications with a specific capability"""
        return [
            app_id for app_id, app in self.applications.items()
            if capability in app.capabilities
        ]

    def print_summary(self):
        """Print registry summary"""
        print("=" * 70)
        print("ARES APPLICATION REGISTRY")
        print("=" * 70)

        stats = self.registry_data.get('metadata', {})
        print(f"Total Applications: {stats.get('total_applications', 0)}")
        print(f"Active: {stats.get('active_applications', 0)}")
        print(f"Registered: {stats.get('registered_applications', 0)}")
        print()

        # Show status of each app
        print("Application Status:")
        for app_id, app in self.applications.items():
            status = self.get_status(app_id)
            status_icon = {
                AppStatus.RUNNING: "✓",
                AppStatus.STOPPED: "○",
                AppStatus.ERROR: "✗",
                AppStatus.UNKNOWN: "?"
            }.get(status, "?")

            print(f"  {status_icon} {app.name} ({app_id}) - {status.value}")

        print("=" * 70)


# Convenience function
def create_app_orchestrator(registry_path: Optional[Path] = None) -> ApplicationOrchestrator:
    """Create application orchestrator instance"""
    return ApplicationOrchestrator(registry_path)
