"""
Simple IB connection test without Playwright.

Tests:
1. Check if ib_insync is installed
2. Check if TWS/Gateway is running
3. Attempt API connection

Author: Claude Code
Date: 2025-10-13
"""

import sys
import os


def check_ib_insync():
    """Check if ib_insync is installed."""
    print("\n" + "="*60)
    print("1. IB_INSYNC LIBRARY CHECK")
    print("="*60)

    try:
        import ib_insync
        print(f"[OK] ib_insync installed (v{ib_insync.__version__})")
        return True
    except ImportError:
        print("[X] ib_insync not installed")
        print("-> Install: pip install ib_insync")
        return False


def check_tws_running():
    """Check if TWS or Gateway is running."""
    print("\n" + "="*60)
    print("2. TWS/GATEWAY PROCESS CHECK")
    print("="*60)

    import psutil

    tws_processes = ['tws.exe', 'ibgateway.exe', 'java.exe']
    found = []

    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            name = proc.info['name']
            if name in tws_processes:
                cmdline = proc.info.get('cmdline', [])
                if any('tws' in str(c).lower() or 'ibgateway' in str(c).lower() for c in cmdline):
                    found.append(name)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    if found:
        print(f"[OK] IB software running: {', '.join(set(found))}")
        return True
    else:
        print("[X] TWS/Gateway not running")
        print("-> Start TWS or IB Gateway first")
        return False


def test_connection():
    """Test API connection to TWS/Gateway."""
    print("\n" + "="*60)
    print("3. API CONNECTION TEST")
    print("="*60)

    try:
        from ib_insync import IB

        ib = IB()

        # Try TWS port (7497 paper, 7496 live)
        print("\nAttempting connection to TWS (port 7497)...")
        try:
            ib.connect('127.0.0.1', 7497, clientId=1, timeout=5)
            print("[OK] Connected to TWS Paper Trading!")

            # Get account info
            accounts = ib.managedAccounts()
            print(f"[OK] Accounts: {accounts}")

            ib.disconnect()
            return True
        except Exception as e:
            print(f"[!] TWS connection failed: {e}")

        # Try Gateway port (4002 paper, 4001 live)
        print("\nAttempting connection to Gateway (port 4002)...")
        try:
            ib.connect('127.0.0.1', 4002, clientId=1, timeout=5)
            print("[OK] Connected to Gateway Paper Trading!")

            accounts = ib.managedAccounts()
            print(f"[OK] Accounts: {accounts}")

            ib.disconnect()
            return True
        except Exception as e:
            print(f"[!] Gateway connection failed: {e}")

        print("\n[X] Could not connect to any IB software")
        print("\nTroubleshooting:")
        print("1. Start TWS or Gateway")
        print("2. Enable API: Configure -> API -> Settings")
        print("3. Enable 'Enable ActiveX and Socket Clients'")
        print("4. Check port: TWS=7497 (paper) Gateway=4002 (paper)")

        return False

    except ImportError:
        print("[X] ib_insync not installed")
        return False


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("INTERACTIVE BROKERS CONNECTION TEST")
    print("="*60)

    # Check 1: ib_insync installed
    has_lib = check_ib_insync()

    if not has_lib:
        print("\n" + "="*60)
        print("INSTALL REQUIRED")
        print("="*60)
        print("\nRun: pip install ib_insync")
        return

    # Check 2: TWS/Gateway running
    is_running = check_tws_running()

    if not is_running:
        print("\n" + "="*60)
        print("START TWS/GATEWAY")
        print("="*60)
        print("\n1. Download TWS: https://www.interactivebrokers.com/en/trading/tws.php")
        print("2. Install and launch")
        print("3. Log in with your IB account")
        print("4. Run this script again")
        return

    # Check 3: API connection
    connected = test_connection()

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    if has_lib and is_running and connected:
        print("\n[OK] All checks passed! Ready for algo trading.")
        print("\nNext: Test ASX stock data retrieval")
    else:
        print("\n[!] Setup incomplete")
        if not has_lib:
            print("- Install ib_insync")
        if not is_running:
            print("- Start TWS/Gateway")
        if not connected:
            print("- Enable API in TWS settings")

    print("\n" + "="*60 + "\n")


if __name__ == '__main__':
    main()
