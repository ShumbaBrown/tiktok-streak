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

A browser will open — log into TikTok, then close the browser. The script will give you a base64 string to copy.

### 3. Add GitHub Secrets

Go to your forked repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret Name | Value |
|---|---|
| `TIKTOK_COOKIES` | The base64 string from step 2 (copied to your clipboard) |
| `TIKTOK_RECIPIENT` | The display name of the person you want to message |
| `TIKTOK_MESSAGE` | *(optional)* The message to send. Defaults to `hey :)` |

### 4. Done

The workflow runs automatically every day at **9:00 AM EST**. You can also trigger it manually from the **Actions** tab → **TikTok Streak** → **Run workflow**.

## Refreshing Your Session

TikTok sessions expire periodically. If the workflow starts failing:

1. Run `python login.py` again on your computer
2. Update the `TIKTOK_COOKIES` secret with the new value

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
TIKTOK_RECIPIENT="Their Name" python send_message.py
```

## How It Works

- **Playwright** (headless Chromium) opens TikTok's web interface
- Your saved session cookies keep you logged in without entering credentials
- The script navigates to your DM conversation and sends the message
- GitHub Actions runs this on a schedule so your computer doesn't need to be on

## Troubleshooting

| Problem | Fix |
|---|---|
| Workflow fails with "session expired" | Re-run `login.py` and update `TIKTOK_COOKIES` secret |
| Workflow fails with "TIKTOK_RECIPIENT is not set" | Add the `TIKTOK_RECIPIENT` secret in repo settings |
| Can't find conversation | Make sure `TIKTOK_RECIPIENT` exactly matches their display name on TikTok |
| Script worked before but stopped | TikTok may have changed their UI — open an issue |
