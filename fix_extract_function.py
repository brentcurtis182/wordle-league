#!/usr/bin/env python3
"""
Fix Extract Wordle Scores Multi League Function

This script updates the extract_wordle_scores_multi_league function in integrated_auto_update_multi_league.py
with improved league handling and extraction flow.
"""

import os
import sys
import logging
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_function_fix.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Update extract_wordle_scores_multi_league function in integrated_auto_update_multi_league.py"""
    logging.info("Starting extract function fix")
    
    file_path = "integrated_auto_update_multi_league.py"
    if not os.path.exists(file_path):
        logging.error(f"File {file_path} not found")
        return False
        
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Define the improved extract function
        improved_extract_function = '''def extract_wordle_scores_multi_league():
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
                
        # Use regex to replace the existing function
        pattern = r"def extract_wordle_scores_multi_league\(\):.*?return any_scores_extracted"
        updated_content = re.sub(pattern, improved_extract_function, content, flags=re.DOTALL)
        
        # Check if replacement was successful
        if updated_content == content:
            # Try a different approach - find the function start and manually replace
            lines = content.splitlines()
            new_lines = []
            skip_mode = False
            found_function = False
            
            for line in lines:
                if "def extract_wordle_scores_multi_league():" in line:
                    skip_mode = True
                    found_function = True
                    new_lines.append(improved_extract_function)
                elif skip_mode and "    return any_scores_extracted" in line:
                    skip_mode = False
                    continue
                elif not skip_mode:
                    new_lines.append(line)
                    
            if found_function:
                updated_content = "\n".join(new_lines)
            else:
                logging.error("Could not find extract_wordle_scores_multi_league function")
                return False
                
        # Write updated content
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        logging.info("Successfully updated extract_wordle_scores_multi_league function")
        return True
        
    except Exception as e:
        logging.error(f"Error updating extract_wordle_scores_multi_league function: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Extract function fix completed with success: {success}")
    sys.exit(0 if success else 1)
