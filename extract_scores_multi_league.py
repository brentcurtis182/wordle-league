#!/usr/bin/env python3
"""
Multi-League Wordle Score Extraction
This script extends the existing extraction functionality to support multiple leagues
while maintaining full compatibility with the current system.
"""

import json
import sqlite3
import logging
import sys
import os
import time
from datetime import datetime
import re

# Import the functions from integrated_auto_update.py
# This ensures we're using the exact same extraction code
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_auto_update import (
    get_todays_wordle_number,
    extract_wordle_scores,
    extract_player_name_from_phone,
    kill_chrome_processes
)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv

# Define database path
WORDLE_DATABASE = 'wordle_league.db'

# Set up logging
log_file = 'extract_multi_league.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Load environment variables
load_dotenv()

def setup_webdriver():
    """Set up and configure the Chrome WebDriver"""
    logging.info("Setting up Chrome WebDriver")
    
    try:
        # Kill any existing Chrome processes
        kill_chrome_processes()
        
        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create and return the driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.maximize_window()
        
        return driver
    except Exception as e:
        logging.error(f"Error setting up WebDriver: {e}")
        return None
        
def login_to_google_voice(driver):
    """Log in to Google Voice"""
    logging.info("Logging in to Google Voice")
    
    try:
        # Navigate to Google Voice
        driver.get("https://voice.google.com")
        time.sleep(3)
        
        # Check if we need to log in
        current_url = driver.current_url
        if "accounts.google.com" in current_url:
            logging.info("Login page detected")
            
            # Get credentials from environment variables
            email = os.getenv("GOOGLE_EMAIL")
            password = os.getenv("GOOGLE_PASSWORD")
            
            if not email or not password:
                logging.error("Missing Google credentials in environment variables")
                return False
                
            # Enter email
            try:
                email_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "identifierId"))
                )
                email_field.send_keys(email)
                next_button = driver.find_element(By.ID, "identifierNext")
                next_button.click()
                time.sleep(3)
                
                # Enter password
                password_field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "Passwd"))
                )
                password_field.send_keys(password)
                next_button = driver.find_element(By.ID, "passwordNext")
                next_button.click()
                time.sleep(5)
                
                # Wait for Google Voice to load
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'gvConversation')]"))
                )
                
            except Exception as e:
                logging.error(f"Error during login: {e}")
                return False
                
        # Check if we're successfully logged in
        if "voice.google.com" in driver.current_url:
            logging.info("Successfully logged in to Google Voice")
            return True
        else:
            logging.error(f"Failed to log in. Current URL: {driver.current_url}")
            return False
            
    except Exception as e:
        logging.error(f"Error in login_to_google_voice: {e}")
        return False

def get_league_config():
    """Load league configuration from JSON file"""
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found")
        return None
        
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return None

