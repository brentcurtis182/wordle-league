#!/usr/bin/env python3
"""
Fix Click Conversation Thread Function

This script adds an improved click_conversation_thread function to the integrated_auto_update_multi_league.py file.
"""

import os
import sys
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("click_function_fix.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Add improved click function to the integrated_auto_update_multi_league.py script"""
    logging.info("Starting click function fix")
    
    file_path = "integrated_auto_update_multi_league.py"
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found")
        return False
        
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Define the improved click function
        improved_click_function = '''
def click_conversation_thread(driver, thread, thread_info=None):
    """Click on a conversation thread with robust error handling
    
    Args:
        driver: Selenium WebDriver instance
        thread: Thread element to click
        thread_info: Optional description for logging
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not thread:
        logging.error("No thread provided to click")
        return False
        
    thread_desc = thread_info or "conversation thread"
    logging.info(f"Attempting to click {thread_desc}")
    
    # Take a screenshot before clicking
    driver.save_screenshot(f"before_click_{thread_desc.replace(' ', '_')}.png")
    
    # Try multiple click methods with proper waits
    methods = [
        {
            "name": "Scroll into view then click",
            "action": lambda: (
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread),
                time.sleep(1),
                thread.click()
            )
        },
        {
            "name": "JavaScript click",
            "action": lambda: driver.execute_script("arguments[0].click();", thread)
        },
        {
            "name": "ActionChains click",
            "action": lambda: ActionChains(driver).move_to_element(thread).click().perform()
        }
    ]
    
    for method in methods:
        try:
            logging.info(f"Trying {method['name']}")
            method["action"]()
            time.sleep(3)  # Wait for thread to load
            
            # Check if thread loaded successfully
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-input, textarea.input"))
                )
                logging.info(f"{method['name']} successful!")
                driver.save_screenshot(f"after_successful_click_{thread_desc.replace(' ', '_')}.png")
                return True
            except TimeoutException:
                logging.warning(f"{method['name']} didn't load thread completely, trying next method")
                continue
                
        except Exception as e:
            logging.error(f"Error with {method['name']}: {str(e)}")
    
    logging.error(f"All click methods failed for {thread_desc}")
    driver.save_screenshot(f"all_click_methods_failed_{thread_desc.replace(' ', '_')}.png")
    return False
'''
        
        # Look for the existing click_conversation_thread function
        if "def click_conversation_thread(" in content:
            # Replace existing function with improved version
            lines = content.splitlines()
            new_lines = []
            skip_mode = False
            
            for line in lines:
                if "def click_conversation_thread(" in line:
                    skip_mode = True
                    new_lines.append(improved_click_function)
                elif skip_mode and line.startswith("def "):
                    skip_mode = False
                    new_lines.append(line)
                elif not skip_mode:
                    new_lines.append(line)
                    
            updated_content = "\n".join(new_lines)
        else:
            # Add function if it doesn't exist (after imports)
            import_section_end = content.find("def ")
            if import_section_end != -1:
                updated_content = content[:import_section_end] + improved_click_function + content[import_section_end:]
            else:
                updated_content = improved_click_function + content
                
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        logging.info("Successfully updated click_conversation_thread function")
        return True
        
    except Exception as e:
        logging.error(f"Error updating click_conversation_thread function: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Click function fix completed with success: {success}")
    sys.exit(0 if success else 1)
