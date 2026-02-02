"""
Sends a TikTok DM to maintain a streak.
Uses saved session cookies to avoid needing to log in each time.

Usage:
    python send_message.py           # Uses cookies.json from disk
    TIKTOK_COOKIES_B64=... python send_message.py  # Uses base64-encoded cookies from env

All config is read from environment variables (see README).
"""

import base64
import json
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright
from config import RECIPIENT, MESSAGE, COOKIES_FILE


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")


def load_cookies():
    """Load cookies from base64 env var (GitHub Actions) or local file."""
    cookies_b64 = os.environ.get("TIKTOK_COOKIES_B64")
    if cookies_b64:
        log("Loading cookies from TIKTOK_COOKIES_B64 environment variable")
        return json.loads(base64.b64decode(cookies_b64).decode("utf-8"))

    if os.path.exists(COOKIES_FILE):
        log(f"Loading cookies from {COOKIES_FILE}")
        with open(COOKIES_FILE) as f:
            return json.load(f)

    log("ERROR: No cookies found.")
    log("  Run `python login.py` first, then copy your cookies to GitHub Secrets.")
    log("  See README for full instructions.")
    sys.exit(1)


def main():
    if not RECIPIENT:
        log("ERROR: TIKTOK_RECIPIENT is not set.")
        log("  Set it as a GitHub Actions secret or environment variable.")
        log("  See README for instructions.")
        sys.exit(1)

    log(f"Sending message to {RECIPIENT}: {MESSAGE}")

    storage_state = load_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            storage_state=storage_state,
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Navigate to TikTok messages
        log("Navigating to TikTok messages...")
        page.goto("https://www.tiktok.com/messages", wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Check if we're redirected to login (session expired)
        if "/login" in page.url:
            log("ERROR: Session expired. Re-run login.py and update TIKTOK_COOKIES secret.")
            browser.close()
            sys.exit(1)

        # Find the conversation with the recipient
        log(f"Looking for conversation with {RECIPIENT}...")
        conversation = page.locator(f'text="{RECIPIENT}"').first
        conversation.wait_for(state="visible", timeout=10000)
        conversation.click()
        page.wait_for_timeout(2000)

        # Find the message input and type the message
        log("Typing message...")
        message_input = page.locator(
            '[data-e2e="message-input"], '
            '[contenteditable="true"], '
            'div[role="textbox"]'
        ).last
        message_input.wait_for(state="visible", timeout=10000)
        message_input.click()
        message_input.fill(MESSAGE)
        page.wait_for_timeout(500)

        # Send the message (press Enter or click send button)
        log("Sending message...")
        send_button = page.locator(
            '[data-e2e="message-send"], '
            'button[aria-label="Send"], '
            'button:has-text("Send")'
        ).first
        try:
            send_button.wait_for(state="visible", timeout=3000)
            send_button.click()
        except Exception:
            message_input.press("Enter")

        page.wait_for_timeout(2000)

        # Save updated cookies locally (in case session was refreshed)
        if not os.environ.get("TIKTOK_COOKIES_B64"):
            updated_storage = context.storage_state()
            with open(COOKIES_FILE, "w") as f:
                json.dump(updated_storage, f, indent=2)

        browser.close()

    log("Message sent successfully!")


if __name__ == "__main__":
    main()
