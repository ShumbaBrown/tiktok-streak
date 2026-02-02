"""
Extracts TikTok cookies from Safari and saves them in Playwright's storage_state format.

Usage:
    python extract_safari_cookies.py

Note: macOS may prompt you to grant Full Disk Access or a similar permission
for Terminal/iTerm to read Safari's cookie database.
"""

import base64
import json
import platform
import shutil
import sqlite3
import subprocess
import tempfile
from config import COOKIES_FILE


SAFARI_COOKIES_DB = (
    "/Users/{user}/Library/Containers/com.apple.Safari/Data/Library/Cookies/Cookies.binarycookies"
)
# Safari also stores cookies in a sqlite database
SAFARI_COOKIES_SQLITE = (
    "/Users/{user}/Library/Cookies/Cookies.binarycookies"
)


def copy_to_clipboard(text):
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def extract_via_javascript():
    """Use osascript to grab cookies from Safari via JavaScript."""
    # We'll navigate Safari to TikTok and extract cookies via document.cookie
    script = '''
    tell application "Safari"
        activate
        tell window 1
            set current tab to (make new tab with properties {URL:"https://www.tiktok.com/messages"})
        end tell
        delay 5
        set cookieStr to do JavaScript "document.cookie" in current tab of window 1
        return cookieStr
    end tell
    '''
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def parse_cookie_string(cookie_str):
    """Convert a document.cookie string into Playwright storage_state format."""
    cookies = []
    for pair in cookie_str.split("; "):
        if "=" not in pair:
            continue
        name, _, value = pair.partition("=")
        cookies.append({
            "name": name.strip(),
            "value": value.strip(),
            "domain": ".tiktok.com",
            "path": "/",
            "httpOnly": False,
            "secure": True,
            "sameSite": "None",
        })
    return {"cookies": cookies, "origins": []}


def main():
    print("=" * 60)
    print("  TikTok Streak — Extract Safari Cookies")
    print("=" * 60)
    print()
    print("Make sure you're logged into TikTok in Safari.")
    print("This will briefly use Safari to grab your session cookies.")
    print()

    cookie_str = extract_via_javascript()
    if not cookie_str:
        print("ERROR: Could not extract cookies from Safari.")
        print("Make sure Safari is open and you're logged into TikTok.")
        print("You may need to allow Terminal access in:")
        print("  System Settings → Privacy & Security → Automation")
        return

    storage = parse_cookie_string(cookie_str)

    if not storage["cookies"]:
        print("ERROR: No cookies found. Make sure you're logged into TikTok in Safari.")
        return

    print(f"Extracted {len(storage['cookies'])} cookies from Safari.")

    with open(COOKIES_FILE, "w") as f:
        json.dump(storage, f, indent=2)

    cookies_b64 = base64.b64encode(json.dumps(storage).encode()).decode()

    print()
    print("=" * 60)
    print("  Cookies saved! Now add your GitHub Secrets.")
    print("=" * 60)
    print()
    print("Go to your repo → Settings → Secrets and variables → Actions")
    print("Add these secrets:")
    print()
    print("  TIKTOK_RECIPIENT  →  The display name of the person to message")
    print("  TIKTOK_MESSAGE    →  The message to send (or skip for default 'hey :)')")
    print("  TIKTOK_COOKIES    →  Your base64-encoded session (see below)")
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
