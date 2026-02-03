#!/usr/bin/env python3
"""
Z-Library Login - One-time login, save session state

Works similar to notebooklm login
"""

import asyncio
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright not installed")
    print("Please run: pip install playwright")
    sys.exit(1)


def zlibrary_login():
    """Login to Z-Library and save session"""

    config_dir = Path.home() / ".zlibrary"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_dir.chmod(0o700)

    storage_state = config_dir / "storage_state.json"

    print("="*70)
    print("🔐 Z-Library Login")
    print("="*70)
    print("")
    print("Instructions:")
    print("  1. Browser will automatically open and visit Z-Library")
    print("  2. Please manually complete login (if needed)")
    print("  3. After successful login, return to terminal and press ENTER")
    print("  4. Session state will be saved, no need to login again")
    print("")

    with sync_playwright() as p:
        print("🚀 Launching browser...")
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(config_dir / "browser_profile"),
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        try:
            print("📖 Visiting Z-Library...")
            page.goto("https://zh.zlib.li/", wait_until='domcontentloaded', timeout=30000)

            print("")
            print("="*70)
            print("📋 Action Steps:")
            print("="*70)
            print("1. Complete login in the browser (if not logged in)")
            print("2. Wait until you see the Z-Library homepage")
            print("3. Return to terminal and press ENTER to continue")
            print("="*70)
            print("")

            input("✅ Login completed? Press ENTER to save session... ")

            # Save session state
            browser.storage_state(path=str(storage_state))
            storage_state.chmod(0o600)

            print("")
            print("✅ Session saved!")
            print(f"📁 Location: {storage_state}")
            print("")
            print("💡 You can now run the automation script:")
            print("   python3 /tmp/auto_download_and_upload.py <Z-Library URL>")
            print("")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()


def main():
    """Main function"""
    zlibrary_login()


if __name__ == "__main__":
    main()
