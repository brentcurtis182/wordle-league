import os
import sys
import time
import logging
import subprocess
import sqlite3
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Import enhanced functions
from enhanced_functions import update_website, push_to_github

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integrated_auto_update.log"),
        logging.StreamHandler()
    ]
)

def kill_chrome_processes():
    """Kill any running Chrome processes"""
    logging.info("Attempting to kill any running Chrome processes")
    try:
        # For Windows
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        logging.info("Chrome processes terminated")
    except Exception as e:
        logging.error(f"Error killing Chrome processes: {e}")
    
    # Wait a moment for processes to fully terminate
    time.sleep(2)

def get_todays_wordle_number():
    """Get today's Wordle number"""
    # Hardcoded for July 26, 2025
    return 1498

def get_yesterdays_wordle_number():
    """Get yesterday's Wordle number"""
    # Hardcoded for July 25, 2025
    return 1497

def extract_player_name_from_phone(phone_number):
    """Extract player name from phone number
    
    Args:
        phone_number: Phone number string to map to a player name
        
    Returns:
        str: Player name or None if not found
    """
    # Define a mapping of phone numbers to player names
    phone_to_name = {
        "(310) 926-3555": "Joanna",
        "(949) 230-4472": "Nanna",
        "(858) 735-9353": "Brent",
        "(760) 334-1190": "Malia",
        "(760) 846-2302": "Evan"
    }
    
    if phone_number in phone_to_name:
        return phone_to_name[phone_number]
    
    return None

def extract_player_name(conversation_text):
    """Extract player name from conversation"""
    logging.info("Extracting player name from conversation")
    
    # Define a mapping of phone numbers to player names
    phone_to_name = {
        "(310) 926-3555": "Joanna",
        "(949) 230-4472": "Nanna",
        "(858) 735-9353": "Brent",
        "(760) 334-1190": "Malia",
        "(760) 846-2302": "Evan"
    }
    
    # First try to find a phone number and map it to a name
    phone_pattern = re.compile(r'\(\d{3}\)\s*\d{3}-\d{4}')
    phone_matches = phone_pattern.findall(conversation_text)
    
    if phone_matches:
        phone = phone_matches[0]
        if phone in phone_to_name:
            player_name = phone_to_name[phone]
            logging.info(f"Mapped phone {phone} to player: {player_name}")
            return player_name
        else:
            logging.info(f"Found phone number but no mapping: {phone}")
            # If we find a phone but don't have a mapping, use a default name
            return "Unknown Player"
    
    # If no phone number found, try to extract from conversation text
    lines = conversation_text.split('\n')
    
    # Look for known player name patterns
    if lines and len(lines) > 0:
        # Try first few non-empty lines
        for i in range(min(5, len(lines))):
            if i >= len(lines) or not lines[i].strip():
                continue
                
            line = lines[i].strip()
            
            # Skip lines that are likely not names
            if "Wordle" in line or "http" in line or len(line) > 30:
                continue
                
            # Look for common name patterns
            # 1. Name followed by timestamp (common in message threads)
            name_time_match = re.match(r'^([\w\s]+)[,:]?\s+\d{1,2}:\d{2}', line)
            if name_time_match:
                potential_name = name_time_match.group(1).strip()
                if potential_name and len(potential_name) < 30:
                    logging.info(f"Extracted player name: {potential_name}")
                    return potential_name
                
            # 2. Name in a typical chat format
            chat_match = re.match(r'^([\w\s]+)[:]', line)
            if chat_match:
                potential_name = chat_match.group(1).strip()
                if potential_name and len(potential_name) < 30:
                    logging.info(f"Extracted player name: {potential_name}")
                    return potential_name
    
    # Default name if we couldn't determine
    logging.info("Could not extract player name, using default: Unknown Player")
    return "Unknown Player"

