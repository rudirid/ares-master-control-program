"""
Check Interactive Brokers setup status using Playwright.

Verifies:
1. IB account login page accessible
2. TWS/Gateway software status (check if installed)
3. API settings accessible

Author: Claude Code
Date: 2025-10-13
"""

import asyncio
from playwright.async_api import async_playwright
import sys


async def check_ib_setup():
    """Check IB setup status."""
    print("\n" + "="*60)
    print("INTERACTIVE BROKERS SETUP CHECK")
    print("="*60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Check 1: IB Login Page
        print("1. Checking IB website access...")
        try:
            await page.goto('https://www.interactivebrokers.com/en/home.php', timeout=10000)
            print("   [OK] IB website accessible")
        except Exception as e:
            print(f"   [X] Cannot access IB website: {e}")
            await browser.close()
            return False

        # Check 2: Navigate to Client Portal
        print("\n2. Checking Client Portal...")
        try:
            await page.goto('https://www.interactivebrokers.com/sso/Login', timeout=10000)

            # Check if login form exists
            login_visible = await page.is_visible('input[name="username"]', timeout=5000)
            if login_visible:
                print("   [OK] Client Portal login page loaded")
                print("   -> You can log in manually to verify account access")
            else:
                print("   [!] Login form not detected (page structure may have changed)")
        except Exception as e:
            print(f"   [!] Client Portal check failed: {e}")

        # Check 3: TWS Download Page
        print("\n3. Checking TWS (Trader Workstation) download...")
        try:
            await page.goto('https://www.interactivebrokers.com/en/trading/tws.php', timeout=10000)
            print("   [OK] TWS download page accessible")
            print("   -> Download TWS if not already installed")
        except Exception as e:
            print(f"   [X] Cannot access TWS page: {e}")

        # Keep browser open for manual verification
        print("\n" + "="*60)
        print("MANUAL VERIFICATION REQUIRED")
        print("="*60)
        print("\nThe browser will stay open. Please verify:")
        print("1. Log in to Client Portal (if not logged in)")
        print("2. Check if you have API access enabled")
        print("3. Verify ASX trading permissions")
        print("\nPress ENTER when done to close browser...")

        # Wait for user input
        await asyncio.get_event_loop().run_in_executor(None, input)

        await browser.close()
        return True


async def check_tws_installed():
    """Check if TWS is installed locally."""
    import os

    print("\n" + "="*60)
    print("LOCAL TWS INSTALLATION CHECK")
    print("="*60 + "\n")

    # Common TWS installation paths
    possible_paths = [
        r"C:\Jts\tws.exe",
        r"C:\Program Files\Jts\tws.exe",
        r"C:\Program Files (x86)\Jts\tws.exe",
        r"C:\Users\{}\Jts\tws.exe".format(os.getenv('USERNAME')),
    ]

    found = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"[OK] TWS found at: {path}")
            found = True
            break

    if not found:
        print("[!] TWS not found in common locations")
        print("-> Download from: https://www.interactivebrokers.com/en/trading/tws.php")

    return found


async def check_ib_gateway():
    """Check if IB Gateway is installed."""
    import os

    print("\n" + "="*60)
    print("IB GATEWAY CHECK")
    print("="*60 + "\n")

    # Common Gateway paths
    possible_paths = [
        r"C:\Jts\ibgateway\latest\ibgateway.exe",
        r"C:\Program Files\Jts\ibgateway\latest\ibgateway.exe",
    ]

    found = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"[OK] IB Gateway found at: {path}")
            found = True
            break

    if not found:
        print("[!] IB Gateway not found")
        print("-> Gateway is lighter than TWS for API trading")

    return found


async def main():
    """Main check routine."""

    # Check local installations first
    tws_installed = await check_tws_installed()
    gateway_installed = await check_ib_gateway()

    # Check web access
    await check_ib_setup()

    # Summary
    print("\n" + "="*60)
    print("SETUP SUMMARY")
    print("="*60 + "\n")

    if tws_installed or gateway_installed:
        print("[OK] IB software installed")
    else:
        print("[X] Need to install TWS or Gateway")

    print("\nNext Steps:")
    print("1. Install TWS/Gateway if not installed")
    print("2. Log in to TWS/Gateway")
    print("3. Enable API in settings (Configure → API → Settings)")
    print("4. Run test connection script")

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
