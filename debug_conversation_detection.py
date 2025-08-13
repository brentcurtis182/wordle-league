import os
import sys
import time
import logging
import datetime
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler()])

# Import from the main script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from integrated_auto_update_multi_league import (
        setup_driver, 
        login_to_google_voice, 
        navigate_to_google_voice, 
        identify_wordle_numbers,
        get_conversation_items,
        extract_emoji_pattern,
        parse_score
    )
    
    def debug_conversations():
        """Debug function to just display what's in the conversations without extracting"""
        driver = None
        try:
            # Set up Chrome driver
            driver = setup_driver()
            
            # Navigate to Google Voice
            navigate_to_google_voice(driver)
            
            # Login if needed
            login_success = login_to_google_voice(driver)
            if not login_success:
                logging.error("Failed to login to Google Voice")
                return
            
            # Wait for the page to load completely
            time.sleep(5)
            
            # Get conversation items
            conversation_items = get_conversation_items(driver)
            logging.info(f"Found {len(conversation_items)} conversation items")
            
            # Calculate today's Wordle number
            wordle_base_num = 1452  # Known Wordle number on a known date
            base_date = datetime.datetime(2024, 6, 5).date()  # Date of Wordle 1452
            today = datetime.datetime.now().date()
            days_since_base = (today - base_date).days
            today_wordle = wordle_base_num + days_since_base
            yesterday_wordle = today_wordle - 1
            
            # Also try to identify wordle numbers from conversations
            identified_nums = identify_wordle_numbers(conversation_items, 5)
            if identified_nums:
                logging.info(f"Dynamic Wordle number detection: Today likely #{max(identified_nums)}")
                
            logging.info(f"Calculated today's Wordle #{today_wordle} for date {today}")
            logging.info(f"Yesterday's Wordle was #{yesterday_wordle}")
            
            # Process each conversation item
            for i, convo in enumerate(conversation_items[:5]):  # Only check first 5 conversations
                try:
                    # Click on the conversation to view it
                    logging.info(f"Checking conversation {i+1}...")
                    convo.click()
                    time.sleep(2)
                    
                    # Get the phone number
                    phone_elements = driver.find_elements(By.CSS_SELECTOR, ".header-title span")
                    phone_number = "Unknown"
                    for elem in phone_elements:
                        if elem.text and ("(" in elem.text or "+" in elem.text):
                            phone_number = elem.text
                            break
                    
                    logging.info(f"Phone number: {phone_number}")
                    
                    # Get message contents
                    message_elements = driver.find_elements(By.CSS_SELECTOR, ".message-content-wrapper .message-content")
                    
                    # Debug output - show recent messages
                    found_wordle_scores = False
                    for idx, message in enumerate(message_elements[:10]):  # Look at 10 most recent messages
                        msg_text = message.text.strip()
                        logging.info(f"  Message {idx+1}: {msg_text[:100]}{'...' if len(msg_text) > 100 else ''}")
                        
                        # Check if this message contains a Wordle score
                        if "Wordle" in msg_text:
                            wordle_match = re.search(r'Wordle[^\d]*(\d+(?:,\d+)?)', msg_text)
                            score_match = re.search(r'(\d|X)/6', msg_text)
                            emoji_pattern = extract_emoji_pattern(msg_text)
                            
                            if wordle_match and score_match:
                                found_wordle_scores = True
                                wordle_num = wordle_match.group(1).replace(",", "")
                                score_val = parse_score(score_match.group(1))
                                
                                logging.info(f"  >>> FOUND WORDLE SCORE: #{wordle_num}, Score: {score_val}/6")
                                if emoji_pattern:
                                    logging.info(f"  >>> EMOJI PATTERN: {emoji_pattern}")
                    
                    if not found_wordle_scores:
                        logging.info("  No Wordle scores found in recent messages")
                    
                    # Go back to the conversation list
                    back_btn = driver.find_element(By.CSS_SELECTOR, ".gv-nav-tab-button[title='Messages']")
                    back_btn.click()
                    time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Error processing conversation {i+1}: {str(e)}")
                    # Try to go back to the conversation list
                    try:
                        back_btn = driver.find_element(By.CSS_SELECTOR, ".gv-nav-tab-button[title='Messages']")
                        back_btn.click()
                        time.sleep(1)
                    except:
                        pass
            
        except Exception as e:
            logging.error(f"Error during debug: {str(e)}")
        finally:
            if driver:
                driver.quit()
                
if __name__ == "__main__":
    debug_conversations()
except ImportError as e:
    logging.error(f"Could not import from integrated_auto_update_multi_league.py: {e}")
    logging.error("Make sure you're running this from the same directory as integrated_auto_update_multi_league.py")
    sys.exit(1)
