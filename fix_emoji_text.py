#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix emoji patterns in exported Wordle League HTML files by removing the
"No emoji pattern available" text that's appearing after the emoji patterns.
"""

import os
import re
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_EXPORT_PATH = os.path.join(SCRIPT_DIR, "website_export")

def fix_emoji_patterns(file_path):
    """Remove 'No emoji pattern available' text from HTML files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if the file contains the problematic text
        if "No emoji pattern available" in content:
            # Remove the problematic text
            fixed_content = content.replace("No emoji pattern available", "")
            
            # Write the fixed content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            logging.info(f"Fixed emoji pattern in: {os.path.relpath(file_path, SCRIPT_DIR)}")
            return True
        else:
            logging.debug(f"No issues found in: {os.path.relpath(file_path, SCRIPT_DIR)}")
            return False
    except Exception as e:
        logging.error(f"Error fixing emoji pattern in {file_path}: {e}")
        return False

def main():
    """Main function to fix all HTML files in the website export directory"""
    logging.info("Starting emoji pattern fix")
    
    fixed_files = 0
    total_html_files = 0
    
    # Walk through all files in the website export directory
    for root, _, files in os.walk(WEBSITE_EXPORT_PATH):
        for file in files:
            if file.endswith('.html'):
                total_html_files += 1
                file_path = os.path.join(root, file)
                if fix_emoji_patterns(file_path):
                    fixed_files += 1
    
    logging.info(f"Processed {total_html_files} HTML files, fixed {fixed_files} files with emoji pattern issues")
    
    if fixed_files > 0:
        logging.info("Fix complete! You can now safely deploy the website.")
    else:
        logging.info("No emoji pattern issues found in HTML files.")
    
    return fixed_files > 0

if __name__ == "__main__":
    main()
