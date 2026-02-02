"""
One-time setup: Opens a stealth browser so you can log into TikTok manually.
Saves the full browser profile (all cookies) for use by the automation script.

Usage:
    python login.py
"""

import base64
import json
import subprocess
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from config import PROFILE_DIR, COOKIES_FILE


def copy_to_clipboard(text):
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def main():
    print("=" * 60)
    print("  TikTok Streak — Login Setup (Stealth Mode)")
    print("=" * 60)
    print()
    print("A browser window will open.")
    print("1. Log into your TikTok account (QR code is easiest)")
    print("2. After login, navigate to Messages to confirm it works")
    print("3. Close the browser window when done")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        stealth = Stealth()
        page = context.new_page()
        stealth.apply_stealth_sync(page)

        page.goto("https://www.tiktok.com/login")

        print("Waiting for you to log in...")
        print("(Close the browser window when you're done)")
        print()

        # Wait until the browser is closed by the user
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass

        # Try to save — browser might already be closed
        try:
            storage = context.storage_state()
            with open(COOKIES_FILE, "w") as f:
                json.dump(storage, f, indent=2)
        except Exception:
            pass

        try:
            browser.close()
        except Exception:
            pass

    if not _cookies_saved():
        print("ERROR: Could not save cookies. Try again.")
        return

    cookies_b64 = _encode_cookies()

    print()
    print("=" * 60)
    print("  Login saved! Now add your GitHub Secrets.")
    print("=" * 60)
    print()
    print("Go to your repo → Settings → Secrets and variables → Actions")
    print("Add (or update) these secrets:")
    print()
    print("  TIKTOK_RECIPIENT  →  Display name of the person to message")
    print("  TIKTOK_MESSAGE    →  Message to send (default: 'hey :)')")
    print("  TIKTOK_COOKIES    →  Your session (see below)")
    print()

    if copy_to_clipboard(cookies_b64):
        print("TIKTOK_COOKIES value copied to your clipboard!")
        print("Just paste it as the secret value.")
    else:
        print("Copy this entire value for TIKTOK_COOKIES:")
        print()
        print(cookies_b64)

    print()
    print("Once secrets are set, the workflow runs daily at 9 AM EST.")
    print("You can also trigger it manually from the Actions tab.")


def _cookies_saved():
    try:
        with open(COOKIES_FILE) as f:
            data = json.load(f)
        return bool(data.get("cookies"))
    except Exception:
        return False


def _encode_cookies():
    """Encode only essential cookies to keep the value under GitHub's 64KB secret limit."""
    with open(COOKIES_FILE) as f:
        data = json.load(f)
    trimmed = {
        "cookies": [c for c in data["cookies"] if c["name"] in ESSENTIAL_COOKIES],
        "origins": [],
    }
    return base64.b64encode(json.dumps(trimmed).encode()).decode()


ESSENTIAL_COOKIES = [
    "sessionid", "sessionid_ss", "sid_tt", "sid_guard",
    "uid_tt", "uid_tt_ss", "sid_ucp_v1", "ssid_ucp_v1",
    "tt_csrf_token", "passport_csrf_token", "passport_csrf_token_default",
    "cmpl_token", "s_v_web_id", "ttwid", "odin_tt", "msToken",
    "multi_sids", "tt_chain_token", "store-idc", "store-country-code",
    "store-country-code-src", "tt-target-idc", "tt-target-idc-sign",
    "store-country-sign", "passport_fe_beating_status",
    "tt_session_tlb_tag", "last_login_method",
]


if __name__ == "__main__":
    main()
