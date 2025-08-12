#!/usr/bin/env python3
# Completely rewritten extract_wordle_scores_multi_league function

import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

def extract_wordle_scores_multi_league(driver, 
                                      extract_hidden_scores_func, 
                                      get_todays_wordle_number_func,
                                      get_yesterdays_wordle_number_func,
                                      is_league_thread_func=None):
    """
    Extract Wordle scores from all leagues
    
    This function handles the extraction process for multiple leagues,
    ensuring each thread is opened only once per league.
    
    Args:
        driver: Selenium WebDriver instance
        extract_hidden_scores_func: Function to extract scores from thread
        get_todays_wordle_number_func: Function to get today's Wordle number
        get_yesterdays_wordle_number_func: Function to get yesterday's Wordle number
        is_league_thread_func: Function to identify which league a thread belongs to
    
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    logging.info("Starting improved multi-league extraction process")
    
    if not driver:
        logging.error("No WebDriver provided to extract_wordle_scores_multi_league")
        return False
        
    try:
        # Navigate to Google Voice
        logging.info("Navigating to Google Voice")
        driver.get("https://voice.google.com/messages")
        
        # Take screenshot for verification
        driver.save_screenshot("google_voice_navigation.png")
        
        # Wait for page to fully load
        time.sleep(5)
        
        # Wait for conversations to load
        try:
            logging.info("Waiting for conversation list to load...")
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
            )
            logging.info("Successfully loaded Google Voice conversations")
        except TimeoutException:
            logging.error("Timed out waiting for Google Voice conversations")
            return False
        
        # Find all conversation threads using multiple selectors
        logging.info("Finding conversation threads with multiple selectors")
        
        # Try multiple CSS selectors to find conversation threads
        selectors = [
            "gv-conversation-list gv-text-thread",
            "gv-conversation-list gv-thread-list-item", 
            "gv-message-thread-list-item gv-thread-list-item", 
            ".list-item",
            ".container.read[role='button']",
            "div[role='button'].container",
            "gv-thread-item"
        ]
        
        conversation_items = []
        for selector in selectors:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    conversation_items = items
                    logging.info(f"Found {len(items)} threads using selector: {selector}")
                    break
            except Exception as e:
                logging.warning(f"Selector '{selector}' failed: {e}")
        
        if not conversation_items:
            logging.error("No conversation threads found with any selector")
            driver.save_screenshot("no_threads_found.png")
            return False
            
        # Take screenshot of found threads
        driver.save_screenshot("threads_found.png")
        
        # Get today's and yesterday's Wordle numbers
        today_wordle = get_todays_wordle_number_func()
        yesterday_wordle = get_yesterdays_wordle_number_func()
        
        # Map threads to leagues
        thread_league_map = {}
        
        # Process the first 10 threads to identify which league they belong to
        for i, thread in enumerate(conversation_items[:10]):
            try:
                # Log full text for debugging
                thread_text = thread.text
                logging.info(f"Thread {i+1} text: {thread_text[:150]}..." if len(thread_text) > 150 else f"Thread {i+1} text: {thread_text}")
                
                # Take screenshot of thread for debugging
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread)
                    driver.save_screenshot(f"thread_{i+1}_view.png")
                except Exception as e:
                    logging.error(f"Error taking screenshot of thread {i+1}: {e}")
                
                # Identify which league this thread belongs to
                if is_league_thread_func:
                    if is_league_thread_func(thread_text, 1):
                        thread_league_map[i] = 1  # League 1: Wordle Warriorz
                        logging.info(f"Thread {i+1} identified as League 1 (Wordle Warriorz)")
                    elif is_league_thread_func(thread_text, 3):
                        thread_league_map[i] = 3  # League 3: PAL
                        logging.info(f"Thread {i+1} identified as League 3 (PAL)")
                    else:
                        logging.info(f"Thread {i+1} does not match any known league")
                else:
                    # Fallback identification if is_league_thread_func not provided
                    if any(id_marker in thread_text for id_marker in ["Wordle Warriorz", "Joanna", "Nanna", "310", "760", "858"]):
                        thread_league_map[i] = 1
                        logging.info(f"Thread {i+1} identified as League 1 (Wordle Warriorz) using fallback method")
                    elif any(id_marker in thread_text for id_marker in ["PAL", "Fuzwuz", "Vox", "Pants", "Starslider", "469"]):
                        thread_league_map[i] = 3
                        logging.info(f"Thread {i+1} identified as League 3 (PAL) using fallback method")
                
                # Log which identifiers were found in the thread text for debugging
                for marker, desc in [
                    ("310", "area code 310"), 
                    ("760", "area code 760"),
                    ("858", "area code 858"),
                    ("469", "area code 469"),
                    ("Joanna", "name Joanna"),
                    ("Nanna", "name Nanna"),
                    ("Brent", "name Brent"),
                    ("Wordle Warriorz", "'Wordle Warriorz'"),
                    ("PAL", "'PAL'"),
                    ("Fuzwuz", "name Fuzwuz"),
                    ("Vox", "name Vox"),
                    ("Pants", "name Pants")
                ]:
                    if marker in thread_text: 
                        logging.info(f"Thread {i+1} contains {desc}")
                
            except Exception as e:
                logging.error(f"Error identifying league for thread {i+1}: {e}")
        
        # Track total scores extracted
        total_scores = 0
        
        # Process League 1 threads (Wordle Warriorz)
        league_1_threads = [idx for idx, league in thread_league_map.items() if league == 1]
        if league_1_threads:
            logging.info(f"Found {len(league_1_threads)} threads for League 1 (Wordle Warriorz)")
            
            for thread_idx in league_1_threads:
                try:
                    # Get thread element
                    thread = conversation_items[thread_idx]
                    
                    # Take screenshot before clicking
                    driver.save_screenshot(f"before_click_league1_thread{thread_idx}.png")
                    
                    # Try multiple click methods
                    click_success = False
                    
                    # Method 1: Direct click with scrolling into view first
                    try:
                        logging.info(f"Attempting direct click on League 1 thread {thread_idx}")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread)
                        time.sleep(1)
                        thread.click()
                        time.sleep(2)
                        click_success = True
                        logging.info("Direct click succeeded")
                    except Exception as e:
                        logging.error(f"Direct click failed: {e}")
                    
                    # Method 2: JavaScript click
                    if not click_success:
                        try:
                            logging.info("Trying JavaScript click")
                            driver.execute_script("arguments[0].click();", thread)
                            time.sleep(2)
                            click_success = True
                            logging.info("JavaScript click succeeded")
                        except Exception as e:
                            logging.error(f"JavaScript click failed: {e}")
                    
                    # Method 3: ActionChains
                    if not click_success:
                        try:
                            logging.info("Trying ActionChains click")
                            actions = ActionChains(driver)
                            actions.move_to_element(thread).click().perform()
                            time.sleep(2)
                            click_success = True
                            logging.info("ActionChains click succeeded")
                        except Exception as e:
                            logging.error(f"ActionChains click failed: {e}")
                    
                    # Take screenshot after clicking
                    driver.save_screenshot(f"after_click_league1_thread{thread_idx}.png")
                    
                    if not click_success:
                        logging.error("All click methods failed, skipping thread")
                        continue
                    
                    # Wait additional time for thread to load completely
                    time.sleep(3)
                    
                    # Extract scores
                    logging.info("Extracting scores from League 1 conversation")
                    league_1_scores = extract_hidden_scores_func(driver, 1)
                    total_scores += league_1_scores
                    logging.info(f"Extracted {league_1_scores} scores from League 1")
                    
                except Exception as e:
                    logging.error(f"Error processing League 1 thread {thread_idx}: {e}")
        else:
            logging.warning("No threads found for League 1 (Wordle Warriorz)")
        
        # Go back to thread list
        driver.get("https://voice.google.com/messages")
        time.sleep(5)
        
        # Wait for conversations to load again
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
            )
            logging.info("Successfully reloaded Google Voice conversations for PAL league")
        except TimeoutException:
            logging.error("Timed out waiting for Google Voice conversations reload")
            return total_scores > 0
        
        # Get fresh conversation items
        conversation_items = []
        for selector in selectors:
            try:
                items = driver.find_elements(By.CSS_SELECTOR, selector)
                if items:
                    conversation_items = items
                    logging.info(f"Found {len(items)} threads after reload using selector: {selector}")
                    break
            except Exception as e:
                logging.warning(f"Selector '{selector}' failed after reload: {e}")
        
        if not conversation_items:
            logging.error("No conversation threads found after reload")
            driver.save_screenshot("no_threads_after_reload.png")
            return total_scores > 0
            
        # Take screenshot of found threads after reload
        driver.save_screenshot("threads_found_after_reload.png")
        
        # Re-map threads to leagues
        thread_league_map = {}
        for i, thread in enumerate(conversation_items[:10]):
            try:
                thread_text = thread.text
                logging.info(f"Reload thread {i+1} text: {thread_text[:150]}..." if len(thread_text) > 150 else f"Reload thread {i+1} text: {thread_text}")
                
                if is_league_thread_func:
                    if is_league_thread_func(thread_text, 1):
                        thread_league_map[i] = 1
                    elif is_league_thread_func(thread_text, 3):
                        thread_league_map[i] = 3
                else:
                    # Fallback identification
                    if any(id_marker in thread_text for id_marker in ["Wordle Warriorz", "Joanna", "Nanna", "310", "760", "858"]):
                        thread_league_map[i] = 1
                    elif any(id_marker in thread_text for id_marker in ["PAL", "Fuzwuz", "Vox", "Pants", "Starslider", "469"]):
                        thread_league_map[i] = 3
            except Exception as e:
                logging.error(f"Error identifying league after reload for thread {i+1}: {e}")
        
        # Process League 3 threads (PAL)
        league_3_threads = [idx for idx, league in thread_league_map.items() if league == 3]
        if league_3_threads:
            logging.info(f"Found {len(league_3_threads)} threads for League 3 (PAL)")
            
            for thread_idx in league_3_threads:
                try:
                    # Get thread element
                    thread = conversation_items[thread_idx]
                    
                    # Take screenshot before clicking
                    driver.save_screenshot(f"before_click_league3_thread{thread_idx}.png")
                    
                    # Try multiple click methods
                    click_success = False
                    
                    # Method 1: Direct click with scrolling into view first
                    try:
                        logging.info(f"Attempting direct click on League 3 thread {thread_idx}")
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", thread)
                        time.sleep(1)
                        thread.click()
                        time.sleep(2)
                        click_success = True
                        logging.info("Direct click succeeded for PAL league")
                    except Exception as e:
                        logging.error(f"Direct click failed for PAL league: {e}")
                    
                    # Method 2: JavaScript click
                    if not click_success:
                        try:
                            logging.info("Trying JavaScript click for PAL league")
                            driver.execute_script("arguments[0].click();", thread)
                            time.sleep(2)
                            click_success = True
                            logging.info("JavaScript click succeeded for PAL league")
                        except Exception as e:
                            logging.error(f"JavaScript click failed for PAL league: {e}")
                    
                    # Method 3: ActionChains
                    if not click_success:
                        try:
                            logging.info("Trying ActionChains click for PAL league")
                            actions = ActionChains(driver)
                            actions.move_to_element(thread).click().perform()
                            time.sleep(2)
                            click_success = True
                            logging.info("ActionChains click succeeded for PAL league")
                        except Exception as e:
                            logging.error(f"ActionChains click failed for PAL league: {e}")
                    
                    # Take screenshot after clicking
                    driver.save_screenshot(f"after_click_league3_thread{thread_idx}.png")
                    
                    if not click_success:
                        logging.error("All click methods failed for PAL league, skipping thread")
                        continue
                    
                    # Wait additional time for thread to load completely
                    time.sleep(3)
                    
                    # Extract scores
                    logging.info("Extracting scores from League 3 conversation (PAL)")
                    league_3_scores = extract_hidden_scores_func(driver, 3)
                    total_scores += league_3_scores
                    logging.info(f"Extracted {league_3_scores} scores from League 3 (PAL)")
                    
                except Exception as e:
                    logging.error(f"Error processing League 3 thread {thread_idx}: {e}")
        else:
            logging.warning("No threads found for League 3 (PAL)")
        
        # Return success if we found at least one score
        logging.info(f"Total scores extracted across all leagues: {total_scores}")
        return total_scores > 0
        
    except Exception as e:
        logging.error(f"Error in extract_wordle_scores_multi_league: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
