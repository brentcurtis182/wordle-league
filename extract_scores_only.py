import os
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
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
        # Try multiple times in case of connection issues
        for attempt in range(3):
            try:
                driver.get("https://voice.google.com/messages")
                logging.info("Navigated to Google Voice messages")
                
                # Take screenshot for verification
                driver.save_screenshot(f"google_voice_navigation_{attempt}.png")
                logging.info(f"Saved screenshot to google_voice_navigation_{attempt}.png")
                
                # First wait for the page to have any content
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Then wait for the conversation list specifically
                WebDriverWait(driver, 45).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
                )
                
                logging.info("Google Voice conversation list loaded successfully")
                print("Google Voice loaded! You should see a browser window with Google Voice")
                time.sleep(5)  # Give a moment for UI to stabilize
                return True
                
            except TimeoutException as te:
                logging.warning(f"Timeout on attempt {attempt+1}/3: {te}")
                if attempt == 2:  # Last attempt
                    raise
            except Exception as e:
                logging.warning(f"Error on attempt {attempt+1}/3: {e}")
                if attempt == 2:  # Last attempt
                    raise
                
        logging.error("Failed to load Google Voice after multiple attempts")
        return False
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

def scroll_conversation(driver):
    """Scroll through the conversation to load all messages"""
    try:
        # Find the scrollable element
        scroll_element = driver.find_element(By.CSS_SELECTOR, "gv-message-list")
        
        # Initial scroll position
        last_height = driver.execute_script("return arguments[0].scrollHeight", scroll_element)
        
        # Scroll up to load older messages
        for _ in range(15):  # Try scrolling up to 15 times
            # Scroll to top
            driver.execute_script("arguments[0].scrollTo(0, 0)", scroll_element)
            time.sleep(1)
            
            # Check if we've reached the top
            new_height = driver.execute_script("return arguments[0].scrollHeight", scroll_element)
            if new_height == last_height:
                # No more messages loaded, break the loop
                break
                
            last_height = new_height
            
        logging.info("Finished scrolling through conversation")
        return True
    except Exception as e:
        logging.error(f"Error scrolling conversation: {e}")
        return False

def extract_player_name_from_phone(phone_number, league_id):
    """Extract player name from phone number based on league mappings"""
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

