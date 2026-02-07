"""
Sends a TikTok DM to maintain a streak.
Uses saved session cookies to avoid needing to log in each time.

Usage:
    python send_message.py           # Uses cookies.json from disk
    TIKTOK_COOKIES_B64=... python send_message.py  # Uses base64-encoded cookies from env

All config is read from environment variables (see README).

TIKTOK_RECIPIENT can be either:
  - A username (starting with @, e.g., "@johndoe") — will search for user and open DM
  - A display name (e.g., "John Doe") — will look for this name in existing conversations
"""

import base64
import json
import os
import sys
from datetime import datetime
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
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
        log(f"Current URL: {page.url}")
        log(f"Page title: {page.title()}")
    except Exception as e:
        log(f"Could not save screenshot: {e}")


def find_conversation_by_username(page, username):
    """Navigate to user's profile and open DM from there."""
    username_clean = username.lstrip("@")
    log(f"Looking up user profile: @{username_clean}")

    # Go to user's profile
    profile_url = f"https://www.tiktok.com/@{username_clean}"
    page.goto(profile_url, wait_until="networkidle")
    page.wait_for_timeout(3000)

    save_debug_screenshot(page, "user-profile")

    # Look for the message/DM button on their profile
    message_button = page.locator(
        '[data-e2e="message-button"], '
        'button:has-text("Message"), '
        '[aria-label*="Message"], '
        '[aria-label*="message"]'
    ).first

    try:
        message_button.wait_for(state="visible", timeout=10000)
        log("Found message button on profile")
        message_button.click()
        page.wait_for_timeout(3000)
        return True
    except Exception:
        log("Could not find message button on profile")
        return False


def find_conversation_by_display_name(page, display_name):
    """Search through conversation list for display name."""
    log(f"Looking for conversation with display name: {display_name}")

    # Navigate to messages
    page.goto("https://www.tiktok.com/messages", wait_until="networkidle")
    page.wait_for_timeout(5000)

    # Check if logged in
    if "/login" in page.url:
        return False, "login_required"

    # Wait for conversation list to load
    log("Waiting for conversations to load...")
    for attempt in range(15):
        page.wait_for_timeout(2000)
        body_text = page.locator("body").inner_text()
        lines = [l.strip() for l in body_text.split("\n") if l.strip()]
        non_nav = [l for l in lines if l not in (
            "TikTok", "For You", "Shop", "Explore", "Following", "Friends",
            "LIVE", "Messages", "Activity", "Upload", "Profile", "More",
            "Post video", ""
        ) and not l.isdigit()]
        if len(non_nav) > 3:
            log(f"Conversations loaded (attempt {attempt + 1})")
            break
        log(f"Still loading... (attempt {attempt + 1})")

    save_debug_screenshot(page, "messages-page")

    # Try to find and click the conversation
    for scroll_attempt in range(10):
        # Try exact match
        loc = page.locator(f'text="{display_name}"').first
        try:
            loc.wait_for(state="visible", timeout=3000)
            log("Found conversation via exact text match")
            loc.click()
            page.wait_for_timeout(3000)
            return True, None
        except Exception:
            pass

        # Try partial match
        loc = page.get_by_text(display_name, exact=False).first
        try:
            loc.wait_for(state="visible", timeout=3000)
            log("Found conversation via partial text match")
            loc.click()
            page.wait_for_timeout(3000)
            return True, None
        except Exception:
            pass

        # Scroll and try again
        if scroll_attempt < 9:
            log(f"Not found yet, scrolling... (attempt {scroll_attempt + 1})")
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(1500)

    return False, "not_found"


def main():
    if not RECIPIENT:
        log("ERROR: TIKTOK_RECIPIENT is not set.")
        log("  Set it as a GitHub Actions secret or environment variable.")
        log("  Use @username (e.g., @johndoe) or display name (e.g., John Doe)")
        sys.exit(1)

    log(f"Sending message to {RECIPIENT}: {MESSAGE}")

    storage_state = load_cookies()
    is_username = RECIPIENT.startswith("@")

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
        stealth = Stealth()
        page = context.new_page()
        stealth.apply_stealth_sync(page)

        if is_username:
            # Use username approach: go to profile -> click message
            success = find_conversation_by_username(page, RECIPIENT)
            if not success:
                save_debug_screenshot(page, "username-lookup-failed")
                log(f"ERROR: Could not open DM with {RECIPIENT}")
                log("  Make sure the username is correct and you can message this user.")
                browser.close()
                sys.exit(1)
        else:
            # Use display name approach: search conversation list
            # First check if we're logged in by going to messages
            page.goto("https://www.tiktok.com/messages", wait_until="networkidle")
            page.wait_for_timeout(3000)

            if "/login" in page.url:
                save_debug_screenshot(page, "login-redirect")
                log("ERROR: Session expired. Re-run login.py and update TIKTOK_COOKIES secret.")
                browser.close()
                sys.exit(1)

            success, error = find_conversation_by_display_name(page, RECIPIENT)
            if not success:
                save_debug_screenshot(page, "conversation-not-found")
                try:
                    body_text = page.locator("body").inner_text()
                    log(f"Page text preview (first 1000 chars):\n{body_text[:1000]}")
                except Exception:
                    pass
                log(f"ERROR: Could not find conversation with '{RECIPIENT}'.")
                log("  Try using @username instead of display name.")
                browser.close()
                sys.exit(1)

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

        # Send the message
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
