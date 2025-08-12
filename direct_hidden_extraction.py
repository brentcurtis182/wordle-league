#!/usr/bin/env python3
"""
Direct Hidden Element Score Extraction

This script provides a focused extraction function that specifically targets the
.cdk-visually-hidden elements in Google Voice conversations to reliably extract
complete Wordle score data, including phone numbers, scores, and emoji patterns.
"""

import re
import logging
import sqlite3
from datetime import datetime
from selenium.webdriver.common.by import By

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def extract_hidden_scores(driver, today_wordle, yesterday_wordle, league_id=1, league_name="Wordle Warriorz"):
    """
    Extract scores from hidden elements in Google Voice conversations
    
    This function specifically targets the .cdk-visually-hidden elements that contain
    complete score data in a consistent format.
    """
    logging.info(f"Extracting hidden scores for {league_name} (league_id: {league_id})")
    logging.info(f"Looking for Wordle #{today_wordle} and #{yesterday_wordle}")
    
    # Get all hidden elements
    hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
    logging.info(f"Found {len(hidden_elements)} hidden elements")
    
    # Save DOM for debugging if needed
    with open(f"dom_captures/hidden_elements_{league_id}.txt", 'w', encoding='utf-8') as f:
        for i, el in enumerate(hidden_elements):
            try:
                text = el.get_attribute("textContent").strip()
                f.write(f"Element {i+1}:\n{text}\n{'='*40}\n")
            except:
                f.write(f"Element {i+1}: [Error retrieving text]\n{'='*40}\n")
    
    # Regex patterns
    wordle_pattern = re.compile(r'Wordle\s+(?:#)?(\d[\d,]*)\s+(\d|X)/6', re.IGNORECASE)
    # Updated pattern to capture both phone numbers and text identifiers like "Dinkbeach"
    phone_pattern = re.compile(r'Message from\s+([^,]+?),', re.IGNORECASE)
    
    scores_found = 0
    saved_scores = 0
    
    for el in hidden_elements:
        try:
            # Get the complete text content
            text = el.get_attribute("textContent").strip()
            if not text or "Wordle" not in text:
                continue
                
            logging.info(f"Processing hidden element: {text[:100]}...")
            
            # Extract Wordle number and score
            wordle_match = wordle_pattern.search(text)
            if not wordle_match:
                logging.info(f"No Wordle match in: {text[:50]}...")
                continue
                
            # Get Wordle number (remove commas)
            wordle_num_str = wordle_match.group(1).replace(',', '')
            try:
                wordle_num = int(wordle_num_str)
                logging.info(f"Found Wordle #{wordle_num}")
            except ValueError:
                logging.warning(f"Invalid Wordle number: {wordle_match.group(1)}")
                continue
                
            # Get score
            score_str = wordle_match.group(2)
            score = 7 if score_str == 'X' else int(score_str)
            logging.info(f"Found score: {score_str}/6")
            
            # STRICT MODE: Only allow today's Wordle
            is_relevant = False
            if wordle_num == today_wordle:
                logging.info(f"This is today's Wordle #{today_wordle} - ALLOWING")
                is_relevant = True
            else:
                logging.info(f"Wordle #{wordle_num} is not today's Wordle #{today_wordle} - REJECTING")
                is_relevant = False
                    
            if not is_relevant:
                logging.info(f"Skipping irrelevant Wordle #{wordle_num}")
                continue
                
            # Check if this is a reaction to a message rather than a submission
            reaction_patterns = ['Emphasized', 'Loved', 'Liked', 'Laughed at', 'Reacted to']
            is_reaction = False
            
            for pattern in reaction_patterns:
                if pattern in text:
                    logging.info(f"SKIPPING: This is a {pattern} reaction, not a submission")
                    is_reaction = True
                    break
                    
            if is_reaction:
                logging.info("Skipping message reaction")
                continue
                
            # Extract phone number or identifier
            phone = None
            phone_match = phone_pattern.search(text)
            if phone_match:
                # Get the original matched text (could be digits or a name like "Dinkbeach")
                original_match = phone_match.group(1).strip()
                logging.info(f"Found message from: {original_match}")
                
                # Extract digits if it's a phone number
                phone_digits = re.sub(r'\D', '', original_match)
                
                # Decide if we have a phone number or a text identifier
                if len(phone_digits) >= 10:  # It's likely a phone number
                    if len(phone_digits) == 10:
                        phone = '1' + phone_digits  # Add leading 1 for US numbers
                    elif len(phone_digits) == 11 and phone_digits.startswith('1'):
                        phone = phone_digits
                    else:
                        phone = phone_digits  # Use as-is for unusual formats
                    logging.info(f"Identified as phone number: {phone}")
                else:
                    # It's likely a text identifier like "Dinkbeach"
                    phone = original_match
                    logging.info(f"Identified as text identifier: {phone}")
            else:
                logging.warning("No message sender found in hidden element")
                continue
                
            # Extract emoji pattern - each line that contains emoji characters
            emoji_chars = ['🟩', '🟨', '⬛', '⬜', '⬜']
            lines = text.split('\n')
            emoji_lines = []
            
            for line in lines:
                # Line must contain at least one emoji character
                if any(emoji in line for emoji in emoji_chars):
                    # First split by comma to handle cases like "🟩🟩🟩🟩🟩, Saturday, August 2 2025"
                    cleaned_line = line.split(',')[0].strip()
                    
                    # Now handle cases where text is appended without a comma like "🟩🟩🟩🟩🟩boom"
                    # Extract just the emoji part by finding the longest prefix that contains only emojis and spaces
                    emoji_only = ''
                    for char in cleaned_line:
                        if char in '🟩🟨⬛⬜ ':
                            emoji_only += char
                        else:
                            # Stop once we hit a non-emoji character
                            break
                    
                    # If we extracted a valid emoji pattern, add it
                    if emoji_only and any(emoji in emoji_only for emoji in emoji_chars):
                        logging.info(f"Extracted emoji pattern: {emoji_only} from line: {line[:30]}...")
                        emoji_lines.append(emoji_only.strip())
            
            if emoji_lines:
                emoji_pattern = '\n'.join(emoji_lines)
                logging.info(f"Found emoji pattern with {len(emoji_lines)} lines")
            else:
                emoji_pattern = None
                logging.info("No emoji pattern found")
                
            # Map phone to player using existing function
            try:
                from integrated_auto_update_multi_league import get_player_by_phone_for_league
                player = get_player_by_phone_for_league(phone, league_id)
                
                # Try alternative phone formats if needed
                if not player:
                    if phone.startswith('1') and len(phone) == 11:
                        alt_phone = phone[1:]
                        player = get_player_by_phone_for_league(alt_phone, league_id)
                    elif len(phone) == 10:
                        alt_phone = '1' + phone
                        player = get_player_by_phone_for_league(alt_phone, league_id)
                        
                if not player:
                    logging.warning(f"Could not map phone {phone} to player in league {league_id}")
                    continue
                    
                logging.info(f"Mapped to player: {player}")
                
                # Save the score using existing function
                from save_score_functions import save_score_to_db
                result = save_score_to_db(player, wordle_num, score, emoji_pattern, league_id)
                
                logging.info(f"Save result: {result}")
                if result in ('new', 'updated'):
                    saved_scores += 1
                
                scores_found += 1
                    
            except ImportError as e:
                logging.error(f"Import error: {e}")
                continue
            except Exception as e:
                logging.error(f"Error processing score: {e}")
                continue
                
        except Exception as e:
            logging.error(f"Error processing element: {e}")
            continue
            
    logging.info(f"Extracted {scores_found} scores, saved {saved_scores} to database")
    return scores_found

