import sys
import os
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re
import sqlite3
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def setup_chrome_driver(use_profile=True):
    """Set up Chrome WebDriver with appropriate options"""
    options = Options()
    if use_profile:
        # Use existing Chrome profile to avoid login
        profile_dir = os.path.join(os.getcwd(), "automation_profile")
        options.add_argument(f"user-data-dir={profile_dir}")
    
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-notifications")
    options.add_argument("--mute-audio")
    
    # Initialize Chrome driver
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

def navigate_to_google_voice(driver):
    """Navigate to Google Voice website"""
    try:
        driver.get("https://voice.google.com/messages")
        logging.info("Navigated to Google Voice messages")
        
        # Take screenshot for verification
        driver.save_screenshot("google_voice_navigation.png")
        logging.info("Saved screenshot to google_voice_navigation.png")
        
        # Wait for messages to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
        )
        logging.info("Google Voice conversation list loaded")
        return True
    except TimeoutException:
        logging.error("Timeout while loading Google Voice website")
        return False
    except Exception as e:
        logging.error(f"Error navigating to Google Voice: {e}")
        return False

def find_conversation_threads(driver, league_id):
    """Find relevant conversation threads for the specified league"""
    try:
        # Wait for conversation items to be loaded
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-annotation.participants"))
        )
        
        # Get all conversation elements
        conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list-item")
        logging.info(f"Found {len(conversation_items)} conversation items total")
        
        # Filter conversations by league
        league_conversations = []
        
        # Different phone number patterns for different leagues
        league_phone_patterns = {
            1: ["3109263555", "7603341190"],  # Main league
            2: ["7143387893"],                # Gang league
            3: ["8587359353", "4698345364"]   # PAL league
        }
        
        patterns = league_phone_patterns.get(league_id, [])
        if not patterns:
            logging.error(f"No phone patterns defined for league {league_id}")
            return []
            
        for item in conversation_items:
            try:
                participants = item.find_element(By.CSS_SELECTOR, "gv-annotation.participants")
                text = participants.text
                
                if any(pattern in text.replace(" ", "") for pattern in patterns):
                    league_conversations.append(item)
            except NoSuchElementException:
                continue
            except Exception as e:
                logging.error(f"Error checking conversation item: {e}")
        
        logging.info(f"Found {len(league_conversations)} conversations for league {league_id}")
        return league_conversations
    except Exception as e:
        logging.error(f"Error finding conversation threads: {e}")
        return []

def calculate_today_wordle():
    """Calculate today's Wordle number based on the start date"""
    # Wordle started at Wordle #0 on June 19, 2021
    start_date = datetime(2021, 6, 19).date()
    today = datetime.now().date()
    delta = (today - start_date).days
    return delta

def extract_dom_elements(driver, league_id=1):
    """Extract DOM elements with Wordle scores and show them directly"""
    # Calculate today's Wordle number
    today_wordle = calculate_today_wordle()
    logging.info(f"Today's Wordle number should be: {today_wordle}")
    
    # Find relevant conversation threads
    conversation_items = find_conversation_threads(driver, league_id)
    if not conversation_items:
        logging.warning(f"No conversation threads found for league {league_id}")
        return False
    
    found_elements = []
    
    # Process each conversation
    for i, conversation in enumerate(conversation_items):
        try:
            # Click on conversation to load messages
            conversation.click()
            logging.info(f"Clicked on conversation {i+1}")
            
            # Wait for message thread to load
            time.sleep(3)
            
            # Try to find hidden elements containing message text
            hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
            logging.info(f"Found {len(hidden_elements)} hidden elements in conversation {i+1}")
            
            # Extract text from hidden elements
            for element in hidden_elements:
                try:
                    # Try to get text from element
                    text = element.text
                    
                    # Skip empty text
                    if not text or len(text) < 10:  # Minimum meaningful length
                        continue
                        
                    # Skip reaction messages
                    reaction_patterns = ['Loved', 'Liked', 'Laughed at', 'Emphasized', 'Reacted to']
                    if any(pattern in text for pattern in reaction_patterns):
                        continue
                        
                    # Check for Wordle pattern
                    wordle_match = re.search(r'Wordle\s+([0-9,]+)\s+([1-6]|X)/6', text)
                    if wordle_match:
                        # Extract Wordle number and score
                        wordle_num_str = wordle_match.group(1).replace(',', '')
                        try:
                            wordle_num = int(wordle_num_str)
                            
                            # Only include scores from the last few days
                            if wordle_num >= today_wordle - 5:
                                found_elements.append({
                                    'text': text,
                                    'wordle_num': wordle_num,
                                    'league_id': league_id
                                })
                                logging.info(f"Found Wordle {wordle_num} score in league {league_id}")
                        except ValueError:
                            pass
                except Exception as e:
                    logging.error(f"Error processing hidden element: {e}")
            
        except Exception as e:
            logging.error(f"Error processing conversation {i+1}: {e}")
    
    # Display the found elements
    print("\n" + "="*80)
    print(f"DOM ELEMENTS FOUND FOR LEAGUE {league_id}")
    print("="*80)
    
    for i, element in enumerate(found_elements):
        print(f"\nElement {i+1}:")
        print("-" * 40)
        print(f"League ID: {element['league_id']}")
        print(f"Wordle Number: {element['wordle_num']}")
        print(f"Text Content:")
        print(element['text'])
        print("-" * 40)
    
    return len(found_elements) > 0

def main():
    # Set up Chrome driver
    driver = setup_chrome_driver(use_profile=True)
    
    try:
        # Navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return
        
        # Process leagues
        leagues = [1, 3]  # Main league and PAL league
        
        for league_id in leagues:
            logging.info(f"Processing league ID: {league_id}")
            
            # Extract DOM elements for current league
            extracted = extract_dom_elements(driver, league_id)
            
            if not extracted:
                logging.warning(f"No elements extracted for league {league_id}")
        
    except Exception as e:
        logging.error(f"Error in main process: {e}")
    finally:
        # Clean up
        driver.quit()
        logging.info("Browser closed")

if __name__ == "__main__":
    main()
