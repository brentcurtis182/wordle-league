#!/usr/bin/env python3
"""
Direct Thread Fix for Wordle League Multi-League Extraction

This script provides a drop-in replacement for the extract_wordle_scores_multi_league function
with improved thread clicking and identification capabilities.
"""

import os
import sys
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("direct_thread_fix.log"),
        logging.StreamHandler()
    ]
)

def click_thread_robustly(driver, thread_element, league_id):
    """
    Improved thread clicking with multiple methods and scrolling
    
    Args:
        driver: Selenium WebDriver instance
        thread_element: The thread element to click
        league_id: League ID for logging
        
    Returns:
        bool: True if clicked successfully, False otherwise
    """
    league_name = "Wordle Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
    logging.info(f"Attempting to click {league_name} thread robustly")
    
    # Take screenshot before clicking
    screenshot_name = f"before_click_league{league_id}.png"
    try:
        driver.save_screenshot(screenshot_name)
        logging.info(f"Screenshot saved: {screenshot_name}")
    except Exception as e:
        logging.error(f"Error saving screenshot: {e}")
    
    # Try multiple methods with scrolling
    methods = [
        {
            "name": "Direct click with scrollIntoView",
            "action": lambda: (
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread_element),
                time.sleep(1),
                thread_element.click()
            )
        },
        {
            "name": "JavaScript click",
            "action": lambda: driver.execute_script("arguments[0].click();", thread_element)
        },
        {
            "name": "ActionChains move and click",
            "action": lambda: ActionChains(driver).move_to_element(thread_element).click().perform()
        },
        {
            "name": "ElementClickInterceptedException handling",
            "action": lambda: (
                driver.execute_script("arguments[0].scrollIntoView(true);", thread_element),
                time.sleep(1),
                driver.execute_script("""
                    var evt = document.createEvent('MouseEvents');
                    evt.initMouseEvent('click', true, true, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
                    arguments[0].dispatchEvent(evt);
                """, thread_element)
            )
        }
    ]
    
    success = False
    for method in methods:
        try:
            logging.info(f"Trying method: {method['name']}")
            method["action"]()
            time.sleep(3)  # Wait for thread to load
            
            # Check if thread loaded by looking for message input area
            try:
                message_input = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-input"))
                )
                logging.info(f"{method['name']} succeeded! Thread opened successfully")
                success = True
                break
            except TimeoutException:
                logging.warning(f"Thread may not have loaded after {method['name']}")
                continue
                
        except Exception as e:
            logging.error(f"Error with {method['name']}: {str(e)}")
    
    # Take screenshot after click attempts
    screenshot_name = f"after_click_league{league_id}.png"
    try:
        driver.save_screenshot(screenshot_name)
        logging.info(f"Screenshot saved: {screenshot_name}")
    except Exception as e:
        logging.error(f"Error saving screenshot: {e}")
    
    return success