def extract_wordle_scores():
    """Extract Wordle scores from Google Voice"""
    logging.info("Starting Wordle score extraction")
    
    # Kill any running Chrome processes
    kill_chrome_processes()
    
    # Set up Chrome profile directory
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    logging.info(f"Using Chrome profile at: {profile_dir}")
    
    if not os.path.exists(profile_dir):
        logging.error(f"Profile directory does not exist: {profile_dir}")
        return False
    
    try:
        # Set up Chrome options - EXACTLY as in the simplified script that worked
        chrome_options = Options()
        chrome_options.add_argument(f"user-data-dir={profile_dir}")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Create Chrome driver
        logging.info("Creating Chrome driver")
        driver = webdriver.Chrome(options=chrome_options)
        
        # Navigate to Google Voice
        url = "https://voice.google.com/messages"
        logging.info(f"Navigating to Google Voice: {url}")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(10)
        
        # Take screenshot
        screenshot_path = os.path.join(os.getcwd(), "google_voice_navigation.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot saved to: {screenshot_path}")
        
        # Get current URL
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        # Check if we're on Google Voice
        if "voice.google.com" in current_url:
            logging.info("Successfully navigated to Google Voice")
            
            # Look for conversation list items with more robust detection
            try:
                logging.info("Looking for conversation list items")
                
                # Take a screenshot before looking for elements
                driver.save_screenshot("before_conversation_search.png")
                logging.info("Screenshot saved before conversation search")
                
                # Try different selectors to find conversation items
                selectors_to_try = [
                    "gv-annotation.participants",
                    "gv-conversation-list-item",
                    "div:has(gv-annotation.participants)",
                    ".participants",
                    "[role='listitem']"
                ]
                
                conversation_items = []
                for selector in selectors_to_try:
                    try:
                        logging.info(f"Trying selector: {selector}")
                        items = driver.find_elements(By.CSS_SELECTOR, selector)
                        if items:
                            logging.info(f"Found {len(items)} items with selector: {selector}")
                            conversation_items = items
                            break
                    except Exception as e:
                        logging.warning(f"Error with selector {selector}: {e}")
                
                if conversation_items:
                    logging.info(f"Found {len(conversation_items)} conversation items")
                    
                    # Get today's and yesterday's Wordle numbers
                    today_wordle = get_todays_wordle_number()
                    yesterday_wordle = get_yesterdays_wordle_number()
                    logging.info(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
                    
                    # Extract scores from conversations
                    scores_extracted = extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle)
                    
                    # Close the browser
                    driver.quit()
                    
                    return scores_extracted > 0
                else:
                    logging.error("No conversation items found with any selector")
                    driver.quit()
                    return False
            except Exception as e:
                logging.error(f"Error finding conversation items: {e}")
                driver.quit()
                return False
        else:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {current_url}")
            driver.quit()
            return False
    except Exception as e:
        logging.error(f"Error in extract_wordle_scores: {e}")
        try:
            driver.quit()
        except:
            pass
        return False

def extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle):
    """Extract Wordle scores from conversations
    
    Args:
        driver: Selenium WebDriver instance
        conversation_items: List of conversation elements to process
        today_wordle: Today's Wordle number
        yesterday_wordle: Yesterday's Wordle number
        
    Returns:
        int: Number of new scores extracted
    """
    logging.info(f"Processing {len(conversation_items)} conversations")
    
    scores_extracted = 0
    today_scores = []
    
    # Function to save score to database
    def save_score_to_db(player, wordle_num, score):
        """Save score to database
        
        Returns:
            str: Status code - 'new_score_added', 'duplicate_score', or 'error'
        """
        logging.info(f"Saving score: Player={player}, Wordle#{wordle_num}, Score={score}")
        
        try:
            # Connect to the database
            conn = sqlite3.connect('wordle_scores.db')
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY,
                wordle_num INTEGER,
                score INTEGER,
                player_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Check if this score already exists
            cursor.execute("SELECT id FROM scores WHERE wordle_num = ? AND player_name = ?", 
                          (wordle_num, player))
            existing = cursor.fetchone()
            
            if existing:
                logging.info(f"Score already exists for {player} on Wordle #{wordle_num}")
                conn.close()
                return 'duplicate_score'
            
            # Try to insert with player_name column
            try:
                cursor.execute("INSERT INTO scores (wordle_num, score, player_name) VALUES (?, ?, ?)", 
                              (wordle_num, score, player))
                conn.commit()
                logging.info(f"Score saved successfully with player_name")
                conn.close()
                return 'new_score_added'
            except sqlite3.OperationalError as e:
                # If player_name column doesn't exist, try without it
                if "no such column: player_name" in str(e):
                    logging.warning("player_name column doesn't exist, trying without it")
                    try:
                        cursor.execute("INSERT INTO scores (wordle_num, score) VALUES (?, ?)", 
                                      (wordle_num, score))
                        conn.commit()
                        logging.info("Score saved successfully without player_name")
                        conn.close()
                        return 'new_score_added'
                    except Exception as inner_e:
                        logging.error(f"Error saving score without player_name: {inner_e}")
                        conn.close()
                        return 'error'
                else:
                    logging.error(f"Error saving score: {e}")
                    conn.close()
                    return 'error'
        except Exception as e:
            logging.error(f"Database error: {e}")
            return 'error'
    
    # Process each conversation
    for i, item in enumerate(conversation_items):
        try:
            logging.info(f"Processing conversation {i+1}/{len(conversation_items)}")
            
            # Click on the conversation item
            driver.execute_script("arguments[0].click();", item)
            time.sleep(2)
            
            # Get conversation text
            try:
                conversation_container = driver.find_element(By.CSS_SELECTOR, "gv-message-list")
                conversation_html = conversation_container.get_attribute('innerHTML')
                
                # Save conversation HTML for debugging
                with open(f"conversation_{i+1}.html", "w", encoding="utf-8") as f:
                    f.write(conversation_html)
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(conversation_html, 'html.parser')
                conversation_text = soup.get_text()
                
                # Save extracted text for debugging
                with open(f"conversation_{i+1}.txt", "w", encoding="utf-8") as f:
                    f.write(conversation_text)
                
                # Extract player name from conversation
                player_name = extract_player_name(conversation_text)
                
                # Look for Wordle scores in the conversation text
                wordle_pattern = re.compile(r'Wordle\s+(\d+)\s+(\d+)/6')
                wordle_matches = wordle_pattern.findall(conversation_text)
                
                # Also look for failed attempts (X/6)
                failed_pattern = re.compile(r'Wordle\s+(\d+)\s+X/6')
                failed_matches = failed_pattern.findall(conversation_text)
                
                # Process regular scores
                for wordle_match in wordle_matches:
                    wordle_num = int(wordle_match[0])
                    score = int(wordle_match[1])
                    
                    # Only process today's or yesterday's scores
                    if wordle_num == today_wordle or wordle_num == yesterday_wordle:
                        logging.info(f"Found score: Wordle #{wordle_num}, Score: {score}/6, Player: {player_name}")
                        
                        # Save score to database
                        result = save_score_to_db(player_name, wordle_num, score)
                        
                        if result == 'new_score_added':
                            scores_extracted += 1
                            if wordle_num == today_wordle:
                                today_scores.append(f"{player_name}: {score}/6")
                
                # Process failed attempts (X/6) - we'll store these as score=7
                for failed_match in failed_matches:
                    wordle_num = int(failed_match)
                    score = 7  # Use 7 to represent X/6 (failed attempt)
                    
                    # Only process today's or yesterday's scores
                    if wordle_num == today_wordle or wordle_num == yesterday_wordle:
                        logging.info(f"Found failed attempt: Wordle #{wordle_num}, Score: X/6, Player: {player_name}")
                        
                        # Save score to database
                        result = save_score_to_db(player_name, wordle_num, score)
                        
                        if result == 'new_score_added':
                            scores_extracted += 1
                            if wordle_num == today_wordle:
                                today_scores.append(f"{player_name}: X/6")
                
                # Add annotations to the saved text file
                with open(f"conversation_{i+1}_annotated.txt", "w", encoding="utf-8") as f:
                    f.write(f"Player Name: {player_name}\n\n")
                    f.write(f"Regular Matches: {wordle_matches}\n")
                    f.write(f"Failed Matches: {failed_matches}\n\n")
                    f.write(conversation_text)
                
            except Exception as e:
                logging.error(f"Error extracting conversation text: {e}")
            
            # Go back to the conversation list
            try:
                back_button = driver.find_element(By.CSS_SELECTOR, "button[aria-label='Back']")
                driver.execute_script("arguments[0].click();", back_button)
                time.sleep(1)
            except Exception as e:
                logging.warning(f"Error clicking back button: {e}")
                # Try to navigate back to the main page
                driver.get("https://voice.google.com/messages")
                time.sleep(3)
                
        except Exception as e:
            logging.error(f"Error processing conversation {i+1}: {e}")
    
    # Log summary
    logging.info(f"Extracted {scores_extracted} new scores")
    if today_scores:
        logging.info(f"Today's scores: {today_scores}")
    
    return scores_extracted > 0

