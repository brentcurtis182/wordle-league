#!/usr/bin/env python3
# Test script for scrolling functionality in Google Voice threads

import os
import sys
import time
import logging
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv

# Import the robust scrolling function from the actual module
from scroll_in_thread import scroll_up_in_thread

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_scrolling.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

def get_yesterdays_wordle_number():
    """Get yesterday's Wordle number dynamically based on yesterday's date"""
    # Wordle #1 was released on June 19, 2021
    wordle_start_date = datetime(2021, 6, 19).date()
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    # Calculate days between start date and yesterday
    days_since_start = (yesterday - wordle_start_date).days
    
    # Wordle number is days since start + 1
    wordle_number = days_since_start + 1
    logging.info(f"Calculated yesterday's Wordle #{wordle_number} for date {yesterday}")
    
    return wordle_number


def check_hidden_elements(driver, processed_ids=None):
    """Check hidden elements for Wordle scores.
    
    Args:
        driver: The WebDriver instance
        processed_ids: Set of already processed element IDs to avoid duplicates
        
    Returns:
        tuple: (number of new scores found, updated processed_ids set, found_yesterday_wordle flag)
    """
    if processed_ids is None:
        processed_ids = set()
        
    try:
        logging.info("Looking for hidden elements with Wordle scores")
        yesterday_wordle = get_yesterdays_wordle_number()
        logging.info(f"Calculated yesterday's Wordle #{yesterday_wordle} for date {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}")
        
        found_scores = 0
        found_yesterday_wordle = False
        all_found_scores = []
        
        # Wait for hidden elements to be present
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".cdk-visually-hidden"))
        )
        
        # Find all hidden elements that may contain message text
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements")
        
        # Process each hidden element
        for i, element in enumerate(hidden_elements):
            try:
                # Get element's unique identifier (hash of its content and position)
                element_text = element.get_attribute("textContent")
                element_id = hash(f"{element_text}_{element.location}")
                
                # Skip if already processed
                if element_id in processed_ids:
                    continue
                    
                # Add to processed set
                processed_ids.add(element_id)
                
                # Log first part of the text content
                try:
                    logging.info(f"Hidden element {i}: {element_text[:100]}...")
                except UnicodeEncodeError:
                    # Handle encoding issues with emojis
                    logging.info(f"Hidden element {i}: [Text with emoji - encoding error]")
                
                # First check for the word "Wordle" in the element text
                if "Wordle" in element_text:
                    logging.info(f"Element {i} contains 'Wordle' - attempting to extract score")
                    
                    # Try multiple patterns to catch different formats
                    patterns = [
                        r"Wordle\s+([\d,]+)\s+([\d]/[\d])",  # Standard format: Wordle 1,503 5/6
                        r"Wordle\s*#?\s*([\d,]+)\s+([\d]/[\d])",  # With optional #: Wordle #1503 5/6
                        r"Wordle\s*:?\s*([\d,]+)\s*:?\s*([\d]/[\d])",  # With colon: Wordle: 1503: 5/6
                    ]
                    
                    score_found = False
                    for pattern in patterns:
                        match = re.search(pattern, element_text)
                        if match:
                            wordle_num_str = match.group(1)
                            score = match.group(2)
                            logging.info(f"FOUND SCORE: Wordle {wordle_num_str} {score}")
                            # Extract phone number if available
                            phone_match = re.search(r"Message from ([\d\s]+),\s*Wordle", element_text)
                            phone_number = phone_match.group(1).strip() if phone_match else "Unknown"
                            logging.info(f"From phone: {phone_number}")
                            
                            found_scores += 1
                            score_info = f"Phone: {phone_number}, Wordle {wordle_num_str} {score}"
                            all_found_scores.append(score_info)
                            
                            # Store the score in a JavaScript variable for cross-thread access
                            driver.execute_script(
                                "if (!window._foundScores) window._foundScores = []; " + 
                                f"window._foundScores.push('{score_info}')"
                            )
                            score_found = True
                            
                            # Check if this is yesterday's Wordle
                            try:
                                wordle_num = int(wordle_num_str.replace(',', ''))
                                if wordle_num == yesterday_wordle:
                                    found_yesterday_wordle = True
                                    logging.info(f"Found yesterday's Wordle #{yesterday_wordle}")
                            except ValueError:
                                logging.warning(f"Could not parse Wordle number: {wordle_num_str}")
                                
                            break  # Stop after finding first match
                            
                    # If no pattern matched but "Wordle" is present, log for debugging
                    if not score_found:
                        logging.warning(f"Element contains 'Wordle' but no score pattern matched: {element_text[:200]}")
                    
                # Look for emoji patterns that might indicate Wordle even without the word "Wordle"
                elif "🟩" in element_text or "🟨" in element_text or "⬛" in element_text or "\u2b1c" in element_text:
                    logging.info(f"Element {i} contains Wordle emoji pattern but no 'Wordle' text")
            except Exception as e:
                logging.error(f"Error processing hidden element {i}: {e}")
        
        # Log summary of all found scores
        logging.info("============= FOUND SCORES SUMMARY =================")
        for idx, score in enumerate(all_found_scores):
            logging.info(f"Score {idx+1}: {score}")
        logging.info("=================================================")
        
        # Log extraction summary
        logging.info(f"This extraction: {found_scores} new scores found, yesterday's Wordle found: {found_yesterday_wordle}")
        return found_scores, processed_ids, found_yesterday_wordle
        
    except Exception as e:
        logging.error(f"Error checking hidden elements: {e}")
        return 0, processed_ids, False

