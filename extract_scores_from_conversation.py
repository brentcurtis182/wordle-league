# Extraction function for Google Voice conversations
# This file should be imported in integrated_auto_update_multi_league.py

import re
import time
import logging
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By

def extract_scores_from_conversation(driver, league_id):
    """Extract scores from the currently open conversation
    
    Args:
        driver: Selenium WebDriver instance
        league_id: League ID for this conversation
        
    Returns:
        int: Number of scores found
    """
    league_name = "Wordle Warriorz" if league_id == 1 else "PAL"
    logging.info(f"Extracting scores from {league_name} conversation")
    
    try:
        # Capture DOM snapshot for diagnostics
        dom_filename = f"dom_{league_name.replace(' ', '_')}_{int(time.time())}.html"
        # Assuming capture_dom_snapshot is defined in the main file
        try:
            from integrated_auto_update_multi_league import capture_dom_snapshot
            capture_dom_snapshot(driver, dom_filename)
        except ImportError:
            logging.warning("Could not import capture_dom_snapshot function")
        
        # Calculate today and yesterday's wordle numbers
        # Using functions from the main file
        try:
            from integrated_auto_update_multi_league import get_todays_wordle_number, get_yesterdays_wordle_number
            today_wordle = get_todays_wordle_number()
            yesterday_wordle = get_yesterdays_wordle_number()
        except ImportError:
            # Fallback to hardcoded values
            # Calculate Wordle # based on days since June 19, 2021
            start_date = datetime(2021, 6, 19)
            today = datetime.now()
            days_since_start = (today - start_date).days
            today_wordle = days_since_start + 1
            yesterday_wordle = today_wordle - 1
        
        logging.info(f"Today's Wordle: #{today_wordle}, Yesterday's Wordle: #{yesterday_wordle}")
        
        # Regular expressions to match Wordle scores - handles comma formatting
        # Updated regex to handle 'Message from...' prefix and ensure better matching
        wordle_regex = re.compile(r'.*?Wordle\s+(?:#)?(\d[\d,]*)\s+(\d|X)/6', re.IGNORECASE)
        
        scores_found = 0
        today_scores_found = 0
        
        # Try multiple DOM element types to find Wordle scores
        # First look for elements with the preview class which contain formatted scores
        annotation_elements = driver.find_elements(By.CSS_SELECTOR, "gv-annotation.preview")
        logging.info(f"Found {len(annotation_elements)} gv-annotation.preview elements")
        
        # Also check aria-label attributes which often contain the full message text
        aria_elements = driver.find_elements(By.CSS_SELECTOR, "[aria-label*='Wordle']")
        logging.info(f"Found {len(aria_elements)} elements with Wordle in aria-label")
        
        # Check visually-hidden elements which contain message text
        hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} visually-hidden elements")
        
        # Combine all elements to search
        message_elements = annotation_elements + aria_elements + hidden_elements
        
        # If no specialized elements found, fall back to traditional message elements
        if not message_elements:
            message_elements = driver.find_elements(By.CSS_SELECTOR, ".message-item, gv-message-item")
            logging.info(f"Falling back to message-item elements: found {len(message_elements)} elements")
            
        logging.info(f"Processing total of {len(message_elements)} elements for score extraction")
        
        # Get the entire page source and check for Wordle scores
        page_source = driver.page_source
        if "Wordle" in page_source and "/6" in page_source:
            logging.info("Page source contains Wordle scores, proceeding with extraction")
        
        # Process each element to find scores
        for element in message_elements:
            try:
                text = element.text.strip()
                
                # Skip any reactions like "Loved" or "Liked"
                if text.startswith("Loved ") or text.startswith("Liked ") or "reacted with" in text.lower() or "reacted to" in text.lower():
                    continue
                
                # Skip non-Wordle messages or ones without scores
                if not text.lstrip().startswith("Wordle") or ("/6" not in text and "X/6" not in text):
                    continue
                
                # Extract text from the "Message from" prefix through the end
                message_start = text.find("Message from")
                if message_start >= 0:
                    message_content = text[message_start:]
                    logging.info(f"Processing message: {message_content[:100]}...")
                else:
                    message_content = text
                
                # Now extract the Wordle details
                match = wordle_regex.search(message_content)
                # Debug logging to show exact text being searched
                logging.info(f"Searching for Wordle score in text: '{message_content[:100]}...'")
                if not match:
                    # Try alternate regex patterns for debugging
                    alt_patterns = [
                        r'Wordle\s+#?(\d[\d,]*)\s+(\d|X)/6',
                        r'Wordle\s+(\d[\d,]*)\s+(\d|X)/6',
                        r'Wordle[:\s]+(\d[\d,]*)[:\s]+(\d|X)/6'
                    ]
                    for i, pattern in enumerate(alt_patterns):
                        alt_match = re.search(pattern, message_content, re.IGNORECASE)
                        if alt_match:
                            logging.info(f"Alternative pattern {i+1} matched: {alt_match.groups()}")
                            match = alt_match  # Use this match instead
                            break
                if not match:
                    logging.debug(f"Regex didn't match despite Wordle text: {message_content[:50]}...")
                    continue
                    
                # Extract wordle number (handle commas)
                wordle_num_str = match.group(1)
                if wordle_num_str:
                    # Remove commas and convert to integer
                    cleaned_num_str = wordle_num_str.replace(',', '')
                    try:
                        wordle_num = int(cleaned_num_str)
                        logging.info(f"Found Wordle number: {wordle_num}")
                    except ValueError:
                        logging.warning(f"Could not convert Wordle number to int: {wordle_num_str}")
                        continue
                else:
                    continue
                
                # Check if this is today's or yesterday's Wordle
                if wordle_num == today_wordle:
                    logging.info(f"VALIDATED: This is today's Wordle #{today_wordle}")
                elif wordle_num == yesterday_wordle:
                    logging.info(f"VALIDATED: This is yesterday's Wordle #{yesterday_wordle}")
                else:
                    # PAL league may use different Wordle numbers or have future-dated scores
                    # Allow any Wordle number for PAL league (league_id != 1)
                    if league_id == 1:  # Only restrict for Wordle Warriorz league
                        logging.info(f"REJECTED: Wordle #{wordle_num} is neither today's ({today_wordle}) nor yesterday's ({yesterday_wordle})")
                        continue
                    else:
                        # For PAL league, allow scores within a reasonable range (±50 from today's number)
                        if abs(wordle_num - today_wordle) > 50:
                            logging.warning(f"REJECTED: PAL Wordle #{wordle_num} is too far from today's ({today_wordle})")
                            continue
                        logging.info(f"ALLOWING PAL league Wordle #{wordle_num} despite not matching today/yesterday")
                
                # Extract score
                score_str = match.group(2)
                if score_str == 'X':
                    score = 7  # X = 7 in our system
                else:
                    score = int(score_str)
                
                # Extract emoji pattern if available
                emoji_pattern = None
                if '\n' in message_content:
                    lines = message_content.split('\n')
                    emoji_lines = []
                    in_emoji_pattern = False
                    
                    for i in range(1, min(len(lines), 15)):
                        pattern_part = lines[i]
                        if '🟩' in pattern_part or '⬛' in pattern_part or '⬜' in pattern_part or '🟨' in pattern_part:
                            emoji_lines.append(pattern_part)
                            in_emoji_pattern = True
                        elif in_emoji_pattern:
                            break
                    
                    if emoji_lines:
                        emoji_pattern = '\n'.join(emoji_lines)
                        logging.info(f"Extracted emoji pattern with {len(emoji_lines)} lines")
                        logging.info(f"Extracted emoji pattern:\n{emoji_pattern}")
                
                # Find phone number for player mapping
                phone_match = re.search(r'Message from (\d[\s\d-]+\d)', message_content)
                phone = None
                
                if phone_match:
                    # Extract phone from 'Message from' format
                    phone = phone_match.group(1)
                    phone = re.sub(r'[\s\-\(\)]+', '', phone)
                    # Handle +1 prefix
                    if phone.startswith('+1'):
                        phone = phone[1:]  # Keep the 1 but remove the +
                else:
                    # Try to extract from (XXX) XXX-XXXX format
                    phone_matches = re.findall(r'\((\d{3})\)[\s-]*(\d{3})[\s-]*(\d{4})', message_content)
                    if phone_matches:
                        area_code = phone_matches[0][0]
                        prefix = phone_matches[0][1]
                        suffix = phone_matches[0][2]
                        phone = f"1{area_code}{prefix}{suffix}"  # Always add leading 1
                
                # Ensure consistent format for lookup
                if phone:
                    # Make sure we have exactly 11 digits with leading 1
                    if len(phone) == 10 and not phone.startswith('1'):
                        phone = '1' + phone
                    elif len(phone) > 11 and phone.startswith('1'):
                        phone = phone[:11]  # Truncate to 11 digits if too long
                    
                    logging.info(f"Normalized phone number for lookup: {phone}")
                
                if not phone:
                    logging.warning("Could not extract phone number from message")
                    continue
                    
                logging.info(f"Extracted phone: {phone} for Wordle {wordle_num}")
                
                # Get player name from phone number
                # Assuming get_player_by_phone_for_league is defined in the main file
                try:
                    from integrated_auto_update_multi_league import get_player_by_phone_for_league
                    from save_score_functions import save_score_to_db
                    
                    # Try with the current phone format first
                    player = get_player_by_phone_for_league(phone, league_id)
                    
                    # If not found, try alternative formats
                    if not player:
                        logging.info(f"Player not found for {phone} in league {league_id}, trying alternate formats")
                        
                        # Try without leading 1 if it has one
                        if phone.startswith('1') and len(phone) == 11:
                            alt_phone = phone[1:]  # Remove leading 1
                            logging.info(f"Trying alternate format without leading 1: {alt_phone}")
                            player = get_player_by_phone_for_league(alt_phone, league_id)
                        
                        # If still not found and original didn't have leading 1, try with it
                        if not player and not phone.startswith('1') and len(phone) == 10:
                            alt_phone = '1' + phone  # Add leading 1
                            logging.info(f"Trying alternate format with leading 1: {alt_phone}")
                            player = get_player_by_phone_for_league(alt_phone, league_id)
                except ImportError:
                    logging.error("Could not import player mapping functions")
                    continue
                
                if player:
                    logging.info(f"Player {player} scored {score} on Wordle #{wordle_num} in {league_name}")
                    
                    # Save the score to database
                    result = save_score_to_db(player, wordle_num, score, emoji_pattern, league_id)
                     
                    logging.info(f"Result of save_score_to_db: {result}")
                    
                    if result == 'new':
                        scores_found += 1
                        if wordle_num == today_wordle:
                            today_scores_found += 1
                            logging.info(f"*** FOUND TODAY'S SCORE: {player} - Wordle #{wordle_num} - {score}/6 ***")
                        elif wordle_num == yesterday_wordle:
                            logging.info(f"Found yesterday's score: {player} - Wordle #{wordle_num} - {score}/6")
                    
                    logging.info(f"Score save result: {result} for {player} in {league_name}")
                else:
                    logging.warning(f"Could not identify player for phone {phone} in {league_name}")
            except Exception as elem_error:
                logging.error(f"Error processing element text in {league_name}: {elem_error}")
                continue
        
        # Add debugging for PAL league score extraction
        if league_id != 1:
            logging.info(f"PAL league extraction summary: wordle_regex matches found in DOM, scores saved: {scores_found}")
        
        logging.info(f"Found {scores_found} new scores total, {today_scores_found} new scores for today's Wordle #{today_wordle} in {league_name}")
        return scores_found
    
    except Exception as e:
        logging.error(f"Error extracting current scores from {league_name}: {e}")
        return 0
