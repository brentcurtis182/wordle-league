#!/usr/bin/env python3
"""
Direct Fix for Wordle Score Extraction

This script applies a focused fix to the regex pattern in the extraction script
to properly detect modern Wordle score formats.
"""

import re
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_extraction_regex():
    """Update the regex pattern in extract_scores_from_conversation.py to match current Wordle formats"""
    filepath = 'extract_scores_from_conversation.py'
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return False
    
    # Create backup
    if os.path.exists(filepath):
        backup_path = f"{filepath}.bak"
        import shutil
        shutil.copy2(filepath, backup_path)
        print(f"Created backup at {backup_path}")
    
    try:
        # Read the file
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the regex pattern
        old_pattern = r"wordle_regex = re.compile\(r'Wordle \([\d,]+\)\(?: #\([\d,]+\)\)? \([1-6X]\)/6'\)"
        
        # More robust pattern that handles:
        # - Optional "Message from..." prefix
        # - Comma-formatted numbers
        # - Spaces before the score
        # - Case insensitivity
        new_pattern = r"""wordle_regex = re.compile(r'(?:.*)?Wordle\s+(?:#)?(\d[\d,]*)\s+(\d|X)/6', re.IGNORECASE)"""
        
        # Direct replacement of the exact line
        if "wordle_regex = re.compile(r'Wordle ([\d,]+)(?: #([\d,]+)?)? ([1-6X])/6')" in content:
            content = content.replace(
                "wordle_regex = re.compile(r'Wordle ([\d,]+)(?: #([\d,]+)?)? ([1-6X])/6')",
                "wordle_regex = re.compile(r'(?:.*)?Wordle\\s+(?:#)?(\\d[\\d,]*)\\s+(\\d|X)/6', re.IGNORECASE)"
            )
            
            # Update group references because our new regex has only 2 capture groups
            content = content.replace("match.group(3)", "match.group(2)")
            
            print("Updated the regex pattern successfully")
        else:
            print("Warning: Could not find the exact regex pattern line to update")
            return False
            
        # Write the updated content back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print("Extraction regex updated successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating regex: {e}")
        return False

if __name__ == "__main__":
    print("Updating Wordle extraction regex pattern...")
    success = fix_extraction_regex()
    if success:
        print("Done! You can now run the extraction again with the updated pattern.")
    else:
        print("Failed to update regex pattern. Check the error messages above.")
