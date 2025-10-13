"""
Ares Browser Automation Module

Purpose: Automate browser interactions for tasks like:
- Creating MCP projects on claude.ai
- Uploading files to web interfaces
- Navigating authenticated sessions
- Future web-based operations

Usage:
    python browser_automation.py --task create_mcp_project --project-name "Ares MCP"
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeout
import json
import argparse
from datetime import datetime


class AresBrowserAutomation:
    """Master Control Program - Browser Automation Commander"""

    def __init__(self, headless: bool = False, session_dir: str = None):
        self.headless = headless
        self.session_dir = session_dir or str(Path.home() / ".ares-mcp" / "browser-session")
        self.browser: Browser = None
        self.page: Page = None
        self.browser_context = None
        self.playwright = None

    async def initialize(self):
        """Initialize browser with persistent session"""
        print(f"[ARES] Initializing browser automation...")
        print(f"[ARES] Session directory: {self.session_dir}")

        self.playwright = await async_playwright().start()

        # Use Chromium with persistent context for session management
        self.browser_context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.session_dir,
            headless=self.headless,
            viewport={"width": 1920, "height": 1080},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )

        # Get or create first page
        if len(self.browser_context.pages) > 0:
            self.page = self.browser_context.pages[0]
        else:
            self.page = await self.browser_context.new_page()

        print(f"[ARES] Browser initialized successfully")

    async def close(self):
        """Close browser and cleanup"""
        if self.browser_context:
            await self.browser_context.close()
        if self.playwright:
            await self.playwright.stop()
        print(f"[ARES] Browser automation closed")

    async def navigate_to_claude_ai(self) -> bool:
        """
        Navigate to claude.ai and check authentication status

        Returns:
            bool: True if authenticated, False if login required
        """
        print(f"[ARES] Navigating to claude.ai...")

        try:
            await self.page.goto("https://claude.ai", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)  # Wait for page to settle

            # Check if we're on login page or authenticated
            current_url = self.page.url
            print(f"[ARES] Current URL: {current_url}")

            # Common patterns for authenticated state
            if "claude.ai/chat" in current_url or "claude.ai/projects" in current_url:
                print(f"[ARES] [OK] Already authenticated")
                return True
            elif "login" in current_url or "auth" in current_url:
                print(f"[ARES] [X] Login required")
                return False
            else:
                # Ambiguous - check for login button
                login_button = await self.page.query_selector('button:has-text("Login"), a:has-text("Login")')
                if login_button:
                    print(f"[ARES] [X] Login required (login button detected)")
                    return False
                else:
                    print(f"[ARES] [OK] Likely authenticated (no login button)")
                    return True

        except PlaywrightTimeout:
            print(f"[ARES] [X] Timeout navigating to claude.ai")
            return False
        except Exception as e:
            print(f"[ARES] [X] Error navigating: {str(e)}")
            return False

    async def wait_for_manual_login(self, timeout: int = 300):
        """
        Wait for user to manually complete login

        Args:
            timeout: Maximum seconds to wait (default 5 minutes)
        """
        print(f"[ARES] Waiting for manual login (timeout: {timeout}s)...")
        print(f"[ARES] Please complete login in the browser window")

        start_time = datetime.now()

        while (datetime.now() - start_time).seconds < timeout:
            await asyncio.sleep(2)
            current_url = self.page.url

            # Check if login completed
            if "claude.ai/chat" in current_url or "claude.ai/projects" in current_url:
                print(f"[ARES] [OK] Login completed successfully")
                return True

            # Check if still on login page
            if "login" not in current_url and "auth" not in current_url:
                # Might be authenticated
                login_button = await self.page.query_selector('button:has-text("Login"), a:has-text("Login")')
                if not login_button:
                    print(f"[ARES] [OK] Login appears successful")
                    return True

        print(f"[ARES] [X] Login timeout reached")
        return False

    async def create_mcp_project(self, project_name: str, files_to_upload: list[str]) -> bool:
        """
        Create an MCP project on claude.ai and upload files

        Args:
            project_name: Name of the project to create
            files_to_upload: List of file paths to upload

        Returns:
            bool: True if successful, False otherwise
        """
        print(f"[ARES] Creating MCP project: {project_name}")
        print(f"[ARES] Files to upload: {len(files_to_upload)}")

        try:
            # Navigate to projects page
            await self.page.goto("https://claude.ai/projects", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)

            # Look for "New Project" button (selector will need to be updated based on actual page)
            # This is a template - actual selectors need to be discovered
            new_project_button = await self.page.query_selector(
                'button:has-text("New Project"), button:has-text("Create Project")'
            )

            if not new_project_button:
                print(f"[ARES] [X] Could not find 'New Project' button")
                print(f"[ARES] Current page HTML structure:")
                # Get page structure for debugging
                buttons = await self.page.query_selector_all('button')
                print(f"[ARES] Found {len(buttons)} buttons on page")
                for i, btn in enumerate(buttons[:10]):  # Show first 10
                    text = await btn.inner_text()
                    print(f"[ARES]   Button {i}: {text[:50]}")
                return False

            # Click new project button
            await new_project_button.click()
            await asyncio.sleep(1)

            # Enter project name
            name_input = await self.page.query_selector('input[placeholder*="name" i], input[type="text"]')
            if name_input:
                await name_input.fill(project_name)
                print(f"[ARES] [OK] Entered project name")
            else:
                print(f"[ARES] [X] Could not find project name input")
                return False

            # Upload files
            for file_path in files_to_upload:
                if not os.path.exists(file_path):
                    print(f"[ARES] [X] File not found: {file_path}")
                    continue

                # Look for file upload input
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(file_path)
                    print(f"[ARES] [OK] Uploaded: {os.path.basename(file_path)}")
                    await asyncio.sleep(1)
                else:
                    print(f"[ARES] [X] Could not find file upload input")
                    return False

            # Submit/Create project
            create_button = await self.page.query_selector(
                'button:has-text("Create"), button:has-text("Submit"), button[type="submit"]'
            )
            if create_button:
                await create_button.click()
                print(f"[ARES] [OK] Clicked create button")
                await asyncio.sleep(3)
            else:
                print(f"[ARES] [X] Could not find create/submit button")
                return False

            print(f"[ARES] [OK] Project creation completed")
            return True

        except Exception as e:
            print(f"[ARES] [X] Error creating project: {str(e)}")
            return False

    async def take_screenshot(self, filename: str = None):
        """Take screenshot for debugging"""
        if not filename:
            filename = f"ares-screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
        filepath = str(Path.home() / ".ares-mcp" / filename)
        await self.page.screenshot(path=filepath, full_page=True)
        print(f"[ARES] Screenshot saved: {filepath}")
        return filepath

    async def interactive_mode(self):
        """
        Launch browser in interactive mode for manual operations
        Keeps browser open until user closes it
        """
        print(f"[ARES] Interactive mode activated")
        print(f"[ARES] Browser will stay open - close window when done")

        # Navigate to claude.ai
        authenticated = await self.navigate_to_claude_ai()

        if not authenticated:
            print(f"[ARES] Waiting for manual login...")
            await self.wait_for_manual_login()

        # Keep alive until browser closes
        try:
            while True:
                await asyncio.sleep(1)
                # Check if page still exists
                if self.page.is_closed():
                    break
        except KeyboardInterrupt:
            print(f"\n[ARES] Interrupted by user")

        print(f"[ARES] Interactive mode ended")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Ares Browser Automation")
    parser.add_argument("--task", choices=["create_mcp_project", "interactive", "test_auth"],
                       default="interactive", help="Task to perform")
    parser.add_argument("--project-name", default="Master Control Program Ares",
                       help="Project name for MCP creation")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--files", nargs="+", help="Files to upload (for create_mcp_project task)")

    args = parser.parse_args()

    # Initialize automation
    automation = AresBrowserAutomation(headless=args.headless)

    try:
        await automation.initialize()

        if args.task == "test_auth":
            # Test authentication status
            authenticated = await automation.navigate_to_claude_ai()
            if not authenticated:
                print("[ARES] Not authenticated - launching interactive mode for login")
                await automation.wait_for_manual_login()
            await automation.take_screenshot("auth-test.png")

        elif args.task == "create_mcp_project":
            # Create MCP project
            authenticated = await automation.navigate_to_claude_ai()
            if not authenticated:
                login_success = await automation.wait_for_manual_login()
                if not login_success:
                    print("[ARES] Login failed or timeout - aborting")
                    return

            # Default files if none specified
            files = args.files or [
                str(Path.home() / ".ares-mcp" / "proven-patterns.md"),
                str(Path.home() / ".ares-mcp" / "project-evolution.md"),
                str(Path.home() / ".ares-mcp" / "decision-causality.md"),
                str(Path.home() / ".ares-mcp" / "tech-success-matrix.md"),
                str(Path.home() / ".ares-mcp" / "ares-core-directives.md"),
            ]

            success = await automation.create_mcp_project(args.project_name, files)
            if success:
                print("[ARES] [OK] MCP project created successfully")
            else:
                print("[ARES] [X] MCP project creation failed")
                await automation.take_screenshot("creation-failed.png")

        elif args.task == "interactive":
            # Interactive mode
            await automation.interactive_mode()

    finally:
        await automation.close()


if __name__ == "__main__":
    print("=" * 70)
    print("ARES MASTER CONTROL PROGRAM - BROWSER AUTOMATION")
    print("=" * 70)
    asyncio.run(main())
