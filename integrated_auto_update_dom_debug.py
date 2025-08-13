#!/usr/bin/env python3
"""
Modified version of integrated_auto_update_multi_league.py
that outputs DOM elements during extraction.

This script DOES NOT change any core functionality - it just adds
debug output for the DOM elements found during extraction.
"""

import os
import re
import time
import sqlite3
import logging
import json
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Create a file handler for DOM elements
dom_logger = logging.getLogger('dom_elements')
dom_handler = logging.FileHandler('dom_elements.log', mode='w')
dom_handler.setLevel(logging.INFO)
dom_handler.setFormatter(logging.Formatter('%(message)s'))
dom_logger.addHandler(dom_handler)
dom_logger.setLevel(logging.INFO)

# Additionally create an HTML log file for DOM elements
html_log = open('dom_elements.html', 'w', encoding='utf-8')
html_log.write('''<!DOCTYPE html>
<html>
<head>
    <title>DOM Elements - Wordle Score Extraction Debug</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .element { border: 1px solid #ccc; padding: 10px; margin: 10px 0; }
        .wordle-num { font-weight: bold; color: blue; }
        .player { font-weight: bold; }
        .score { color: green; font-weight: bold; }
        .emoji { font-family: monospace; white-space: pre; }
        pre { background-color: #f5f5f5; padding: 10px; overflow-x: auto; }
        .match { background-color: #ffffcc; }
        .today { background-color: #ccffcc; }
    </style>
</head>
<body>
    <h1>Wordle Score DOM Elements Debug</h1>
    <p>Extraction time: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
''')

# League configuration 
LEAGUES = [
    {
        "league_id": 1, 
        "name": "Wordle Warriorz",
        "is_default": True
    },
    {
        "league_id": 2, 
        "name": "Wordle Gang",
        "is_default": False
    },
    {
        "league_id": 3, 
        "name": "Wordle PAL",
        "is_default": False
    }
]

# Database connection string
DATABASE_FILE = os.environ.get("DATABASE_FILE", "wordle_league.db")

def get_db_connection():
    """Get a connection to the SQLite database"""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

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
    # Wordle #1 was released on June 19, 2021
    wordle_start_date = datetime(2021, 6, 19).date()
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    # Calculate days between start date and yesterday
    days_since_start = (yesterday - wordle_start_date).days
    
    # Wordle number is days since start + 1
    wordle_number = days_since_start + 1
    logging.info(f"Calculated yesterday's Wordle #{wordle_number} for date {yesterday}")
    
    return wordle_number

def extract_player_name_from_phone(phone_number, league_id=1):
    """Extract player name from phone number for a specific league"""
    # Main league mappings
    if league_id == 1:
        phone_to_name = {
            "13109263555": "Brent",
            "17603341190": "Evan",
            "17147338207": "Joanna",
            "17147255943": "Malia",
            "18058954944": "Nanna"
        }
    # Gang league mappings
    elif league_id == 2:
        phone_to_name = {
            "17143387893": "Adam",
            "13233773684": "Ali",
            "17147556163": "Charlie",
            "17147747680": "Dan",
            "19495733317": "Kaleb",
            "13106253768": "Laura",
            "17144705551": "Tommy"
        }
    # PAL league mappings
    elif league_id == 3:
        phone_to_name = {
            "18587359353": "Vox",
            "14698345364": "Fuzwuz",
            "16197729672": "Pants",
            "17604206113": "Starslider"
        }
    else:
        return None
        
    # Clean and format phone number
    clean_phone = phone_number.replace(" ", "").replace("+", "")
    if len(clean_phone) == 10:  # Add country code if missing
        clean_phone = "1" + clean_phone
        
    return phone_to_name.get(clean_phone)

