#!/usr/bin/env python3
"""
Apply League Thread Fix

This script patches the integrated_auto_update_multi_league.py file with improved
thread identification and clicking logic for both Wordle Warriorz and PAL leagues.
"""

import os
import sys
import shutil
import re
import logging
import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("league_thread_fix.log"),
        logging.StreamHandler()
    ]
)

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"{os.path.basename(file_path)}.{timestamp}.bak")
    
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup at {backup_path}")
    return backup_path

def read_file(file_path):
    """Read file contents"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {str(e)}")
        return None

def write_file(file_path, content):
    """Write content to file"""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        logging.info(f"Successfully wrote to {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {str(e)}")
        return False

def patch_find_conversation_threads(content):
    """Patch the find_conversation_threads function with improved thread identification"""
    find_conversation_threads_pattern = r"def find_conversation_threads\(driver, league_id=1\):.*?return None"
    
    improved_find_conversation_threads = '''def find_conversation_threads(driver, league_id=1):
    """Find conversation threads for a specific league
    
    Args:
        driver: Selenium WebDriver instance
        league_id: League ID to find conversations for
        
    Returns:
        list: List of conversation thread elements or None if not found
    """
    try:
        # Wait for threads to appear
        logging.info(f"Looking for conversation threads for league {league_id}")
        
        # Take a screenshot to verify the state before searching
        driver.save_screenshot(f"before_thread_search_league_{league_id}.png")
        
        # Wait for thread items to be present with a longer timeout
        logging.info("Waiting for thread items to appear...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item, div[role='button'].container, .mat-ripple.container"))
        )
        
        # Try multiple selector strategies to find conversation items
        selectors_to_try = [
            "div[role='button'].container",  # Most reliable selector based on testing
            "gv-conversation-list gv-thread-item",
            ".mat-ripple.container",
            "div.container[tabindex='0']",
            "gv-thread-item",
            "div.container.read"
        ]
        
        conversation_items = []
        for selector in selectors_to_try:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    logging.info(f"Found {len(items)} items with selector: {selector}")
                    conversation_items = items
                    break
            except Exception as e:
                logging.warning(f"Error with selector {selector}: {str(e)}")
        
        logging.info(f"Found {len(conversation_items)} total conversation threads")
        
        if len(conversation_items) == 0:
            logging.warning("No conversation threads found")
            driver.save_screenshot(f"no_threads_found_league_{league_id}.png")
            return None
            
        # If we're looking for Wordle Warriorz league (league_id 1)
        if league_id == 1:
            # Look for the thread with Wordle Warriorz identifiers
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    logging.info(f"Thread {i+1} text: {item_text[:50]}...")
                    
                    # Check if this has Wordle Warriorz participants - look for area code 310 which is unique to Warriorz
                    if any(identifier in item_text for identifier in ["(310)", "310", "Joanna", "Nanna", "Brent", "Malia", "Evan"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle Warriorz league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for Warriorz: {e}")
            
        # If we're looking for PAL league (league_id 3)
        elif league_id == 3:
            # Look for the PAL thread with specific identifiers
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    logging.info(f"Thread {i+1} text: {item_text[:50]}...")
                    
                    # Check if this has PAL participants - look for area code 469 which is unique to PAL
                    if any(identifier in item_text for identifier in ["(469)", "469", "Fuzwuz", "Vox", "PAL", "Pants", "Starslider"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle PAL league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for PAL: {e}")
        
        # If we reach here, we didn't find the right thread for the requested league
        logging.warning(f"Could not identify specific thread for league {league_id}")
        driver.save_screenshot(f"thread_identification_failed_league_{league_id}.png")
        
        # As a fallback, if we have exactly 2 threads total, use process of elimination
        if len(conversation_items) == 2:
            logging.info("Using process of elimination with 2 threads")
            # If we're looking for Warriorz and thread 1 has "310", return thread 1
            # If we're looking for PAL and thread 2 has "469", return thread 2
            # Otherwise return all threads
            for i, item in enumerate(conversation_items):
                item_text = item.text
                if league_id == 1 and "(310)" in item_text:
                    logging.info("Found Wordle Warriorz thread by area code 310")
                    return [item]
                elif league_id == 3 and "(469)" in item_text:
                    logging.info("Found PAL thread by area code 469")
                    return [item]
        
        # Last resort fallback
        logging.info("Returning all threads as a fallback")
        return conversation_items
        
    except Exception as e:
        logging.error(f"Error finding conversation threads: {str(e)}")
        driver.save_screenshot(f"thread_search_error_league_{league_id}.png")
        return None'''

    # Use re.DOTALL to match across multiple lines
    updated_content = re.sub(find_conversation_threads_pattern, improved_find_conversation_threads, content, flags=re.DOTALL)
    
    if updated_content == content:
        logging.warning("Could not patch find_conversation_threads function")
        return content
    else:
        logging.info("Successfully patched find_conversation_threads function")
        return updated_content

def patch_click_conversation_thread(content):
    """Patch the click_conversation_thread function with improved clicking logic"""
    click_conversation_pattern = r"def click_conversation_thread\(driver, thread, thread_info=None\):.*?return False"
    
    improved_click_conversation = '''def click_conversation_thread(driver, thread, thread_info=None):
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
    return False'''

    # Use re.DOTALL to match across multiple lines
    updated_content = re.sub(click_conversation_pattern, improved_click_conversation, content, flags=re.DOTALL)
    
    if updated_content == content:
        logging.warning("Could not patch click_conversation_thread function")
        return content
    else:
        logging.info("Successfully patched click_conversation_thread function")
        return updated_content

def patch_extract_wordle_scores_multi_league(content):
    """Patch the extract_wordle_scores_multi_league function with improved extraction flow"""
    extract_pattern = r"def extract_wordle_scores_multi_league\(\):.*?return any_scores_extracted"
    
    improved_extract = '''def extract_wordle_scores_multi_league():
    """Extract Wordle scores from multiple leagues
    
    Returns:
        bool: True if any scores were extracted, False otherwise
    """
    logging.info("Starting multi-league Wordle score extraction")
    
    driver = None
    any_scores_extracted = False
    
    try:
        # Set up Chrome driver
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use existing Chrome profile to avoid login issues
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"user-data-dir={profile_path}")
            logging.info(f"Using existing Chrome profile at {profile_path}")
        else:
            logging.warning(f"Chrome profile not found at {profile_path}")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # League extraction order: First Wordle Warriorz (1), then PAL (3)
        leagues_to_extract = [
            {"id": 1, "name": "Wordle Warriorz"},
            {"id": 3, "name": "PAL"}
        ]
        
        for league in leagues_to_extract:
            league_id = league["id"]
            league_name = league["name"]
            
            logging.info(f"Starting extraction for {league_name} (league_id: {league_id})")
            
            # Navigate to Google Voice
            driver.get("https://voice.google.com/u/0/messages")
            
            # Wait for page to load
            try:
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item, div[role='button'].container, .mat-ripple.container"))
                )
                logging.info("Google Voice loaded successfully")
            except TimeoutException:
                logging.error("Timed out waiting for Google Voice to load")
                driver.save_screenshot(f"gv_timeout_{league_name.replace(' ', '_')}.png")
                continue
                
            # Find conversation threads for this league
            conversation_threads = find_conversation_threads(driver, league_id)
            
            if not conversation_threads:
                logging.warning(f"No conversation threads found for {league_name}")
                continue
                
            # Take a screenshot of the threads we found
            driver.save_screenshot(f"threads_found_{league_name.replace(' ', '_')}.png")
            
            # Try each thread (usually should be just one)
            for thread_idx, thread in enumerate(conversation_threads[:3]):  # Limit to first 3 threads max
                thread_desc = f"{league_name} thread {thread_idx+1}"
                
                # Click on the conversation thread
                if not click_conversation_thread(driver, thread, thread_desc):
                    logging.error(f"Failed to click {thread_desc}")
                    continue
                    
                # Wait for conversation to load
                time.sleep(2)
                
                # Extract scores
                scores_extracted = extract_scores_from_conversation(driver, league_id)
                if scores_extracted:
                    logging.info(f"Successfully extracted scores from {thread_desc}")
                    any_scores_extracted = True
                else:
                    logging.warning(f"No scores extracted from {thread_desc}")
                
                # Take a screenshot after extraction
                driver.save_screenshot(f"after_extraction_{league_name.replace(' ', '_')}.png")
                
                # Break after first successful thread
                break
            
            logging.info(f"Completed extraction for {league_name}")
        
        return any_scores_extracted
            
    except Exception as e:
        logging.error(f"Error in multi-league extraction: {str(e)}")
        if driver:
            driver.save_screenshot("multi_league_extraction_error.png")
        return False
        
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
            except:
                pass'''

    # Use re.DOTALL to match across multiple lines
    updated_content = re.sub(extract_pattern, improved_extract, content, flags=re.DOTALL)
    
    if updated_content == content:
        logging.warning("Could not patch extract_wordle_scores_multi_league function")
        return content
    else:
        logging.info("Successfully patched extract_wordle_scores_multi_league function")
        return updated_content

def main():
    """Main function to apply fixes to the integrated_auto_update_multi_league.py script"""
    logging.info("Starting application of league thread fixes")
    
    target_file = "integrated_auto_update_multi_league.py"
    if not os.path.exists(target_file):
        logging.error(f"Target file {target_file} not found")
        return False
    
    # Create backup
    backup_path = backup_file(target_file)
    logging.info(f"Backup created at {backup_path}")
    
    # Read file content
    content = read_file(target_file)
    if not content:
        return False
    
    # Apply patches
    content = patch_find_conversation_threads(content)
    content = patch_click_conversation_thread(content)
    content = patch_extract_wordle_scores_multi_league(content)
    
    # Write updated content
    if write_file(target_file, content):
        logging.info(f"Successfully updated {target_file} with league thread fixes")
        return True
    else:
        logging.error(f"Failed to write updated content to {target_file}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"League thread fix application completed with success: {success}")
    sys.exit(0 if success else 1)
