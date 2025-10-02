#!/bin/bash
# Script to fix the deploy.py file to work with Pydantic v2

DEPLOY_FILE="/app/script/deploy.py"

if [ ! -f "$DEPLOY_FILE" ]; then
    echo "Error: $DEPLOY_FILE not found"
    exit 1
fi

echo "Fixing deploy.py file..."

# Create a backup
cp "$DEPLOY_FILE" "${DEPLOY_FILE}.bak"

# Fix the import
sed -i 's/from pydantic import BaseModel, Dict, List/from typing import Dict, List\nfrom pydantic import BaseModel/g' "$DEPLOY_FILE"

# Check if the fix was applied
if grep -q "from pydantic import BaseModel, Dict, List" "$DEPLOY_FILE"; then
    echo "❌ Failed to fix the file"
    exit 1
else
    echo "✅ Fixed $DEPLOY_FILE"
    echo "Original file backed up to ${DEPLOY_FILE}.bak"
    exit 0
fi
