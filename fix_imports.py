#!/usr/bin/env python3
"""
Fix Missing Imports

This script adds the missing ActionChains import to the integrated_auto_update_multi_league.py file.
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
        logging.FileHandler("fix_imports.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Add missing imports to the integrated_auto_update_multi_league.py script"""
    logging.info("Starting import fix")
    
    file_path = "integrated_auto_update_multi_league.py"
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found")
        return False
        
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Check if ActionChains is already imported
        if "from selenium.webdriver.common.action_chains import ActionChains" in content:
            logging.info("ActionChains import already exists")
            return True
            
        # Find the import section
        import_section = re.search(r"import.*?from selenium\.webdriver\.common\.keys import Keys", content, re.DOTALL)
        if not import_section:
            logging.error("Could not find import section")
            return False
            
        import_end = import_section.end()
        
        # Add ActionChains import after Keys import
        updated_content = (
            content[:import_end] + 
            "\nfrom selenium.webdriver.common.action_chains import ActionChains" + 
            content[import_end:]
        )
            
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        logging.info("Successfully added ActionChains import")
        return True
        
    except Exception as e:
        logging.error(f"Error fixing imports: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Import fix completed with success: {success}")
    sys.exit(0 if success else 1)
