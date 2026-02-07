# TikTok Streak

Automatically sends a daily TikTok DM to keep your streak alive. Runs on GitHub Actions — no server or always-on computer needed.

## Quick Start

### 1. Fork this repo

Click the **Fork** button at the top right of this page.

### 2. Run local setup (one time)

You need to log into TikTok once from your computer so the script can save your session cookies.

```bash
git clone https://github.com/YOUR_USERNAME/tiktok-streak.git
cd tiktok-streak
bash setup.sh
source venv/bin/activate
python login.py
```

A browser will open — log into TikTok (QR code is easiest), then close the browser. The script will copy your session to the clipboard.

### 3. Add GitHub Secrets

Go to your forked repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value |
|---|---|
| `TIKTOK_COOKIES` | Paste from clipboard (copied automatically by login.py) |
| `TIKTOK_RECIPIENT` | The person to message (see format below) |
| `TIKTOK_MESSAGE` | *(optional)* The message to send. Defaults to `hey :)` |

#### Recipient Format

`TIKTOK_RECIPIENT` supports multiple formats:

- **Display name only**: `Lauren` — looks for this name in your conversation list
- **Username only**: `@laurenrenease` — searches for this username
- **Both (recommended)**: `Lauren|@laurenrenease` — tries display name first, falls back to username search

Using the `DisplayName|@username` format is most reliable.

### 4. Done!

The workflow runs automatically every day at **9:00 AM EST**. You can also trigger it manually from the **Actions** tab → **TikTok Streak** → **Run workflow**.

## Adding Multiple People

To send messages from multiple accounts (e.g., you and your partner both sending to each other):

1. Create a new workflow file (copy `.github/workflows/streak.yml` to `streak-person2.yml`)
2. Update the secret names in the new workflow (e.g., `PERSON2_TIKTOK_COOKIES`, etc.)
3. Run `python login.py` for the second person and add their secrets

See `.github/workflows/streak-lauren.yml` for an example.

## Refreshing Your Session

TikTok sessions expire periodically (usually weeks to months). If the workflow starts failing with "session expired":

1. Run `python login.py` again on your computer
2. Log into TikTok in the browser that opens
3. Close the browser — new cookies are copied to clipboard
4. Update the `TIKTOK_COOKIES` secret with the new value

## Changing the Schedule

Edit `.github/workflows/streak.yml` and update the cron expression:

```yaml
schedule:
  - cron: '0 14 * * *'  # 9 AM EST (14:00 UTC)
```

Use [crontab.guru](https://crontab.guru/) to build your cron schedule. Remember to convert your local time to UTC.

## Local Testing

```bash
source venv/bin/activate
TIKTOK_RECIPIENT="PersonName|@username" python send_message.py
```

## How It Works

1. **Playwright** (headless Chromium with stealth mode) opens TikTok's web interface
2. Your saved session cookies keep you logged in without entering credentials
3. The script navigates to your DM conversation and sends the message
4. GitHub Actions runs this on a schedule so your computer doesn't need to be on

## Files

| File | Purpose |
|---|---|
| `send_message.py` | Main script — finds conversation and sends message |
| `login.py` | One-time setup — opens browser for TikTok login, saves cookies |
| `config.py` | Configuration (reads from environment variables) |
| `setup.sh` | Installs Python dependencies and Playwright |
| `.github/workflows/streak.yml` | GitHub Actions workflow (daily schedule) |

## Troubleshooting

| Problem | Fix |
|---|---|
| "Session expired" | Re-run `login.py` and update `TIKTOK_COOKIES` secret |
| "TIKTOK_RECIPIENT is not set" | Add the `TIKTOK_RECIPIENT` secret in repo settings |
| Can't find conversation | Use the `DisplayName|@username` format for recipient |
| "Could not find conversation" | Make sure the display name matches exactly, or add the @username |
| CAPTCHA appears | TikTok detected automation — wait and try again, or re-login |
| Workflow never runs | Check that Actions are enabled in your fork's Settings |

## Privacy & Security

- Your TikTok session cookies are stored as GitHub Secrets (encrypted, never visible in logs)
- The `cookies.json` file is gitignored — never commit it
- Only you have access to your fork's secrets
