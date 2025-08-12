#!/usr/bin/env python3
# DOM Capture Diagnostic Tool for Wordle Score Extraction

import os
import sys
import time
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dom_capture_diagnostic.log"),
        logging.StreamHandler()
    ]
)

# League configuration 
LEAGUES = [
    {
        "league_id": 1, 
        "name": "Wordle Warriorz",
        "is_default": True
    }
]

# Create a directory for DOM captures if it doesn't exist
os.makedirs("dom_captures", exist_ok=True)

def get_todays_wordle_number():
    """Get today's Wordle number dynamically based on the current date"""
    # Wordle #1 was released on June 19, 2021
    wordle_start_date = datetime(2021, 6, 19).date()
    today = datetime.now().date()
    
    # Calculate days between start date and today
    days_since_start = (today - wordle_start_date).days
    
    # Wordle number is days since start + 1
    wordle_number = days_since_start + 1
    logging.info(f"Calculated today's Wordle #{wordle_number} for date {today}")
    
    return wordle_number

def get_yesterdays_wordle_number():
    """Get yesterday's Wordle number dynamically based on yesterday's date"""
    return get_todays_wordle_number() - 1

def capture_dom_snapshot(driver, filename):
    """Save a DOM snapshot to a file"""
    try:
        # Ensure dom_captures directory exists
        os.makedirs("dom_captures", exist_ok=True)
        
        # Get the full page source
        page_source = driver.page_source
        
        # Save to file
        with open(os.path.join("dom_captures", filename), "w", encoding="utf-8") as f:
            f.write(page_source)
            
        logging.info(f"Saved DOM snapshot to {filename}")
        
        # Parse with BeautifulSoup for better analysis
        soup = BeautifulSoup(page_source, 'html.parser')
        
        # Look for specific elements that might indicate a problem
        messages = soup.select("gv-message-item")
        logging.info(f"Found {len(messages)} message items in the DOM")
        
        return True
    except Exception as e:
        logging.error(f"Error capturing DOM snapshot: {e}")
        return False

def capture_hidden_elements(driver, filename):
    """Capture all .cdk-visually-hidden elements and save their text to a file"""
    try:
        # Ensure dom_captures directory exists
        os.makedirs("dom_captures", exist_ok=True)
        
        # Find all hidden elements
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements")
        
        # Create a file to store the content
        with open(os.path.join("dom_captures", filename), "w", encoding="utf-8") as f:
            f.write(f"=== Hidden Elements Capture ===\n")
            f.write(f"Timestamp: {datetime.now()}\n")
            f.write(f"Total hidden elements: {len(hidden_elements)}\n\n")
            
            # Track stats on Wordle scores found
            wordle_count = 0
            today_wordle = get_todays_wordle_number()
            yesterday_wordle = get_yesterdays_wordle_number()
            
            today_wordle_str = f"Wordle {today_wordle}"
            today_wordle_comma_str = f"Wordle {today_wordle:,}"
            yesterday_wordle_str = f"Wordle {yesterday_wordle}"
            yesterday_wordle_comma_str = f"Wordle {yesterday_wordle:,}"
            
            # Regular expression to extract scores
            wordle_regex = re.compile(r'Wordle ([\d,]+)(?: #([\d,]+)?)? ([1-6X])/6')
            
            # Check each hidden element
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.text.strip()
                    
                    # Skip any reactions
                    if text.startswith("Loved ") or text.startswith("Liked ") or "reacted with" in text.lower() or "reacted to" in text.lower():
                        continue
                    
                    f.write(f"--- Element {i+1} ---\n")
                    f.write(f"{text}\n\n")
                    
                    # Check for Wordle scores
                    if today_wordle_str in text or today_wordle_comma_str in text or yesterday_wordle_str in text or yesterday_wordle_comma_str in text:
                        wordle_count += 1
                        f.write(f"*** WORDLE SCORE DETECTED! ***\n\n")
                        
                        # Extract specific information about the score
                        match = wordle_regex.search(text)
                        if match:
                            wordle_num_str = match.group(1)
                            score_str = match.group(3)
                            
                            # Extract phone number for player mapping
                            phone_match = re.search(r'Message from (\d[\s\d-]+\d)', text)
                            phone = "Unknown"
                            if phone_match:
                                phone = phone_match.group(1)
                                phone = re.sub(r'[\s\-\(\)]+', '', phone)
                                
                            # Look for player names directly
                            player = "Unknown"
                            for name in ["Malia", "Evan", "Joanna", "Brent", "Nanna", "Vox", "Fuzwuz", "Starslider", "Pants"]:
                                if name in text:
                                    player = name
                                    break
                                    
                            f.write(f"Player hint: {player}\n")
                            f.write(f"Phone: {phone}\n")
                            f.write(f"Wordle #: {wordle_num_str}\n")
                            f.write(f"Score: {score_str}/6\n")
                            
                            # Check for emoji pattern
                            if '\n' in text:
                                lines = text.split('\n')
                                emoji_lines = []
                                in_emoji_pattern = False
                                
                                for line in lines[1:15]:  # Check up to 15 lines after header
                                    if '🟩' in line or '⬛' in line or '⬜' in line or '🟨' in line:
                                        emoji_lines.append(line)
                                        in_emoji_pattern = True
                                    elif in_emoji_pattern:
                                        break
                                
                                if emoji_lines:
                                    f.write(f"Emoji Pattern: Found ({len(emoji_lines)} lines)\n")
                                else:
                                    f.write("Emoji Pattern: Not found\n")
                except Exception as e:
                    f.write(f"Error processing element: {str(e)}\n\n")
                
            # Write summary
            f.write(f"\n=== SUMMARY ===\n")
            f.write(f"Total Wordle scores detected: {wordle_count}\n")
            f.write(f"Today's Wordle number: {today_wordle}\n")
            f.write(f"Yesterday's Wordle number: {yesterday_wordle}\n")
        
        logging.info(f"Saved hidden elements to {filename} (Found {wordle_count} Wordle scores)")
        return wordle_count
    except Exception as e:
        logging.error(f"Error capturing hidden elements: {e}")
        return 0

