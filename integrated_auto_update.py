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
    
    # Clean the phone number by removing Unicode directional characters
    if phone_number:
        # Remove Unicode directional characters (\u202a, \u202c, etc.)
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
    
    # Take a screenshot of the page before processing
    driver.save_screenshot("before_processing_conversations.png")
    logging.info("Saved screenshot before processing conversations")
    
    # IMPROVED EXTRACTION: First look for all cdk-visually-hidden elements
    # which contain complete data in one place
    try:
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements to process")
        
        for hidden_elem in hidden_elements:
            try:
                hidden_text = hidden_elem.get_attribute('textContent')
                if hidden_text and "Wordle" in hidden_text and "/6" in hidden_text:
                    logging.info(f"Found Wordle data in hidden element: {hidden_text[:100]}...")
                    
                    # Extract phone number - look for patterns like "from 7 6 0 8 4 6 2 3 0 2" or "(760) 846-2302"
                    phone_match = re.search(r'from\s+(\d[\s\d]+\d)', hidden_text)
                    if not phone_match:
                        phone_match = re.search(r'from\s+\(?(\d{3})\)?[\s-]*(\d{3})[\s-]*(\d{4})', hidden_text)
                        if phone_match:
                            phone_number = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
                    else:
                        # Remove spaces from the phone number
                        phone_number = phone_match.group(1).replace(" ", "")
                    
                    if not phone_match:
                        logging.warning(f"Could not extract phone number from: {hidden_text[:100]}")
                        continue
                    
                    # Get player name from phone number
                    player_name = extract_player_name_from_phone(phone_number)
                    if not player_name:
                        logging.warning(f"Could not identify player for phone {phone_number}")
                        continue
                    
                    # Extract Wordle number - handle formats like "Wordle 1,500" or "Wordle #1500"
                    wordle_match = re.search(r'Wordle\s+#?([\d,]+)', hidden_text)
                    if not wordle_match:
                        logging.warning(f"Could not extract Wordle number from: {hidden_text[:100]}")
                        continue
                    
                    wordle_num = int(wordle_match.group(1).replace(',', ''))
                    
                    # Extract score - handle both "X/6" and "5/6" formats
                    score_match = re.search(r'([\dX])/6', hidden_text)
                    if not score_match:
                        logging.warning(f"Could not extract score from: {hidden_text[:100]}")
                        continue
                    
                    score_value = score_match.group(1)
                    score = 7 if score_value.upper() == 'X' else int(score_value)
                    
                    # Extract emoji pattern - look for sequences of square emojis
                    emoji_rows = re.findall(r'[⬛⬜🟨🟩]{5}', hidden_text)
                    if not emoji_rows:
                        logging.warning(f"Could not extract emoji pattern from: {hidden_text[:100]}")
                    
                    emoji_pattern = "\n".join(emoji_rows) if emoji_rows else None
                    
                    logging.info(f"Extracted from hidden element: Player={player_name}, Wordle#{wordle_num}, Score={score}/6")
                    if emoji_pattern:
                        logging.info(f"Emoji pattern with {len(emoji_rows)} rows: {emoji_pattern}")
                    
                    # Save score to database
                    status = save_score_to_db(player_name, wordle_num, score, emoji_pattern)
                    logging.info(f"Save status for {player_name}: {status}")
            except Exception as e:
                logging.error(f"Error processing hidden element: {e}")
    except Exception as e:
        logging.error(f"Error extracting from hidden elements: {e}")
        # Continue with existing extraction methods as fallback
    
    scores_extracted = 0
    today_scores = []
    
    # Function to save score to database
    def save_score_to_db(player, wordle_num, score, emoji_pattern=None):
        """Save score to database
        
        Args:
            player: Player name
            wordle_num: Wordle number
            score: Score value (1-6, or 7 for X/6)
            emoji_pattern: Optional emoji pattern string
            
        Returns:
            str: Status code - 'new_score_added', 'score_updated', 'emoji_updated', 'no_change', or 'error'
        """
        logging.info(f"Saving score: Player={player}, Wordle#{wordle_num}, Score={score}, Pattern={emoji_pattern}")
        
        conn = None
        try:
            # Connect to the database
            conn = sqlite3.connect('wordle_league.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Create table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY,
                    wordle_num INTEGER,
                    score INTEGER,
                    player_name TEXT,
                    emoji_pattern TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            
            # Check if emoji_pattern column exists, add it if not
            try:
                cursor.execute("SELECT emoji_pattern FROM scores LIMIT 1")
            except sqlite3.OperationalError:
                logging.info("Adding emoji_pattern column to scores table")
                try:
                    cursor.execute("ALTER TABLE scores ADD COLUMN emoji_pattern TEXT")
                    conn.commit()
                except sqlite3.Error as e:
                    logging.error(f"Error adding emoji_pattern column: {e}")
            
            # Check the table structure to determine column names
            cursor.execute("PRAGMA table_info(scores)")
            columns = {row['name']: row['cid'] for row in cursor.fetchall()}
            logging.info(f"Database columns found: {list(columns.keys())}")
            
            # Determine the wordle number column name
            wordle_col = 'wordle_num'
            if 'wordle_number' in columns and 'wordle_num' not in columns:
                wordle_col = 'wordle_number'
            
            # Determine the player name column
            player_col = 'player_name'
            if 'player' in columns and 'player_name' not in columns:
                player_col = 'player'
            
            # Check if emoji_pattern column exists
            has_emoji_pattern = 'emoji_pattern' in columns
            
            # Check if this score already exists
            query = f"SELECT id, score FROM scores WHERE {wordle_col} = ? AND {player_col} = ?"
            cursor.execute(query, (wordle_num, player))
            existing = cursor.fetchone()
            
            if existing:
                logging.info(f"Found existing score: {existing['score']} for Wordle #{wordle_num} by {player}")
                
                # Don't update scores that are already in the database
                # This ensures we preserve the first valid score we find
                logging.info(f"Preserving existing score {existing['score']} for Wordle #{wordle_num} by {player}")
                
                # Only update emoji pattern if it's missing
                if emoji_pattern and has_emoji_pattern:
                    cursor.execute(f"SELECT emoji_pattern FROM scores WHERE id = ?", (existing['id'],))
                    result = cursor.fetchone()
                    existing_emoji = result['emoji_pattern'] if result else None
                    
                    # Only update if the emoji pattern is missing or empty
                    # Also verify the new emoji pattern is valid (has multiple rows for a real pattern)
                    if (not existing_emoji or existing_emoji.strip() == '') and emoji_pattern.count('\n') > 0:
                        # Count the rows in the emoji pattern to ensure it's valid
                        row_count = emoji_pattern.count('\n') + 1
                        if 1 <= row_count <= 6:  # Valid Wordle patterns have 1-6 rows
                            logging.info(f"Adding valid emoji pattern ({row_count} rows) for {player}'s Wordle #{wordle_num} score")
                            query = f"UPDATE scores SET emoji_pattern = ? WHERE id = ?"
                            cursor.execute(query, (emoji_pattern, existing['id']))
                            conn.commit()
                            conn.close()
                            return "emoji_updated"
                        else:
                            logging.warning(f"Rejecting invalid emoji pattern with {row_count} rows for {player}'s Wordle #{wordle_num}")
                            conn.close()
                            return "no_change"
                    else:
                        logging.info(f"Preserving existing emoji pattern for {player}'s Wordle #{wordle_num} score")
                        conn.close()
                        return "no_change"
                else:
                    # No emoji pattern to update
                    conn.close()
                    return "no_change"
            else:
                # Insert new score
                if has_emoji_pattern and emoji_pattern:
                    query = f"INSERT INTO scores ({wordle_col}, score, {player_col}, emoji_pattern) VALUES (?, ?, ?, ?)"
                    cursor.execute(query, (wordle_num, score, player, emoji_pattern))
                else:
                    query = f"INSERT INTO scores ({wordle_col}, score, {player_col}) VALUES (?, ?, ?)"
                    cursor.execute(query, (wordle_num, score, player))
                
                conn.commit()
                logging.info(f"New score added: {score} for Wordle #{wordle_num} by {player}")
                conn.close()
                return "new_score_added"
        except Exception as e:
            logging.error(f"Database error: {e}")
            if conn:
                conn.close()
            return "error"
        except Exception as e:
            logging.error(f"Database error: {e}")
            return 'error'
    
    # Process each conversation
    for i, item in enumerate(conversation_items):
        try:
            logging.info(f"Processing conversation {i+1}/{len(conversation_items)}")
            
            # Click on the conversation item to open it
            try:
                logging.info("Attempting to click on conversation item")
                driver.save_screenshot(f"before_click_{i+1}.png")
                
                # Try to find the participants annotation within the item
                try:
                    participants = item.find_element(By.CSS_SELECTOR, "gv-annotation.participants")
                    logging.info("Found participants element, clicking on it")
                    
                    # Try multiple click methods
                    try:
                        # Method 1: JavaScript click
                        driver.execute_script("arguments[0].click();", participants)
                        logging.info("Clicked using JavaScript")
                    except Exception as e:
                        logging.warning(f"JavaScript click failed: {e}")
                        try:
                            # Method 2: Regular click
                            participants.click()
                            logging.info("Clicked using regular click")
                        except Exception as e:
                            logging.warning(f"Regular click failed: {e}")
                            try:
                                # Method 3: Action chains
                                actions = ActionChains(driver)
                                actions.move_to_element(participants).click().perform()
                                logging.info("Clicked using action chains")
                            except Exception as e:
                                logging.warning(f"Action chains click failed: {e}")
                                # Method 4: Click on the parent item instead
                                driver.execute_script("arguments[0].click();", item)
                                logging.info("Clicked on parent item using JavaScript")
                except Exception as e:
                    logging.warning(f"Could not find participants element: {e}")
                    # Click on the item itself
                    driver.execute_script("arguments[0].click();", item)
                    logging.info("Clicked on item using JavaScript")
                
                # Wait for conversation to load
                time.sleep(3)
                driver.save_screenshot(f"after_click_{i+1}.png")
                logging.info("Waited for conversation to load")
                
                # Save the HTML for debugging
                with open(f"conversation_item_{i+1}.html", "w", encoding="utf-8") as f:
                    f.write(item.get_attribute('outerHTML'))
                    
                # Get conversation HTML
                conversation_html = driver.page_source
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(conversation_html, 'html.parser')
                
                # Find all message items in the conversation
                message_items = soup.select('gv-text-message-item')
                logging.info(f"Found {len(message_items)} message items in conversation")
                
                # Save the full HTML for debugging
                with open(f"conversation_{i+1}_full.html", "w", encoding="utf-8") as f:
                    f.write(conversation_html)
                
                # Process each message individually to associate sender with content
                messages_data = []
                
                # First try to find structured message items
                if message_items:
                    for msg_idx, msg in enumerate(message_items):
                        try:
                            # Extract the sender phone number
                            sender_span = msg.select_one('span.sender')
                            phone_number = sender_span.text.strip() if sender_span else None
                            
                            # Extract message content
                            message_content = ""
                            
                            # First try the hidden content which has the full text
                            hidden_div = msg.select_one('.cdk-visually-hidden')
                            if hidden_div:
                                message_content = hidden_div.text.strip()
                            
                            # If no hidden content, try visible content
                            if not message_content or "Wordle" not in message_content:
                                content_div = msg.select_one('gv-annotation.content')
                                if content_div:
                                    message_content = content_div.text.strip()
                            
                            # Only process messages with content and phone number
                            if phone_number and message_content:
                                player_name = extract_player_name_from_phone(phone_number)
                                logging.info(f"Message {msg_idx+1}: Phone={phone_number}, Player={player_name}")
                                
                                # Add to our list of messages
                                messages_data.append({
                                    'phone_number': phone_number,
                                    'player_name': player_name,
                                    'content': message_content
                                })
                        except Exception as e:
                            logging.warning(f"Error processing message {msg_idx+1}: {e}")
                
                # If we couldn't find structured messages, fall back to the old method
                if not messages_data:
                    logging.warning("No structured messages found, falling back to old method")
                    # Get conversation text from ALL possible elements
                    conversation_text = ""
                    conversation_html = driver.page_source
                
                try:
                    # First, get all the hidden elements which contain the full message text
                    hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
                    logging.info(f"Found {len(hidden_elements)} hidden elements")
                    
                    for hidden in hidden_elements:
                        try:
                            hidden_text = hidden.get_attribute('textContent')
                            if hidden_text and "Wordle" in hidden_text:
                                logging.info(f"Found Wordle in hidden element: {hidden_text[:100]}...")
                                conversation_text += "\n" + hidden_text
                        except Exception as e:
                            logging.warning(f"Error getting hidden text: {e}")
                            
                    # If no Wordle content found in hidden elements, get all text content
                    if "Wordle" not in conversation_text:
                        logging.info("No Wordle content found in hidden elements, getting all text")
                        conversation_text = driver.find_element(By.TAG_NAME, "body").text
                        
                except Exception as e:
                    logging.error(f"Error extracting conversation content: {e}")
                    conversation_text = driver.find_element(By.TAG_NAME, "body").text
                    
                # Save the full HTML and text for debugging
                with open(f"conversation_{i+1}_full.html", "w", encoding="utf-8") as f:
                    f.write(conversation_html)
                    
                with open(f"conversation_{i+1}_full.txt", "w", encoding="utf-8") as f:
                    f.write(conversation_text)
                    
                # Log the full text for debugging
                logging.info(f"Extracted conversation text (length: {len(conversation_text)})")
                
                # Parse the HTML with BeautifulSoup for further processing
                soup = BeautifulSoup(conversation_html, 'html.parser')
                
                # Save conversation HTML for debugging
                with open(f"conversation_{i+1}.html", "w", encoding="utf-8") as f:
                    f.write(conversation_html)
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(conversation_html, 'html.parser')
                conversation_text = soup.get_text()
                
                # Save extracted text for debugging
                with open(f"conversation_{i+1}.txt", "w", encoding="utf-8") as f:
                    f.write(conversation_text)
                
                # Extract player name from phone number if available, otherwise from conversation text
                player_name = None
                if phone_number:
                    player_name = extract_player_name_from_phone(phone_number)
                    logging.info(f"Extracted player name from phone: {player_name}")
                
                # If no player name found from phone, try extracting from conversation text
                if not player_name:
                    player_name = extract_player_name(conversation_text)
                    logging.info(f"Extracted player name from text: {player_name}")
                
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
                
                # Also look for emoji patterns with alt text in img tags
                alt_text_pattern = re.compile(r'alt="([⬛⬜])"')
                alt_text_matches = alt_text_pattern.findall(conversation_html)
                
                valid_emoji_matches = []
                if emoji_matches:
                    for match in emoji_matches:
                        # Clean up the pattern by splitting into lines and rejoining with newlines
                        rows = [row for row in re.findall(r'[⬛⬜🟨🟩]{5}', match) if row]
                        if rows:  # If we have valid rows
                            clean_pattern = '\n'.join(rows)
                            valid_emoji_matches.append(clean_pattern)
                            logging.info(f"Found emoji pattern with {len(rows)} rows: {clean_pattern}")
                
                # Find the best emoji pattern for this conversation
                emoji_pattern_to_save = None
                if valid_emoji_matches:
                    # Select the pattern with the most rows (instead of just the longest string)
                    emoji_pattern_to_save = max(valid_emoji_matches, key=lambda p: p.count('\n') + 1)
                    logging.info(f"Selected emoji pattern to save: {emoji_pattern_to_save}")
                
                # If we have structured message data, process each message individually
                if messages_data:
                    for msg_data in messages_data:
                        phone_number = msg_data['phone_number']
                        player_name = msg_data['player_name']
                        message_content = msg_data['content']
                        
                        # Skip if we couldn't determine the player
                        if not player_name:
                            logging.warning(f"Could not identify player for phone {phone_number}, skipping")
                            continue
                        
                        # Extract emoji pattern from this specific message - improved for multi-row patterns
                        emoji_pattern_to_save = None
                        emoji_pattern_regex = re.compile(r'((?:[⬛⬜🟨🟩]{5}[\s\n]*){1,6})', re.MULTILINE)
                        emoji_matches = re.findall(emoji_pattern_regex, message_content)
                        
                        valid_emoji_matches = []
                        if emoji_matches:
                            for match in emoji_matches:
                                # Clean up the pattern by splitting into lines and rejoining with newlines
                                rows = [row for row in re.findall(r'[⬛⬜🟨🟩]{5}', match) if row]
                                if rows:  # If we have valid rows
                                    clean_pattern = '\n'.join(rows)
                                    valid_emoji_matches.append(clean_pattern)
                        
                        if valid_emoji_matches:
                            # Select the pattern with the most rows (instead of just the longest string)
                            emoji_pattern_to_save = max(valid_emoji_matches, key=lambda p: p.count('\n') + 1)
                            logging.info(f"Found emoji pattern for {player_name}: {emoji_pattern_to_save}")
                        
                        # Look for Wordle scores in this message
                        wordle_matches = []
                        for pattern in wordle_patterns:
                            matches = pattern.findall(message_content)
                            if matches:
                                wordle_matches.extend(matches)
                        
                        # Look for failed attempts
                        failed_matches = []
                        for pattern in failed_patterns:
                            matches = pattern.findall(message_content)
                            if matches:
                                failed_matches.extend(matches)
                        
                        # Process regular scores for this player's message
                        for wordle_match in wordle_matches:
                            # Remove commas from the Wordle number before converting to int
                            wordle_num_str = wordle_match[0].replace(',', '')
                            wordle_num = int(wordle_num_str)
                            score = int(wordle_match[1])
                            
                            # Only process today's or yesterday's scores
                            if wordle_num == today_wordle or wordle_num == yesterday_wordle:
                                logging.info(f"Found score: Wordle #{wordle_num}, Score: {score}/6, Player: {player_name}")
                                
                                # Save score to database with emoji pattern
                                result = save_score_to_db(player_name, wordle_num, score, emoji_pattern_to_save)
                                
                                if result == 'new_score_added':
                                    scores_extracted += 1
                                    if wordle_num == today_wordle:
                                        pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                                        today_scores.append(f"{player_name}: {score}/6{pattern_display}")
                        
                        # Process failed attempts (X/6) for this player's message
                        for failed_match in failed_matches:
                            # Remove commas from the Wordle number before converting to int
                            wordle_num_str = failed_match.replace(',', '')
                            wordle_num = int(wordle_num_str)
                            score = 7  # Use 7 to represent X/6 (failed attempt)
                            
                            # Only process today's or yesterday's scores
                            if wordle_num == today_wordle or wordle_num == yesterday_wordle:
                                logging.info(f"Found failed attempt: Wordle #{wordle_num}, Score: X/6, Player: {player_name}")
                                
                                # Save score to database with emoji pattern
                                result = save_score_to_db(player_name, wordle_num, score, emoji_pattern_to_save)
                                
                                if result == 'new_score_added':
                                    scores_extracted += 1
                                    if wordle_num == today_wordle:
                                        pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                                        today_scores.append(f"{player_name}: X/6{pattern_display}")
                else:
                    # Fall back to old method - process all scores with the same player
                    # Process regular scores
                    for wordle_match in wordle_matches:
                        # Remove commas from the Wordle number before converting to int
                        wordle_num_str = wordle_match[0].replace(',', '')
                        wordle_num = int(wordle_num_str)
                        score = int(wordle_match[1])
                        
                        # Only process today's or yesterday's scores
                        if wordle_num == today_wordle or wordle_num == yesterday_wordle:
                            logging.info(f"Found score: Wordle #{wordle_num}, Score: {score}/6, Player: {player_name}")
                            
                            # Save score to database with emoji pattern
                            result = save_score_to_db(player_name, wordle_num, score, emoji_pattern_to_save)
                            
                            if result == 'new_score_added':
                                scores_extracted += 1
                                if wordle_num == today_wordle:
                                    pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                                    today_scores.append(f"{player_name}: {score}/6{pattern_display}")
                    
                    # Process failed attempts (X/6) - we'll store these as score=7
                    for failed_match in failed_matches:
                        # Remove commas from the Wordle number before converting to int
                        wordle_num_str = failed_match.replace(',', '')
                        wordle_num = int(wordle_num_str)
                        score = 7  # Use 7 to represent X/6 (failed attempt)
                        
                        # Only process today's or yesterday's scores
                        if wordle_num == today_wordle or wordle_num == yesterday_wordle:
                            logging.info(f"Found failed attempt: Wordle #{wordle_num}, Score: X/6, Player: {player_name}")
                            
                            # Save score to database with emoji pattern
                            result = save_score_to_db(player_name, wordle_num, score, emoji_pattern_to_save)
                            
                            if result == 'new_score_added':
                                scores_extracted += 1
                                if wordle_num == today_wordle:
                                    pattern_display = f" ({emoji_pattern_to_save})" if emoji_pattern_to_save else ""
                                    today_scores.append(f"{player_name}: X/6{pattern_display}")
                
                # Add annotations to the saved text file
                with open(f"conversation_{i+1}_annotated.txt", "w", encoding="utf-8") as f:
                    f.write(f"Player Name: {player_name}\n\n")
                    f.write(f"Regular Matches: {wordle_matches}\n")
                    f.write(f"Failed Matches: {failed_matches}\n")
                    f.write(f"Emoji Matches: {valid_emoji_matches}\n")
                    f.write(f"Selected Emoji Pattern: {emoji_pattern_to_save}\n\n")
                    f.write(conversation_text)
                
                # Take a screenshot after processing
                driver.save_screenshot(f"conversation_{i+1}_processed.png")
                logging.info(f"Processed conversation {i+1} successfully")
                
            except Exception as e:
                logging.error(f"Error extracting conversation text: {e}")
                
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
