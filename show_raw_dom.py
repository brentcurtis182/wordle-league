#!/usr/bin/env python3
# Modified version of integrated_auto_update_multi_league.py to show DOM elements

import os
import sys
import time
import logging
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
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

def extract_and_show_scores(driver, league_id):
    """Extract Wordle scores from conversations and show DOM elements"""
    # Calculate today's and yesterday's Wordle numbers
    today_wordle = get_todays_wordle_number()
    yesterday_wordle = get_yesterdays_wordle_number()
    logging.info(f"Looking for Wordle scores - Today: #{today_wordle}, Yesterday: #{yesterday_wordle}")
    
    # Find relevant conversation threads
    conversation_items = find_conversation_threads(driver, league_id)
    if not conversation_items:
        logging.warning(f"No conversation threads found for league {league_id}")
        return False
    
    # Create HTML file for output
    output_file = f"wordle_scores_league_{league_id}.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Wordle Scores - League {league_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .element {{ border: 1px solid #ccc; padding: 10px; margin: 10px 0; }}
        .wordle-num {{ font-weight: bold; color: blue; }}
        .player {{ font-weight: bold; }}
        .score {{ color: green; font-weight: bold; }}
        .emoji {{ font-family: monospace; white-space: pre; }}
        pre {{ background-color: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>Wordle Scores - League {league_id}</h1>
    <p>Extracted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Today's Wordle: <span class="wordle-num">#{today_wordle}</span></p>
    <p>Yesterday's Wordle: <span class="wordle-num">#{yesterday_wordle}</span></p>
""")
    
    # Process each conversation
    scores_found = {}
    
    for i, conversation in enumerate(conversation_items):
        try:
            # Click on conversation to load messages
            driver.execute_script("arguments[0].click();", conversation)
            logging.info(f"Clicked on conversation {i+1} for league {league_id}")
            
            # Wait for message thread to load
            time.sleep(3)
            
            # Scroll up in thread to load more messages
            scroll_up_in_thread(driver, today_wordle)
            
            # Find hidden elements containing message text
            hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
            logging.info(f"Found {len(hidden_elements)} hidden elements in conversation {i+1}")
            
            # Log to HTML file
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(f"""
    <h2>Conversation {i+1}</h2>
    <p>Found {len(hidden_elements)} hidden elements</p>
""")
            
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
                                # Store score info
                                if wordle_num not in scores_found:
                                    scores_found[wordle_num] = []
                                
                                # Extract phone number
                                phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                                element_phone = None
                                player_name = None
                                
                                if phone_match:
                                    element_phone = phone_match.group(1) + phone_match.group(2) + phone_match.group(3)
                                    if len(element_phone) == 10:
                                        element_phone = "1" + element_phone
                                    player_name = extract_player_name_from_phone(element_phone, league_id)
                                
                                # Extract emoji pattern
                                emoji_pattern = None
                                if '\u2b1b' in text or '\u2b1c' in text or '\ud83d\udfe8' in text or '\ud83d\udfe9' in text:
                                    pattern_lines = []
                                    for line in text.split('\n'):
                                        if any(emoji in line for emoji in ['\u2b1b', '\u2b1c', '\ud83d\udfe8', '\ud83d\udfe9']):
                                            pattern_lines.append(line.strip())
                                    
                                    if pattern_lines:
                                        emoji_pattern = '\n'.join(pattern_lines)
                                
                                # Add to scores found
                                scores_found[wordle_num].append({
                                    'player': player_name or f"Unknown ({element_phone})" if element_phone else "Unknown",
                                    'score': score,
                                    'score_text': score_text,
                                    'emoji': emoji_pattern,
                                    'element_index': j,
                                    'conversation': i+1
                                })
                                
                                # Write to HTML file
                                with open(output_file, "a", encoding="utf-8") as f:
                                    f.write(f"""
    <div class="element">
        <h3>Element {j+1} - Wordle {wordle_num}</h3>
        <p>Player: <span class="player">{player_name or (f"Unknown ({element_phone})" if element_phone else "Unknown")}</span></p>
        <p>Score: <span class="score">{score_text}/6</span></p>
""")
                                    if emoji_pattern:
                                        f.write(f"""
        <p>Emoji Pattern:</p>
        <pre class="emoji">{emoji_pattern}</pre>
""")
                                    
                                    # Include original text
                                    f.write(f"""
        <details>
            <summary>Raw Text</summary>
            <pre>{text}</pre>
        </details>
    </div>
""")
                                
                        except ValueError:
                            continue
                        
                except Exception as e:
                    logging.error(f"Error processing hidden element {j+1}: {e}")
            
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
    
    # Write summary to HTML file
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(f"""
    <h2>Score Summary</h2>
""")
        if scores_found:
            f.write("""
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Wordle #</th>
            <th>Player</th>
            <th>Score</th>
            <th>Emoji Pattern</th>
        </tr>
""")
            # Sort by Wordle number (newest first) then by player name
            for wordle_num in sorted(scores_found.keys(), reverse=True):
                for score in sorted(scores_found[wordle_num], key=lambda x: x['player']):
                    emoji_cell = f"<pre>{score['emoji']}</pre>" if score['emoji'] else "None"
                    f.write(f"""
        <tr>
            <td>{wordle_num}</td>
            <td>{score['player']}</td>
            <td>{score['score_text']}/6</td>
            <td>{emoji_cell}</td>
        </tr>
""")
            f.write("""
    </table>
""")
        else:
            f.write("""
    <p>No scores found</p>
""")
            
        f.write("""
</body>
</html>
""")
    
    # Print summary to console
    print(f"\n{'='*50}")
    print(f"SUMMARY OF SCORES FOR LEAGUE {league_id}")
    print(f"{'='*50}")
    
    if scores_found:
        for wordle_num in sorted(scores_found.keys(), reverse=True):
            print(f"\nWordle #{wordle_num}:")
            
            for score in sorted(scores_found[wordle_num], key=lambda x: x['player']):
                print(f"  Player: {score['player']}")
                print(f"  Score: {score['score_text']}/6")
                if score['emoji']:
                    print(f"  Emoji Pattern:")
                    print(f"{score['emoji']}")
                print(f"  {'='*20}")
    else:
        print("No Wordle scores found")
        
    print(f"\nComplete results saved to: {output_file}")
    return True

def main():
    # Set up Chrome driver
    driver = setup_driver()
    if not driver:
        logging.error("Failed to set up Chrome driver")
        return
    
    try:
        # Navigate to Google Voice
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return
        
        # Process each league
        for league_config in LEAGUES:
            league_id = league_config["league_id"]
            league_name = league_config["name"]
            
            logging.info(f"Processing league: {league_name} (ID: {league_id})")
            
            # Extract and show scores for this league
            extract_and_show_scores(driver, league_id)
            
    except Exception as e:
        logging.error(f"Error in main process: {e}")
    finally:
        # Clean up
        driver.quit()
        logging.info("Browser closed")

if __name__ == "__main__":
    main()
