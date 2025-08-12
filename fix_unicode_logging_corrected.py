#!/usr/bin/env python3
"""
Fix Unicode Logging (Corrected)

This script fixes the Unicode encoding error in the logging by manually editing the file
and using a simpler approach to avoid regex escape issues.
"""

import os
import sys
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_unicode_corrected.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Fix Unicode encoding error in logging"""
    logging.info("Starting Unicode logging fix")
    
    file_path = "integrated_auto_update_multi_league.py"
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found")
        return False
        
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        # Find and modify the problematic line
        for i, line in enumerate(lines):
            if "logging.info(f\"Thread {i+1} text: {item_text[:50]}...\")" in line:
                lines[i] = line.replace(
                    "logging.info(f\"Thread {i+1} text: {item_text[:50]}...\")",
                    "logging.info(f\"Thread {i+1} text: {item_text[:50].encode('ascii', 'replace').decode('ascii')}...\")"
                )
                
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
            
        logging.info("Successfully fixed Unicode encoding in logging")
        return True
        
    except Exception as e:
        logging.error(f"Error fixing Unicode encoding: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Unicode logging fix completed with success: {success}")
    sys.exit(0 if success else 1)
