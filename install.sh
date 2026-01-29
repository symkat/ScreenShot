#!/bin/bash
set -e

echo "Installing Screenshot Service dependencies..."

# Install Python packages
echo "Installing Python packages..."
pip install -r requirements.txt

# Install Playwright system dependencies
echo "Installing Playwright system dependencies..."
python -m playwright install-deps chromium

# Install Playwright browser
echo "Installing Playwright Chromium browser..."
python -m playwright install chromium

echo ""
echo "Installation complete!"
echo ""
echo "To start the server, run:"
echo "  python main.py"
echo ""
echo "The server will be available at http://localhost:8080"
