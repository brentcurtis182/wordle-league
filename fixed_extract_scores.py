#!/usr/bin/env python3
# Simplified extract_scores function that fixes syntax errors and ensures proper scrolling
# This should be incorporated into integrated_auto_update_multi_league.py

def extract_scores_from_hidden_elements(driver, league_id, today_wordle, yesterday_wordle):
    """
    Extract Wordle scores from hidden elements in Google Voice
    
    Args:
        driver: Selenium WebDriver instance
        league_id: The league ID (1=main, 3=PAL)
        today_wordle: Today's Wordle number
        yesterday_wordle: Yesterday's Wordle number
        
    Returns:
        int: Number of new scores extracted
    """
    import logging
    import re
    import sqlite3
    import time
    
    # Initialize counter for extracted scores
    scores_extracted = 0
    
    try:
        # Look for hidden elements containing the full message text
        logging.info(f"Looking for hidden elements with scores in league {league_id}...")
        hidden_elements = driver.find_elements(By.CLASS_NAME, "cdk-visually-hidden")
        logging.info(f"Found {len(hidden_elements)} hidden elements in league {league_id}")
        
        # Save raw elements to a file for debugging
        with open(f"hidden_elements_league_{league_id}.txt", "w", encoding="utf-8") as f:
            for i, element in enumerate(hidden_elements):
                try:
                    text = element.text
                    f.write(f"\n--- ELEMENT {i} ---\n{text}\n")
                except:
                    f.write(f"\n--- ELEMENT {i} ERROR ---\n")
        
        # Wordle pattern that handles comma-formatted numbers (like "1,502")
        wordle_pattern = re.compile(r'Wordle\s+([\d,]+)\s+([1-6]|X)/6')
        
        # Process each element individually
        for element in hidden_elements:
            try:
                text = element.text
                logging.info(f"Processing hidden element text: {text[:50]}...")  # Log first 50 chars
                
                # Skip reaction messages like 'Loved'
                reaction_patterns = ['Loved', 'Liked', 'Laughed at', 'Emphasized', 'Reacted to']
                if any(pattern in text for pattern in reaction_patterns):
                    logging.info(f"Skipping reaction message: {text[:50]}...")
                    continue
                
                # Special handling for PAL league to extract FuzWuz's scores (7604206113)
                if league_id == 3 and ('7604206113' in text or '7 6 0 4 2 0 6 1 1 3' in text):
                    logging.info(f"PAL LEAGUE: Found message from FuzWuz: {text[:100]}")
                
                # Special handling for PAL league to extract Starslider's scores (8587353353)
                if league_id == 3 and ('8587353353' in text or '8 5 8 7 3 5 3 3 5 3' in text):
                    logging.info(f"PAL LEAGUE: Found message from Starslider: {text[:100]}")
                
                # Look for Wordle score pattern
                match = wordle_pattern.search(text)
                if match:
                    # Extract Wordle number and score
                    wordle_num_str, score_text = match.groups()
                    
                    # Remove commas from the Wordle number string before converting to int
                    wordle_num = int(wordle_num_str.replace(',', ''))
                    score = score_text  # Keep as string ('1'-'6' or 'X')
                    
                    # Check if this is a valid Wordle number we want to process
                    # We accept today's, yesterday's, or any from the past week
                    wordle_cutoff = today_wordle - 7  # Include scores from up to a week ago
                    if wordle_num >= wordle_cutoff:
                        logging.info(f"Found Wordle score: {wordle_num} {score}/6")
                        
                        # Extract phone number using multiple patterns
                        element_phone = None
                        
                        # Try pattern 1: Standard US format (555) 123-4567
                        phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', text)
                        if phone_match:
                            element_phone = phone_match.group(1) + phone_match.group(2) + phone_match.group(3)
                            logging.info(f"Found phone number pattern 1: {element_phone}")
                        
                        # Try pattern 2: Non-formatted sequence 5551234567
                        if not element_phone:
                            phone_match = re.search(r'(?<!\d)(\d{10})(?!\d)', text)
                            if phone_match:
                                element_phone = phone_match.group(1)
                                logging.info(f"Found phone number pattern 2: {element_phone}")
                        
                        # Try pattern 3: Spaced digits 5 5 5 1 2 3 4 5 6 7
                        if not element_phone:
                            phone_match = re.search(r'(\d\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d\s+\d)', text)
                            if phone_match:
                                element_phone = phone_match.group(1).replace(' ', '')
                                logging.info(f"Found phone number pattern 3: {element_phone}")
                                
                        # Extract emoji pattern if present
                        emoji_pattern = None
                        if '⬛' in text or '⬜' in text or '🟨' in text or '🟩' in text:
                            pattern_lines = []
                            for line in text.split('\n'):
                                if any(emoji in line for emoji in ['⬛', '⬜', '🟨', '🟩']):
                                    pattern_lines.append(line.strip())
                            if pattern_lines:
                                emoji_pattern = '\n'.join(pattern_lines)
                                
                        # If we found a phone number, try to map it to a player
                        if element_phone:
                            logging.info(f"League {league_id}: Trying to extract player name for phone {element_phone}")
                            player_name = extract_player_name_from_phone(element_phone, league_id)
                            
                            # Extra detailed logging for PAL league
                            if league_id == 3:
                                logging.info(f"PAL LEAGUE DEBUG: Phone={element_phone}, Mapped Player={player_name}")
                                
                            if player_name:
                                logging.info(f"Found score: Wordle {wordle_num} {score_text}/6 for {player_name} (league: {league_id})")
                                
                                # Connect to the database and check if score exists
                                conn = None
                                try:
                                    conn = sqlite3.connect('wordle_league.db')
                                    cursor = conn.cursor()
                                    
                                    # Check if score already exists
                                    cursor.execute(
                                        "SELECT score FROM scores WHERE player_name = ? AND wordle_num = ? AND league_id = ?",
                                        (player_name, wordle_num, league_id)
                                    )
                                    existing_score = cursor.fetchone()
                                    
                                    if not existing_score:
                                        # Add new score
                                        score_int = 7 if score == 'X' else int(score)
                                        save_score_to_db(
                                            player=player_name,
                                            wordle_num=wordle_num,
                                            score=score_int,
                                            emoji_pattern=emoji_pattern,
                                            league_id=league_id
                                        )
                                        scores_extracted += 1
                                        logging.info(f"Added new score: {player_name}, Score: {score}, Wordle: {wordle_num}, League: {league_id}")
                                
                                except Exception as e:
                                    logging.error(f"Error processing score: {e}")
                                finally:
                                    if conn:
                                        try:
                                            conn.close()
                                        except:
                                            pass
                            else:
                                logging.warning(f"Could not find player name for phone {element_phone} in league {league_id}")
                        else:
                            logging.warning(f"Could not extract phone number from message with Wordle score in league {league_id}")
            except Exception as e:
                logging.error(f"Error processing hidden element: {e}")
                
    except Exception as e:
        logging.error(f"Error extracting from hidden elements: {e}")
        
    return scores_extracted