def main():
    logging.info("Starting scrolling test for Google Voice")
    
    # Dictionary to store scores by league
    all_leagues_scores = {}
    
    # Use Chrome profile from the automation directory
    profile_path = os.path.join(os.getcwd(), "automation_profile")
    logging.info(f"Using Chrome profile at: {profile_path}")
    
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--disable-extensions")
    
    # Initialize WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Navigate to Google Voice
        logging.info("Navigating to Google Voice")
        driver.get("https://voice.google.com/messages")
        
        # Wait for conversation threads to load
        logging.info("Waiting for conversation threads to load")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']"))
        )
        
        # Find clickable conversation threads container elements
        logging.info("Searching for thread container elements...")
        threads = driver.find_elements(By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']")
        
        if not threads:
            logging.info("No threads found with primary selector, trying alternates...")
            alternate_selectors = [
                "div[shifthover][matripple].container[role='button']", 
                "gv-annotation.participants",
                ".item.thread", 
                ".thread-list .thread"
            ]
            for selector in alternate_selectors:
                threads = driver.find_elements(By.CSS_SELECTOR, selector)
                if threads:
                    logging.info(f"Found {len(threads)} threads with alternate selector: {selector}")
                    break
        
        # Process all threads (main league and PAL league)
        # Process each league thread sequentially
        all_leagues_scores = {}
        
        # Calculate yesterday's Wordle number once
        yesterday_wordle = get_yesterdays_wordle_number()
        logging.info(f"Calculated yesterday's Wordle #{yesterday_wordle} for date {(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')}")
        
        # Count the threads to process
        initial_thread_count = len(threads)
        logging.info(f"Found {initial_thread_count} conversation threads to process")
        
        # Process each thread individually
        for league_idx in range(initial_thread_count):
            league_name = f"League {league_idx+1}"
            all_leagues_scores[league_name] = []
            
            logging.info(f"\n{'='*30} PROCESSING {league_name} {'='*30}")
            
            # For each thread, start fresh from the messages page
            logging.info(f"Navigating to Google Voice messages page")
            driver.get("https://voice.google.com/messages")
            
            # Wait for conversation threads to load
            logging.info("Waiting for conversation threads to load...")
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']"))
            )
            
            # Find the threads again
            current_threads = driver.find_elements(By.CSS_SELECTOR, "gv-thread-list-item .container[role='button']")
            if not current_threads:
                logging.info("No threads found with primary selector, trying alternates...")
                alternate_selectors = [
                    "div[shifthover][matripple].container[role='button']", 
                    "gv-annotation.participants",
                    ".item.thread", 
                    ".thread-list .thread"
                ]
                for selector in alternate_selectors:
                    current_threads = driver.find_elements(By.CSS_SELECTOR, selector)
                    if current_threads:
                        logging.info(f"Found {len(current_threads)} threads with alternate selector: {selector}")
                        break
            
            # Check if threads were found
            if not current_threads:
                logging.error(f"No conversation threads found for {league_name}")
                continue
                
            # Make sure the index is within range
            if league_idx >= len(current_threads):
                logging.error(f"Thread index {league_idx} is out of range (only {len(current_threads)} threads available)")
                continue
                
            # Get the thread for this league
            current_thread = current_threads[league_idx]
            
            # Try to get the thread participants to identify the league
            try:
                # First check if we can find a participants annotation inside this thread
                participant_elements = current_thread.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                if participant_elements:
                    annotation_text = participant_elements[0].text
                    logging.info(f"{league_name} participants (from annotation): {annotation_text}")
                else:
                    # Fallback to using the thread container's text
                    annotation_text = current_thread.text
                    logging.info(f"{league_name} participants (from container): {annotation_text}")
                
                # Identify which league this is based on phone numbers
                if any(phone_num in annotation_text for phone_num in ["(310) 926-3555", "(760) 334-1190", "(760) 846-2302"]):
                    logging.info(f"{league_name} appears to be the main Wordle Warriorz league")
                elif any(phone_num in annotation_text for phone_num in ["(858) 735-9353", "(469) 834-5364"]):
                    logging.info(f"{league_name} appears to be the PAL league")
            except Exception as e:
                logging.error(f"Failed to get thread text: {e}")
            
            # Take screenshot before clicking to show thread state
            driver.save_screenshot(f"before_click_{league_idx}.png")
            logging.info(f"Saved screenshot before clicking thread {league_idx}")
            
            # Try multiple click methods to ensure reliability
            click_success = False
            
            # Method 1: Using JavaScript click on the container element
            try:
                driver.execute_script("arguments[0].click();", current_thread)
                logging.info(f"Clicked on {league_name} thread using JavaScript method 1")
                click_success = True
            except Exception as e:
                logging.error(f"Failed to click with JavaScript method 1: {e}")
            
            # Method 2: Click on any participant annotation inside (if not already clicked)
            if not click_success:
                try:
                    participant_elements = current_thread.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                    if participant_elements:
                        driver.execute_script("arguments[0].click();", participant_elements[0])
                        logging.info(f"Clicked on {league_name} thread's participant annotation")
                        click_success = True
                except Exception as e:
                    logging.error(f"Failed to click participant annotation: {e}")
            
            # Method 3: Regular Selenium click as fallback
            if not click_success:
                try:
                    current_thread.click()
                    logging.info(f"Clicked on {league_name} thread using regular click")
                    click_success = True
                except Exception as click_error:
                    logging.error(f"Regular click also failed: {click_error}")
            
            # Skip this thread if all click methods failed
            if not click_success:
                logging.error(f"All click methods failed for thread {league_idx}, skipping to next thread")
                continue  # Skip to next thread
            
            try:
                # Reset window._foundScores for this thread
                driver.execute_script("window._foundScores = [];")
                
                # Wait for thread to load
                logging.info(f"Waiting for {league_name} conversation thread to load")
                time.sleep(3)
                
                # Take a screenshot for verification
                driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_initial.png")
                
                # ITERATIVE SCROLLING AND EXTRACTION
                # Keep track of processed elements to avoid duplicates
                processed_ids = set()
                total_scores_found = 0
                found_yesterday = False
                max_scroll_attempts = 5
                
                logging.info(f"Starting iterative scrolling and extraction for {league_name}...")
                
                # Initial scroll and extraction
                scroll_success = scroll_up_in_thread(driver, yesterday_wordle)
                if not scroll_success:
                    logging.warning("Initial scroll may not have been successful")
                
                # Keep scrolling and extracting until we find yesterday's Wordle or reach max attempts
                for attempt in range(max_scroll_attempts):
                    logging.info(f"{league_name} - Scrolling and extraction attempt {attempt+1}/{max_scroll_attempts}")
                    
                    # Extract scores from current view
                    new_scores, processed_ids, found_yesterday = check_hidden_elements(driver, processed_ids)
                    total_scores_found += new_scores
                    
                    # Get scores from JavaScript variable
                    js_scores = driver.execute_script("return window._foundScores || []")
                    logging.info(f"Retrieved {len(js_scores)} scores from JavaScript variable")
                    
                    # Identify league key based on annotation text
                    league_key = "Unknown League"
                    if any(phone_num in annotation_text for phone_num in ["(310) 926-3555", "(760) 334-1190", "(760) 846-2302"]):
                        league_key = "Wordle Warriorz"
                    elif any(phone_num in annotation_text for phone_num in ["(858) 735-9353", "(469) 834-5364"]):
                        league_key = "PAL League"
                    
                    # Initialize list for this league if not already present
                    if league_key not in all_leagues_scores:
                        all_leagues_scores[league_key] = []
                    
                    # Add scores to the appropriate league
                    for score in js_scores:
                        logging.info(f"Score found in {league_key}: {score}")
                        if score not in all_leagues_scores[league_key]:
                            all_leagues_scores[league_key].append(score)
                    
                    if found_yesterday:
                        logging.info(f"Success! Found yesterday's Wordle #{yesterday_wordle} on attempt {attempt+1}")
                        break
                    
                    # If we haven't found yesterday's Wordle, scroll more
                    if not found_yesterday and attempt < max_scroll_attempts - 1:
                        logging.info(f"Haven't found yesterday's Wordle yet. Scrolling more...")
                        scroll_up_in_thread(driver, yesterday_wordle)
                        # Give time for new content to load
                        time.sleep(2)
                
                # Take a screenshot after extraction
                driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_after_extraction.png")
                
                # Final summary for this thread
                logging.info(f"{league_name} extraction complete. Found {total_scores_found} scores across {attempt+1} scrolling attempts")
                logging.info(f"{league_name} - Found yesterday's Wordle #{yesterday_wordle}: {found_yesterday}")
                
            except Exception as e:
                logging.error(f"Error processing {league_name}: {e}")
                # Take a screenshot if there was an error
                try:
                    driver.save_screenshot(f"{league_name.lower().replace(' ', '_')}_error.png")
                except:
                    pass
            
            # Overall summary across all leagues
            logging.info("\n" + "="*30 + " ALL LEAGUES SUMMARY " + "="*30)
            for league, scores in all_leagues_scores.items():
                logging.info(f"{league}: Found {len(scores)} scores")
                for idx, score in enumerate(scores):
                    logging.info(f"  Score {idx+1}: {score}")
            logging.info("="*80)
                
        time.sleep(3)  # Wait before closing the browser
        
    except Exception as e:
        logging.error(f"Error during test: {e}")
        
    finally:
        # Close the browser
        logging.info("Scrolling test completed")
        try:
            driver.save_screenshot("final_state.png")
            logging.info("Saved final screenshot")
        except Exception as e:
            logging.error(f"Error saving final screenshot: {e}")
        driver.quit()

if __name__ == "__main__":
    main()
