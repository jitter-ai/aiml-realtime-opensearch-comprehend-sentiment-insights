#!/bin/bash
# Script to install dependencies inside the container

echo "Installing Python dependencies..."
pip install --no-cache-dir -r /app/script/requirements.txt

echo "Checking installed packages..."
pip list | grep -E 'pydantic|rich'

echo "Dependencies installation complete!"
