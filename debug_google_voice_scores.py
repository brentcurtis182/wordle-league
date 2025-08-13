import os
import sys
import time
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_extraction.log"),
        logging.StreamHandler()
    ]
)

def get_todays_wordle_number():
    """Calculate today's Wordle number based on the known base date"""
    base_date = datetime(2021, 6, 19).date()  # Wordle #0 date
    today = datetime.now().date()
    delta = (today - base_date).days
    return delta

def get_yesterdays_wordle_number():
    """Calculate yesterday's Wordle number"""
    return get_todays_wordle_number() - 1

def get_player_league(player_name):
    """Map player to their league"""
    player_league_map = {
        # Wordle Warriorz (league_id 1)
        "Joanna": 1,
        "Nanna": 1,
        "Brent": 1,
        "Malia": 1,
        "Evan": 1,
        
        # PAL League (league_id 3)
        "Vox": 3,
        "Fuzwuz": 3,
        "Pants": 3,
        "Starslider": 3
    }
    
    # If we can't identify the player directly, try looking for PAL members by name in the string
    if player_name == "Unknown Player" or player_name not in player_league_map:
        pal_players = ["Vox", "Fuzwuz", "Pants", "Starslider"]
        for pal in pal_players:
            # Check if the name appears in the unknown player name string
            if pal.lower() in player_name.lower():
                logging.info(f"Identified PAL player from name: {pal}")
                return 3
    
    return player_league_map.get(player_name, 0)

def extract_player_name_from_phone(phone_number):
    """Extract player name from phone number"""
    # Define a mapping of phone numbers to player names
    # Add all known phone numbers from both leagues here
    phone_to_name = {
        # Wordle Warriorz
        "(310) 926-3555": "Joanna",
        "(949) 230-4472": "Nanna",
        "(858) 735-9353": "Brent",
        "(760) 334-1190": "Malia",
        "(760) 846-2302": "Evan",
        
        # PAL League - actual phone numbers from the integrated script
        # Replace these with actual numbers from your system
        "(480) 382-7865": "Vox",
        "(602) 405-8617": "Fuzwuz",
        "(602) 510-9119": "Pants",
        "(602) 616-7777": "Starslider"
    }
    
    # Clean the phone number by removing Unicode directional characters
    if phone_number:
        cleaned_phone = ''
        for char in phone_number:
            if ord(char) < 128:  # Only keep ASCII characters
                cleaned_phone += char
        phone_number = cleaned_phone.strip()
        logging.info(f"Cleaned phone number: '{phone_number}'")
    
    if phone_number in phone_to_name:
        return phone_to_name[phone_number]
    
    return None