def run_diagnostic():
    """Run diagnostic to capture DOM and analyze for Wordle scores"""
    logging.info("Starting DOM capture diagnostic")
    
    driver = None
    
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
            logging.warning(f"Chrome profile directory not found at {profile_path}, using default profile")
        
        # Initialize Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google Voice
        driver.get("https://voice.google.com/messages")
        logging.info("Navigated to Google Voice messages")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Take a screenshot to verify navigation
        driver.save_screenshot("google_voice_navigation.png")
        logging.info("Saved screenshot of Google Voice navigation")
        
        # Capture the DOM after navigation
        capture_dom_snapshot(driver, "initial_dom.html")
        
        # Find conversation threads - we're specifically looking for the Wordle Warriorz thread
        try:
            # Wait for threads to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item"))
            )
            
            # Get all thread items
            conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list gv-thread-item")
            logging.info(f"Found {len(conversation_items)} conversation threads")
            
            # Look for Warriorz thread with multiple participants
            warriorz_thread = None
            
            for i, item in enumerate(conversation_items):
                try:
                    # Check if this has multiple participants (group thread)
                    annotations = item.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                    
                    if annotations:
                        annotation_text = annotations[0].text
                        logging.info(f"Thread {i+1} participants: {annotation_text}")
                        
                        # Look for specific number patterns that would identify the Warriorz thread
                        # Main league: (310) 926-3555, (760) 334-1190, etc.
                        if "(310)" in annotation_text or "(760)" in annotation_text:
                            logging.info(f"Thread {i+1} appears to be the main Wordle Warriorz league")
                            warriorz_thread = item
                            break
                except Exception as e:
                    logging.error(f"Error checking thread {i+1}: {e}")
            
            if not warriorz_thread:
                logging.error("Could not find the Wordle Warriorz thread")
                return False
            
            # Click on the Warriorz thread to load conversation
            logging.info("Clicking on Wordle Warriorz thread")
            try:
                warriorz_thread.click()
                logging.info("Clicked on Warriorz thread")
            except Exception as click_error:
                logging.error(f"Error clicking thread: {click_error}")
                try:
                    # Try JavaScript click as fallback
                    driver.execute_script("arguments[0].click();", warriorz_thread)
                    logging.info("Clicked on Warriorz thread using JavaScript")
                except Exception as js_error:
                    logging.error(f"JavaScript click also failed: {js_error}")
                    return False
            
            # Wait for conversation to load
            time.sleep(5)
            
            # Capture DOM after clicking thread
            capture_dom_snapshot(driver, "after_thread_click.html")
            
            # Capture hidden elements right after clicking
            scores_found = capture_hidden_elements(driver, "initial_hidden_elements.txt")
            logging.info(f"Initial hidden elements capture found {scores_found} Wordle scores")
            
            # Now let's implement aggressive scrolling to ensure all messages are loaded
            logging.info("Starting aggressive scrolling to load all messages")
            
            # Find the scrollable container
            message_container = driver.find_element(By.CSS_SELECTOR, "gv-message-list")
            
            # Perform multiple scroll attempts
            for i in range(10):
                logging.info(f"Scroll attempt #{i+1}")
                
                # Scroll to top using multiple methods
                driver.execute_script("arguments[0].scrollTop = 0;", message_container)
                time.sleep(1)
                
                # Take screenshot after each scroll
                driver.save_screenshot(f"scroll_attempt_{i+1}.png")
                
                # Capture hidden elements after each scroll
                scores_found = capture_hidden_elements(driver, f"hidden_elements_after_scroll_{i+1}.txt")
                logging.info(f"Found {scores_found} Wordle scores after scroll attempt #{i+1}")
                
                # If we found a good number of scores, we can stop
                if scores_found >= 5:
                    logging.info(f"Found {scores_found} scores, which seems sufficient")
                    break
            
            # Final capture
            capture_dom_snapshot(driver, "final_dom.html")
            scores_found = capture_hidden_elements(driver, "final_hidden_elements.txt")
            logging.info(f"Final hidden elements capture found {scores_found} Wordle scores")
            
            return True
            
        except Exception as e:
            logging.error(f"Error during thread navigation and analysis: {e}")
            return False
            
    except Exception as e:
        logging.error(f"Error during diagnostic: {e}")
        return False
    finally:
        if driver:
            # Capture final screenshot
            try:
                driver.save_screenshot("diagnostic_final.png")
            except:
                pass
                
            # Close the driver
            try:
                driver.quit()
            except:
                pass
                
    logging.info("DOM capture diagnostic completed")

if __name__ == "__main__":
    run_diagnostic()
