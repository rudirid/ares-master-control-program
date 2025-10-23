"""
Download TWS installer using Playwright.

Author: Claude Code
Date: 2025-10-13
"""

import asyncio
from playwright.async_api import async_playwright
import os


async def download_tws():
    """Navigate to TWS download page and initiate download."""

    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    print("\n" + "="*60)
    print("TWS INSTALLER DOWNLOAD")
    print("="*60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("1. Opening TWS download page...")
        await page.goto('https://www.interactivebrokers.com/en/trading/tws.php', timeout=15000)

        print("2. Page loaded - looking for download button...")

        # Wait a moment for page to fully load
        await page.wait_for_timeout(2000)

        # Look for download links
        print("\nAvailable download options:")
        print("- Windows installer should be visible on page")
        print("- Look for 'Download TWS' or 'Latest' button")

        print("\n" + "="*60)
        print("MANUAL DOWNLOAD")
        print("="*60)
        print("\nClick the Windows download button in the browser.")
        print("Browser will stay open for 60 seconds...")
        print("File will download to: " + download_dir)

        # Wait for download to start (60 seconds max)
        try:
            async with page.expect_download(timeout=60000) as download_info:
                print("\nWaiting for download to start...")
                print("(Click any download button on the page)")

            download = await download_info.value
            filename = download.suggested_filename
            save_path = os.path.join(download_dir, filename)

            print(f"\n[OK] Download started: {filename}")
            await download.save_as(save_path)
            print(f"[OK] Saved to: {save_path}")

            print("\n" + "="*60)
            print("NEXT STEPS")
            print("="*60)
            print(f"\n1. Go to: {download_dir}")
            print(f"2. Run: {filename}")
            print("3. Follow installation wizard")
            print("4. Launch TWS and log in")
            print("5. Run: python test_ib_connection.py")

        except Exception as e:
            print(f"\n[!] No download detected: {e}")
            print("\nManually click the download button and wait...")
            await page.wait_for_timeout(30000)

        await browser.close()


if __name__ == '__main__':
    asyncio.run(download_tws())
