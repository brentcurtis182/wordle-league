import os
import sys
import time
import logging
import sqlite3
import re
import inspect
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("emergency_extraction.log")
    ]
)

# League configurations (simplified for emergency extraction)
LEAGUES = [
    {"league_id": 1, "name": "Wordle Warriorz"},
    {"league_id": 3, "name": "Wordle PAL"}
]

def kill_chrome_processes():
    """Kill any existing Chrome processes"""
    try:
        logging.info("Attempting to kill any running Chrome processes")
        os.system("taskkill /f /im chrome.exe 2>nul")
        time.sleep(0.1)  # Brief pause
        logging.info("Chrome processes terminated")
    except:
        pass

def setup_driver():
    """Set up Chrome driver with profile"""
    logging.info("Setting up Chrome driver")
    try:
        # Kill any existing Chrome processes
        kill_chrome_processes()
        
        # Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use existing profile to avoid login
        profile_path = os.path.join(os.getcwd(), "automation_profile")
        if os.path.exists(profile_path):
            chrome_options.add_argument(f"user-data-dir={profile_path}")
            logging.info(f"Using existing Chrome profile at {profile_path}")
        else:
            logging.warning(f"Chrome profile not found at {profile_path}")
            
        # Initialize driver
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {e}")
        return None

def navigate_to_google_voice(driver):
    """Navigate to Google Voice"""
    try:
        logging.info("Navigating to Google Voice...")
        driver.get("https://voice.google.com/messages")
        
        # Take a screenshot
        time.sleep(5)
        driver.save_screenshot("emergency_google_voice_nav.png")
        logging.info("Saved screenshot of Google Voice navigation")
        
        # Verify navigation
        if "voice.google.com" in driver.current_url:
            logging.info("Successfully navigated to Google Voice")
            return True
        else:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {driver.current_url}")
            return False
    except Exception as e:
        logging.error(f"Error navigating to Google Voice: {e}")
        return False

def find_conversation_threads(driver, league_id=1):
    """Find conversation threads for a specific league"""
    try:
        # Wait for threads to appear (with increased timeout)
        logging.info(f"Looking for conversation threads for league {league_id}")
        
        # Take screenshot before looking for threads
        driver.save_screenshot(f"before_threads_league_{league_id}.png")
        
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item"))
        )
        
        # Get all thread items
        conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list gv-thread-item")
        logging.info(f"Found {len(conversation_items)} conversation threads")
        
        # Take another screenshot after finding threads
        driver.save_screenshot(f"after_threads_league_{league_id}.png")
        
        if len(conversation_items) == 0:
            logging.warning("No conversation threads found")
            return None
        
        # League-specific thread identification
        if league_id == 1:  # Wordle Warriorz
            for i, item in enumerate(conversation_items):
                try:
                    annotations = item.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                    
                    if annotations:
                        annotation_text = annotations[0].text
                        logging.info(f"Thread {i+1} participants: {annotation_text}")
                        
                        if "(310)" in annotation_text or "(760)" in annotation_text:
                            logging.info(f"Thread {i+1} appears to be the Wordle Warriorz league")
                            return [item]
                except Exception as e:
                    logging.error(f"Error checking thread {i+1}: {e}")
        
        elif league_id == 3:  # PAL
            for i, item in enumerate(conversation_items):
                try:
                    annotations = item.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                    
                    if annotations:
                        annotation_text = annotations[0].text
                        logging.info(f"Thread {i+1} participants: {annotation_text}")
                        
                        if "(858)" in annotation_text or "(469)" in annotation_text:
                            logging.info(f"Thread {i+1} appears to be the Wordle PAL league")
                            return [item]
                except Exception as e:
                    logging.error(f"Error checking thread {i+1}: {e}")
        
        # If we didn't find the specific thread, return all threads as fallback
        logging.info("Returning all threads as fallback")
        return conversation_items
        
    except Exception as e:
        logging.error(f"Error finding conversation threads: {e}")
        # Take screenshot on error
        driver.save_screenshot(f"error_finding_threads_league_{league_id}.png")
        return None

