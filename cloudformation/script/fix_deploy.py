#!/usr/bin/env python3
"""
Script to fix the deploy.py file to work with Pydantic v2
"""
import os
import sys
from pathlib import Path

def fix_deploy_file():
    """Fix the deploy.py file to work with Pydantic v2"""
    script_dir = Path(__file__).parent
    deploy_path = script_dir / "deploy.py"
    
    if not deploy_path.exists():
        print(f"Error: {deploy_path} not found")
        return False
    
    # Read the current content
    with open(deploy_path, 'r') as f:
        content = f.read()
    
    # Check if the file contains the problematic import
    if "from pydantic import BaseModel, Dict, List" in content:
        print("Found problematic import, fixing...")
        
        # Fix the import
        fixed_content = content.replace(
            "from pydantic import BaseModel, Dict, List",
            "from typing import Dict, List\nfrom pydantic import BaseModel"
        )
        
        # Write the fixed content
        with open(deploy_path, 'w') as f:
            f.write(fixed_content)
        
        print(f"✅ Fixed {deploy_path}")
        return True
    else:
        print("No problematic import found, file may already be fixed")
        return True

if __name__ == "__main__":
    success = fix_deploy_file()
    sys.exit(0 if success else 1)
