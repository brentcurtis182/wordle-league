#!/usr/bin/env python3
# Diagnostic script for Wordle score extraction
# Focused on checking if Malia and Evan's scores are visible in the DOM

import os
import sys
import time
import logging
import sqlite3
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("diagnostic_extraction.log"),
        logging.StreamHandler()
    ]
)

# League configuration
LEAGUES = [
    {
        "league_id": 1, 
        "name": "Wordle Warriorz",
        "is_default": True
    },
    {
        "league_id": 3, 
        "name": "Wordle PAL",
        "is_default": False
    }
]

# Player phone mappings - simplified for diagnostic purposes
PLAYER_PHONES = {
    # League 1 (Wordle Warriorz)
    1: {
        "3109263555": "Brent",
        "7603341190": "Evan",
        "3105009312": "Joanna",
        "5713458086": "Malia",
        "8474205309": "Nanna"
    },
    # League 3 (PAL)
    3: {
        "8587359353": "Vox",
        "4698345364": "Fuzwuz",
        "7325678900": "Pants",
        "4129876543": "Starslider"
    }
}

def kill_chrome_processes():
    """Kill any running Chrome processes"""
    logging.info("Attempting to kill any running Chrome processes")
    try:
        # For Windows
        import subprocess
        subprocess.run(["taskkill", "/f", "/im", "chrome.exe"], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE)
        logging.info("Chrome processes terminated")
    except Exception as e:
        logging.error(f"Error killing Chrome processes: {e}")
    
    # Wait a moment for processes to fully terminate
    time.sleep(2)

def setup_driver():
    """Set up the Chrome driver with appropriate options"""
    logging.info("Setting up Chrome driver")
    try:
        # Kill any existing Chrome processes first
        kill_chrome_processes()
        
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
        
        return driver
    except Exception as e:
        logging.error(f"Error setting up Chrome driver: {e}")
        return None

def navigate_to_google_voice(driver):
    """Navigate to Google Voice and verify successful navigation"""
    try:
        # Navigate to Google Voice
        logging.info("Navigating to Google Voice...")
        driver.get("https://voice.google.com/messages")
        
        # Wait for the page to load
        time.sleep(5)
        
        # Take a screenshot to verify navigation
        driver.save_screenshot("google_voice_navigation.png")
        logging.info("Saved screenshot of Google Voice navigation")
        
        # Verify we're on the Google Voice page
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
    """Find conversation threads for a specific league
    
    Args:
        driver: Selenium WebDriver instance
        league_id: League ID to find conversations for
        
    Returns:
        list: List of conversation thread elements or None if not found
    """
    try:
        # Wait for threads to appear
        logging.info(f"Looking for conversation threads for league {league_id}")
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list gv-thread-item"))
        )
        
        # Get all thread items
        conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list gv-thread-item")
        logging.info(f"Found {len(conversation_items)} conversation threads")
        
        if len(conversation_items) == 0:
            logging.warning("No conversation threads found")
            return None
        
        # If we're looking for Wordle Warriorz league (league_id 1)
        if league_id == 1:
            # Look for the thread with multiple participants
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
                            logging.info(f"Thread {i+1} appears to be the Wordle Warriorz league")
                            return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for Warriorz: {e}")
            
        # If we're looking for PAL league (league_id 3)
        elif league_id == 3:
            # Look for the PAL thread
            for i, item in enumerate(conversation_items):
                try:
                    # Check if this has the PAL participants
                    annotations = item.find_elements(By.CSS_SELECTOR, "gv-annotation.participants")
                    
                    if annotations:
                        annotation_text = annotations[0].text
                        logging.info(f"Thread {i+1} participants: {annotation_text}")
                        
                        # PAL league: (858) 735-9353, (469) 834-5364, etc.
                        if "(858)" in annotation_text or "(469)" in annotation_text:
                            logging.info(f"Thread {i+1} appears to be the Wordle PAL league")
                            return [item]  # Return as a list for consistent handling
                except Exception as e:
                    logging.error(f"Error checking thread {i+1} for PAL: {e}")
        
        # If we reach here, we didn't find the right thread for the requested league
        logging.warning(f"Could not find thread for league {league_id}")
        
        # As a fallback, return all threads if we can't specifically identify the right one
        logging.info("Returning all threads as a fallback")
        return conversation_items
        
    except Exception as e:
        logging.error(f"Error finding conversation threads: {e}")
        return None

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