def scroll_up_in_thread(driver, wordle_num):
    """Scroll up in the conversation thread to load all messages"""
    try:
        # Find the scrollable element
        scroll_element = driver.find_element(By.CSS_SELECTOR, "gv-message-list")
        
        # Initial scroll position
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_element)
        
        # Attempt fast scroll to top first
        for _ in range(5):
            driver.execute_script("arguments[0].scrollTop = 0", scroll_element)
            time.sleep(1)
        
        # Then do gradual scrolling if needed
        for _ in range(10):
            # Scroll to top
            driver.execute_script("arguments[0].scrollTo(0, 0)", scroll_element)
            time.sleep(1)
            
            # Check if we've reached the top or found yesterday's Wordle
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_element)
            
            # Check for target Wordle pattern
            page_source = driver.page_source
            wordle_pattern = f"Wordle {wordle_num}"
            if wordle_pattern in page_source:
                logging.info(f"Found target {wordle_pattern} in thread, stopping scroll")
                break
                
            if new_height == last_height:
                # No more messages loaded, break the loop
                logging.info("No more messages loading, reached top of conversation")
                break
                
            last_height = new_height
            
        logging.info("Finished scrolling through conversation")
        return True
    except Exception as e:
        logging.error(f"Error scrolling conversation: {e}")
        return False

