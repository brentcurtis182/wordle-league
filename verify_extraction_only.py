import os
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
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_todays_wordle_number():
    """Calculate today's Wordle number"""
    wordle_base_num = 1452  # Known Wordle number on a known date
    base_date = datetime.datetime(2024, 6, 5).date()  # Date of Wordle 1452
    today = datetime.datetime.now().date()
    days_since_base = (today - base_date).days
    return wordle_base_num + days_since_base

def get_yesterdays_wordle_number():
    """Calculate yesterday's Wordle number"""
    return get_todays_wordle_number() - 1

def setup_chrome_driver():
    """Set up and return a Chrome WebDriver instance"""
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("detach", True)
    
    service = Service()
    return webdriver.Chrome(service=service, options=options)

def login_to_google_voice(driver):
    """Login to Google Voice using the credentials in environment variables"""
    # Wait for email input
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        email_input = driver.find_element(By.CSS_SELECTOR, "input[type='email']")
        email_input.clear()
        email_input.send_keys(os.environ.get('GOOGLE_VOICE_EMAIL', 'wordlewarriorz@gmail.com'))
        driver.find_element(By.CSS_SELECTOR, "#identifierNext").click()
        
        # Wait for password input
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))
        )
        time.sleep(2)  # Wait a moment for animation
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_input.clear()
        password_input.send_keys(os.environ.get('GOOGLE_VOICE_PASSWORD', 'wordle4life!'))
        driver.find_element(By.CSS_SELECTOR, "#passwordNext").click()
        
        # Wait for redirect to Google Voice
        WebDriverWait(driver, 30).until(
            EC.url_contains("voice.google.com")
        )
        return True
    except Exception as e:
        logging.error(f"Login error: {e}")
        return False

def find_conversation_items(driver):
    """Find conversation items in Google Voice"""
    # Try different selectors to find conversation items
    selectors_to_try = [
        "div[role='button'].container",
        "div.container[tabindex='0']",
        "div.container.active",
        "div.thread-details",
        "gv-annotation.participants",
        "gv-conversation-list-item",
        "div:has(gv-annotation.participants)",
        ".participants",
        "[role='listitem']",
        "[role='button']"
    ]
    
    for selector in selectors_to_try:
        try:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            if items:
                logging.info(f"Found {len(items)} items with selector: {selector}")
                return items
        except Exception as e:
            logging.warning(f"Error with selector {selector}: {e}")
    
    return []

def extract_emoji_pattern(text):
    """Extract emoji pattern from text"""
    emoji_pattern_regex = re.compile(r'((?:[⬛⬜🟨🟩]{5}[\s\n]*){1,6})', re.MULTILINE)
    emoji_matches = re.findall(emoji_pattern_regex, text)
    
    valid_emoji_matches = []
    if emoji_matches:
        for match in emoji_matches:
            # Clean up the pattern
            rows = [row for row in re.findall(r'[⬛⬜🟨🟩]{5}', match) if row]
            if rows:
                clean_pattern = '\n'.join(rows)
                valid_emoji_matches.append(clean_pattern)
    
    if valid_emoji_matches:
        return max(valid_emoji_matches, key=lambda p: p.count('\n') + 1)
    return None

def parse_score(score_text):
    """Parse score value from text"""
    if score_text == 'X':
        return 'X'
    try:
        return int(score_text)
    except:
        return None

def get_phone_to_player_mapping():
    """Get mapping of phone numbers to player names"""
    # Default mapping
    phone_to_player = {
        # Wordle Warriors (League 1)
        '(303) 641-0737': 'Brent',
        '(404) 713-9042': 'Evan', 
        '(303) 817-7113': 'Joanna',
        '(303) 842-7514': 'Malia',
        '(303) 956-0959': 'Nanna',
        
        # PAL League (League 3)
        '(520) 309-6475': 'Vox',
        '(908) 745-1063': 'Fuzwuz',
        '(908) 745-1064': 'Starslider'
    }
    return phone_to_player

def get_player_league_mapping():
    """Get mapping of player names to league IDs"""
    # Default mapping
    player_to_league = {
        'Brent': 1,
        'Evan': 1,
        'Joanna': 1,
        'Malia': 1,
        'Nanna': 1,
        'Vox': 3,
        'Fuzwuz': 3,
        'Pants': 3,
        'Starslider': 3
    }
    return player_to_league