def scroll_up_in_thread(driver):
    """Scroll up in the conversation thread to load all messages"""
    try:
        logging.info("Scrolling up in conversation thread to load messages")
        
        # Find the conversation container
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        )
        
        # Try several scroll methods to ensure all messages are loaded
        # Method 1: Fast scroll to the top multiple times
        for _ in range(5):
            driver.execute_script("document.querySelector(\"div[role='main']\").scrollTop = 0")
            time.sleep(1)
        
        # Method 2: Slower incremental scrolling
        scroll_height = driver.execute_script("return document.querySelector(\"div[role='main']\").scrollHeight")
        position = scroll_height
        
        while position > 0:
            position -= 500
            driver.execute_script(f"document.querySelector(\"div[role='main']\").scrollTop = {position}")
            time.sleep(0.5)
        
        # Method 3: Final scroll to the top to ensure we're at the beginning
        driver.execute_script("document.querySelector(\"div[role='main']\").scrollTop = 0")
        time.sleep(2)
        
        logging.info("Completed scrolling in thread")
        
        # Take a screenshot to verify scrolling
        driver.save_screenshot("after_scrolling.png")
        
    except Exception as e:
        logging.error(f"Error during conversation scrolling: {e}")
        # Fallback: try a simple scroll if the container approach failed
        try:
            # Simple page scroll
            driver.execute_script("window.scrollTo(0, 0)")
            time.sleep(2)
        except Exception as scroll_error:
            logging.error(f"Fallback scrolling also failed: {scroll_error}")

