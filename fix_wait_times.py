#!/usr/bin/env python3
"""
Fix Wait Times in Click Function

This script optimizes the wait times in the click_conversation_thread function
to make the extraction process more efficient.
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
        logging.FileHandler("fix_wait_times.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Optimize wait times in the click_conversation_thread function"""
    logging.info("Starting wait time optimization")
    
    file_path = "integrated_auto_update_multi_league.py"
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found")
        return False
        
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Update wait times in click_conversation_thread function
        # 1. Replace wait time after scroll into view click
        content = re.sub(
            r'driver\.execute_script\("arguments\[0\].scrollIntoView\(\);", thread\)\s+thread\.click\(\)\s+# Wait for the conversation to load\s+time\.sleep\(([0-9]+)\)',
            r'driver.execute_script("arguments[0].scrollIntoView();", thread)\n            thread.click()\n            # Wait for the conversation to load\n            time.sleep(3)',
            content
        )
        
        # 2. Replace wait time after JavaScript click
        content = re.sub(
            r'driver\.execute_script\("arguments\[0\].click\(\);", thread\)\s+# Wait for the conversation to load\s+time\.sleep\(([0-9]+)\)',
            r'driver.execute_script("arguments[0].click();", thread)\n            # Wait for the conversation to load\n            time.sleep(3)',
            content
        )
        
        # 3. Replace wait time after ActionChains click
        content = re.sub(
            r'ActionChains\(driver\)\.move_to_element\(thread\)\.click\(\)\.perform\(\)\s+# Wait for the conversation to load\s+time\.sleep\(([0-9]+)\)',
            r'ActionChains(driver).move_to_element(thread).click().perform()\n            # Wait for the conversation to load\n            time.sleep(3)',
            content
        )
        
        # 4. Replace wait times in extract_wordle_scores_multi_league function
        content = re.sub(
            r'# Wait for conversation to load\s+time\.sleep\(([0-9]+)\)',
            r'# Wait for conversation to load\n                time.sleep(2)',
            content
        )
        
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
            
        logging.info("Successfully optimized wait times")
        return True
        
    except Exception as e:
        logging.error(f"Error optimizing wait times: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Wait time optimization completed with success: {success}")
    sys.exit(0 if success else 1)
