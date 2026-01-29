#!/bin/bash
set -e

echo "Installing Screenshot Service..."

# Clone the repository
echo "Cloning repository..."
git clone https://github.com/symkat/ScreenShot.git /home/sprite/ScreenShot
cd /home/sprite/ScreenShot

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
echo "Registering Screenshot Service..."
sprite-env services create screenshot \
    --cmd python \
    --args /home/sprite/ScreenShot/main.py \
    --http-port 8080

echo ""
echo "Installation complete!"
echo "The screenshot service is now running and available at http://localhost:8080"
