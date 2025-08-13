#!/usr/bin/env python
# Targeted fix for X/6 detection in integrated_auto_update.py
# Makes the regex patterns case-insensitive to catch both "X/6" and "x/6"

import re
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def make_backup(file_path):
    """Create a backup of the file before modifying it"""
    backup_path = f"{file_path}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup at {backup_path}")
    return backup_path

def fix_regex_patterns():
    """Add re.IGNORECASE flag to the failed attempt patterns"""
    file_path = "integrated_auto_update.py"
    
    # Create a backup first
    backup_path = make_backup(file_path)
    
    # Read the file
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Find the failed_patterns block
    pattern_start = None
    pattern_end = None
    
    for i, line in enumerate(lines):
        if "failed_patterns = [" in line:
            pattern_start = i
        elif pattern_start is not None and "]" in line and pattern_end is None:
            pattern_end = i + 1
            break
    
    if pattern_start is None or pattern_end is None:
        logging.error("Could not find the failed_patterns block")
        return False
    
    # Get the original pattern block
    original_block = lines[pattern_start:pattern_end]
    logging.info(f"Found failed_patterns block at lines {pattern_start+1}-{pattern_end}")
    
    # Create the new pattern block with IGNORECASE flag
    new_block = []
    new_block.append(original_block[0])  # Add the "failed_patterns = [" line
    
    # Add the patterns with IGNORECASE flag
    new_block.append("                    re.compile(r'Wordle\\s+#?([\\d,]+)\\s+X/6', re.IGNORECASE),  # Standard format\n")
    new_block.append("                    re.compile(r'Wordle[:\\s]+#?([\\d,]+)\\s*[:\\s]+X/6', re.IGNORECASE),  # With colons\n")
    new_block.append("                    re.compile(r'Wordle[^\\d]*([\\d,]+)[^\\d]*X/6', re.IGNORECASE)  # Very flexible\n")
    
    # Add the closing bracket
    new_block.append(original_block[-1])
    
    # Replace the original block with the new block
    modified_lines = lines[:pattern_start] + new_block + lines[pattern_end:]
    
    # Write the modified content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(modified_lines)
    
    logging.info("Successfully updated the patterns to be case-insensitive")
    return True

if __name__ == "__main__":
    logging.info("Fixing X/6 detection in integrated_auto_update.py...")
    
    try:
        if fix_regex_patterns():
            logging.info("✅ Successfully added re.IGNORECASE flag to failed attempt patterns")
            logging.info("This will fix issues with lowercase 'x/6' not being detected")
        else:
            logging.error("❌ Failed to update the patterns")
    except Exception as e:
        logging.error(f"Error: {e}")
        logging.info("You can restore from the backup if needed")
