#!/usr/bin/env python
# Simple fix to make X/6 detection case-insensitive in integrated_auto_update.py
# This ensures both "X/6" and "x/6" are detected as failed attempts

import re
import os
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("case_insensitive_fix.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def make_backup(file_path):
    """Make a backup of the file before modifying it"""
    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    try:
        shutil.copy2(file_path, backup_path)
        logging.info(f"Created backup at {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return False

def add_case_insensitive_flag():
    """Add re.IGNORECASE flag to failed attempt regex patterns"""
    file_path = "integrated_auto_update.py"
    
    # Make a backup first
    if not make_backup(file_path):
        return False
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Define the patterns to search for and their replacements
        replacements = [
            # Standard format
            (
                r"re\.compile\(r'Wordle\\s\+#\?\(\\d\+\(?:,\\d\+\)\?\)\\s\+X/6'\)",
                r"re.compile(r'Wordle\\s+#?(\\d+(?:,\\d+)?)\\s+X/6', re.IGNORECASE)"
            ),
            # With colons
            (
                r"re\.compile\(r'Wordle\[:\\s\]\+#\?\(\\d\+\(?:,\\d\+\)\?\)\\s\*\[:\\s\]\+X/6'\)",
                r"re.compile(r'Wordle[:\\s]+#?(\\d+(?:,\\d+)?)\\s*[:\\s]+X/6', re.IGNORECASE)"
            ),
            # Very flexible
            (
                r"re\.compile\(r'Wordle\[\\^\\d\]\*\(\\d\+\(?:,\\d\+\)\?\)\[\\^\\d\]\*X/6'\)",
                r"re.compile(r'Wordle[^\\d]*(\\d+(?:,\\d+)?)[^\\d]*X/6', re.IGNORECASE)"
            )
        ]
        
        modified_content = content
        changes_made = 0
        
        # Alternative approach: Find the failed_patterns block and modify it directly
        failed_patterns_block = re.search(r'failed_patterns\s*=\s*\[(.*?)\]', content, re.DOTALL)
        
        if failed_patterns_block:
            original_block = failed_patterns_block.group(0)
            modified_block = original_block
            
            # Add re.IGNORECASE to each pattern in the block that doesn't already have it
            for pattern in re.finditer(r"re\.compile\((r'.*?')\)", original_block):
                pattern_str = pattern.group(1)
                if 'IGNORECASE' not in pattern_str and 'X/6' in pattern_str:
                    replacement = f"re.compile({pattern_str}, re.IGNORECASE)"
                    modified_block = modified_block.replace(f"re.compile({pattern_str})", replacement)
            
            if modified_block != original_block:
                modified_content = content.replace(original_block, modified_block)
                changes_made += 1
        
        if changes_made == 0:
            logging.warning("Could not find the failed_patterns block or no changes were needed")
            return False
        
        # Write the modified content back to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
            
        logging.info(f"Successfully added re.IGNORECASE flag to {changes_made} pattern blocks")
        return True
    except Exception as e:
        logging.error(f"Error modifying file: {e}")
        return False

if __name__ == "__main__":
    logging.info("Adding case-insensitive flag to X/6 detection patterns...")
    if add_case_insensitive_flag():
        logging.info("✅ Successfully updated the patterns to be case-insensitive")
        logging.info("This will fix the issue with lowercase 'x/6' not being detected correctly")
    else:
        logging.error("❌ Failed to update the patterns")
