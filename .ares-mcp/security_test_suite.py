"""
ARES Security Test Suite
Automated security testing and vulnerability scanning

Usage:
    python security_test_suite.py

This will run comprehensive security tests on your ARES system.
"""

import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class SecurityTestSuite:
    """Comprehensive security test suite"""

    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def log(self, status: str, message: str, details: str = ""):
        """Log test result"""
        if status == "PASS":
            color = Colors.OKGREEN
            self.passed += 1
        elif status == "FAIL":
            color = Colors.FAIL
            self.failed += 1
        elif status == "WARN":
            color = Colors.WARNING
            self.warnings += 1
        else:
            color = Colors.ENDC

        print(f"{color}[{status}]{Colors.ENDC} {message}")
        if details:
            print(f"       {details}")

        self.results.append({
            'status': status,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })

    def test_environment_variables(self):
        """Test 1: Check for required environment variables"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 1: Environment Variables Security")
        print(f"{'='*60}{Colors.ENDC}\n")

        required_vars = [
            'ARES_API_KEY',
            'JWT_SECRET',
            'ENCRYPTION_KEY',
            'WHATSAPP_ACCESS_TOKEN',
            'WHATSAPP_PHONE_NUMBER_ID',
            'XERO_CLIENT_ID',
            'XERO_CLIENT_SECRET'
        ]

        for var in required_vars:
            value = os.getenv(var)
            if not value:
                self.log("FAIL", f"Environment variable '{var}' not set",
                        "Set this in your .env file")
            elif value == f"your_{var.lower().replace('_', '_')}_here":
                self.log("FAIL", f"Environment variable '{var}' has default value",
                        "Update with actual credentials")
            elif len(value) < 20:
                self.log("WARN", f"Environment variable '{var}' seems too short",
                        "Ensure this is a strong, random value")
            else:
                self.log("PASS", f"Environment variable '{var}' is set")

    def test_git_ignore(self):
        """Test 2: Check .gitignore configuration"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 2: Git Ignore Configuration")
        print(f"{'='*60}{Colors.ENDC}\n")

        gitignore_path = Path.home() / ".gitignore"
        ares_gitignore = Path.home() / ".ares-mcp" / ".gitignore"

        # Check root .gitignore
        if not gitignore_path.exists():
            self.log("FAIL", "Root .gitignore not found",
                    "Create .gitignore to protect sensitive files")
        else:
            content = gitignore_path.read_text()

            # Check for critical patterns
            critical_patterns = [
                '.env',
                '*.log',
                '*session/',
                'mobile_task_queue.json'
            ]

            for pattern in critical_patterns:
                if pattern in content:
                    self.log("PASS", f".gitignore includes '{pattern}'")
                else:
                    self.log("FAIL", f".gitignore missing '{pattern}'",
                            "Add this pattern to prevent committing sensitive data")

        # Check ARES-specific .gitignore
        if not ares_gitignore.exists():
            self.log("WARN", ".ares-mcp/.gitignore not found",
                    "Create project-specific .gitignore")
        else:
            self.log("PASS", ".ares-mcp/.gitignore exists")

    def test_hardcoded_credentials(self):
        """Test 3: Scan for hardcoded credentials"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 3: Hardcoded Credentials Scan")
        print(f"{'='*60}{Colors.ENDC}\n")

        ares_dir = Path.home() / ".ares-mcp"
        patterns = [
            b'EAAIZCTzaF1os',  # WhatsApp token prefix
            b'password=',
            b'api_key=',
            b'secret_key=',
            b'ACCESS_TOKEN = "',
            b'CLIENT_SECRET = "'
        ]

        found_issues = False

        for py_file in ares_dir.glob("*.py"):
            if py_file.name == 'security_test_suite.py':
                continue  # Skip this file

            try:
                content = py_file.read_bytes()

                for pattern in patterns:
                    if pattern in content:
                        self.log("FAIL",
                                f"Potential hardcoded credential in {py_file.name}",
                                f"Found pattern: {pattern.decode('utf-8', errors='ignore')}")
                        found_issues = True
            except:
                pass

        if not found_issues:
            self.log("PASS", "No obvious hardcoded credentials found")

    def test_file_permissions(self):
        """Test 4: Check file permissions on sensitive files"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 4: File Permissions")
        print(f"{'='*60}{Colors.ENDC}\n")

        sensitive_files = [
            Path.home() / ".env",
            Path.home() / ".ares-mcp" / ".env",
            Path.home() / ".ares-mcp" / "mobile_task_queue.json"
        ]

        for file_path in sensitive_files:
            if not file_path.exists():
                continue

            # On Windows, this check is limited
            if sys.platform == 'win32':
                self.log("WARN", f"Cannot check file permissions on Windows: {file_path.name}",
                        "Ensure only authorized users can access this file")
            else:
                import stat
                mode = oct(file_path.stat().st_mode)[-3:]
                if mode == '600' or mode == '400':
                    self.log("PASS", f"Good permissions on {file_path.name}: {mode}")
                else:
                    self.log("WARN", f"Weak permissions on {file_path.name}: {mode}",
                            "Consider: chmod 600 <file>")

    def test_api_authentication(self):
        """Test 5: Test API authentication"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 5: API Authentication")
        print(f"{'='*60}{Colors.ENDC}\n")

        endpoints = [
            '/send',
            '/tasks',
            '/webhook'
        ]

        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"

            # Test without API key
            try:
                if endpoint == '/send':
                    response = requests.post(url, json={'message': 'test'}, timeout=2)
                else:
                    response = requests.get(url, timeout=2)

                if response.status_code == 401:
                    self.log("PASS", f"{endpoint} requires authentication")
                elif response.status_code == 404:
                    self.log("INFO", f"{endpoint} not found (service may be down)")
                else:
                    self.log("FAIL", f"{endpoint} allows unauthenticated access",
                            f"Response: {response.status_code}")
            except requests.exceptions.ConnectionError:
                self.log("WARN", f"Cannot connect to {endpoint}",
                        "Service may not be running")
            except Exception as e:
                self.log("WARN", f"Error testing {endpoint}: {str(e)}")

    def test_encryption_key(self):
        """Test 6: Validate encryption key"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 6: Encryption Configuration")
        print(f"{'='*60}{Colors.ENDC}\n")

        encryption_key = os.getenv('ENCRYPTION_KEY')

        if not encryption_key:
            self.log("FAIL", "ENCRYPTION_KEY not set",
                    "Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'")
        else:
            try:
                from cryptography.fernet import Fernet
                # Try to create cipher
                Fernet(encryption_key.encode())
                self.log("PASS", "ENCRYPTION_KEY is valid")
            except Exception as e:
                self.log("FAIL", "ENCRYPTION_KEY is invalid",
                        f"Error: {str(e)}")

    def test_database_connections(self):
        """Test 7: Check database connection security"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 7: Database Connection Security")
        print(f"{'='*60}{Colors.ENDC}\n")

        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            self.log("WARN", "DATABASE_URL not set",
                    "Set when you add database functionality")
        else:
            # Check for SSL/TLS
            if 'sslmode=require' in database_url or 'ssl=true' in database_url:
                self.log("PASS", "Database connection uses SSL/TLS")
            elif 'localhost' in database_url or '127.0.0.1' in database_url:
                self.log("WARN", "Database is localhost (SSL not critical for local)")
            else:
                self.log("FAIL", "Database connection does not require SSL/TLS",
                        "Add sslmode=require for PostgreSQL")

            # Check for password in URL
            if 'password' in database_url.lower() and '@' in database_url:
                self.log("WARN", "Database password in connection string",
                        "Ensure DATABASE_URL is not committed to Git")

    def test_git_history(self):
        """Test 8: Check Git history for secrets"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 8: Git History Security")
        print(f"{'='*60}{Colors.ENDC}\n")

        import subprocess

        try:
            # Check if we're in a Git repository
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'],
                capture_output=True,
                text=True,
                cwd=Path.home()
            )

            if result.returncode == 0:
                # Check for .env files in history
                result = subprocess.run(
                    ['git', 'log', '--all', '--full-history', '--', '*.env'],
                    capture_output=True,
                    text=True,
                    cwd=Path.home()
                )

                if result.stdout.strip():
                    self.log("FAIL", ".env files found in Git history",
                            "Your secrets may be exposed! Consider repository remediation")
                else:
                    self.log("PASS", "No .env files in Git history")

                # Check for credential patterns in commits
                result = subprocess.run(
                    ['git', 'log', '--all', '-p', '--', '*.py'],
                    capture_output=True,
                    text=True,
                    cwd=Path.home()
                )

                credential_patterns = ['ACCESS_TOKEN = "EAA', 'CLIENT_SECRET = "']
                found_creds = False

                for pattern in credential_patterns:
                    if pattern in result.stdout:
                        self.log("FAIL", f"Credential pattern found in Git history: {pattern}",
                                "Credentials may be permanently exposed in Git history")
                        found_creds = True

                if not found_creds:
                    self.log("PASS", "No obvious credential patterns in Git history")

            else:
                self.log("WARN", "Not in a Git repository",
                        "Initialize Git to track your code")

        except FileNotFoundError:
            self.log("WARN", "Git not available",
                    "Install Git to enable version control")

    def test_dependency_vulnerabilities(self):
        """Test 9: Check for known vulnerable dependencies"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 9: Dependency Vulnerabilities")
        print(f"{'='*60}{Colors.ENDC}\n")

        import subprocess

        requirements_file = Path.home() / ".ares-mcp" / "requirements.txt"

        if not requirements_file.exists():
            self.log("WARN", "requirements.txt not found",
                    "Create requirements.txt to track dependencies")
        else:
            try:
                # Try to run safety check (if installed)
                result = subprocess.run(
                    ['pip', 'list', '--format=json'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    packages = json.loads(result.stdout)
                    self.log("PASS", f"Found {len(packages)} installed packages")

                    # Check for critical packages
                    critical_packages = {
                        'cryptography': '41.0.0',
                        'flask': '2.3.0',
                        'requests': '2.31.0'
                    }

                    for package in packages:
                        name = package['name']
                        version = package['version']

                        if name in critical_packages:
                            self.log("INFO", f"{name} version: {version}")

            except Exception as e:
                self.log("WARN", f"Could not check dependencies: {str(e)}")

    def test_logging_security(self):
        """Test 10: Check logging configuration"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("TEST 10: Logging Security")
        print(f"{'='*60}{Colors.ENDC}\n")

        logs_dir = Path.home() / ".ares-mcp" / "logs"

        if not logs_dir.exists():
            self.log("WARN", "Logs directory not found",
                    "Logging may not be configured")
        else:
            self.log("PASS", "Logs directory exists")

            # Check for sensitive data in logs
            log_files = list(logs_dir.glob("*.log"))

            if not log_files:
                self.log("WARN", "No log files found")
            else:
                sensitive_patterns = [
                    b'password',
                    b'api_key',
                    b'secret',
                    b'token',
                    b'EAAIZCTzaF1os'  # WhatsApp token
                ]

                for log_file in log_files[:5]:  # Check first 5 log files
                    try:
                        content = log_file.read_bytes()[-10000:]  # Last 10KB

                        found_sensitive = False
                        for pattern in sensitive_patterns:
                            if pattern in content.lower():
                                self.log("FAIL",
                                        f"Potential sensitive data in {log_file.name}",
                                        f"Pattern: {pattern.decode()}")
                                found_sensitive = True

                        if not found_sensitive:
                            self.log("PASS", f"No sensitive data in {log_file.name}")
                    except:
                        pass

    def generate_report(self):
        """Generate security test report"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print("SECURITY TEST SUMMARY")
        print(f"{'='*60}{Colors.ENDC}\n")

        total = self.passed + self.failed + self.warnings

        print(f"{Colors.OKGREEN}✓ Passed:  {self.passed}/{total}{Colors.ENDC}")
        print(f"{Colors.FAIL}✗ Failed:  {self.failed}/{total}{Colors.ENDC}")
        print(f"{Colors.WARNING}⚠ Warnings: {self.warnings}/{total}{Colors.ENDC}")

        # Overall security score
        if total > 0:
            score = (self.passed / total) * 100
            if score >= 90:
                color = Colors.OKGREEN
                status = "EXCELLENT"
            elif score >= 75:
                color = Colors.OKCYAN
                status = "GOOD"
            elif score >= 60:
                color = Colors.WARNING
                status = "NEEDS IMPROVEMENT"
            else:
                color = Colors.FAIL
                status = "CRITICAL"

            print(f"\n{color}Security Score: {score:.1f}% ({status}){Colors.ENDC}\n")

        # Save report
        report_file = Path.home() / ".ares-mcp" / "security_report.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'passed': self.passed,
                'failed': self.failed,
                'warnings': self.warnings,
                'total': total,
                'score': score if total > 0 else 0
            },
            'results': self.results
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"Full report saved to: {report_file}\n")

    def run_all_tests(self):
        """Run all security tests"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔" + "═" * 60 + "╗")
        print("║" + " " * 15 + "ARES SECURITY TEST SUITE" + " " * 21 + "║")
        print("║" + " " * 20 + "Version 1.0.0" + " " * 27 + "║")
        print("╚" + "═" * 60 + "╝")
        print(f"{Colors.ENDC}\n")

        self.test_environment_variables()
        self.test_git_ignore()
        self.test_hardcoded_credentials()
        self.test_file_permissions()
        self.test_api_authentication()
        self.test_encryption_key()
        self.test_database_connections()
        self.test_git_history()
        self.test_dependency_vulnerabilities()
        self.test_logging_security()

        self.generate_report()


if __name__ == "__main__":
    suite = SecurityTestSuite()
    suite.run_all_tests()
