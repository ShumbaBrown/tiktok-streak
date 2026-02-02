"""
One-time setup: Opens a browser so you can log into TikTok manually.
Your session cookies are saved to cookies.json for use by the automation script.

Usage:
    python login.py
"""

import base64
import json
import platform
import subprocess
from playwright.sync_api import sync_playwright
from config import PROFILE_DIR, COOKIES_FILE


def copy_to_clipboard(text):
    """Try to copy text to system clipboard."""
    system = platform.system()
    try:
        if system == "Darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        elif system == "Linux":
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
            return True
        elif system == "Windows":
            subprocess.run(["clip"], input=text.encode(), check=True)
            return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return False


def main():
    print("=" * 60)
    print("  TikTok Streak — Login Setup")
    print("=" * 60)
    print()
    print("A browser window will open.")
    print("1. Log into your TikTok account")
    print("2. Navigate to Messages to confirm you're logged in")
    print("3. Close the browser window when done")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()
        page.goto("https://www.tiktok.com/login")

        print("Waiting for login to complete...")
        print("(After scanning the QR code, wait for the page to redirect)")
        print()

        # Wait until URL changes away from /login (means login succeeded)
        page.wait_for_url("**/!(login)*", timeout=300000)
        print("Login detected! Navigating to messages to verify...")

        page.goto("https://www.tiktok.com/messages", wait_until="networkidle")
        page.wait_for_timeout(3000)

        if "/login" in page.url:
            print("WARNING: Still on login page. Session may not have saved correctly.")
        else:
            print("Messages page loaded successfully!")

        # Save session cookies and storage state
        storage = context.storage_state()
        with open(COOKIES_FILE, "w") as f:
            json.dump(storage, f, indent=2)

        browser.close()

    # Base64 encode for GitHub Actions
    with open(COOKIES_FILE) as f:
        cookies_b64 = base64.b64encode(f.read().encode()).decode()

    print()
    print("=" * 60)
    print("  Login saved! Now add your GitHub Secrets.")
    print("=" * 60)
    print()
    print("Go to your forked repo → Settings → Secrets and variables → Actions")
    print("Add these 3 secrets:")
    print()
    print("  TIKTOK_RECIPIENT  →  The display name of the person to message")
    print("  TIKTOK_MESSAGE    →  The message to send (or skip for default 'hey :)')")
    print(f"  TIKTOK_COOKIES    →  Your base64-encoded session (see below)")
    print()

    if copy_to_clipboard(cookies_b64):
        print("Your TIKTOK_COOKIES value has been copied to your clipboard!")
        print("Just paste it as the secret value.")
    else:
        print("Copy this entire value for TIKTOK_COOKIES:")
        print()
        print(cookies_b64)

    print()
    print("Once secrets are set, the workflow runs daily at 9 AM EST.")
    print("You can also trigger it manually from the Actions tab.")


if __name__ == "__main__":
    main()
