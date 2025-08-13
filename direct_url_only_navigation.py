#!/usr/bin/env python3
# Direct thread navigation using thread IDs from league_config.json
# This version only uses direct URL navigation without any fallbacks

import json
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def navigate_to_thread_by_url(driver, league_id):
    """
    Navigate directly to a Google Voice thread using its itemId from league_config.json
    
    Args:
        driver: Selenium WebDriver instance
        league_id: League ID to navigate to
        
    Returns:
        bool: True if navigation was successful, False otherwise
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
            logging.error(f"No valid thread ID found for league {league_id}")
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
            
            # Thread loaded successfully - we trust the direct URL is correct
            # Adding a small scroll to ensure content is loaded
            try:
                # Scroll down a bit to trigger content loading
                driver.execute_script("window.scrollBy(0, 300);") 
                time.sleep(1)
                
                # We consider navigation successful if we got to this point
                logging.info(f"Thread loaded successfully via direct URL")
                return True
            except Exception as e:
                logging.warning(f"Thread loaded but scroll failed: {str(e)}")
                # Still return True because navigation was successful
                return True
            
        except TimeoutException:
            logging.error(f"Timed out waiting for thread to load for league {league_id}")
            driver.save_screenshot(f"thread_timeout_league_{league_id}.png")
            return False
            
    except Exception as e:
        logging.error(f"Error navigating to thread for league {league_id}: {str(e)}")
        return False
