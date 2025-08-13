#!/usr/bin/env python3
# Helper function to robustly click on Google Voice threads

import time
import logging
from selenium.webdriver.common.action_chains import ActionChains

def click_thread_robustly(driver, thread, thread_idx, league_id):
    """
    Attempts to click on a thread element using multiple methods to ensure success
    
    Args:
        driver: Selenium WebDriver instance
        thread: Thread element to click
        thread_idx: Index of the thread for logging
        league_id: League ID for logging
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Take a screenshot before attempting to click
    driver.save_screenshot(f"before_click_league_{league_id}_thread_{thread_idx}.png")
    logging.info(f"Attempting to click on League {league_id} thread {thread_idx}")
    
    # Scroll into view first
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread)
        time.sleep(1)
    except Exception as e:
        logging.error(f"Error scrolling thread into view: {e}")
    
    # Try multiple click methods
    click_success = False
    
    # Method 1: Direct click
    try:
        logging.info("Trying direct click method")
        thread.click()
        time.sleep(2)
        click_success = True
        logging.info("Direct click succeeded")
    except Exception as click_error:
        logging.error(f"Direct click failed: {click_error}")
    
    # Method 2: JavaScript click if direct click failed
    if not click_success:
        try:
            logging.info("Trying JavaScript click method")
            driver.execute_script("arguments[0].click();", thread)
            time.sleep(2)
            click_success = True
            logging.info("JavaScript click succeeded")
        except Exception as click_error:
            logging.error(f"JavaScript click failed: {click_error}")
    
    # Method 3: Action chains click if both previous methods failed
    if not click_success:
        try:
            logging.info("Trying ActionChains click method")
            actions = ActionChains(driver)
            actions.move_to_element(thread).click().perform()
            time.sleep(2)
            click_success = True
            logging.info("ActionChains click succeeded")
        except Exception as click_error:
            logging.error(f"ActionChains click failed: {click_error}")
    
    # Take a screenshot after attempting to click
    driver.save_screenshot(f"after_click_league_{league_id}_thread_{thread_idx}.png")
    
    if not click_success:
        logging.error("All click methods failed, thread not clicked")
        return False
    
    # Additional wait to ensure thread fully loads
    time.sleep(3)
    return True
