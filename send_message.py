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


def save_debug_screenshot(page, name):
    """Save a screenshot for debugging CI failures."""
    try:
        path = f"/tmp/{name}.png"
        page.screenshot(path=path)
        log(f"Debug screenshot saved to {path}")
        # Print page URL and title for context
        log(f"Current URL: {page.url}")
        log(f"Page title: {page.title()}")
    except Exception as e:
        log(f"Could not save screenshot: {e}")


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
        page.wait_for_timeout(5000)

        # Check if we're redirected to login (session expired)
        if "/login" in page.url:
            save_debug_screenshot(page, "login-redirect")
            log("ERROR: Session expired. Re-run login.py and update TIKTOK_COOKIES secret.")
            browser.close()
            sys.exit(1)

        # Wait for conversation list to fully load (skeleton placeholders disappear)
        log("Waiting for conversations to load...")
        for attempt in range(30):
            page.wait_for_timeout(2000)
            body_text = page.locator("body").inner_text()
            # Once we see real user names (not just nav items), the list has loaded
            lines = [l.strip() for l in body_text.split("\n") if l.strip()]
            non_nav = [l for l in lines if l not in (
                "TikTok", "For You", "Shop", "Explore", "Following", "Friends",
                "LIVE", "Messages", "Activity", "Upload", "Profile", "More",
                "Post video", "", "39"
            )]
            if len(non_nav) > 3:
                log(f"Conversations loaded (attempt {attempt + 1})")
                break
            log(f"Still loading... (attempt {attempt + 1})")
        else:
            log("WARNING: Conversations may not have fully loaded")

        save_debug_screenshot(page, "messages-page")

        # Find the conversation with the recipient — try multiple strategies
        log(f"Looking for conversation with {RECIPIENT}...")
        conversation = None

        # Strategy 1: Exact text match
        loc = page.locator(f'text="{RECIPIENT}"').first
        try:
            loc.wait_for(state="visible", timeout=10000)
            conversation = loc
            log("Found conversation via exact text match")
        except Exception:
            log("Exact text match failed, trying partial match...")

        # Strategy 2: Case-insensitive partial match
        if not conversation:
            loc = page.get_by_text(RECIPIENT, exact=False).first
            try:
                loc.wait_for(state="visible", timeout=10000)
                conversation = loc
                log("Found conversation via partial text match")
            except Exception:
                log("Partial text match also failed, trying broader search...")

        if not conversation:
            save_debug_screenshot(page, "conversation-not-found")
            # Dump visible text to help debug
            try:
                body_text = page.locator("body").inner_text()
                log(f"Page text preview (first 1000 chars):\n{body_text[:1000]}")
            except Exception:
                pass
            log(f"ERROR: Could not find conversation with '{RECIPIENT}'.")
            log("  Make sure TIKTOK_RECIPIENT matches the exact display name in your messages.")
            browser.close()
            sys.exit(1)

        conversation.click()
        page.wait_for_timeout(3000)

        save_debug_screenshot(page, "conversation-opened")

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

        save_debug_screenshot(page, "message-sent")

        # Save updated cookies locally (in case session was refreshed)
        if not os.environ.get("TIKTOK_COOKIES_B64"):
            updated_storage = context.storage_state()
            with open(COOKIES_FILE, "w") as f:
                json.dump(updated_storage, f, indent=2)

        browser.close()

    log("Message sent successfully!")


if __name__ == "__main__":
    main()
