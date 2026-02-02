#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "================================================"
echo "  TikTok Streak — Local Setup"
echo "================================================"
echo ""

echo "Creating Python virtual environment..."
python3 -m venv venv

echo "Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "Installing Playwright's Chromium browser..."
playwright install chromium

echo ""
echo "================================================"
echo "  Setup complete! Next steps:"
echo "================================================"
echo ""
echo "  1. Activate the virtual environment:"
echo "       source venv/bin/activate"
echo ""
echo "  2. Log into TikTok:"
echo "       python login.py"
echo ""
echo "  3. Follow the on-screen instructions to add"
echo "     your GitHub Secrets, then you're done!"
echo ""
