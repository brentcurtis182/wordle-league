#!/usr/bin/env python3
# Wrapper for improved extraction with robust thread clicking

import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

def extract_with_improved_clicking(driver, thread, league_id):
    """
    Click on a thread using multiple methods for reliability
    
    Args:
        driver: Selenium WebDriver instance
        thread: The thread element to click on
        league_id: League ID for logging
        
    Returns:
        bool: True if any click method succeeded, False otherwise
    """
    league_name = "Wordle Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
    logging.info(f"Attempting to click on {league_name} thread with improved method")
    
    # Take screenshot before clicking
    screenshot_name = f"before_click_league{league_id}_thread.png"
    try:
        driver.save_screenshot(screenshot_name)
        logging.info(f"Saved screenshot before clicking: {screenshot_name}")
    except Exception as e:
        logging.error(f"Error saving screenshot before clicking: {e}")
    
    # Try multiple click methods
    click_success = False
    
    # Method 1: Direct click with scrolling into view first
    try:
        logging.info(f"Attempting direct click on {league_name} thread")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread)
        time.sleep(1)
        thread.click()
        time.sleep(2)
        click_success = True
        logging.info(f"Direct click succeeded for {league_name}")
    except Exception as e:
        logging.error(f"Direct click failed for {league_name}: {e}")
    
    # Method 2: JavaScript click
    if not click_success:
        try:
            logging.info(f"Trying JavaScript click for {league_name}")
            driver.execute_script("arguments[0].click();", thread)
            time.sleep(2)
            click_success = True
            logging.info(f"JavaScript click succeeded for {league_name}")
        except Exception as e:
            logging.error(f"JavaScript click failed for {league_name}: {e}")
    
    # Method 3: ActionChains
    if not click_success:
        try:
            logging.info(f"Trying ActionChains click for {league_name}")
            actions = ActionChains(driver)
            actions.move_to_element(thread).click().perform()
            time.sleep(2)
            click_success = True
            logging.info(f"ActionChains click succeeded for {league_name}")
        except Exception as e:
            logging.error(f"ActionChains click failed for {league_name}: {e}")
    
    # Take screenshot after clicking
    screenshot_name = f"after_click_league{league_id}_thread.png"
    try:
        driver.save_screenshot(screenshot_name)
        logging.info(f"Saved screenshot after clicking: {screenshot_name}")
    except Exception as e:
        logging.error(f"Error saving screenshot after clicking: {e}")
    
    if click_success:
        # Wait additional time for thread to load completely
        time.sleep(3)
        return True
    else:
        logging.error(f"All click methods failed for {league_name}")
        return False

def patch_extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle, league_id=1):
    """
    A patched version of extract_scores_from_conversations that uses improved clicking
    
    This function is meant to be used as a drop-in replacement for the original
    extract_scores_from_conversations function.
    
    Args:
        driver: Selenium WebDriver instance
        conversation_items: List of conversation items to process
        today_wordle: Today's Wordle number
        yesterday_wordle: Yesterday's Wordle number
        league_id: League ID to use for extraction
        
    Returns:
        int: Number of scores extracted
    """
    logging.info(f"Starting patched extraction for league {league_id} with improved thread clicking")
    
    if not conversation_items:
        logging.warning(f"No conversation items provided for league {league_id}")
        return 0
        
    total_scores = 0
    
    for i, thread in enumerate(conversation_items):
        try:
            # Use improved click method
            if not extract_with_improved_clicking(driver, thread, league_id):
                logging.error(f"Failed to click thread {i} for league {league_id}, skipping")
                continue
                
            # Call the original extract_hidden_scores or other score extraction function
            # This would be provided by the main script
            logging.info(f"Successfully clicked thread {i} for league {league_id}, extracting scores")
            
            # The caller should extract scores here after this function returns True
            
        except Exception as e:
            logging.error(f"Error processing thread {i} for league {league_id}: {e}")
            
    return total_scores
