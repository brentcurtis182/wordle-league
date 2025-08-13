#!/usr/bin/env python3
# Direct thread navigation using thread IDs from league_config.json
# Includes fallback to original content-based thread identification

import json
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import the original content-based thread identification
from is_league_thread import is_league_thread

def navigate_to_thread(driver, league_id):
    """
    Navigate directly to a Google Voice thread using its itemId
    with fallback to content-based identification
    
    Args:
        driver: Selenium WebDriver instance
        league_id: League ID to navigate to
        
    Returns:
        bool: True if navigation was successful, False otherwise
    """
    # First try direct navigation
    if direct_thread_navigation(driver, league_id):
        return True
        
    # If direct navigation fails, fall back to content-based identification
    logging.warning(f"Direct navigation failed for league {league_id}, trying content-based fallback")
    return content_based_navigation(driver, league_id)


def direct_thread_navigation(driver, league_id):
    """
    Navigate directly to a thread using its URL
    """
    try:
        # Load league configuration
        with open('league_config.json', 'r') as config_file:
            config_data = json.load(config_file)
            
        # Find the league with matching ID
        league_info = None
        for league in config_data['leagues']:
            if league['league_id'] == league_id:
                league_info = league
                break
                
        if not league_info:
            logging.error(f"League with ID {league_id} not found in configuration")
            return False
            
        # Get thread ID
        thread_id = league_info.get('thread_id')
        if not thread_id or not thread_id.startswith('g.Group'):
            logging.warning(f"No valid thread ID found for league {league_id}, will use content-based identification")
            return False
            
        # Navigate directly to the thread URL
        thread_url = f"https://voice.google.com/u/0/messages?itemId={thread_id}"
        logging.info(f"Navigating directly to thread for league {league_id} ({league_info['name']})")
        driver.get(thread_url)
        
        # Wait for conversation to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-list, gv-thread-details"))
            )
            logging.info(f"Successfully loaded thread for {league_info['name']} via direct URL")
            
            # Verify thread loaded properly by checking for Wordle content
            page_source = driver.page_source.lower()
            if "wordle" in page_source:
                logging.info(f"Verified thread contains Wordle content")
                return True
            else:
                logging.warning(f"Thread loaded but no Wordle content found, might be wrong thread")
                return False
            
        except TimeoutException:
            logging.error(f"Timed out waiting for thread to load for league {league_id}")
            driver.save_screenshot(f"thread_timeout_league_{league_id}.png")
            return False
            
    except Exception as e:
        logging.error(f"Error in direct navigation for league {league_id}: {str(e)}")
        return False


def content_based_navigation(driver, league_id):
    """
    Find and navigate to a thread using content-based identification
    (Original approach as fallback)
    """
    try:
        # Navigate to Google Voice main page
        driver.get("https://voice.google.com/u/0/messages")
        
        # Wait for thread list to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item, div[role='button'].container"))
            )
            logging.info("Thread list loaded for content-based search")
        except TimeoutException:
            logging.error("Timed out waiting for thread list to load")
            return False
            
        # Get all thread elements
        selectors = [
            "div[role='button'].container",
            "gv-conversation-list gv-thread-item",
            ".mat-ripple.container"
        ]
        
        thread_elements = []
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                thread_elements = elements
                logging.info(f"Found {len(elements)} threads with selector: {selector}")
                break
                
        if not thread_elements:
            logging.error("No thread elements found")
            return False
            
        # Find thread matching our league
        league_thread = None
        for thread in thread_elements:
            if is_league_thread(thread, league_id):
                league_thread = thread
                break
                
        if not league_thread:
            logging.error(f"No thread found for league {league_id}")
            return False
            
        # Click the thread
        try:
            logging.info(f"Clicking thread for league {league_id} using content-based identification")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", league_thread)
            time.sleep(1)
            league_thread.click()
            
            # Wait for thread to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-message-list, gv-thread-details"))
            )
            
            logging.info(f"Successfully loaded thread for league {league_id} via content-based identification")
            return True
            
        except Exception as e:
            logging.error(f"Error clicking thread: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"Error in content-based navigation for league {league_id}: {str(e)}")
        return False