def get_todays_wordle_number():
    """Calculate today's Wordle number"""
    start_date = datetime(2021, 6, 19)
    today = datetime.now()
    delta = today - start_date
    wordle_number = delta.days + 1
    logging.info(f"Today's Wordle number: {wordle_number}")
    return wordle_number

def get_yesterdays_wordle_number():
    """Calculate yesterday's Wordle number"""
    start_date = datetime(2021, 6, 19)
    yesterday = datetime.now() - timedelta(days=1)
    delta = yesterday - start_date
    wordle_number = delta.days + 1
    logging.info(f"Yesterday's Wordle number: {wordle_number}")
    return wordle_number

def extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle, league_id):
    """Extract scores from conversation threads"""
    try:
        if not conversation_items:
            logging.warning("No conversation items to process")
            return
        
        wordle_numbers = [today_wordle, yesterday_wordle]
        logging.info(f"Looking for scores for Wordle numbers: {wordle_numbers}")
        
        for item in conversation_items:
            try:
                # Click on the conversation thread
                logging.info("Clicking on conversation thread")
                item.click()
                time.sleep(3)
                
                # Take screenshot after clicking thread
                driver.save_screenshot(f"thread_clicked_league_{league_id}.png")
                
                # Scroll to load all messages
                logging.info("Scrolling to load all messages")
                for _ in range(10):
                    # Scroll to top of messages
                    driver.execute_script("document.querySelector('gv-message-list').scrollTop = 0")
                    time.sleep(1)
                
                # Now extract scores from hidden elements (the reliable method)
                hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                logging.info(f"Found {len(hidden_elements)} hidden elements to analyze")
                
                # Save current DOM for debugging
                with open(f"dom_snapshot_league_{league_id}.html", "w", encoding="utf-8") as f:
                    f.write(driver.page_source)
                
                for element in hidden_elements:
                    text = element.get_attribute("textContent")
                    if text and "Wordle" in text:
                        logging.info(f"Found potential Wordle score: {text[:100]}")
                        
                        # Extract wordle number, score and phone number
                        wordle_match = re.search(r'Wordle (\d+) (\d|X)/6', text)
                        phone_match = re.search(r'\+1 \((\d{3})\) (\d{3})-(\d{4})', text)
                        
                        if wordle_match and phone_match:
                            wordle_num = int(wordle_match.group(1))
                            score_val = wordle_match.group(2)
                            phone = f"+1 ({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                            
                            # Convert score to integer (X becomes 7)
                            score_int = 7 if score_val == "X" else int(score_val)
                            
                            logging.info(f"Extracted: Wordle {wordle_num}, score {score_val}, phone {phone}")
                            
                            # Check if this is a relevant Wordle number
                            if wordle_num in wordle_numbers:
                                # Save score to database
                                save_score_to_db(wordle_num, score_int, phone, league_id)
                
                # Go back to thread list
                logging.info("Going back to thread list")
                back_button = driver.find_element(By.CSS_SELECTOR, "gv-icon-button[icon-name='arrow_back']")
                back_button.click()
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error processing thread: {e}")
                driver.save_screenshot(f"error_processing_thread_league_{league_id}.png")
                
                # Try to go back to thread list
                try:
                    back_button = driver.find_element(By.CSS_SELECTOR, "gv-icon-button[icon-name='arrow_back']")
                    back_button.click()
                    time.sleep(2)
                except:
                    logging.error("Could not go back to thread list")
                    # Try to navigate to Google Voice again
                    navigate_to_google_voice(driver)
                
    except Exception as e:
        logging.error(f"Error extracting scores: {e}")
        driver.save_screenshot(f"error_extracting_scores_league_{league_id}.png")

