#!/usr/bin/env python3
"""
Direct PAL League Thread Fix

This script specifically targets the PAL league thread identification and clicking issue.
It uses the exact working selectors from the integrated_auto_update_multi_league.py script
that you mentioned works reliably.
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
        logging.FileHandler("direct_pal_fix.log"),
        logging.StreamHandler()
    ]
)

def setup_driver():
    """Set up Chrome driver using the exact same settings as the working script"""
    logging.info("Setting up Chrome driver")
    try:
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use existing Chrome profile to avoid login issues
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"user-data-dir={profile_path}")
            logging.info(f"Using existing Chrome profile at {profile_path}")
        else:
            logging.warning(f"Chrome profile not found at {profile_path}")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {e}")
        return None

def navigate_to_google_voice(driver):
    """Navigate to Google Voice using the exact same approach as the working script"""
    try:
        logging.info("Navigating to Google Voice")
        driver.get("https://voice.google.com/u/0/messages")
        
        # Wait for threads to appear - using the same selector as the working script
        logging.info("Waiting for Google Voice to load")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item, div[role='button'].container, .mat-ripple.container"))
        )
        
        logging.info("Successfully loaded Google Voice")
        driver.save_screenshot("google_voice_loaded.png")
        return True
    except TimeoutException:
        logging.error("Timed out waiting for Google Voice to load")
        driver.save_screenshot("google_voice_timeout.png")
        return False
    except Exception as e:
        logging.error(f"Error navigating to Google Voice: {e}")
        return False

def find_conversation_threads(driver, league_id=3):  # Default to PAL league
    """Find conversation threads using the exact same method as the working script"""
    try:
        logging.info(f"Looking for conversation threads for league {league_id}")
        
        # Take a screenshot to verify the state before searching
        driver.save_screenshot(f"before_thread_search_league_{league_id}.png")
        
        # Try multiple selector strategies to find conversation items - SAME as working script
        selectors_to_try = [
            "gv-conversation-list gv-thread-item",
            "div[role='button'].container",
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
        
        # For PAL league (league_id 3)
        if league_id == 3:
            # Look for the PAL thread using SAME identifiers as working script
            for i, item in enumerate(conversation_items):
                try:
                    # Try to get the item's text content
                    item_text = item.text
                    html = item.get_attribute('outerHTML')
                    logging.info(f"Thread {i+1} text: {item_text[:50]}...")
                    logging.info(f"Thread {i+1} HTML snippet: {html[:100]}...")
                    
                    # Check if this has PAL participants - SAME as working script
                    if any(identifier in item_text for identifier in ["469", "858", "Fuzwuz", "Vox", "PAL", "Pants", "Starslider"]):
                        logging.info(f"Thread {i+1} appears to be the Wordle PAL league")
                        return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for PAL: {e}")
        
        # If we reach here, we didn't find the right thread
        logging.warning(f"Could not identify specific thread for league {league_id}")
        driver.save_screenshot(f"thread_identification_failed_league_{league_id}.png")
        
        # Log all thread texts for debugging
        logging.info("All thread texts:")
        for i, item in enumerate(conversation_items[:10]):  # Log up to 10 threads
            try:
                logging.info(f"Thread {i+1}: {item.text[:100]}...")
            except:
                logging.info(f"Thread {i+1}: [Could not get text]")
        
        return conversation_items  # Return all threads as fallback
    
    except Exception as e:
        logging.error(f"Error finding conversation threads: {str(e)}")
        driver.save_screenshot(f"thread_search_error_league_{league_id}.png")
        return None

def click_thread_robustly(driver, thread):
    """Enhanced thread clicking with multiple methods"""
    logging.info("Attempting to click PAL thread robustly")
    
    # Take screenshot before clicking
    driver.save_screenshot("before_thread_click.png")
    
    # Try multiple methods
    methods = [
        {
            "name": "Direct click",
            "action": lambda: thread.click()
        },
        {
            "name": "JavaScript click",
            "action": lambda: driver.execute_script("arguments[0].click();", thread)
        },
        {
            "name": "ActionChains click",
            "action": lambda: ActionChains(driver).move_to_element(thread).click().perform()
        },
        {
            "name": "Scroll and click",
            "action": lambda: (
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread),
                time.sleep(1),
                thread.click()
            )
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
                driver.save_screenshot("after_successful_click.png")
                return True
            except TimeoutException:
                logging.warning(f"{method['name']} didn't load thread completely, trying next method")
                continue
                
        except Exception as e:
            logging.error(f"Error with {method['name']}: {str(e)}")
    
    logging.error("All click methods failed")
    driver.save_screenshot("all_click_methods_failed.png")
    return False

def main():
    """Main function to fix PAL league thread clicking"""
    logging.info("Starting PAL league thread fix")
    
    driver = None
    try:
        # Set up driver
        driver = setup_driver()
        if not driver:
            logging.error("Failed to set up driver")
            return False
        
        # Navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return False
        
        # Find PAL league thread
        threads = find_conversation_threads(driver, league_id=3)
        if not threads:
            logging.error("No PAL league threads found")
            return False
        
        # If multiple threads returned, try each one
        for i, thread in enumerate(threads):
            logging.info(f"Attempting to click thread {i+1}/{len(threads)}")
            
            # Try clicking this thread
            if click_thread_robustly(driver, thread):
                logging.info(f"Successfully clicked thread {i+1}")
                # Thread opened successfully - you could extract scores here
                return True
        
        logging.error("Failed to click any PAL league thread")
        return False
        
    except Exception as e:
        logging.error(f"Error in main function: {str(e)}")
        if driver:
            driver.save_screenshot("main_function_error.png")
        return False
        
    finally:
        # Clean up
        if driver:
            driver.quit()
            logging.info("Driver closed")

if __name__ == "__main__":
    success = main()
    print(f"PAL league thread fix completed with success: {success}")
    sys.exit(0 if success else 1)