def extract_scores_direct(driver, league_id=1):
    """Extract Wordle scores from conversations directly"""
    # Calculate today's Wordle number
    today_wordle = calculate_today_wordle()
    logging.info(f"Today's Wordle number should be: {today_wordle}")
    
    # Find relevant conversation threads
    conversation_items = find_conversation_threads(driver, league_id)
    if not conversation_items:
        logging.warning(f"No conversation threads found for league {league_id}")
        return False
    
    # Process each conversation
    for i, conversation in enumerate(conversation_items):
        try:
            # Click on conversation to load messages
            conversation.click()
            logging.info(f"Clicked on conversation {i+1} for league {league_id}")
            
            # Wait for message thread to load
            time.sleep(3)
            
            # Scroll through conversation to load all messages
            scroll_conversation(driver)
            
            # Find hidden elements containing message text
            hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
            logging.info(f"Found {len(hidden_elements)} hidden elements in conversation {i+1}")
            
            # Extract scores from hidden elements
            wordle_pattern = re.compile(r'Wordle\s+([0-9,]+)\s+([1-6]|X)/6')
            
            # Track scores by wordle number
            scores_found = {}
            
            # Process each hidden element for scores
            for element in hidden_elements:
                try:
                    # Get text content of element
                    text = element.get_attribute("textContent") if hasattr(element, "get_attribute") else element.text
                    if not text or len(text) < 10:
                        continue
                        
                    # Skip reaction messages
                    reaction_patterns = ['Loved', 'Liked', 'Laughed at', 'Emphasized', 'Reacted to']
                    if any(pattern in text for pattern in reaction_patterns):
                        continue
                    
                    # Look for Wordle pattern in text
                    match = wordle_pattern.search(text)
                    if not match:
                        continue
                        
                    # Extract wordle number and score
                    try:
                        wordle_num = int(match.group(1).replace(',', ''))
                        score_text = match.group(2)
                        score = 7 if score_text == 'X' else int(score_text)
                        
                        # Focus on recent wordles (today and yesterday)
                        if wordle_num < today_wordle - 5:  # Only include last 5 days
                            continue
                            
                        # Extract phone number from text
                        phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                        element_phone = None
                        
                        if phone_match:
                            # Format phone number consistently
                            element_phone = phone_match.group(1) + phone_match.group(2) + phone_match.group(3)
                            # Add country code if missing
                            if len(element_phone) == 10:
                                element_phone = "1" + element_phone
                        else:
                            # Try direct "Message from" format
                            direct_phone_match = re.search(r'Message from ([0-9 ]+)', text)
                            if direct_phone_match:
                                direct_phone = direct_phone_match.group(1).replace(' ', '')
                                if len(direct_phone) == 10:
                                    direct_phone = '1' + direct_phone
                                element_phone = direct_phone
                            else:
                                # Special case for PAL league 
                                if league_id == 3 and ("8587359353" in text or "7604206113" in text):
                                    element_phone = "18587359353" if "8587359353" in text else "17604206113"
                        
                        # If we got a phone number, map to player name
                        player_name = None
                        if element_phone:
                            player_name = extract_player_name_from_phone(element_phone, league_id)
                            
                        # Extract emoji pattern if present
                        emoji_pattern = None
                        if '\u2b1b' in text or '\u2b1c' in text or '\ud83d\udfe8' in text or '\ud83d\udfe9' in text:
                            pattern_lines = []
                            for line in text.split('\n'):
                                if any(emoji in line for emoji in ['\u2b1b', '\u2b1c', '\ud83d\udfe8', '\ud83d\udfe9']):
                                    pattern_lines.append(line.strip())
                            if pattern_lines:
                                emoji_pattern = '\n'.join(pattern_lines)
                        
                        # Store the score info
                        key = f"{wordle_num}"
                        if key not in scores_found:
                            scores_found[key] = []
                            
                        scores_found[key].append({
                            'player': player_name or f"Unknown ({element_phone or 'No Phone'})",
                            'score': score,
                            'score_text': score_text,
                            'emoji': emoji_pattern,
                            'text': text[:200] + "..." if len(text) > 200 else text  # First 200 chars for context
                        })
                        
                    except ValueError as ve:
                        logging.warning(f"Invalid wordle number or score: {ve}")
                    except Exception as e:
                        logging.error(f"Error processing score: {e}")
                        
                except Exception as e:
                    logging.error(f"Error processing hidden element: {e}")
                    
            # Print all found scores
            print(f"\n{'='*50}")
            print(f"SCORES FOUND FOR LEAGUE {league_id}")
            print(f"{'='*50}")
            
            if not scores_found:
                print("No scores found in this conversation.")
            else:
                for wordle_num, scores in sorted(scores_found.items(), key=lambda x: int(x[0]), reverse=True):
                    print(f"\nWordle #{wordle_num}")
                    print(f"{'-'*30}")
                    
                    for score_info in scores:
                        print(f"Player: {score_info['player']}")
                        print(f"Score: {score_info['score_text']}/6")
                        if score_info['emoji']:
                            print(f"Emoji Pattern:")
                            print(score_info['emoji'])
                        else:
                            print("No emoji pattern found")
                        print(f"Raw Text: {score_info['text']}")
                        print(f"{'-'*30}")
                        
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
    
    return True

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
            
            # Extract and show scores for current league
            extract_scores_direct(driver, league_id)
            
    except Exception as e:
        logging.error(f"Error in main process: {e}")
    finally:
        # Clean up
        driver.quit()
        logging.info("Browser closed")

if __name__ == "__main__":
    main()
