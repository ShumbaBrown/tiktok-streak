import os

# All configuration is read from environment variables.
# For GitHub Actions: set these as repository secrets.
# For local use: set them in your shell or a .env file.

RECIPIENT = os.environ.get("TIKTOK_RECIPIENT", "")
MESSAGE = os.environ.get("TIKTOK_MESSAGE", "hey :)")

# Local paths (not used in GitHub Actions)
_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILE_DIR = os.path.join(_DIR, "browser_data")
COOKIES_FILE = os.path.join(_DIR, "cookies.json")