def improved_extract_wordle_scores_multi_league(driver=None):
    """
    Enhanced version of extract_wordle_scores_multi_league with improved thread clicking
    
    Returns:
        bool: True if any scores were extracted, False otherwise
    """
    # Import needed functions from the original script
    # We import inside the function to avoid circular imports
    from integrated_auto_update_multi_league import (
        setup_driver, get_todays_wordle_number, get_yesterdays_wordle_number,
        navigate_to_google_voice, find_conversation_threads, extract_scores_from_conversations,
        kill_chrome_processes, LEAGUES
    )
    
    # Import our enhanced thread identification
    from is_league_thread import is_league_thread
    
    logging.info("Starting improved multi-league extraction")
    
    # Create or use provided driver
    close_driver_when_done = False
    if driver is None:
        driver = setup_driver()
        close_driver_when_done = True
        
    if driver is None:
        logging.error("Failed to set up Chrome driver")
        return False
    
    try:
        # Get Wordle numbers
        today_wordle = get_todays_wordle_number()
        yesterday_wordle = get_yesterdays_wordle_number()
        
        # Get scores from each league
        scores_extracted = False
        
        # First, navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return False
            
        # Process each league
        for league in LEAGUES:
            league_id = league["league_id"]
            league_name = league["name"]
            
            logging.info(f"Processing {league_name} (League ID: {league_id})")
            
            # Take screenshot before finding threads
            screenshot_name = f"before_finding_threads_league{league_id}.png"
            try:
                driver.save_screenshot(screenshot_name)
                logging.info(f"Screenshot saved: {screenshot_name}")
            except Exception as e:
                logging.error(f"Error saving screenshot: {e}")
                
            # Find conversation threads for this league using multiple selectors
            css_selectors = [
                ".conversation-wrapper .conversation", 
                "gv-conversation-list gv-conversation-item",
                "[aria-label='Conversation list'] [role='listitem']",
                ".gvConversationListItem"
            ]
            
            conversation_threads = None
            for selector in css_selectors:
                try:
                    logging.info(f"Trying to find threads with selector: {selector}")
                    conversation_items = driver.find_elements(By.CSS_SELECTOR, selector)
                    if conversation_items:
                        conversation_threads = conversation_items
                        logging.info(f"Found {len(conversation_items)} threads with selector: {selector}")
                        break
                except Exception as e:
                    logging.error(f"Error finding threads with selector '{selector}': {e}")
            
            # Filter conversation threads for this league
            if conversation_threads:
                league_threads = []
                for thread in conversation_threads:
                    try:
                        if is_league_thread(thread, league_id):
                            league_threads.append(thread)
                            logging.info(f"Identified thread for league {league_id}")
                    except Exception as e:
                        logging.error(f"Error checking if thread belongs to league {league_id}: {e}")
                
                if league_threads:
                    logging.info(f"Found {len(league_threads)} threads for league {league_id}")
                    
                    # Process each thread in this league
                    for i, thread in enumerate(league_threads):
                        try:
                            logging.info(f"Processing thread {i+1}/{len(league_threads)} for {league_name}")
                            
                            # Use improved thread clicking
                            if click_thread_robustly(driver, thread, league_id):
                                # Extract scores from this thread
                                scores = extract_scores_from_conversations(
                                    driver, 
                                    [thread],  # We're already in the thread
                                    today_wordle,
                                    yesterday_wordle,
                                    league_id
                                )
                                
                                if scores > 0:
                                    logging.info(f"Extracted {scores} scores from thread {i+1} in {league_name}")
                                    scores_extracted = True
                            else:
                                logging.error(f"Failed to open thread {i+1} for {league_name}")
                            
                            # Navigate back to Google Voice main page after each thread
                            logging.info("Navigating back to Google Voice main page")
                            driver.get("https://voice.google.com/u/0/messages")
                            time.sleep(5)  # Wait for page to load
                            
                        except Exception as e:
                            logging.error(f"Error processing thread {i+1} for {league_name}: {e}")
                            # Navigate back to Google Voice main page after exception
                            try:
                                driver.get("https://voice.google.com/u/0/messages")
                                time.sleep(5)  # Wait for page to load
                            except:
                                pass
                else:
                    logging.warning(f"No threads found for league {league_id}")
            else:
                logging.error(f"Failed to find any conversation threads for league {league_id}")
                
        return scores_extracted
            
    except Exception as e:
        logging.error(f"Error in improved_extract_wordle_scores_multi_league: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
    
    finally:
        # Close driver if we created it
        if close_driver_when_done and driver is not None:
            try:
                driver.quit()
                logging.info("Chrome driver closed")
            except Exception as e:
                logging.error(f"Error closing Chrome driver: {e}")

if __name__ == "__main__":
    # When run directly, execute the improved extraction
    success = improved_extract_wordle_scores_multi_league()
    print(f"Extraction completed with success: {success}")
    sys.exit(0 if success else 1)
