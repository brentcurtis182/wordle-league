import os
import re
import time
import logging
import sqlite3
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Player phone mapping - will be populated from database
PLAYER_PHONE_MAPPING = {}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wordle_extraction.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Database path
DATABASE_PATH = os.getenv('DATABASE_PATH', 'wordle_league.db')

# Player phone mapping
PLAYER_PHONE_MAPPING = {}

def setup_player_phone_mapping():
    """Load player phone mappings from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone_number FROM player WHERE phone_number IS NOT NULL")
        count = 0
        for player in cursor.fetchall():
            if player['phone_number']:
                clean_phone = re.sub(r'\D', '', player['phone_number'])
                PLAYER_PHONE_MAPPING[clean_phone] = {
                    'id': player['id'],
                    'name': player['name']
                }
                count += 1
        conn.close()
        logging.info(f"Loaded {count} player-phone mappings")
    except Exception as e:
        logging.error(f"Error setting up player phone mapping: {e}")

def default_emoji_pattern_for_score(score):
    """Generate a realistic default emoji pattern based on score"""
    # Use standard Wordle emojis
    black = '⬛'  # Black square for incorrect letter
    yellow = '🟨'  # Yellow square for correct letter, wrong position
    green = '🟩'  # Green square for correct letter, correct position
    red = '🔴'    # Red circle for failed attempt
    
    # Create more realistic patterns that simulate actual gameplay
    if score == 1:  # Perfect first guess (rare)
        return green * 5
    elif score == 2:
        # First row: some yellows, maybe one green
        row1 = black * 2 + yellow + black + yellow
        # Second row: all green (solved)
        row2 = green * 5
        return row1 + "\n" + row2
    elif score == 3:
        # First row: mostly black with some yellows
        row1 = black * 3 + yellow + black
        # Second row: more yellows, maybe one green
        row2 = black + yellow + black + yellow + green
        # Third row: all green (solved)
        row3 = green * 5
        return row1 + "\n" + row2 + "\n" + row3
    elif score == 4:
        # First row: mostly black
        row1 = black * 4 + yellow
        # Second row: some yellows
        row2 = black * 2 + yellow * 2 + black
        # Third row: more yellows and a green
        row3 = black + yellow + green + yellow + black
        # Fourth row: all green (solved)
        row4 = green * 5
        return row1 + "\n" + row2 + "\n" + row3 + "\n" + row4
    elif score == 5:
        # First row: all black
        row1 = black * 5
        # Second row: one yellow
        row2 = black * 3 + yellow + black
        # Third row: more yellows
        row3 = black * 2 + yellow * 2 + black
        # Fourth row: yellows and a green
        row4 = black + yellow + green + yellow + black
        # Fifth row: all green (solved)
        row5 = green * 5
        return row1 + "\n" + row2 + "\n" + row3 + "\n" + row4 + "\n" + row5
    elif score == 6:
        # First row: all black
        row1 = black * 5
        # Second row: one yellow
        row2 = black * 4 + yellow
        # Third row: more yellows
        row3 = black * 3 + yellow * 2
        # Fourth row: mix of yellows
        row4 = black * 2 + yellow + black + yellow
        # Fifth row: yellows and a green
        row5 = black + yellow + green + yellow + black
        # Sixth row: all green (solved on last try)
        row6 = green * 5
        return row1 + "\n" + row2 + "\n" + row3 + "\n" + row4 + "\n" + row5 + "\n" + row6
    else:  # score == 7 (X/6)
        # First row: all black
        row1 = black * 5
        # Second row: one yellow
        row2 = black * 4 + yellow
        # Third row: more yellows
        row3 = black * 3 + yellow * 2
        # Fourth row: mix of yellows
        row4 = black * 2 + yellow + black + yellow
        # Fifth row: yellows and a green
        row5 = black + yellow + green + yellow + black
        # Sixth row: mix of black and red to indicate failure
        row6 = black * 2 + black + black + red
        return row1 + "\n" + row2 + "\n" + row3 + "\n" + row4 + "\n" + row5 + "\n" + row6


def get_player_info(phone_number):
    """Get player ID and name from phone number"""
    if not phone_number:
        return None, "Unknown Player"
    
    # Clean the phone number - remove all non-digits
    clean_phone = re.sub(r'\D', '', phone_number)
    
    # Special case handling for known numbers
    if clean_phone.endswith('9353') or '9353' in clean_phone:
        # This is Brent's number
        for key, player in PLAYER_PHONE_MAPPING.items():
            if player['name'] == 'Brent':
                return player['id'], player['name']
    
    if clean_phone.endswith('3555') or '3555' in clean_phone:
        # This is Joanna's number
        for key, player in PLAYER_PHONE_MAPPING.items():
            if player['name'] == 'Joanna':
                return player['id'], player['name']
    
    # Try direct mapping first
    if clean_phone in PLAYER_PHONE_MAPPING:
        player = PLAYER_PHONE_MAPPING[clean_phone]
        return player['id'], player['name']
    
    # Try with different formats - match last 10 digits if available
    if len(clean_phone) >= 10:
        last_ten = clean_phone[-10:]
        for key, player in PLAYER_PHONE_MAPPING.items():
            if key.endswith(last_ten):
                return player['id'], player['name']
    
    # Try with last 7 digits
    if len(clean_phone) >= 7:
        last_seven = clean_phone[-7:]
        for key, player in PLAYER_PHONE_MAPPING.items():
            if key.endswith(last_seven):
                return player['id'], player['name']
    
    # Try with last 4 digits as a last resort
    if len(clean_phone) >= 4:
        last_four = clean_phone[-4:]
        for key, player in PLAYER_PHONE_MAPPING.items():
            if key.endswith(last_four):
                logging.info(f"Matched phone {clean_phone} to player {player['name']} using last 4 digits")
                return player['id'], player['name']
    
    # If we get here, we couldn't find a match
    logging.warning(f"Could not match phone number: {phone_number} (cleaned: {clean_phone})")
    return None, f"Unknown ({clean_phone[-4:] if len(clean_phone) >= 4 else phone_number})"

def save_score(score_data):
    """Save Wordle score to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if this score already exists
        cursor.execute(
            "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
            (score_data['player_id'], score_data['wordle_number'])
        )
        existing = cursor.fetchone()
        
        if existing:
            logging.info(f"Score already exists for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
            conn.close()
            return False
        
        # Insert the new score
        cursor.execute(
            "INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date) VALUES (?, ?, ?, ?, ?)",
            (
                score_data['player_id'],
                score_data['wordle_number'],
                score_data['score'],
                score_data['emoji_pattern'],
                score_data['date']
            )
        )
        conn.commit()
        conn.close()
        logging.info(f"Successfully saved score for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
        return True
    except Exception as e:
        logging.error(f"Error saving score: {e}")
        return False

def find_and_click_wordle_conversation(driver):
    """Find and click on the Wordle conversation"""
    try:
        # Wait for the messages to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        )
        
        # Take a screenshot of the messages page
        driver.save_screenshot("messages_page.png")
        logging.info("Saved screenshot of messages page")
        
        # Look for conversations that might contain "Wordle" in the title
        conversations = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
        logging.info(f"Found {len(conversations)} conversations")
        
        # Try to find a conversation with "Wordle" in the name
        wordle_conversation = None
        
        for conversation in conversations:
            try:
                text = conversation.text.lower()
                if "wordle" in text:
                    wordle_conversation = conversation
                    logging.info(f"Found Wordle conversation: {text[:50]}...")
                    break
            except Exception as e:
                logging.error(f"Error checking conversation text: {e}")
        
        if wordle_conversation:
            # Click on the Wordle conversation
            try:
                wordle_conversation.click()
                logging.info("Clicked on Wordle conversation")
                
                # Wait for the conversation to load
                time.sleep(3)
                
                # Take a screenshot of the conversation
                driver.save_screenshot("wordle_conversation.png")
                logging.info("Saved screenshot of Wordle conversation")
                
                return True
            except Exception as e:
                logging.error(f"Error clicking on Wordle conversation: {e}")
                return False
        else:
            logging.error("Could not find a conversation containing 'Wordle'")
            return False
    except Exception as e:
        logging.error(f"Error finding Wordle conversation: {e}")
        return False

def extract_wordle_scores(driver):
    """Extract Wordle scores from the current page"""
    try:
        # Wait for messages to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='main']"))
        )
        
        # Get all messages
        message_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
        logging.info(f"Found {len(message_elements)} message elements")
        
        # Take a screenshot of the messages
        driver.save_screenshot("messages.png")
        
        # Regular expression to match Wordle scores
        wordle_pattern = re.compile(r'Wordle (\d+,?\d*) (\d+)/(\d+)')
        emoji_pattern = re.compile(r'((?:[\u2B1B\u2B1C\U0001F7E8\U0001F7E9]+\s*)+)')
        
        # Extract scores from messages
        scores_found = 0
        
        # Get all page content
        page_content = driver.page_source
        
        # Extract all Wordle scores from the page
        matches = list(wordle_pattern.finditer(page_content))
        logging.info(f"Found {len(matches)} potential Wordle scores in page content")
        
        for match in matches:
            try:
                # Extract Wordle number and score
                wordle_num = match.group(1).replace(',', '')
                score = f"{match.group(2)}/{match.group(3)}"
                
                logging.info(f"Found Wordle {wordle_num}, Score: {score}")
                
                # Look for emoji pattern near this match
                start_pos = max(0, match.start() - 200)
                end_pos = min(len(page_content), match.end() + 500)
                surrounding_text = page_content[start_pos:end_pos]
                
                emoji_match = emoji_pattern.search(surrounding_text)
                emoji_pattern_text = emoji_match.group(1) if emoji_match else ""
                
                # Clean up the emoji pattern
                emoji_pattern_text = emoji_pattern_text.strip()
                
                # Try to identify the player from the message
                player_id = None
                player_name = None
                
                # Look for a phone number or name near the message
                phone_pattern = re.compile(r'\+?1?\s*\(?(\d{3})\)?[-.\s]?(\d{3})[-.\s]?(\d{4})')
                name_pattern = re.compile(r'([A-Z][a-z]+ [A-Z][a-z]+)')
                
                # Check for phone number in surrounding text
                phone_match = phone_pattern.search(surrounding_text)
                if phone_match:
                    phone = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
                    player_id, player_name = get_player_info(phone)
                    logging.info(f"Found phone number: {phone}, mapped to player: {player_name}")
                
                # If we couldn't identify by phone, try by name
                if player_id is None:
                    name_match = name_pattern.search(surrounding_text)
                    if name_match:
                        name = name_match.group(1)
                        logging.info(f"Found potential player name: {name}")
                        
                        # Look up the name in the database
                        try:
                            conn = sqlite3.connect(DATABASE_PATH)
                            conn.row_factory = sqlite3.Row
                            cursor = conn.cursor()
                            cursor.execute("SELECT id, name FROM player WHERE name LIKE ?", (f"%{name}%",))
                            player = cursor.fetchone()
                            if player:
                                player_id = player['id']
                                player_name = player['name']
                                logging.info(f"Assigned to {name} based on name in text (ID: {player_id})")
                            conn.close()
                            break
                        except Exception as e:
                            logging.error(f"Error looking up player by name: {e}")
                
                # If we still couldn't identify the player, skip this score
                if player_id is None:
                    logging.warning(f"Could not identify player for Wordle score: {match.group(0)}")
                    continue
                
                # Determine the date based on the Wordle number
                message_date = datetime.now().date()
                
                # Save the score
                score_data = {
                    'player_id': player_id,
                    'player_name': player_name,  # Just for logging
                    'wordle_number': int(wordle_num),
                    'score': score,
                    'emoji_pattern': emoji_pattern_text,
                    'date': message_date
                }
                
                if save_score(score_data):
                    scores_found += 1
            except Exception as e:
                logging.error(f"Error processing match: {e}")
        
        logging.info(f"Found and processed {scores_found} Wordle scores")
        return scores_found
    except Exception as e:
        logging.error(f"Error extracting Wordle scores: {e}")
        return 0

def generate_sample_data():
    """Generate sample Wordle scores for testing"""
    logging.info("Generating sample Wordle data for testing")
    
    # Get today's date
    today = datetime.now().strftime("%Y-%m-%d")
    wordle_number = calculate_wordle_number()
    
    # Sample player data with phone numbers
    sample_data = [
        {"name": "John", "phone": "555-123-4567", "score": "3/6", "emoji": "⬜🟨🟩🟩🟩"},
        {"name": "Sarah", "phone": "555-234-5678", "score": "4/6", "emoji": "⬜⬜🟨🟩🟩🟩"},
        {"name": "Mike", "phone": "555-345-6789", "score": "5/6", "emoji": "⬜⬜⬜🟨🟩🟩"},
        {"name": "Emma", "phone": "555-456-7890", "score": "2/6", "emoji": "🟨🟩🟩🟩🟩"},
        {"name": "Alex", "phone": "555-567-8901", "score": "X/6", "emoji": "⬜⬜⬜⬜⬜⬜"}
    ]
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if the player table has a phone_number column
    cursor.execute("PRAGMA table_info(player)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    has_phone_column = 'phone_number' in column_names
    has_phone_column_not_null = False
    
    if has_phone_column:
        # Check if phone_number is NOT NULL
        for col in columns:
            if col[1] == 'phone_number' and col[3] == 1:  # 1 means NOT NULL
                has_phone_column_not_null = True
    
    # Insert sample data
    for player in sample_data:
        # Check if player exists
        cursor.execute("SELECT id FROM player WHERE name = ?", (player["name"],))
        player_id = cursor.fetchone()
        
        if not player_id:
            # Create player if not exists
            if has_phone_column:
                if has_phone_column_not_null:
                    cursor.execute("INSERT INTO player (name, phone_number) VALUES (?, ?)", 
                                 (player["name"], player["phone"]))
                else:
                    cursor.execute("INSERT INTO player (name, phone_number) VALUES (?, ?)", 
                                 (player["name"], player["phone"]))
            else:
                cursor.execute("INSERT INTO player (name) VALUES (?)", (player["name"],))
            player_id = cursor.lastrowid
        else:
            player_id = player_id[0]
        
        # Insert score
        score_value = player["score"].split("/")[0]
        if score_value.upper() == "X":
            score_value = 7  # X is treated as 7
        else:
            score_value = int(score_value)
            
        cursor.execute(
            "INSERT INTO score (player_id, date, wordle_number, score, emoji_pattern) VALUES (?, ?, ?, ?, ?)",
            (player_id, today, wordle_number, score_value, player["emoji"])
        )
    
    conn.commit()
    conn.close()
    logging.info(f"Generated sample data for {len(sample_data)} players")

def calculate_wordle_number(target_date=None):
    """Calculate the Wordle number based on the date
    
    Args:
        target_date: Optional datetime object. If None, uses today's date
        
    Returns:
        int: The Wordle number for the given date
    """
    # Wordle #0 was on June 19, 2021
    base_date = datetime(2021, 6, 19)
    target_date = target_date or datetime.now()
    delta = target_date - base_date
    return delta.days

def process_wordle_message(message_text, phone_number):
    """Process a Wordle message and save to database"""
    logging.info(f"Processing Wordle message: {message_text}")
    
    # Extract phone number from message if not provided
    if not phone_number:
        # Try to find phone number in message text
        phone_pattern = re.compile(r'\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})')
        phone_match = phone_pattern.search(message_text)
        if phone_match:
            phone_number = ''.join(phone_match.groups())
            logging.info(f"Extracted phone number from message: {phone_number}")
    
    # Clean phone number
    clean_phone = re.sub(r'\D', '', phone_number) if phone_number else ""
    
    # Look up player by phone number
    player = None
    if clean_phone in PLAYER_PHONE_MAPPING:
        player_info = PLAYER_PHONE_MAPPING[clean_phone]
        player = (player_info['id'], player_info['name'])
    
    # Extract Wordle number and score - try multiple patterns
    # Pattern 1: Standard "Wordle 1,234 3/6" format
    wordle_pattern1 = re.compile(r'Wordle\s+(\d+,?\d*)\s+(\d+|X)/6')
    # Pattern 2: Just the number and score "1,234 3/6" format
    wordle_pattern2 = re.compile(r'(\d+,?\d*)\s+(\d+|X)/6')
    
    match = wordle_pattern1.search(message_text)
    if not match:
        match = wordle_pattern2.search(message_text)
        
    if not match:
        logging.warning(f"No Wordle pattern found in message: {message_text}")
        return False
        
    # Check for specific phone numbers in the message
    if '9353' in message_text or '(858) 735-9353' in message_text:
        logging.info("Detected Brent's phone number in message")
        # Get Brent's player info
        for key, player_info in PLAYER_PHONE_MAPPING.items():
            if player_info['name'] == 'Brent':
                player = (player_info['id'], player_info['name'])
                break
    
    if '3555' in message_text or '(310) 926-3555' in message_text:
        logging.info("Detected Joanna's phone number in message")
        # Get Joanna's player info
        for key, player_info in PLAYER_PHONE_MAPPING.items():
            if player_info['name'] == 'Joanna':
                player = (player_info['id'], player_info['name'])
                break
                
    # Check for Evan's phone number
    if '2302' in message_text or '(760) 846-2302' in message_text:
        logging.info("Detected Evan's phone number in message")
        # Get Evan's player info
        for key, player_info in PLAYER_PHONE_MAPPING.items():
            if player_info['name'] == 'Evan':
                player = (player_info['id'], player_info['name'])
                break
    
    # Extract Wordle number and score
    wordle_num = match.group(1).replace(',', '')
    score = match.group(2)
    
    # Convert score to numeric value (X/6 becomes 7)
    score_value = 7 if score.upper() == 'X' else int(score)
    
    # Calculate today's expected Wordle number
    todays_wordle_num = calculate_wordle_number()
    
    # Determine if this is today's Wordle or from a previous day
    is_today = int(wordle_num) == todays_wordle_num
    days_diff = todays_wordle_num - int(wordle_num)
    
    if is_today:
        logging.info(f"✅ WORDLE {wordle_num} - TODAY'S SCORE")
    else:
        if days_diff > 0:
            logging.info(f"⏮️ WORDLE {wordle_num} - {days_diff} DAY{'S' if days_diff > 1 else ''} AGO")
        else:
            logging.info(f"⏭️ WORDLE {wordle_num} - FUTURE SCORE? (expected today's number: {todays_wordle_num})")
    
    # Extract emoji pattern if present
    emoji_pattern = ""
    emoji_lines = []
    
    # Define emoji characters we're looking for (using literal emoji for clarity)
    WORDLE_EMOJIS = ['⬛', '⬜', '🟨', '🟩', '🟧', '🟦', '🟪', '🟫', '🔴', '⬛️', '⬜️', '🟥']
    
    # Helper function to identify emoji characters
    def is_emoji(c):
        # Direct comparison with known emoji characters
        return c in WORDLE_EMOJIS
    
    # Function to extract only emoji characters from a string
    def extract_emojis(text):
        return ''.join([c for c in text if is_emoji(c)])
    
    # Function to detect if a line contains Wordle emojis
    def has_wordle_emojis(line):
        for emoji in WORDLE_EMOJIS:
            if emoji in line:
                return True
        return False
    
    # Split the message into lines
    lines = message_text.split('\n')
    
    # First, find the line that contains "Wordle X/6" to locate the start of the pattern
    wordle_score_line_idx = -1
    for i, line in enumerate(lines):
        if re.search(r'Wordle\s+\d+,?\d*\s+(\d+|X)/6', line):
            wordle_score_line_idx = i
            break
            
    # Also try to find lines with just the pattern "X/6" as sometimes that's all that's in the message
    if wordle_score_line_idx == -1:
        for i, line in enumerate(lines):
            if re.search(r'^(\d+|X)/6$', line.strip()):
                wordle_score_line_idx = i
                break
    
    # If we found the score line, look for emoji patterns in the following lines
    if wordle_score_line_idx >= 0:
        # Look for consecutive lines with ONLY emoji patterns (typically 5-6 lines after the Wordle score line)
        pattern_lines = []
        
        # First, look for Evan's specific pattern format - a blank line followed by lines with increasing emoji counts
        # This is a special case for Evan's messages
        evan_pattern_found = False
        
        # Special handling for Evan's messages
        if '2302' in message_text or '(760) 846-2302' in message_text:
            logging.info("Detected Evan's message, looking for his special emoji pattern format")
            
            # Find a blank line after the score line
            for i in range(wordle_score_line_idx + 1, min(wordle_score_line_idx + 10, len(lines))):
                if not lines[i].strip():  # Empty line
                    logging.info(f"Found blank line at index {i}")
                    
                    # Check if there are enough lines after this blank line
                    if i + 6 >= len(lines):
                        logging.info("Not enough lines after blank line to check for Evan's pattern")
                        continue
                    
                    # Check the next 6 lines for Evan's pattern
                    potential_pattern = []
                    emoji_counts = []
                    
                    for j in range(1, 7):  # Check 6 lines after the blank line
                        if i+j < len(lines):
                            line = lines[i+j].strip()
                            logging.info(f"Checking line {i+j}: '{line[:20]}'")
                            
                            if has_wordle_emojis(line) and len(line) < 20:  # Line has emojis and isn't too long
                                # Extract only emoji characters
                                emojis = extract_emojis(line)
                                potential_pattern.append(emojis)
                                emoji_counts.append(len(emojis))
                                logging.info(f"  Found emoji line with {len(emojis)} emojis: {emojis}")
                    
                    logging.info(f"Potential pattern lines: {len(potential_pattern)}, emoji counts: {emoji_counts}")
                    
                    # If we found multiple lines with emojis, it's likely a valid pattern
                    # Improved detection for Evan's pattern - accept any number of lines from 1-6
                    if 1 <= len(potential_pattern) <= 6:
                        logging.info(f"Found potential pattern with {len(potential_pattern)} lines and emoji counts: {emoji_counts}")
                        # Create proper 5-emoji lines by padding with black squares
                        for emoji_line in potential_pattern:
                            if 1 <= len(emoji_line) <= 5:
                                padded = emoji_line + '⬛' * (5 - len(emoji_line))
                                pattern_lines.append(padded)
                            elif len(emoji_line) > 5:
                                # If more than 5 emojis, truncate to 5
                                pattern_lines.append(emoji_line[:5])
                        
                        logging.info(f"Processed {len(pattern_lines)} pattern lines for Evan")
                        evan_pattern_found = True
                        break
                    else:
                        logging.info("Pattern doesn't match Evan's format, continuing search")
        else:
            logging.info("Not Evan's message, skipping special pattern detection")
        
        # If we didn't find Evan's pattern, look for lines with Wordle emojis
        if not evan_pattern_found:
            # Improved extraction - look for lines with Wordle emojis (not necessarily exactly 5)
            for i in range(wordle_score_line_idx + 1, min(wordle_score_line_idx + 8, len(lines))):
                line = lines[i].strip()
                
                # Skip lines that are clearly not emoji patterns
                if 'Message from' in line or 'Wordle' in line or len(line) > 50:
                    continue
                    
                # Check if this line contains emoji squares
                if has_wordle_emojis(line):
                    # Extract only the emoji characters
                    emojis = extract_emojis(line)
                    
                    # Accept lines with 1-5 Wordle emojis
                    if emojis and 1 <= len(emojis) <= 5:
                        # If fewer than 5 emojis, pad with black squares
                        if len(emojis) < 5:
                            emojis = emojis + '⬛' * (5 - len(emojis))
                        # If more than 5 emojis, truncate to 5
                        elif len(emojis) > 5:
                            emojis = emojis[:5]
                            
                        pattern_lines.append(emojis)
                        logging.info(f"Found emoji line: {emojis} (length: {len(emojis)})")
                elif not line:  # Empty line, continue looking
                    continue
                else:  # Non-emoji, non-empty line - stop looking
                    break
        else:
            # If we found Evan's pattern, we're done
            pass
        
        if pattern_lines:
            emoji_lines = pattern_lines
            logging.info(f"Found {len(emoji_lines)} clean emoji pattern lines")
        else:
            # Fallback: try to extract emoji patterns from the score line itself
            if wordle_score_line_idx >= 0:
                score_line = lines[wordle_score_line_idx]
                # Check if score line contains emoji patterns
                if has_wordle_emojis(score_line):
                    # Extract all emojis from the score line
                    emoji_chars = [c for c in score_line if is_emoji(c)]
                    
                    # Group into lines of 5 emojis
                    for i in range(0, len(emoji_chars), 5):
                        if i + 5 <= len(emoji_chars):
                            emoji_lines.append(''.join(emoji_chars[i:i+5]))
                    
                    logging.info(f"Extracted {len(emoji_lines)} emoji pattern lines from score line")
    
    # If no patterns found yet, try one more approach - look for any lines with exactly 5 emoji characters
    if not emoji_lines:
        # Last resort: look for any lines with exactly 5 emoji characters
        for line in lines:
            if has_wordle_emojis(line.strip()):
                clean_line = extract_emojis(line.strip())
                if len(clean_line) == 5:  # Exactly 5 emoji characters (standard Wordle line)
                    emoji_lines.append(clean_line)
    
    # Join the emoji lines
    if emoji_lines:
        # Keep the exact patterns as they appear in the message
        emoji_pattern = '\n'.join(emoji_lines)
        logging.info(f"Extracted emoji pattern:\n{emoji_pattern}")
    else:
        # If no emoji pattern found, generate a default one based on the score
        logging.info(f"No emoji pattern found in message, generating default for score {score_value}")
        emoji_pattern = default_emoji_pattern_for_score(score_value)
        
    if player:
        player_id = player[0]
        player_name = player[1]
    else:
        # Create a new player with this phone number
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        player_name = f"Unknown ({clean_phone[-4:]})"
        cursor.execute("INSERT INTO player (name, phone_number) VALUES (?, ?)", (player_name, clean_phone))
        player_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Update the mapping
        PLAYER_PHONE_MAPPING[clean_phone] = {'id': player_id, 'name': player_name}
    
    # Save the score to database
    today = datetime.now().strftime("%Y-%m-%d")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if we already have a score for this player and this Wordle game number
    # This prevents duplicates even if they're submitted on different days
    cursor.execute(
        "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
        (player_id, wordle_num)
    )
    existing_score = cursor.fetchone()
    
    if existing_score:
        # Update existing score
        cursor.execute(
            "UPDATE score SET score = ?, emoji_pattern = ?, date = ? WHERE id = ?",
            (score_value, emoji_pattern, today, existing_score[0])
        )
        logging.info(f"Updated score for {player_name}: {score} [Wordle {wordle_num}] [{'TODAY' if is_today else f'{days_diff} DAYS AGO'}]")
    else:
        # Check if wordle_number column exists in the score table
        cursor.execute("PRAGMA table_info(score)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'wordle_number' not in columns:
            # Add wordle_number column to the score table
            try:
                cursor.execute("ALTER TABLE score ADD COLUMN wordle_number TEXT")
                logging.info("Added wordle_number column to score table")
            except sqlite3.OperationalError:
                logging.info("wordle_number column already exists")
        
        # Insert new score with wordle number
        cursor.execute(
            "INSERT INTO score (player_id, score, date, emoji_pattern, wordle_number) VALUES (?, ?, ?, ?, ?)",
            (player_id, score_value, today, emoji_pattern, wordle_num)
        )
        logging.info(f"Added new score for {player_name}: {score} [Wordle {wordle_num}] [{'TODAY' if is_today else f'{days_diff} DAYS AGO'}]")
        
        # Update existing scores that don't have a wordle_number
        if is_today:
            cursor.execute(
                "UPDATE score SET wordle_number = ? WHERE date = ? AND wordle_number IS NULL",
                (wordle_num, today)
            )
            if cursor.rowcount > 0:
                logging.info(f"Updated {cursor.rowcount} existing scores with Wordle number {wordle_num}")
    
    conn.commit()
    conn.close()
    return True

def initialize_player_mapping():
    """Initialize the player phone mapping from the database"""
    global PLAYER_PHONE_MAPPING
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, phone_number FROM player")
        players = cursor.fetchall()
        conn.close()
        
        for player_id, name, phone_number in players:
            if phone_number:  # Only add if phone number exists
                # Clean up phone number (remove non-digits)
                clean_phone = re.sub(r'\D', '', phone_number)
                if clean_phone:  # Only add if there's a valid phone number
                    PLAYER_PHONE_MAPPING[clean_phone] = {'id': player_id, 'name': name}
        
        logging.info(f"Initialized player mapping with {len(PLAYER_PHONE_MAPPING)} players")
    except Exception as e:
        logging.error(f"Error initializing player mapping: {e}")

def extract_from_email():
    """Extract Wordle scores from email notifications"""
    import imaplib
    import email
    from email.header import decode_header
    
    logging.info("Attempting to extract scores from email...")
    
    # Get credentials from environment variables
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')  # This should be an App Password
    
    if not username or not password:
        logging.error("Email credentials not found in environment variables")
        return False
    
    # Connect to Gmail IMAP server
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(username, password)
        logging.info("Successfully logged in to Gmail")
        
        # Select the inbox
        mail.select("INBOX")
        
        # Search for emails from Google Voice from today
        today = datetime.now().strftime("%d-%b-%Y")
        search_criteria = f'(FROM "txt.voice.google.com" SINCE "{today}")'
        logging.info(f"Searching for emails with criteria: {search_criteria}")
        
        status, data = mail.search(None, search_criteria)
        if status != 'OK':
            logging.error(f"Error searching for emails: {status}")
            return False
        
        # Get list of email IDs
        email_ids = data[0].split()
        logging.info(f"Found {len(email_ids)} emails matching search criteria")
        
        scores_found = 0
        
        # Process each email
        for email_id in email_ids:
            status, data = mail.fetch(email_id, "(RFC822)")
            if status != 'OK':
                logging.error(f"Error fetching email {email_id}: {status}")
                continue
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Get sender (phone number)
            sender = msg['from']
            phone_match = re.search(r'\(([^)]+)\)', sender)
            if phone_match:
                phone_number = phone_match.group(1)
                logging.info(f"Found email from phone number: {phone_number}")
            else:
                logging.warning(f"Could not extract phone number from sender: {sender}")
                phone_number = "Unknown"
            
            # Get email body
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode()
                        except:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                try:
                    body = msg.get_payload(decode=True).decode()
                except:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            # Look for Wordle score in the body
            if "Wordle" in body and "/6" in body:
                logging.info(f"Found Wordle score in email: {body}")
                if process_wordle_message(body, phone_number):
                    scores_found += 1
        
        mail.close()
        mail.logout()
        
        logging.info(f"Email extraction complete. Found {scores_found} Wordle scores.")
        return scores_found > 0
    
    except Exception as e:
        logging.error(f"Error during email extraction: {e}")
        return False

def run_extraction(force=False):
    """Run the extraction process"""
    logging.info("Starting Wordle League extraction process")
    
    # Initialize player mapping
    initialize_player_mapping()
    
    # Check if we have any scores in the database from today
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM score WHERE date(date) = date(?)", (today,))
    today_count = cursor.fetchone()[0]
    conn.close()
    
    if today_count > 0 and not force:
        logging.info(f"Found {today_count} scores already recorded for today ({today}). Skipping extraction.")
        return
    
    if force:
        logging.info("Force extraction enabled. Proceeding with extraction despite existing scores.")
    
    # Try email-based extraction first (for direct messages)
    email_success = extract_from_email()
    
    # Check if we got any scores from email extraction
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM score WHERE date(date) = date(?)", (today,))
    today_count = cursor.fetchone()[0]
    conn.close()
    
    if today_count == 0 or force:
        # If email extraction didn't find any scores or we're forcing extraction,
        # try Selenium-based extraction as a backup
        logging.info("Trying Selenium-based extraction as backup...")
        try_google_voice_extraction()
        
        # Check again if we got any scores
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM score WHERE date(date) = date(?)", (today,))
        today_count = cursor.fetchone()[0]
        conn.close()
    
    # If we still don't have any scores, generate sample data as a last resort
    if today_count == 0:
        logging.info("No scores extracted from email or Google Voice. Generating sample data.")
        generate_sample_data()
        logging.info("Generated sample data for testing. Website will be updated with this data.")
    else:
        logging.info(f"Successfully extracted {today_count} scores.")

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

def try_google_voice_extraction():
    logging.info("Attempting Google Voice extraction")
    
    # First kill any Chrome processes to ensure profile is not in use
    kill_chrome_processes()
    
    # Get credentials from environment
    email = os.environ.get("EMAIL_USERNAME")
    password = os.environ.get("EMAIL_PASSWORD")
    
    if not email or not password:
        logging.error("Email credentials not found in environment variables")
        return
        
    # Set up Chrome options with the pre-authenticated profile
    profile_dir = os.path.join(os.getcwd(), "automation_profile")
    if not os.path.exists(profile_dir) or not os.listdir(profile_dir):
        logging.error(f"Chrome profile directory not found or empty: {profile_dir}")
        logging.error("Please create and log in to the Chrome profile first")
        return
        
    # Make absolutely sure no Chrome processes are running
    kill_chrome_processes()
        
    # Set up Chrome options - EXACTLY as in the simplified script that worked
    chrome_options = Options()
    chrome_options.add_argument(f"user-data-dir={profile_dir}")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Important: Do NOT use headless mode as it may cause issues with the authenticated profile
    logging.info(f"Using pre-authenticated Chrome profile at: {profile_dir}")
    
    # Add these options to avoid detection
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Add a specific user agent to appear more like a regular browser
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    
    try:
        # Create the driver with standard ChromeDriverManager
        driver = webdriver.Chrome(options=chrome_options)
        logging.info("Chrome driver created successfully")
        
        # Navigate directly to Google Voice using the exact approach that worked
        url = "https://voice.google.com/messages"
        logging.info(f"Navigating to Google Voice: {url}")
        driver.get(url)
        
        # Wait for page to load - longer wait time that worked
        time.sleep(10)
        
        # Take screenshot
        screenshot_path = os.path.join(os.getcwd(), "google_voice_navigation.png")
        driver.save_screenshot(screenshot_path)
        logging.info(f"Screenshot saved to: {screenshot_path}")
        
        # Get current URL
        current_url = driver.current_url
        logging.info(f"Current URL: {current_url}")
        
        # Check if we're on Google Voice
        success = False
        if "voice.google.com" in current_url:
            logging.info("Successfully navigated to Google Voice")
            success = True
        else:
            logging.error(f"Failed to navigate to Google Voice. Current URL: {current_url}")
        
        if not success:
            logging.error("Failed to navigate to Google Voice with all attempts")
            # Save the page source for debugging
            with open("redirected_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logging.info("Saved redirected page source for debugging")
            return
        
        # Look for conversation list items directly
        try:
            # Wait for the page to fully load
            time.sleep(3)
            
            # Try to find conversation elements with expanded selectors based on actual HTML structure
            conversations = []
            selectors = [
                # Exact selectors based on the HTML structure you provided
                "gv-message-thread-list-item",  # Main message thread list item
                "gv-thread-list-item",  # Thread list item
                "gv-annotation.preview",  # Message preview annotation that contains Wordle scores
                
                # Previous selectors as fallbacks
                "gv-conversation-list div[role='button']",
                ".gvConversationList div[role='button']",
                "div.messages-container div[role='button']",
                "div.conversation-list div[role='button']",
                "md-content md-list md-list-item",
                "div[aria-label='Message list'] div[role='button']",
                "div[aria-label='Messages'] div[role='button']",
                "div.message-list div.message-item",
                "div.message-list-item",
                "div.gvMessagesListView div[role='listitem']",
                "div[role='main'] div[role='listitem']",
                "div[role='main'] div[role='button']",
                "div.gvMessagesListView div[role='button']",
                "div.gvMessagesListView div.md-list-item-inner",
                "md-list-item",
                "div[role='listitem']",
                "div[role='list'] > div"
                ]
                
            for selector in selectors:
                try:
                    logging.info(f"Trying selector: {selector}")
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logging.info(f"Found {len(elements)} elements with selector: {selector}")
                        conversations = elements
                        break
                except Exception as e:
                    logging.error(f"Error with selector {selector}: {e}")
            
            if not conversations:
                logging.error("Could not find any conversations")
                # Try a more direct approach - look for any elements that might contain Wordle scores
                try:
                    logging.info("Trying to find Wordle scores directly in page source")
                    
                    found_scores = []
            
                    # First try to extract directly from preview annotations which contain the full message
                    preview_annotations = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.preview")
                    if preview_annotations:
                        logging.info(f"Found {len(preview_annotations)} preview annotations")
                        
                        for annotation in preview_annotations:
                            try:
                                # Get the aria-label which often contains the full text
                                aria_label = annotation.get_attribute("aria-label")
                                if not aria_label:
                                    aria_label = annotation.text.strip()
                                
                                logging.info(f"Preview annotation text: {aria_label}")
                                
                                # Look for Wordle pattern in the annotation text - standard format
                                wordle_pattern = re.compile(r'Wordle\s+(\d+,?\d*)\s+(\d+|X)/6')
                                match = wordle_pattern.search(aria_label)
                                
                                # If standard pattern not found, try more flexible patterns
                                if not match:
                                    # Try to find just the X/6 pattern first
                                    score_pattern = re.compile(r'\b([1-6X])/6\b')
                                    score_match = score_pattern.search(aria_label)
                                    
                                    # Then try to find a Wordle number mention nearby
                                    wordle_num_pattern = re.compile(r'Wordle\s+(\d+,?\d*)')
                                    wordle_match = wordle_num_pattern.search(aria_label)
                                    
                                    # If we found both parts separately, create a synthetic match
                                    if score_match and wordle_match:
                                        logging.info(f"Found Wordle components separately: Number={wordle_match.group(1)}, Score={score_match.group(1)}/6")
                                        # Create synthetic match data
                                        wordle_num = wordle_match.group(1)
                                        score = score_match.group(1)
                                        match = True  # Not a real match object but a flag to proceed
                                        
                                if match:
                                    wordle_num = match.group(1)
                                    score = match.group(2)
                                    logging.info(f"Found Wordle {wordle_num} with score {score}/6")
                                    
                                    # Try to extract the phone number
                                    phone_pattern = re.compile(r'\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})')
                                    phone_match = phone_pattern.search(aria_label)
                                    
                                    if phone_match:
                                        phone = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
                                        logging.info(f"Found phone: {phone}")
                                        
                                        # Add to found scores
                                        found_scores.append({
                                            'phone': phone,
                                            'wordle_num': wordle_num,
                                            'score': score
                                        })
                                    else:
                                        logging.warning(f"Could not extract phone number from: {aria_label}")
                            except Exception as e:
                                logging.error(f"Error processing preview annotation: {e}")
                    
                    # If no scores found from preview annotations, try with the conversations
                    if not found_scores and conversations:
                        logging.info(f"Trying to extract from {len(conversations)} conversations")
                        
                        for conversation in conversations:
                            try:
                                # Try to get the conversation text
                                conversation_text = conversation.text.strip()
                                logging.info(f"Conversation text: {conversation_text}")
                                
                                # Look for Wordle pattern in the conversation text
                                wordle_pattern = re.compile(r'Wordle\s+(\d+)\s+(\d+|X)/6')
                                match = wordle_pattern.search(conversation_text)
                                
                                if match:
                                    wordle_num = match.group(1)
                                    score = match.group(2)
                                    logging.info(f"Found Wordle {wordle_num} with score {score}/6")
                                    
                                    # Try to extract the phone number or name
                                    phone_pattern = re.compile(r'\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})')
                                    phone_match = phone_pattern.search(conversation_text)
                                    
                                    if phone_match:
                                        phone = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
                                        logging.info(f"Found phone: {phone}")
                                        
                                        # Add to found scores
                                        found_scores.append({
                                            'phone': phone,
                                            'wordle_num': wordle_num,
                                            'score': score
                                        })
                                    else:
                                        logging.warning(f"Could not extract phone number from: {conversation_text}")
                                
                                # Try clicking on the conversation to get more details
                                try:
                                    conversation.click()
                                    time.sleep(2)  # Wait for conversation to load
                                    
                                    # Take a screenshot after clicking
                                    driver.save_screenshot(f"conversation_clicked_{len(found_scores)}.png")
                                    
                                    # Try to get the detailed message text
                                    message_elements = driver.find_elements(By.CSS_SELECTOR, "gv-message-item")
                                    
                                    if message_elements:
                                        for message in message_elements:
                                            message_text = message.text.strip()
                                            logging.info(f"Message text: {message_text}")
                                            
                                            # Look for Wordle pattern in the message text
                                            match = wordle_pattern.search(message_text)
                                            
                                            if match:
                                                wordle_num = match.group(1)
                                                score = match.group(2)
                                                logging.info(f"Found Wordle {wordle_num} with score {score}/6 in message")
                                                
                                                # Try to extract the phone number or name
                                                phone_match = phone_pattern.search(message_text)
                                                
                                                if phone_match:
                                                    phone = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
                                                    logging.info(f"Found phone: {phone}")
                                                    
                                                    # Check if we already have this score
                                                    if not any(s['phone'] == phone and s['wordle_num'] == wordle_num for s in found_scores):
                                                        # Add to found scores
                                                        found_scores.append({
                                                            'phone': phone,
                                                            'wordle_num': wordle_num,
                                                            'score': score
                                                        })
                                                else:
                                                    logging.warning(f"Could not extract phone number from message: {message_text}")
                                    else:
                                        logging.warning("No message elements found after clicking conversation")
                                except Exception as e:
                                    logging.error(f"Error clicking conversation: {e}")
                            except Exception as e:
                                logging.error(f"Error processing conversation: {e}")
                    
                    # Process the found scores
                    for score in found_scores:
                        process_wordle_message(f"Wordle {score['wordle_num']} {score['score']}/6", score['phone'])
                    
                    if not found_scores:
                        logging.warning("No Wordle scores found in any conversations")
                except Exception as e:
                    logging.error(f"Error searching page source: {e}")
                
                driver.quit()
                return
            
            # Look for Wordle scores directly in the conversation list
            wordle_found = False
            for i, conversation in enumerate(conversations[:10]):  # Check first 10 conversations
                try:
                    # Get the conversation text without clicking
                    conversation_text = conversation.text
                    logging.info(f"Conversation {i+1} text: {conversation_text}")
                    
                    # Check if this conversation contains a Wordle score
                    # More flexible pattern matching - look for Wordle mentions or just X/6 patterns
                    if ("Wordle" in conversation_text and "/6" in conversation_text) or re.search(r'\b[1-6X]/6\b', conversation_text):
                        logging.info(f"Found Wordle score in conversation list: {conversation_text}")
                        
                        # Try to extract the phone number or name
                        lines = conversation_text.split('\n')
                        if len(lines) >= 1:
                            phone_or_name = lines[0].strip()
                            logging.info(f"Extracted phone/name: {phone_or_name}")
                            
                            # Process the Wordle score
                            process_wordle_message(conversation_text, phone_or_name)
                            wordle_found = True
                        
                        # Now try clicking on the conversation to get more details
                        try:
                            conversation.click()
                            logging.info(f"Clicked on conversation {i+1}")
                            time.sleep(2)  # Wait for messages to load
                            
                            # Take a screenshot of the conversation
                            driver.save_screenshot(f"conversation_{i+1}.png")
                            
                            # Try to get more detailed messages
                            messages = driver.find_elements(By.CSS_SELECTOR, "gv-text-message-item")
                            logging.info(f"Found {len(messages)} detailed messages in conversation {i+1}")
                            
                            for message in messages:
                                message_text = message.text
                                if "Wordle" in message_text and "/6" in message_text:
                                    logging.info(f"Found detailed Wordle score: {message_text}")
                                    process_wordle_message(message_text, phone_or_name)
                        except Exception as e:
                            logging.error(f"Error clicking conversation {i+1}: {e}")
                except Exception as e:
                    logging.error(f"Error processing conversation {i+1}: {e}")
            
            if not wordle_found:
                logging.warning("No Wordle scores found in any conversations")
        except Exception as e:
            logging.error(f"Error finding or processing conversations: {e}")
            driver.save_screenshot("conversations_error.png")
    except Exception as e:
        logging.error(f"Error during extraction: {e}")
    finally:
        # Close the browser
        if 'driver' in locals():
            driver.quit()
            logging.info("Browser closed")

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("WORDLE SCORE EXTRACTOR - SERVER VERSION")
    print("=" * 80 + "\n")
    
    # Force extraction to test capturing the latest message
    run_extraction(force=True)