def get_player_name(phone_number, league_id):
    """Get player name from phone number"""
    # Warriorz phone mapping
    warriorz_phones = {
        "+1 (310) 926-3555": "Jordan",
        "+1 (760) 334-1190": "Jonah",
        "+1 (617) 792-6546": "Brent",
        "+1 (213) 700-1114": "Evan",
        "+1 (415) 710-9930": "Malia",
        "+1 (323) 243-8599": "Oliver"
    }
    
    # PAL phone mapping
    pal_phones = {
        "+1 (858) 735-9353": "Vox",
        "+1 (469) 834-5364": "Fuzwuz",
        "+1 (303) 249-4325": "Starslider",
        "+1 (254) 291-9143": "Pants"
    }
    
    if league_id == 1:
        return warriorz_phones.get(phone_number, "Unknown")
    elif league_id == 3:
        return pal_phones.get(phone_number, "Unknown")
    else:
        return "Unknown"

def save_score_to_db(wordle_number, score, phone_number, league_id):
    """Save score to database"""
    try:
        # Get player name based on phone number
        player_name = get_player_name(phone_number, league_id)
        
        # Skip unknown players
        if player_name == "Unknown":
            logging.warning(f"Unknown phone number: {phone_number}")
            return
            
        logging.info(f"Saving score for {player_name}: Wordle {wordle_number}, score {score}, league {league_id}")
        
        # Calculate score date
        wordle_start_date = datetime(2021, 6, 19)
        score_date = wordle_start_date + timedelta(days=wordle_number-1)
        date_str = score_date.strftime('%Y-%m-%d')
        
        # Connect to database
        db_path = os.path.join(os.getcwd(), "wordle_league.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First check if score already exists to avoid duplicates
        cursor.execute(
            "SELECT * FROM scores WHERE wordle_number = ? AND player = ? AND league_id = ?",
            (wordle_number, player_name, league_id)
        )
        existing_score = cursor.fetchone()
        
        if existing_score:
            logging.info(f"Score already exists for {player_name}, Wordle {wordle_number}, league {league_id}")
        else:
            # Insert into scores table (newer table)
            cursor.execute(
                "INSERT INTO scores (wordle_number, score, player, date, score_date, league_id) VALUES (?, ?, ?, ?, ?, ?)",
                (wordle_number, score, player_name, date_str, date_str, league_id)
            )
            
            # Also insert into score table (legacy table) for compatibility
            cursor.execute(
                "INSERT OR IGNORE INTO score (wordle_number, score, player, date, score_date) VALUES (?, ?, ?, ?, ?)",
                (wordle_number, score, player_name, date_str, date_str)
            )
            
            conn.commit()
            logging.info(f"Successfully saved score for {player_name}")
            
        conn.close()
        
    except Exception as e:
        logging.error(f"Error saving score to database: {e}")

def emergency_extract():
    """Main emergency extraction function"""
    logging.info("EMERGENCY EXTRACTION: Starting")
    
    # Calculate Wordle numbers
    today_wordle = get_todays_wordle_number()
    yesterday_wordle = get_yesterdays_wordle_number()
    
    # Set up driver
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
            
            logging.info(f"EMERGENCY EXTRACTION: Processing league {league_name} (ID: {league_id})")
            
            # Find conversation threads
            conversation_items = find_conversation_threads(driver, league_id)
            if not conversation_items:
                logging.warning(f"No conversation threads found for league {league_id}")
                continue
                
            # Extract scores
            extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle, league_id)
        
        logging.info("EMERGENCY EXTRACTION: Completed successfully")
        return True
        
    except Exception as e:
        logging.error(f"EMERGENCY EXTRACTION ERROR: {e}")
        driver.save_screenshot("emergency_extraction_error.png")
        return False
        
    finally:
        # Clean up
        driver.quit()
        logging.info("Browser closed")

if __name__ == "__main__":
    print("Using database at:", os.path.join(os.getcwd(), "wordle_league.db"))
    emergency_extract()
    
    # Optionally sync database tables
    try:
        print("Synchronizing database tables...")
        # Removed sync_database_tables call
        print("Synchronization complete")
    except Exception as e:
        print(f"Error synchronizing database tables: {e}")
