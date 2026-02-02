"""
Builds Playwright storage_state from a manually copied sessionid cookie.

Usage:
    python export_session.py
"""

import base64
import json
import subprocess
from config import COOKIES_FILE


def copy_to_clipboard(text):
    try:
        subprocess.run(["pbcopy"], input=text.encode(), check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def main():
    print("=" * 60)
    print("  TikTok Streak — Export Session")
    print("=" * 60)
    print()
    print("Paste your sessionid cookie value from Safari Web Inspector")
    print("(Storage tab → Cookies → tiktok.com → sessionid)")
    print()

    session_id = input("sessionid: ").strip()
    if not session_id:
        print("ERROR: No value entered.")
        return

    storage = {
        "cookies": [
            {
                "name": "sessionid",
                "value": session_id,
                "domain": ".tiktok.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "sessionid_ss",
                "value": session_id,
                "domain": ".tiktok.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
            {
                "name": "sid_tt",
                "value": session_id,
                "domain": ".tiktok.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "None",
            },
        ],
        "origins": [],
    }

    with open(COOKIES_FILE, "w") as f:
        json.dump(storage, f, indent=2)

    cookies_b64 = base64.b64encode(json.dumps(storage).encode()).decode()

    print()
    if copy_to_clipboard(cookies_b64):
        print("TIKTOK_COOKIES value copied to your clipboard!")
    else:
        print("Copy this value for TIKTOK_COOKIES:")
        print()
        print(cookies_b64)

    print()
    print("Update your TIKTOK_COOKIES secret at:")
    print("  Repo → Settings → Secrets → Actions → TIKTOK_COOKIES → Update")


if __name__ == "__main__":
    main()