def main():
    """Main function to check extraction"""
    driver = None
    try:
        logging.info("Starting Google Voice extraction check")
        
        # Set up Chrome driver
        driver = setup_chrome_driver()
        
        # Navigate to Google Voice
        driver.get("https://voice.google.com/")
        logging.info("Navigating to Google Voice")
        
        # Login if needed
        if "accounts.google.com" in driver.current_url:
            logging.info("Login page detected, attempting login")
            if not login_to_google_voice(driver):
                logging.error("Failed to login")
                driver.quit()
                return
        
        # Wait for Google Voice to load
        time.sleep(5)
        
        # Check the current URL
        current_url = driver.current_url
        if "voice.google.com" in current_url:
            logging.info("Successfully navigated to Google Voice")
            
            # Find conversation items
            conversation_items = find_conversation_items(driver)
            if not conversation_items:
                logging.error("No conversation items found")
                driver.quit()
                return
            
            # Get phone to player mapping
            phone_to_player = get_phone_to_player_mapping()
            player_to_league = get_player_league_mapping()
            
            # Calculate Wordle numbers
            today_wordle = get_todays_wordle_number()
            yesterday_wordle = get_yesterdays_wordle_number()
            logging.info(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
            
            # Connect to the database to check for existing scores
            conn = sqlite3.connect('wordle_league.db')
            cursor = conn.cursor()
            
            # Get existing scores for today and yesterday
            cursor.execute("SELECT player_name, wordle_num, score FROM scores WHERE wordle_num IN (?, ?)", 
                        (today_wordle, yesterday_wordle))
            existing_scores = cursor.fetchall()
            logging.info(f"Found {len(existing_scores)} existing scores for Wordle #{today_wordle} and #{yesterday_wordle}")
            
            # Process conversations (limit to 5 for testing)
            for i, convo in enumerate(conversation_items[:5]):
                try:
                    logging.info(f"Processing conversation {i+1}")
                    convo.click()
                    time.sleep(2)
                    
                    # Get phone number
                    phone_elements = driver.find_elements(By.CSS_SELECTOR, ".header-title span")
                    phone_number = "Unknown"
                    for elem in phone_elements:
                        if elem.text and ("(" in elem.text or "+" in elem.text):
                            phone_number = elem.text
                            break
                    
                    # Get player name from phone number
                    player_name = phone_to_player.get(phone_number)
                    if player_name:
                        league_id = player_to_league.get(player_name, 0)
                        logging.info(f"Found conversation for {player_name} (League {league_id})")
                    else:
                        logging.info(f"Unknown player for phone {phone_number}")
                    
                    # Get messages
                    message_elements = driver.find_elements(By.CSS_SELECTOR, ".message-content-wrapper .message-content")
                    logging.info(f"Found {len(message_elements)} messages")
                    
                    # Look for Wordle scores in recent messages
                    scores_found = []
                    for msg_idx, message in enumerate(message_elements[:10]):  # Check 10 most recent messages
                        message_content = message.text.strip()
                        
                        # Look for Wordle scores
                        if "Wordle" in message_content:
                            # Look for Wordle number
                            wordle_match = re.search(r'Wordle[^\d]*(\d+(?:,\d+)?)', message_content)
                            if wordle_match:
                                wordle_num = int(wordle_match.group(1).replace(",", ""))
                                
                                # Look for score
                                score_match = re.search(r'(\d|X)/6', message_content)
                                if score_match:
                                    score_val = parse_score(score_match.group(1))
                                    
                                    # Get emoji pattern
                                    emoji_pattern = extract_emoji_pattern(message_content)
                                    
                                    scores_found.append({
                                        'wordle_num': wordle_num,
                                        'score': score_val,
                                        'emoji_pattern': emoji_pattern
                                    })
                                    
                                    logging.info(f"Found score: Wordle #{wordle_num}, Score: {score_val}/6")
                                    if emoji_pattern:
                                        logging.info(f"Emoji pattern: {emoji_pattern}")
                    
                    if not scores_found:
                        logging.info("No Wordle scores found in this conversation")
                    else:
                        logging.info(f"Found {len(scores_found)} scores in this conversation")
                    
                    # Go back to conversation list
                    back_btn = driver.find_element(By.CSS_SELECTOR, ".gv-nav-tab-button[title='Messages']")
                    back_btn.click()
                    time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Error processing conversation {i+1}: {e}")
                    try:
                        # Try to go back to conversation list
                        back_btn = driver.find_element(By.CSS_SELECTOR, ".gv-nav-tab-button[title='Messages']")
                        back_btn.click()
                        time.sleep(1)
                    except:
                        pass
            
            conn.close()
        else:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {current_url}")
    
    except Exception as e:
        logging.error(f"Error in main function: {e}")
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