def get_player_by_phone_for_league(phone_number, league_id):
    """Get player name by phone number for a specific league, using CSV files directly"""
    try:
        # Clean phone number to standard format without special characters
        cleaned_phone = re.sub(r'[^0-9]', '', phone_number)
        if not cleaned_phone:
            logging.warning(f"Invalid phone number format: {phone_number}")
            return None
            
        # CSV file mapping based on league_id
        csv_files = {
            1: 'familyPlayers.csv',              # Wordle Warriorz
            2: 'familyPlayers - wordleGang.csv', # Wordle Gang
            3: 'familyPlayers - wordlePal.csv'   # PAL League
        }
        
        # Check if we have a CSV file for this league
        if league_id in csv_files:
            csv_path = csv_files[league_id]
            league_name = "Wordle Warriorz" if league_id == 1 else "Wordle Gang" if league_id == 2 else "PAL League"
            
            # Check if CSV file exists
            if not os.path.exists(csv_path):
                logging.warning(f"CSV file not found for {league_name}: {csv_path}")
            else:
                # Try to find player in the CSV file
                try:
                    import csv
                    with open(csv_path, 'r') as f:
                        reader = csv.reader(f)
                        next(reader)  # Skip header row
                        
                        for row in reader:
                            if len(row) >= 2:
                                player_name = row[0].strip()
                                csv_phone = row[1].strip()
                                
                                # Clean CSV phone number for comparison
                                csv_phone_clean = re.sub(r'[^0-9]', '', csv_phone)
                                
                                # Check for match
                                if cleaned_phone == csv_phone_clean:
                                    logging.info(f"Found player {player_name} for phone {cleaned_phone} in {league_name} CSV mapping")
                                    return player_name
                except Exception as csv_error:
                    logging.error(f"Error reading CSV file {csv_path}: {csv_error}")
        
        # HARDCODED MAPPINGS AS FALLBACK
        # These are taken directly from the CSV files we analyzed
        # League 1: Wordle Warriorz
        warriorz_mapping = {
            '18587359353': 'Brent',
            '17603341190': 'Malia',
            '17608462302': 'Evan',       # THIS IS EVAN'S CORRECT NUMBER!
            '13109263555': 'Joanna',
            '19492304472': 'Nanna'
        }
        
        # League 2: Wordle Gang
        gang_mapping = {
            '18587359353': 'Brent',
            '13102004244': 'Ana',
            '17148228341': 'Kaylie',
            '13109263555': 'Joanna',
            '17148030122': 'Keith',
            '13107953164': 'Rochelle',
            '13102661718': 'Will'
        }
        
        # League 3: PAL League
        pal_mapping = {
            '18587359353': 'Vox',
            '17604206113': 'Fuzwuz',
            '17605830059': 'Pants',
            '14698345364': 'Starslider'
        }
        
        # Select mapping based on league
        if league_id == 1 and cleaned_phone in warriorz_mapping:
            player_name = warriorz_mapping[cleaned_phone]
            logging.info(f"Found player {player_name} for phone {cleaned_phone} in hardcoded Warriorz mapping")
            return player_name
        elif league_id == 2 and cleaned_phone in gang_mapping:
            player_name = gang_mapping[cleaned_phone]
            logging.info(f"Found player {player_name} for phone {cleaned_phone} in hardcoded Gang mapping")
            return player_name
        elif league_id == 3 and cleaned_phone in pal_mapping:
            player_name = pal_mapping[cleaned_phone]
            logging.info(f"Found player {player_name} for phone {cleaned_phone} in hardcoded PAL mapping")
            return player_name
            
        # If we get here, fall back to database lookup
        conn = None
        try:
            conn = sqlite3.connect(WORDLE_DATABASE)
            cursor = conn.cursor()
            
            # Try to find player in the specified league
            cursor.execute("""
            SELECT name FROM players 
            WHERE phone_number = ? AND league_id = ?
            """, (phone_number, league_id))
            
            player = cursor.fetchone()
            
            if player:
                logging.warning(f"Player {player[0]} for phone {phone_number} found in database but not in CSV for league {league_id}")
                return player[0]
                
            # If not found, fallback to original lookup method for compatibility
            cursor.execute("SELECT name FROM players WHERE phone_number = ?", (phone_number,))
            player = cursor.fetchone()
            
            if player:
                logging.warning(f"Player {player[0]} ({phone_number}) found in default players table but not in league {league_id}")
                return player[0]
                
            return None
            
        except Exception as e:
            logging.error(f"Error finding player by phone in database: {e}")
            return None
        finally:
            if conn:
                conn.close()
                
    except Exception as e:
        logging.error(f"Error in get_player_by_phone_for_league: {e}")
        return None

