#!/bin/bash
# Script to update the deploy.py file with the fixed version

# Define paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_ORIGINAL="${SCRIPT_DIR}/deploy.py"
DEPLOY_FIXED="${SCRIPT_DIR}/deploy_complete.py"
DEPLOY_BACKUP="${SCRIPT_DIR}/deploy.py.bak"

# Check if files exist
if [ ! -f "$DEPLOY_FIXED" ]; then
    echo "❌ Error: Fixed deploy script not found at ${DEPLOY_FIXED}"
    exit 1
fi

# Create backup of original file if it exists
if [ -f "$DEPLOY_ORIGINAL" ]; then
    echo "📦 Creating backup of original deploy.py..."
    cp "$DEPLOY_ORIGINAL" "$DEPLOY_BACKUP"
    echo "✅ Backup created at ${DEPLOY_BACKUP}"
fi

# Copy the fixed file to replace the original
echo "🔄 Updating deploy.py with fixed version..."
cp "$DEPLOY_FIXED" "$DEPLOY_ORIGINAL"

# Make the file executable
chmod +x "$DEPLOY_ORIGINAL"

echo "✅ deploy.py has been updated successfully!"
echo "🚀 You can now run the script with: python ${DEPLOY_ORIGINAL}"