def extract_scores_from_hidden_elements(driver, target_wordle_nums, league_id=1):
    """Extract Wordle scores from .cdk-visually-hidden elements
    
    Args:
        driver: Selenium WebDriver instance
        target_wordle_nums: List of Wordle numbers to look for
        league_id: League ID for player mapping
        
    Returns:
        list: List of extracted scores with player names, scores, etc.
    """
    try:
        logging.info(f"Looking for hidden elements containing Wordle scores for league {league_id}")
        
        # Create a directory for diagnostics if it doesn't exist
        os.makedirs("dom_captures", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join("dom_captures", f"hidden_elements_{league_id}_{timestamp}.txt")
        
        # Find all visually hidden elements
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements")
        
        # Regex pattern to match Wordle scores
        pattern = re.compile(r'Wordle (\d+) (\d|X)/6')
        
        # Storage for extracted scores
        extracted_scores = []
        
        # Keep track of seen scores to avoid duplicates
        seen_scores = set()
        
        # Count of Wordle elements found for logging
        wordle_found = 0
        
        # Process all hidden elements and save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Found {len(hidden_elements)} hidden elements at {timestamp}\n\n")
            
            # Wordle number checking
            wordle_nums_str = ", ".join(map(str, target_wordle_nums))
            f.write(f"Looking for Wordle numbers: {wordle_nums_str}\n\n")
            
            # Process each element
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.get_attribute("textContent")
                    f.write(f"Element {i+1}: {text}\n")
                    
                    # Check if this contains a Wordle score
                    match = pattern.search(text)
                    if match:
                        wordle_num = int(match.group(1))
                        score_str = match.group(2)
                        
                        # Only process target Wordle numbers
                        if wordle_num in target_wordle_nums:
                            # Log that we found a relevant score
                            f.write(f"FOUND WORDLE {wordle_num} SCORE: {text}\n")
                            logging.info(f"FOUND WORDLE {wordle_num} SCORE: {text}")
                            wordle_found += 1
                            
                            # Extract phone number to identify the player
                            phone_pattern = re.compile(r'(\d{3}\s?\d{3}\s?\d{4})')
                            phone_match = phone_pattern.search(text)
                            
                            if phone_match:
                                raw_phone = phone_match.group(1)
                                # Clean the phone number
                                digits = ''.join(c for c in raw_phone if c.isdigit())
                                
                                # Look up player by phone
                                player = PLAYER_PHONES.get(league_id, {}).get(digits)
                                
                                if player:
                                    # Extract emoji pattern if available
                                    emoji_pattern = None
                                    if '⬛' in text or '🟨' in text or '🟩' in text:
                                        # Crude emoji pattern extraction - just get the part with emojis
                                        parts = text.split('⬛')
                                        if len(parts) > 1:
                                            emoji_text = '⬛' + '⬛'.join(parts[1:])
                                            # Clean up the pattern
                                            emoji_pattern = emoji_text[:emoji_text.find('\n') if '\n' in emoji_text else len(emoji_text)]
                                    
                                    # Convert score to integer
                                    score = 7 if score_str == 'X' else int(score_str)
                                    
                                    # Create score entry
                                    score_entry = {
                                        'player': player,
                                        'wordle_num': wordle_num,
                                        'score': score,
                                        'emoji_pattern': emoji_pattern,
                                        'phone': digits,
                                        'league_id': league_id,
                                        'raw_text': text
                                    }
                                    
                                    # Create a unique key to avoid duplicates
                                    score_key = f"{player}_{wordle_num}_{league_id}"
                                    
                                    if score_key not in seen_scores:
                                        extracted_scores.append(score_entry)
                                        seen_scores.add(score_key)
                                        f.write(f"  -> Mapped to player: {player}, Score: {score}/6\n")
                                else:
                                    f.write(f"  -> Could not map phone {digits} to player in league {league_id}\n")
                            else:
                                f.write("  -> No phone number found in this element\n")
                except Exception as e:
                    f.write(f"Error getting text for element {i+1}: {e}\n")
            
            f.write(f"\nSummary: Found {wordle_found} elements containing Wordle scores")
            f.write(f"\nExtracted {len(extracted_scores)} unique scores")
            
            # Special section to check for Malia and Evan
            f.write("\n\n== SPECIAL CHECK FOR MALIA AND EVAN ==\n")
            malia_scores = [s for s in extracted_scores if s['player'] == 'Malia']
            evan_scores = [s for s in extracted_scores if s['player'] == 'Evan']
            
            f.write(f"Found {len(malia_scores)} scores for Malia:\n")
            for score in malia_scores:
                f.write(f"  Wordle {score['wordle_num']}: {score['score']}/6\n")
                
            f.write(f"\nFound {len(evan_scores)} scores for Evan:\n")
            for score in evan_scores:
                f.write(f"  Wordle {score['wordle_num']}: {score['score']}/6\n")
        
        logging.info(f"Captured {len(hidden_elements)} hidden elements with {wordle_found} Wordle scores to {filepath}")
        logging.info(f"Extracted {len(extracted_scores)} unique scores")
        
        # Log special info about Malia and Evan
        logging.info(f"Found {len([s for s in extracted_scores if s['player'] == 'Malia'])} scores for Malia")
        logging.info(f"Found {len([s for s in extracted_scores if s['player'] == 'Evan'])} scores for Evan")
        
        return extracted_scores
    except Exception as e:
        logging.error(f"Error extracting scores from hidden elements: {e}")
        return []

def get_scores_from_database(player_names, wordle_nums, league_id=1):
    """Get existing scores for players and Wordle numbers from the database
    
    Args:
        player_names: List of player names to check
        wordle_nums: List of Wordle numbers to check
        league_id: League ID to check
        
    Returns:
        dict: Dictionary mapping player_name -> wordle_num -> score
    """
    conn = None
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Convert lists to comma-separated strings for the SQL query
        players_str = ", ".join(f"'{player}'" for player in player_names)
        wordles_str = ", ".join(map(str, wordle_nums))
        
        query = f"""
        SELECT player_name, wordle_num, score, emoji_pattern FROM scores 
        WHERE player_name IN ({players_str}) 
        AND wordle_num IN ({wordles_str})
        AND league_id = {league_id}
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Create a dictionary mapping player -> wordle_num -> score
        scores_dict = {}
        for player_name, wordle_num, score, emoji_pattern in rows:
            if player_name not in scores_dict:
                scores_dict[player_name] = {}
            scores_dict[player_name][wordle_num] = {"score": score, "emoji_pattern": emoji_pattern}
        
        return scores_dict
    except Exception as e:
        logging.error(f"Error getting scores from database: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def save_score_to_db(player, wordle_num, score, emoji_pattern=None, league_id=1):
    """Save a score to the database
    
    Args:
        player: Player name
        wordle_num: Wordle number
        score: Score (1-6 or 7 for X)
        emoji_pattern: Emoji pattern from the game
        league_id: League ID
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Check if this score already exists
        cursor.execute("""
        SELECT score, emoji_pattern FROM scores 
        WHERE player_name = ? AND wordle_num = ? AND league_id = ?
        """, (player, wordle_num, league_id))
        
        existing_score = cursor.fetchone()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if existing_score is None:
            # New score
            cursor.execute("""
            INSERT INTO scores (player_name, wordle_num, score, emoji_pattern, timestamp, score_date, league_id) 
            VALUES (?, ?, ?, ?, ?, date('now'), ?)
            """, (player, wordle_num, score, emoji_pattern, now, league_id))
            conn.commit()
            logging.info(f"Saved new score for {player}, Wordle {wordle_num}, League {league_id}: {score}/6")
            return True
        else:
            # Score exists - update if different
            db_score = existing_score[0]
            db_pattern = existing_score[1]
            
            if db_score != score or (emoji_pattern and db_pattern != emoji_pattern):
                cursor.execute("""
                UPDATE scores SET score = ?, emoji_pattern = ?, timestamp = ? 
                WHERE player_name = ? AND wordle_num = ? AND league_id = ?
                """, (score, emoji_pattern, now, player, wordle_num, league_id))
                conn.commit()
                logging.info(f"Updated score for {player}, Wordle {wordle_num}, League {league_id}: {score}/6")
                return True
            else:
                logging.info(f"Score for {player}, Wordle {wordle_num}, League {league_id} already exists: {score}/6")
                return False
    except Exception as e:
        logging.error(f"Error saving score to database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def extract_and_check_scores():
    """Main function to extract scores and check if Malia and Evan's scores are present"""
    today_wordle = get_todays_wordle_number()
    yesterday_wordle = get_yesterdays_wordle_number()
    target_wordles = [today_wordle, yesterday_wordle]
    
    logging.info(f"Looking for scores for Wordle numbers: {target_wordles}")
    
    # First check what's already in the database
    logging.info("Checking existing scores in database")
    db_scores = get_scores_from_database(
        ["Malia", "Evan"], 
        target_wordles, 
        league_id=1
    )
    
    for player in ["Malia", "Evan"]:
        logging.info(f"Database scores for {player}:")
        if player in db_scores:
            for wordle_num in target_wordles:
                if wordle_num in db_scores[player]:
                    score_info = db_scores[player][wordle_num]
                    logging.info(f"  Wordle {wordle_num}: {score_info['score']}/6")
                else:
                    logging.info(f"  Wordle {wordle_num}: Not found")
        else:
            logging.info(f"  No scores found for {player}")
    
    # Now extract scores from Google Voice
    driver = setup_driver()
    if not driver:
        logging.error("Failed to set up Chrome driver")
        return False
    
    try:
        # Navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return False
        
        # Only focus on the main league (Wordle Warriorz)
        league_id = 1
        league_name = "Wordle Warriorz"
        
        # Find conversation threads for this league
        logging.info(f"Looking for conversation threads for {league_name}")
        conversation_items = find_conversation_threads(driver, league_id)
        
        if not conversation_items:
            logging.error(f"No conversation threads found for {league_name}")
            return False
        
        # Process the first thread (should be the main league thread)
        thread = conversation_items[0]
        logging.info(f"Processing thread for {league_name}")
        
        # Click on the thread to open it
        try:
            thread.click()
            time.sleep(3)  # Wait for thread to load
            logging.info("Clicked on thread")
        except Exception as e:
            logging.error(f"Error clicking on thread: {e}")
            return False
        
        # Take screenshot of the thread
        driver.save_screenshot(f"thread_{league_id}.png")
        
        # Scroll up in the thread to load all messages
        scroll_up_in_thread(driver)
        
        # Extract scores from hidden elements
        scores = extract_scores_from_hidden_elements(driver, target_wordles, league_id)
        
        # Count scores for Malia and Evan
        malia_scores = [s for s in scores if s['player'] == 'Malia']
        evan_scores = [s for s in scores if s['player'] == 'Evan']
        
        logging.info(f"Extracted {len(malia_scores)} scores for Malia")
        for score in malia_scores:
            logging.info(f"  Wordle {score['wordle_num']}: {score['score']}/6")
            # Save to database
            save_score_to_db(
                player=score['player'],
                wordle_num=score['wordle_num'],
                score=score['score'],
                emoji_pattern=score['emoji_pattern'],
                league_id=score['league_id']
            )
        
        logging.info(f"Extracted {len(evan_scores)} scores for Evan")
        for score in evan_scores:
            logging.info(f"  Wordle {score['wordle_num']}: {score['score']}/6")
            # Save to database
            save_score_to_db(
                player=score['player'],
                wordle_num=score['wordle_num'],
                score=score['score'],
                emoji_pattern=score['emoji_pattern'],
                league_id=score['league_id']
            )
        
        # Check what's now in the database after extraction
        updated_db_scores = get_scores_from_database(
            ["Malia", "Evan"], 
            target_wordles, 
            league_id=1
        )
        
        logging.info("\nUpdated database scores:")
        for player in ["Malia", "Evan"]:
            logging.info(f"Database scores for {player}:")
            if player in updated_db_scores:
                for wordle_num in target_wordles:
                    if wordle_num in updated_db_scores[player]:
                        score_info = updated_db_scores[player][wordle_num]
                        logging.info(f"  Wordle {wordle_num}: {score_info['score']}/6")
                    else:
                        logging.info(f"  Wordle {wordle_num}: Not found")
            else:
                logging.info(f"  No scores found for {player}")
        
        return True
    except Exception as e:
        logging.error(f"Error extracting scores: {e}")
        return False
    finally:
        if driver:
            driver.quit()
            logging.info("Browser closed")

if __name__ == "__main__":
    logging.info("Starting diagnostic score extraction")
    success = extract_and_check_scores()
    if success:
        logging.info("Diagnostic extraction completed successfully")
    else:
        logging.error("Diagnostic extraction failed")
    print("Using database at: wordle_league.db")
