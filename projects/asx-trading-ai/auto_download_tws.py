"""
Auto-download TWS installer using Playwright.

Author: Claude Code
Date: 2025-10-13
"""

import asyncio
from playwright.async_api import async_playwright
import os


async def auto_download_tws():
    """Automatically download TWS installer."""

    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")

    print("\n" + "="*60)
    print("AUTO-DOWNLOADING TWS INSTALLER")
    print("="*60 + "\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("1. Opening TWS download page...")
        await page.goto('https://www.interactivebrokers.com/en/trading/tws.php', timeout=30000)

        print("2. Waiting for page to load...")
        await page.wait_for_load_state('networkidle', timeout=15000)

        # Try multiple selectors for download button
        selectors = [
            'a:has-text("Download")',
            'a:has-text("Windows")',
            'a[href*="download"]',
            'button:has-text("Download")',
            '.download-button',
            '[data-download]'
        ]

        print("3. Looking for download button...")

        download_button = None
        for selector in selectors:
            try:
                elements = await page.query_selector_all(selector)
                for element in elements:
                    text = await element.inner_text()
                    href = await element.get_attribute('href')

                    if 'windows' in text.lower() or (href and 'windows' in href.lower()):
                        download_button = element
                        print(f"   [OK] Found download button: {text.strip()}")
                        break

                if download_button:
                    break
            except:
                continue

        if not download_button:
            print("   [!] Could not find automatic download button")
            print("   -> Showing page for manual download...")
            print("\n" + "="*60)
            print("MANUAL DOWNLOAD INSTRUCTIONS")
            print("="*60)
            print("\n1. Look for 'Download TWS' or 'Latest' section")
            print("2. Click Windows download button")
            print("3. Wait for download to complete")
            print("\nBrowser will stay open for 2 minutes...")
            await page.wait_for_timeout(120000)
            await browser.close()
            return

        # Click download button
        print("4. Clicking download button...")

        try:
            async with page.expect_download(timeout=30000) as download_info:
                await download_button.click()
                print("   [OK] Download initiated...")

            download = await download_info.value
            filename = download.suggested_filename
            save_path = os.path.join(download_dir, filename)

            print(f"5. Saving file: {filename}")
            await download.save_as(save_path)

            print("\n" + "="*60)
            print("DOWNLOAD COMPLETE")
            print("="*60)
            print(f"\n[OK] Downloaded to: {save_path}")

            print("\n" + "="*60)
            print("NEXT STEPS")
            print("="*60)
            print(f"\n1. Run installer: {save_path}")
            print("2. Follow installation wizard")
            print("3. Launch TWS and log in with your IB account")
            print("4. Enable API: Configure -> API -> Settings")
            print("5. Test connection: python test_ib_connection.py")

        except Exception as e:
            print(f"\n[!] Download error: {e}")
            print("\nTrying alternative method...")

            # Alternative: Get direct download link
            href = await download_button.get_attribute('href')
            if href:
                print(f"Direct link: {href}")
                await page.goto(href)
                print("Download should start automatically...")
                await page.wait_for_timeout(30000)

        await browser.close()


if __name__ == '__main__':
    asyncio.run(auto_download_tws())