# Function to get today's Wordle number based on reference date
def get_todays_wordle_number():
    """Calculate today's Wordle number based on reference date"""
    # Wordle #1503 = July 31, 2025
    ref_date = datetime(2025, 7, 31).date()
    ref_wordle = 1503
    today = datetime.now().date()
    days_since_ref = (today - ref_date).days
    todays_wordle = ref_wordle + days_since_ref
    return todays_wordle

# For integration with existing extraction process
def extract_with_hidden_elements(driver, league_id, league_name):
    """Wrapper function for integration with existing extraction system"""
    today_wordle = get_todays_wordle_number()
    yesterday_wordle = today_wordle - 1
    
    logging.info(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
    
    return extract_hidden_scores(driver, today_wordle, yesterday_wordle, league_id, league_name)

# Function to integrate this into the main extraction script
def update_main_extraction_script():
    """Add the hidden element extraction to the main script"""
    main_script = 'integrated_auto_update_multi_league.py'
    import_code = "\n# Import hidden element extraction function\nfrom direct_hidden_extraction import extract_with_hidden_elements\n"
    
    with open(main_script, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "from direct_hidden_extraction import" not in content:
        # Find the first imports block
        import_pos = content.find("import os")
        if import_pos >= 0:
            updated_content = content[:import_pos + len("import os\n")] + import_code + content[import_pos + len("import os\n"):]
            
            # Create backup
            import shutil
            backup_path = f"{main_script}.bak"
            shutil.copy2(main_script, backup_path)
            
            # Write updated content
            with open(main_script, 'w', encoding='utf-8') as f:
                f.write(updated_content)
                
            logging.info(f"Updated {main_script} with hidden element extraction import")
        else:
            logging.error(f"Could not find import section in {main_script}")
    else:
        logging.info(f"Hidden element extraction already imported in {main_script}")
        
    # Now we need to find where to call this function
    # We should look for the extraction code that processes threads for each league

if __name__ == "__main__":
    logging.info("Direct hidden element extraction module loaded")
    logging.info("To integrate with main extraction, run update_main_extraction_script()")
    logging.info("For standalone use, import extract_with_hidden_elements")
