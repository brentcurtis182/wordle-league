#!/usr/bin/env python3
"""
Focused PAL League Thread Fix

This script specifically focuses on finding and clicking the PAL thread
after properly distinguishing it from the Wordle Warriorz thread.
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
        logging.FileHandler("focused_pal_fix.log"),
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
    """Navigate to Google Voice"""
    try:
        logging.info("Navigating to Google Voice")
        driver.get("https://voice.google.com/u/0/messages")
        
        # Wait for threads to appear
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

def identify_league_threads(driver):
    """Identify both league threads with clear logging"""
    try:
        logging.info("Looking for both Wordle Warriorz and PAL league threads")
        driver.save_screenshot("before_thread_identification.png")
        
        # Get all potential conversation threads
        selectors_to_try = [
            "gv-conversation-list gv-thread-item",
            "div[role='button'].container",
            ".mat-ripple.container",
            "div.container[tabindex='0']",
            "gv-thread-item",
            "div.container.read"
        ]
        
        all_threads = []
        used_selector = ""
        for selector in selectors_to_try:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items and len(items) > 0:
                    logging.info(f"Found {len(items)} items with selector: {selector}")
                    all_threads = items
                    used_selector = selector
                    break
            except Exception as e:
                logging.warning(f"Error with selector {selector}: {str(e)}")
        
        if not all_threads:
            logging.error("No conversation threads found")
            driver.save_screenshot("no_threads_found.png")
            return None, None
            
        logging.info(f"Found {len(all_threads)} total conversation threads using selector: {used_selector}")
        
        # Clear identification of each thread
        warriorz_thread = None
        pal_thread = None
        
        # For each thread, log its content and identify if it's Warriorz or PAL
        for i, thread in enumerate(all_threads):
            try:
                thread_text = thread.text
                thread_html = thread.get_attribute('outerHTML')
                
                # Log thread details (limited to avoid encoding issues)
                logging.info(f"Thread {i+1} - First 50 chars: {thread_text[:50]}")
                
                # Check for Wordle Warriorz identifiers
                if any(id in thread_text for id in ["Joanna", "Nanna", "Brent", "Malia", "Evan", "(310)"]):
                    logging.info(f"Thread {i+1} appears to be the Wordle Warriorz thread")
                    warriorz_thread = thread
                
                # Check for PAL identifiers
                if any(id in thread_text for id in ["Fuzwuz", "Vox", "PAL", "Pants", "Starslider", "(469)"]):
                    logging.info(f"Thread {i+1} appears to be the PAL thread")
                    pal_thread = thread
            except Exception as e:
                logging.error(f"Error examining thread {i+1}: {str(e)}")
        
        # Final determination and screenshots
        if warriorz_thread:
            logging.info("Found Wordle Warriorz thread!")
        else:
            logging.warning("Could not identify Wordle Warriorz thread")
            
        if pal_thread:
            logging.info("Found PAL league thread!")
        else:
            logging.warning("Could not identify PAL league thread")
            
        # Last resort: if we have exactly 2 threads and only identified one as Warriorz, the other might be PAL
        if len(all_threads) == 2 and warriorz_thread and not pal_thread:
            other_thread = [t for t in all_threads if t != warriorz_thread][0]
            logging.info("Using process of elimination - second thread must be PAL")
            pal_thread = other_thread
            
        driver.save_screenshot("after_thread_identification.png")
        return warriorz_thread, pal_thread
        
    except Exception as e:
        logging.error(f"Error identifying league threads: {str(e)}")
        driver.save_screenshot("thread_identification_error.png")
        return None, None

def click_thread(driver, thread, thread_name):
    """Click a thread robustly with proper logging"""
    if not thread:
        logging.error(f"No {thread_name} thread provided to click")
        return False
        
    logging.info(f"Attempting to click {thread_name} thread")
    driver.save_screenshot(f"before_{thread_name}_click.png")
    
    # Try multiple methods with proper waits
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
            time.sleep(2)  # Wait for thread to load
            
            # Check if thread loaded successfully
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-input, textarea.input"))
                )
                logging.info(f"{method['name']} successful!")
                driver.save_screenshot(f"after_successful_{thread_name}_click.png")
                return True
            except TimeoutException:
                logging.warning(f"{method['name']} didn't load thread completely, trying next method")
                continue
                
        except Exception as e:
            logging.error(f"Error with {method['name']}: {str(e)}")
    
    logging.error(f"All click methods failed for {thread_name} thread")
    driver.save_screenshot(f"all_click_methods_failed_{thread_name}.png")
    return False

def go_back_to_conversation_list(driver):
    """Go back to the conversation list"""
    try:
        logging.info("Going back to conversation list")
        
        # Try clicking the back button if present
        try:
            back_button = driver.find_element(By.CSS_SELECTOR, "gv-icon-button[icon='arrow_back']")
            back_button.click()
            logging.info("Clicked back button")
        except:
            # Try navigating back to messages
            logging.info("Back button not found, navigating directly to messages")
            driver.get("https://voice.google.com/u/0/messages")
        
        # Wait for conversation list to load again
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item, div[role='button'].container, .mat-ripple.container"))
        )
        
        logging.info("Successfully returned to conversation list")
        driver.save_screenshot("returned_to_conversation_list.png")
        return True
    except Exception as e:
        logging.error(f"Error going back to conversation list: {str(e)}")
        driver.save_screenshot("back_to_list_error.png")
        return False

def main():
    """Main function to fix PAL league thread clicking"""
    logging.info("Starting focused PAL league thread fix")
    
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
        
        # First identify both threads
        warriorz_thread, pal_thread = identify_league_threads(driver)
        
        if not pal_thread:
            logging.error("Could not identify PAL league thread")
            return False
        
        # Click PAL thread directly
        if click_thread(driver, pal_thread, "PAL"):
            logging.info("Successfully clicked PAL thread!")
            time.sleep(5)  # Wait to confirm thread is open
            driver.save_screenshot("pal_thread_opened.png")
            return True
            
        logging.error("Failed to click PAL league thread")
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