def save_score_to_db(player, wordle_num, score, emoji_pattern=None, league_id=1):
    """Save Wordle score to database"""
    try:
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if score for this player and wordle number already exists
        cursor.execute(
            "SELECT id FROM scores WHERE player = ? AND wordle_num = ? AND league_id = ?",
            (player, wordle_num, league_id)
        )
        existing_score = cursor.fetchone()
        
        if existing_score:
            # Update existing score
            cursor.execute(
                """UPDATE scores 
                   SET score = ?, emoji_pattern = ?, updated_at = ? 
                   WHERE player = ? AND wordle_num = ? AND league_id = ?""",
                (score, emoji_pattern, timestamp, player, wordle_num, league_id)
            )
            result = "updated"
        else:
            # Insert new score
            cursor.execute(
                """INSERT INTO scores 
                   (player, wordle_num, score, emoji_pattern, timestamp, league_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (player, wordle_num, score, emoji_pattern, timestamp, league_id)
            )
            result = "inserted"
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        return f"Score {result} for {player}, Wordle #{wordle_num}, League #{league_id}"
        
    except Exception as e:
        logging.error(f"Error saving score to database: {e}")
        return f"Error: {str(e)}"

def setup_driver():
    """Set up Chrome WebDriver with appropriate options"""
    try:
        options = Options()
        
        # Use existing Chrome profile to avoid login
        profile_dir = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_dir):
            options.add_argument(f"user-data-dir={profile_dir}")
            logging.info(f"Using Chrome profile: {profile_dir}")
        else:
            logging.warning(f"Chrome profile directory not found: {profile_dir}")
            
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--mute-audio")
        
        # Initialize and return Chrome driver
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        logging.info("Chrome driver initialized successfully")
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {e}")
        return None

def navigate_to_google_voice(driver):
    """Navigate to Google Voice website"""
    try:
        driver.get("https://voice.google.com/messages")
        logging.info("Navigated to Google Voice messages")
        
        # Wait for conversation list to load
        WebDriverWait(driver, 45).until(
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

def extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle, league_id=1):
    """Extract Wordle scores from conversations"""
    scores_found = 0
    total_elements_found = 0
    
    # Write league header to HTML log
    html_log.write(f'''
    <h2>League ID: {league_id}</h2>
    <p>Today's Wordle: <span class="wordle-num">#{today_wordle}</span>, Yesterday's: <span class="wordle-num">#{yesterday_wordle}</span></p>
''')
    
    for i, conversation in enumerate(conversation_items):
        try:
            # Click on conversation to load messages
            driver.execute_script("arguments[0].click();", conversation)
            logging.info(f"Clicked on conversation {i+1} for league {league_id}")
            
            # Wait for message thread to load
            time.sleep(3)
            
            # Scroll up in thread to load more messages
            scroll_up_in_thread(driver, yesterday_wordle)
            
            # Find hidden elements containing message text
            hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
            total_elements_found += len(hidden_elements)
            logging.info(f"Found {len(hidden_elements)} hidden elements in conversation {i+1}")
            
            # Write to HTML log
            html_log.write(f'''
    <div class="element">
        <h3>Conversation {i+1} - {len(hidden_elements)} Hidden Elements</h3>
''')
            
            # Regular expressions for extracting Wordle scores
            wordle_pattern = re.compile(r'Wordle\s+([0-9,]+)\s+([1-6]|X)/6')
            
            # Process each hidden element
            for j, element in enumerate(hidden_elements):
                try:
                    # Get text content
                    text = element.get_attribute("textContent") or element.text
                    
                    # Skip empty or very short texts
                    if not text or len(text) < 10:
                        continue
                    
                    # Skip reaction messages
                    reaction_patterns = ['Loved', 'Liked', 'Laughed at', 'Emphasized', 'Reacted to']
                    if any(pattern in text for pattern in reaction_patterns):
                        continue
                    
                    # Add to HTML log
                    css_class = ""
                    
                    # Check if this element might have Wordle content
                    if "Wordle" in text:
                        match = wordle_pattern.search(text)
                        if match:
                            # Extract Wordle number and score
                            wordle_num_str = match.group(1).replace(',', '')
                            try:
                                wordle_num = int(wordle_num_str)
                                score_text = match.group(2)
                                
                                # Add highlighting based on Wordle number
                                if wordle_num == today_wordle:
                                    css_class = "today"
                                    # Log this specifically for today's wordle
                                    logging.info(f"!!! FOUND TODAY'S WORDLE #{today_wordle} !!!")
                                    logging.info(f"Text: {text}")
                                elif wordle_num >= yesterday_wordle:
                                    css_class = "match"
                                    
                            except ValueError:
                                pass
                    
                    # Write element to HTML log with appropriate highlighting
                    html_log.write(f'''
        <div class="element {css_class}">
            <h4>Element {j+1}</h4>
            <pre>{text}</pre>
        </div>
''')
                    
                    # Try to extract phone number
                    phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                    element_phone = None
                    if phone_match:
                        element_phone = phone_match.group(1) + phone_match.group(2) + phone_match.group(3)
                        if len(element_phone) == 10:
                            element_phone = "1" + element_phone
                    
                    # Look for Wordle pattern
                    match = wordle_pattern.search(text)
                    if match:
                        # Extract Wordle number and score
                        try:
                            wordle_num_str = match.group(1).replace(',', '')
                            wordle_num = int(wordle_num_str)
                            score_text = match.group(2)
                            score = 7 if score_text == 'X' else int(score_text)
                            
                            # Only process recent Wordle scores
                            if wordle_num >= today_wordle - 5:
                                # Determine player name
                                player_name = None
                                if element_phone:
                                    player_name = extract_player_name_from_phone(element_phone, league_id)
                                
                                if player_name:
                                    # Extract emoji pattern
                                    emoji_pattern = None
                                    if '\u2b1b' in text or '\u2b1c' in text or '\ud83d\udfe8' in text or '\ud83d\udfe9' in text:
                                        pattern_lines = []
                                        for line in text.split('\n'):
                                            if any(emoji in line for emoji in ['\u2b1b', '\u2b1c', '\ud83d\udfe8', '\ud83d\udfe9']):
                                                pattern_lines.append(line.strip())
                                        
                                        if pattern_lines:
                                            emoji_pattern = '\n'.join(pattern_lines)
                                    
                                    # Log score found
                                    logging.info(f"Found Wordle score - Player: {player_name}, Wordle #{wordle_num}, Score: {score_text}/6")
                                    
                                    # Save score to database
                                    save_result = save_score_to_db(player_name, wordle_num, score, emoji_pattern, league_id)
                                    logging.info(save_result)
                                    scores_found += 1
                                    
                                    # Add special logging for today's and yesterday's scores
                                    if wordle_num == today_wordle:
                                        dom_logger.info(f"\n{'='*60}\nTODAY'S WORDLE #{today_wordle} FOUND!\n{'='*60}")
                                        dom_logger.info(f"Player: {player_name}")
                                        dom_logger.info(f"Score: {score_text}/6")
                                        if emoji_pattern:
                                            dom_logger.info(f"Emoji Pattern:\n{emoji_pattern}")
                                        dom_logger.info(f"{'='*60}")
                                    elif wordle_num == yesterday_wordle:
                                        dom_logger.info(f"\nYesterday's Wordle #{yesterday_wordle} found for {player_name}: {score_text}/6")
                                        if emoji_pattern:
                                            dom_logger.info(f"Emoji Pattern:\n{emoji_pattern}")
                        except ValueError:
                            continue
                        
                except Exception as e:
                    logging.error(f"Error processing hidden element {j+1}: {e}")
            
            # Close the conversation element in HTML log
            html_log.write("</div>")
            
            # Go back to conversation list for next conversation
            try:
                back_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "gv-icon-button[icon-name='arrow_back']"))
                )
                back_button.click()
                time.sleep(2)  # Wait for conversation list to reload
            except Exception as e:
                logging.error(f"Error navigating back to conversation list: {e}")
                # Try to navigate back manually
                driver.get("https://voice.google.com/messages")
                time.sleep(3)
                
        except Exception as e:
            logging.error(f"Error processing conversation {i+1}: {e}")
            # Try to get back to the messages list
            driver.get("https://voice.google.com/messages")
            time.sleep(3)
    
    logging.info(f"Finished processing {len(conversation_items)} conversations for league {league_id}")
    logging.info(f"Found {scores_found} scores to save for league {league_id}")
    logging.info(f"Processed {total_elements_found} total DOM elements")
    
    html_log.write(f'''
    <div style="margin: 20px; padding: 10px; border: 2px solid #333; background-color: #f0f0f0;">
        <h3>Summary for League {league_id}</h3>
        <p>Processed {len(conversation_items)} conversations</p>
        <p>Found {scores_found} scores to save</p>
        <p>Processed {total_elements_found} total DOM elements</p>
    </div>
''')
    
    return scores_found

def extract_wordle_scores_multi_league():
    """Extract Wordle scores for multiple leagues"""
    # Calculate today's and yesterday's Wordle numbers
    today_wordle = get_todays_wordle_number()
    yesterday_wordle = get_yesterdays_wordle_number()
    
    # Set up Chrome driver
    driver = setup_driver()
    if not driver:
        logging.error("Failed to set up Chrome driver")
        return False
    
    try:
        # Navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return False
        
        # Process each league
        for league_config in LEAGUES:
            league_id = league_config["league_id"]
            league_name = league_config["name"]
            
            logging.info(f"Processing league: {league_name} (ID: {league_id})")
            dom_logger.info(f"\n{'='*60}\nProcessing league: {league_name} (ID: {league_id})\n{'='*60}")
            
            # Find conversation threads for this league
            conversation_items = find_conversation_threads(driver, league_id)
            if not conversation_items:
                logging.warning(f"No conversation threads found for league {league_id}")
                continue
                
            # Extract scores from conversations
            extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle, league_id)
        
        return True
    except Exception as e:
        logging.error(f"Error extracting Wordle scores: {e}")
        return False
    finally:
        # Clean up
        driver.quit()
        logging.info("Browser closed")
        html_log.write("</body></html>")
        html_log.close()
        logging.info("DOM elements log closed")

# Main entry point
if __name__ == "__main__":
    print("Using database at:", DATABASE_FILE)
    
    # Extract Wordle scores
    dom_logger.info(f"Starting DOM element extraction at {datetime.now()}")
    dom_logger.info(f"Today's Wordle: #{get_todays_wordle_number()}")
    dom_logger.info(f"Yesterday's Wordle: #{get_yesterdays_wordle_number()}")
    dom_logger.info("-" * 60)
    
    extract_wordle_scores_multi_league()
    
    print("\nExtraction completed. DOM elements saved to dom_elements.log and dom_elements.html")