def save_score_to_db_with_league(player, wordle_num, score, emoji_pattern=None, league_id=1):
    """Extended version of save_score_to_db that includes league_id"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # First check if score exists in scores table for this league
        cursor.execute("""
        SELECT wordle_num, score, emoji_pattern FROM scores 
        WHERE phone_number = ? AND wordle_num = ? AND league_id = ?
        """, (player, wordle_num, league_id))
        
        existing = cursor.fetchone()
        
        # Current date for consistent date field
        today = datetime.now().strftime("%Y-%m-%d")
        
        if existing:
            # Score exists, update if needed
            if existing[1] != score or (emoji_pattern and existing[2] != emoji_pattern):
                # Only update emoji if provided and different
                if emoji_pattern:
                    cursor.execute("""
                    UPDATE scores SET score = ?, emoji_pattern = ?, date = ?
                    WHERE phone_number = ? AND wordle_num = ? AND league_id = ?
                    """, (score, emoji_pattern, today, player, wordle_num, league_id))
                else:
                    cursor.execute("""
                    UPDATE scores SET score = ?, date = ?
                    WHERE phone_number = ? AND wordle_num = ? AND league_id = ?
                    """, (score, today, player, wordle_num, league_id))
                logging.info(f"Updated score for {player}, Wordle {wordle_num} in league {league_id}: {score}")
        else:
            # New score
            cursor.execute("""
            INSERT INTO scores (phone_number, wordle_num, score, date, emoji_pattern, league_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (player, wordle_num, score, today, emoji_pattern, league_id))
            logging.info(f"Inserted new score for {player}, Wordle {wordle_num} in league {league_id}: {score}")
            
        # Now handle the score table for website display
        cursor.execute("""
        SELECT score FROM score 
        WHERE player = ? AND wordle_num = ? AND league_id = ?
        """, (player, wordle_num, league_id))
        
        exists_in_score = cursor.fetchone() is not None
        
        if exists_in_score:
            # Update existing score in score table
            if emoji_pattern:
                cursor.execute("""
                UPDATE score SET score = ?, emoji_pattern = ?, date = ?
                WHERE player = ? AND wordle_num = ? AND league_id = ?
                """, (score, emoji_pattern, today, player, wordle_num, league_id))
            else:
                cursor.execute("""
                UPDATE score SET score = ?, date = ?
                WHERE player = ? AND wordle_num = ? AND league_id = ?
                """, (score, today, player, wordle_num, league_id))
        else:
            # Insert new score in score table
            cursor.execute("""
            INSERT INTO score (player, wordle_num, score, date, emoji_pattern, league_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (player, wordle_num, score, today, emoji_pattern, league_id))
            
        conn.commit()
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error saving score to database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def extract_for_league(league_id, thread_id, driver):
    """Extract scores for a specific league thread"""
    logging.info(f"Extracting scores for league {league_id} (thread: {thread_id})")
    
    # Navigate to this specific thread
    try:
        # Go to specific conversation if thread_id is a URL
        if thread_id.startswith('http'):
            driver.get(thread_id)
        else:
            # Otherwise search for the thread by name/number
            # This uses the existing search functionality in Google Voice
            search_box = driver.find_element_by_name('q')
            search_box.clear()
            search_box.send_keys(thread_id)
            time.sleep(2)
            
            # Click the first search result
            results = driver.find_elements_by_css_selector('.gvConversation')
            if results:
                results[0].click()
            else:
                logging.error(f"No conversation found for thread: {thread_id}")
                return False
                
        time.sleep(3)  # Wait for conversation to load
        
        # Use the existing extraction function but with our league-specific player lookup
        today_wordle = get_todays_wordle_number()
        yesterday_wordle = today_wordle - 1
        
        # Define a custom player lookup function for this league
        def league_player_lookup(phone):
            return get_player_by_phone_for_league(phone, league_id)
        
        # Use existing extraction function with our custom player lookup
        scores = extract_wordle_scores(driver, player_lookup_func=league_player_lookup)
        
        # Process and save scores with league_id
        for phone, entry in scores.items():
            player_name = get_player_by_phone_for_league(phone, league_id)
            if player_name and entry.get('wordle_num') and entry.get('score'):
                wordle_num = entry['wordle_num']
                score = entry['score']
                emoji_pattern = entry.get('emoji_pattern')
                
                save_score_to_db_with_league(
                    phone, wordle_num, score, 
                    emoji_pattern=emoji_pattern,
                    league_id=league_id
                )
        
        return True
        
    except Exception as e:
        logging.error(f"Error extracting scores for league {league_id}: {e}")
        return False

def main():
    """Main function to extract scores for all leagues"""
    logging.info("Starting multi-league score extraction")
    
    # Load league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return False
        
    # Set up webdriver
    driver = None
    try:
        driver = setup_webdriver()
        
        # Log in to Google Voice once
        if not login_to_google_voice(driver):
            logging.error("Failed to log in to Google Voice")
            return False
            
        time.sleep(5)  # Wait after login
        
        # Process each league
        for league in config['leagues']:
            league_id = league['league_id']
            thread_id = league['thread_id']
            
            if league.get('is_default', False):
                logging.info(f"Processing default league: {league['name']} (ID: {league_id})")
            else:
                # Only process enabled leagues
                if not league.get('enabled', True):
                    logging.info(f"Skipping disabled league: {league['name']} (ID: {league_id})")
                    continue
                    
                logging.info(f"Processing league: {league['name']} (ID: {league_id})")
            
            extract_for_league(league_id, thread_id, driver)
            
        logging.info("Multi-league extraction completed")
        return True
        
    except Exception as e:
        logging.error(f"Error in multi-league extraction: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
