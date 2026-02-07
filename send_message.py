"""
Sends a TikTok DM to maintain a streak.
Uses saved session cookies to avoid needing to log in each time.

Usage:
    python send_message.py           # Uses cookies.json from disk
    TIKTOK_COOKIES_B64=... python send_message.py  # Uses base64-encoded cookies from env

All config is read from environment variables (see README).

TIKTOK_RECIPIENT format: "DisplayName" or "DisplayName|@username"
  - First tries to find DisplayName in conversation list
  - If not found and @username is provided, uses search to find them
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


def wait_for_conversations_to_load(page):
    """Wait for the conversation list to finish loading."""
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
            return True
        log(f"Still loading... (attempt {attempt + 1})")
    log("WARNING: Conversations may not have fully loaded")
    return False


def find_in_conversation_list(page, display_name):
    """Try to find and click a conversation by display name (with scrolling)."""
    log(f"Looking for '{display_name}' in conversation list...")

    for scroll_attempt in range(5):
        # Try exact match
        loc = page.locator(f'text="{display_name}"').first
        try:
            loc.wait_for(state="visible", timeout=3000)
            log("Found conversation via exact text match")
            loc.click()
            page.wait_for_timeout(3000)
            return True
        except Exception:
            pass

        # Try partial match
        loc = page.get_by_text(display_name, exact=False).first
        try:
            loc.wait_for(state="visible", timeout=3000)
            log("Found conversation via partial text match")
            loc.click()
            page.wait_for_timeout(3000)
            return True
        except Exception:
            pass

        # Scroll and try again
        if scroll_attempt < 4:
            log(f"Not found, scrolling... (attempt {scroll_attempt + 1})")
            page.mouse.wheel(0, 500)
            page.wait_for_timeout(1500)

    return False


def search_for_user(page, username):
    """Use the search feature in messages to find a user by username."""
    username_clean = username.lstrip("@")
    log(f"Searching for @{username_clean} using search...")

    # Click the search icon in the left sidebar
    search_button = page.locator(
        '[data-e2e="search-icon"], '
        'svg[data-icon="search"], '
        'button[aria-label*="Search"], '
        '[class*="search"] svg, '
        'a[href*="search"]'
    ).first

    try:
        search_button.wait_for(state="visible", timeout=5000)
        search_button.click()
        page.wait_for_timeout(2000)
    except Exception:
        log("Could not find search button, trying search input directly...")

    # Look for search input
    search_input = page.locator(
        '[data-e2e="search-input"], '
        'input[placeholder*="Search"], '
        'input[type="search"], '
        'input[aria-label*="Search"]'
    ).first

    try:
        search_input.wait_for(state="visible", timeout=5000)
        search_input.click()
        search_input.fill(username_clean)
        page.wait_for_timeout(2000)

        # Press enter or wait for results
        search_input.press("Enter")
        page.wait_for_timeout(3000)

        save_debug_screenshot(page, "search-results")

        # Look for the user in search results and click
        result = page.get_by_text(username_clean, exact=False).first
        result.wait_for(state="visible", timeout=5000)
        result.click()
        page.wait_for_timeout(3000)

        return True
    except Exception as e:
        log(f"Search failed: {e}")
        return False


def main():
    if not RECIPIENT:
        log("ERROR: TIKTOK_RECIPIENT is not set.")
        log("  Set it as a GitHub Actions secret or environment variable.")
        log("  Format: 'DisplayName' or 'DisplayName|@username'")
        sys.exit(1)

    # Parse recipient - can be "DisplayName" or "DisplayName|@username"
    if "|" in RECIPIENT:
        display_name, username = RECIPIENT.split("|", 1)
        display_name = display_name.strip()
        username = username.strip()
    elif RECIPIENT.startswith("@"):
        display_name = None
        username = RECIPIENT
    else:
        display_name = RECIPIENT
        username = None

    log(f"Sending message: {MESSAGE}")
    if display_name:
        log(f"  Display name: {display_name}")
    if username:
        log(f"  Username: {username}")

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
        stealth = Stealth()
        page = context.new_page()
        stealth.apply_stealth_sync(page)

        # Navigate to messages
        log("Navigating to TikTok messages...")
        page.goto("https://www.tiktok.com/messages", wait_until="networkidle")
        page.wait_for_timeout(3000)

        # Check if logged in
        if "/login" in page.url:
            save_debug_screenshot(page, "login-redirect")
            log("ERROR: Session expired. Re-run login.py and update TIKTOK_COOKIES secret.")
            browser.close()
            sys.exit(1)

        wait_for_conversations_to_load(page)
        save_debug_screenshot(page, "messages-page")

        # Strategy 1: Try to find by display name in conversation list
        found = False
        if display_name:
            found = find_in_conversation_list(page, display_name)

        # Strategy 2: If not found, try search with username
        if not found and username:
            log("Display name not found in list, trying search...")
            found = search_for_user(page, username)

        if not found:
            save_debug_screenshot(page, "conversation-not-found")
            try:
                body_text = page.locator("body").inner_text()
                log(f"Page text preview (first 1000 chars):\n{body_text[:1000]}")
            except Exception:
                pass
            log(f"ERROR: Could not find conversation.")
            log("  Make sure the display name or username is correct.")
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