# This function should be incorporated into the main file
# replacing the current extract_scores_from_conversations function
def extract_scores_from_conversations(driver, conversation_items, today_wordle, yesterday_wordle, league_id=1):
    """Extract Wordle scores from conversations
    
    Args:
        driver: Selenium WebDriver instance
        conversation_items: List of conversation elements to process
        today_wordle: Today's Wordle number
        yesterday_wordle: Yesterday's Wordle number
        league_id: The league ID to use when saving scores
        
    Returns:
        int: Number of new scores extracted
    """
    import logging
    import time
    import re
    from scroll_in_thread import scroll_up_in_thread
    from bs4 import BeautifulSoup
    
    logging.info(f"Extracting scores for league {league_id}")
    logging.info(f"Found {len(conversation_items)} conversation items")
    
    # Special handling for hardcoded scores
    # This section is preserved from the original code
    current_date = datetime.now().strftime("%Y-%m-%d")
    if today_wordle == 1503 and current_date == "2025-07-31":
        # League 1 - Brent's score
        if league_id == 1:
            # (Hardcoded data handling for Brent)
            pass
        
        # League 3 - PAL league - FuzWuz and Starslider scores
        elif league_id == 3:
            # (Hardcoded data handling for FuzWuz and Starslider)
            pass
    
    # Process hidden elements directly
    scores_extracted = extract_scores_from_hidden_elements(driver, league_id, today_wordle, yesterday_wordle)
    
    # Process each conversation normally if we haven't found scores
    if scores_extracted == 0:
        for i, conversation in enumerate(conversation_items):
            try:
                # Wait for message thread to load
                time.sleep(2)
                
                # Click on conversation to open it
                logging.info(f"Clicking on conversation {i+1}/{len(conversation_items)}")
                conversation.click()
                time.sleep(3)  # Allow time for thread to load
                
                # Take a screenshot for debugging
                screenshot_path = f"conversation_{i}_screenshot.png"
                driver.save_screenshot(screenshot_path)
                logging.info(f"Saved screenshot to {screenshot_path}")
                
                # Scroll up to load all messages including yesterday's Wordle scores
                logging.info(f"Scrolling up in thread to find Wordle scores")
                scroll_up_in_thread(driver, yesterday_wordle)
                
                # Now process hidden elements after scrolling
                thread_scores = extract_scores_from_hidden_elements(driver, league_id, today_wordle, yesterday_wordle)
                scores_extracted += thread_scores
                
                logging.info(f"Extracted {thread_scores} new scores from conversation {i+1}")
                
            except Exception as e:
                logging.error(f"Error processing conversation {i+1}: {e}")
    
    return scores_extracted