def check_for_daily_reset(force_reset=False):
    """Check if we need to reset the latest scores for a new day"""
    logging.info("Checking if daily reset is needed")
    
    try:
        # Get today's date
        today = datetime.now().date()
        
        # Check if we have a last update timestamp file
        last_update_file = "last_update_date.txt"
        last_update_date = None
        
        if os.path.exists(last_update_file):
            with open(last_update_file, "r") as f:
                last_update_str = f.read().strip()
                try:
                    last_update_date = datetime.strptime(last_update_str, "%Y-%m-%d").date()
                except:
                    logging.error(f"Could not parse last update date: {last_update_str}")
        
        current_hour = datetime.now().hour
        
        # Check if we've already done a reset today
        reset_already_done_today = (last_update_date is not None and last_update_date == today)
        
        # Reset is needed if:
        # 1. We have no last update date, OR
        # 2. It's a new day AND it's after 3 AM, OR
        # 3. Force reset is requested AND it's after 3 AM AND we haven't already reset today
        reset_needed = (last_update_date is None or 
                       (today > last_update_date and current_hour >= 3) or 
                       (force_reset and current_hour >= 3 and not reset_already_done_today))
        
        if reset_needed:
            logging.info(f"Daily reset needed. Today: {today}, Last update: {last_update_date}, Force: {force_reset}, Hour: {current_hour}, Already done today: {reset_already_done_today}")
            
            # Update the last update file
            with open(last_update_file, "w") as f:
                f.write(today.strftime("%Y-%m-%d"))
            
            return True
        else:
            logging.info(f"No daily reset needed. Today: {today}, Last update: {last_update_date}")
            return False
    except Exception as e:
        logging.error(f"Error checking for daily reset: {e}")
        return False

def main():
    logging.info("Starting integrated auto update")
    
    # Step 1: Extract scores
    extraction_success = extract_wordle_scores()
    
    # Check if we need to do a daily reset even if no scores were found
    # Only force a reset if it's after 3:00 AM or if we're specifically updating today's scores
    current_hour = datetime.now().hour
    force_today_update = True  # We always want to update today's scores
    
    # Only force a full reset if it's a new day (after 3:00 AM)
    force_full_reset = current_hour >= 3
    
    daily_reset_needed = check_for_daily_reset(force_reset=force_full_reset)
    
    # Always update the website for today's scores, regardless of extraction success
    # This ensures today's scores are always displayed on the website
    logging.info(f"Updating website. Extraction success: {extraction_success}, Daily reset: {daily_reset_needed}, Force today update: {force_today_update}")
    website_success = update_website()
    
    if website_success:
        # Step 3: Push to GitHub
        push_success = push_to_github()
        
        if push_success:
            logging.info("Auto update completed successfully")
        else:
            logging.error("Auto update failed at GitHub push step")
    else:
        logging.error("Auto update failed at website update step")

if __name__ == "__main__":
    main()