def extract_player_name(conversation_text):
    """Extract player name from conversation"""
    logging.info("Extracting player name from conversation")
    
    # Define a mapping of phone numbers to player names - same as extract_player_name_from_phone
    phone_to_name = {
        # Wordle Warriorz
        "(310) 926-3555": "Joanna",
        "(949) 230-4472": "Nanna",
        "(858) 735-9353": "Brent",
        "(760) 334-1190": "Malia",
        "(760) 846-2302": "Evan",
        
        # PAL League - actual phone numbers from the integrated script
        "(480) 382-7865": "Vox",
        "(602) 405-8617": "Fuzwuz",
        "(602) 510-9119": "Pants",
        "(602) 616-7777": "Starslider"
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
            return "Unknown Player"
    
    # Default name if we couldn't determine
    logging.info("Could not extract player name, using default: Unknown Player")
    return "Unknown Player"

def debug_extract_wordle_scores():
    """Extract Wordle scores from Google Voice in debug mode - no database changes"""
    logging.info("Starting Wordle score DEBUG extraction")
    
    # Set up Chrome profile directory
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    logging.info(f"Using Chrome profile at: {profile_dir}")
    
    if not os.path.exists(profile_dir):
        logging.error(f"Profile directory does not exist: {profile_dir}")
        return False
    
    try:
        # Set up Chrome options
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
        
        # Get current URL
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        # Check if we're on Google Voice
        if "voice.google.com" in current_url:
            logging.info("Successfully navigated to Google Voice")
            
            # Look for conversation list items with more robust detection
            try:
                logging.info("Looking for conversation list items")
                
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
                    
                    # Extract scores from conversations - without saving to database
                    scores_found = debug_extract_scores(driver, conversation_items, today_wordle, yesterday_wordle)
                    
                    # Close the browser
                    driver.quit()
                    
                    return scores_found > 0
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

def debug_extract_scores(driver, conversation_items, today_wordle, yesterday_wordle):
    """Extract Wordle scores from conversations - debug version, no DB changes
    
    Args:
        driver: Selenium WebDriver instance
        conversation_items: List of conversation elements to process
        today_wordle: Today's Wordle number
        yesterday_wordle: Yesterday's Wordle number
        
    Returns:
        int: Number of scores found
    """
    logging.info(f"Processing {len(conversation_items)} conversations")
    
    scores_found = 0
    today_scores = []
    yesterday_scores = []
    
    # Track all leagues
    league_scores = {
        1: {"name": "Wordle Warriorz", "today": [], "yesterday": []},
        3: {"name": "PAL League", "today": [], "yesterday": []}
    }
    
    # Process each conversation - scan more conversations to find league members
    for i, item in enumerate(conversation_items[:20]):  # Process more conversations to find all league members
        try:
            logging.info(f"Processing conversation {i+1}/{min(10, len(conversation_items))}")
            
            # Click on the conversation item to open it
            try:
                logging.info("Attempting to click on conversation item")
                
                # Try to click using JavaScript
                driver.execute_script("arguments[0].click();", item)
                logging.info("Clicked using JavaScript")
                
                # Wait for conversation to load
                time.sleep(3)
                logging.info("Waited for conversation to load")
                    
                # Get conversation HTML
                conversation_html = driver.page_source
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(conversation_html, 'html.parser')
                
                # Find all message items in the conversation
                message_items = soup.select('gv-text-message-item')
                logging.info(f"Found {len(message_items)} message items in conversation")
                
                # First try to find hidden elements with full message text
                hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                logging.info(f"Found {len(hidden_elements)} hidden elements")
                
                conversation_text = ""
                for hidden in hidden_elements:
                    try:
                        hidden_text = hidden.get_attribute('textContent')
                        if hidden_text and "Wordle" in hidden_text:
                            logging.info(f"Found Wordle in hidden element")
                            conversation_text += "\n" + hidden_text
                    except Exception as e:
                        logging.warning(f"Error getting hidden text: {e}")
                        
                # If no Wordle content found in hidden elements, get all text content
                if "Wordle" not in conversation_text:
                    logging.info("No Wordle content found in hidden elements, getting all text")
                    conversation_text = driver.find_element(By.TAG_NAME, "body").text
                
                # Try to extract player name from conversation text
                player_name = extract_player_name(conversation_text)
                
                # Check if conversation mentions specific players we're looking for
                if player_name == "Unknown Player":
                    # Check for specific player names in the conversation text
                    all_players = ["Joanna", "Nanna", "Brent", "Malia", "Evan", "Vox", "Fuzwuz", "Pants", "Starslider"]
                    for p in all_players:
                        if p in conversation_text:
                            player_name = p
                            logging.info(f"Found player name in conversation: {player_name}")
                            break
                
                logging.info(f"Extracted player name: {player_name}")
                
                # Get player's league
                league_id = get_player_league(player_name)
                league_name = league_scores.get(league_id, {}).get("name", "Unknown League")
                logging.info(f"Player {player_name} belongs to league: {league_name} (ID: {league_id})")
                
                # Look for Wordle scores in the conversation text with more flexible patterns
                # Handle variations like "Wordle 1498 3/6", "Wordle #1498 3/6", "Wordle 1,498 3/6"
                wordle_patterns = [
                    re.compile(r'Wordle\s+#?(\d+(?:,\d+)?)\s+(\d+)/6'),  # Standard format
                    re.compile(r'Wordle[:\s]+#?(\d+(?:,\d+)?)\s*[:\s]+(\d+)/6'),  # With colons
                    re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*(\d+)/6')  # Very flexible
                ]
                
                wordle_matches = []
                for pattern in wordle_patterns:
                    matches = pattern.findall(conversation_text)
                    if matches:
                        wordle_matches.extend(matches)
                        logging.info(f"Found matches with pattern: {pattern.pattern}")
                
                # Also look for failed attempts (X/6) with more flexible patterns
                failed_patterns = [
                    re.compile(r'Wordle\s+#?([\d,]+)\s+X/6'),  # Standard format
                    re.compile(r'Wordle[:\s]+#?([\d,]+)\s*[:\s]+X/6'),  # With colons
                    re.compile(r'Wordle[^\d]*([\d,]+)[^\d]*X/6')  # Very flexible
                ]
                
                failed_matches = []
                for pattern in failed_patterns:
                    matches = pattern.findall(conversation_text)
                    if matches:
                        failed_matches.extend(matches)
                        logging.info(f"Found failed matches with pattern: {pattern.pattern}")
                
                logging.info(f"Found {len(wordle_matches)} regular matches and {len(failed_matches)} failed matches")
                
                # Extract emoji patterns from the conversation text
                emoji_pattern = None
                emoji_rows = []
                
                # Look for emoji patterns in the conversation text - modified to capture complete multi-row patterns
                # Find sequences of emoji rows that make up a complete wordle pattern
                emoji_pattern_regex = re.compile(r'((?:[⬛⬜🟨🟩]{5}[\s\n]*){1,6})', re.MULTILINE)
                emoji_matches = re.findall(emoji_pattern_regex, conversation_text)
                
                valid_emoji_matches = []
                if emoji_matches:
                    for match in emoji_matches:
                        # Clean up the pattern by splitting into lines and rejoining with newlines
                        rows = [row for row in re.findall(r'[⬛⬜🟨🟩]{5}', match) if row]
                        if rows:  # If we have valid rows
                            clean_pattern = '\n'.join(rows)
                            valid_emoji_matches.append(clean_pattern)
                            logging.info(f"Found emoji pattern with {len(rows)} rows")
                
                # Find the best emoji pattern for this conversation
                emoji_pattern_to_save = None
                if valid_emoji_matches:
                    # Select the pattern with the most rows
                    emoji_pattern_to_save = max(valid_emoji_matches, key=lambda p: p.count('\n') + 1)
                    logging.info(f"Selected emoji pattern")
                
                # Process regular scores
                for wordle_match in wordle_matches:
                    # Remove commas from the Wordle number before converting to int
                    wordle_num_str = wordle_match[0].replace(',', '')
                    wordle_num = int(wordle_num_str)
                    score = int(wordle_match[1])
                    
                    # Only process today's or yesterday's scores
                    if wordle_num == today_wordle:
                        logging.info(f"Found TODAY's score: Wordle #{wordle_num}, Score: {score}/6, Player: {player_name}, League: {league_name}")
                        scores_found += 1
                        pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                        today_scores.append(f"{player_name}: {score}/6{pattern_display}")
                        
                        # Add to league-specific score list
                        if league_id in league_scores:
                            league_scores[league_id]["today"].append(f"{player_name}: {score}/6{pattern_display}")
                    
                    elif wordle_num == yesterday_wordle:
                        logging.info(f"Found YESTERDAY's score: Wordle #{wordle_num}, Score: {score}/6, Player: {player_name}, League: {league_name}")
                        scores_found += 1
                        pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                        yesterday_scores.append(f"{player_name}: {score}/6{pattern_display}")
                        
                        # Add to league-specific score list
                        if league_id in league_scores:
                            league_scores[league_id]["yesterday"].append(f"{player_name}: {score}/6{pattern_display}")
                
                # Process failed attempts (X/6)
                for failed_match in failed_matches:
                    # Remove commas from the Wordle number before converting to int
                    wordle_num_str = failed_match.replace(',', '')
                    wordle_num = int(wordle_num_str)
                    
                    # Only process today's or yesterday's scores
                    if wordle_num == today_wordle:
                        logging.info(f"Found TODAY's failed attempt: Wordle #{wordle_num}, Score: X/6, Player: {player_name}, League: {league_name}")
                        scores_found += 1
                        pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                        today_scores.append(f"{player_name}: X/6{pattern_display}")
                        
                        # Add to league-specific score list
                        if league_id in league_scores:
                            league_scores[league_id]["today"].append(f"{player_name}: X/6{pattern_display}")
                    
                    elif wordle_num == yesterday_wordle:
                        logging.info(f"Found YESTERDAY's failed attempt: Wordle #{wordle_num}, Score: X/6, Player: {player_name}, League: {league_name}")
                        scores_found += 1
                        pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                        yesterday_scores.append(f"{player_name}: X/6{pattern_display}")
                        
                        # Add to league-specific score list
                        if league_id in league_scores:
                            league_scores[league_id]["yesterday"].append(f"{player_name}: X/6{pattern_display}")
                
            except Exception as e:
                logging.error(f"Error extracting conversation text: {e}")
                
        except Exception as e:
            logging.error(f"Error processing conversation {i+1}: {e}")
    
    # Log summary
    logging.info(f"Found {scores_found} total scores across all conversations")
    
    # Log today's scores - avoid emoji encoding errors in console
    if today_scores:
        logging.info("TODAY'S SCORES:")
        for score in today_scores:
            try:
                logging.info(f"  {score}")
            except UnicodeEncodeError:
                # Just log the player and score without the emoji pattern
                score_parts = score.split(" (")
                logging.info(f"  {score_parts[0]} (emoji pattern present but not displayed)")
    else:
        logging.info("No scores found for today")
        
    # Log yesterday's scores - avoid emoji encoding errors in console
    if yesterday_scores:
        logging.info("YESTERDAY'S SCORES:")
        for score in yesterday_scores:
            try:
                logging.info(f"  {score}")
            except UnicodeEncodeError:
                # Just log the player and score without the emoji pattern
                score_parts = score.split(" (")
                logging.info(f"  {score_parts[0]} (emoji pattern present but not displayed)")
    else:
        logging.info("No scores found for yesterday")
    
    # Log scores by league
    logging.info("SCORES BY LEAGUE:")
    for league_id, league_data in league_scores.items():
        league_name = league_data["name"]
        logging.info(f"League: {league_name} (ID: {league_id})")
        
        logging.info("  TODAY:")
        if league_data["today"]:
            for score in league_data["today"]:
                logging.info(f"    {score}")
        else:
            logging.info("    No scores for today")
            
        logging.info("  YESTERDAY:")
        if league_data["yesterday"]:
            for score in league_data["yesterday"]:
                logging.info(f"    {score}")
        else:
            logging.info("    No scores for yesterday")
    
    return scores_found

def main():
    """Main function"""
    logging.info("Starting debug extraction")
    debug_extract_wordle_scores()
    logging.info("Debug extraction completed")

if __name__ == "__main__":
    main()
