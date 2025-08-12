import sys
import os
import time
import logging
from datetime import datetime
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Import directly from the main script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from integrated_auto_update_multi_league import (
    setup_chrome_driver, navigate_to_google_voice, 
    find_conversation_threads, scroll_conversation,
    extract_player_name_from_phone, calculate_today_wordle
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("dom_extraction.log")
    ]
)

def extract_and_log_elements(driver, league_id=1):
    """Extract DOM elements with Wordle scores and log them"""
    # Calculate today's Wordle number
    today_wordle = calculate_today_wordle()
    logging.info(f"Today's Wordle number should be: {today_wordle}")
    
    # Find relevant conversation threads
    conversation_items = find_conversation_threads(driver, league_id)
    if not conversation_items:
        logging.warning(f"No conversation threads found for league {league_id}")
        return False
    
    scores_found = []
    log_file = f"wordle_elements_league_{league_id}.html"
    
    # Start HTML log file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Wordle DOM Elements - League {league_id}</title>
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
    <h1>Wordle DOM Elements - League {league_id}</h1>
    <p>Extracted on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p>Today's Wordle should be: <span class="wordle-num">#{today_wordle}</span></p>
""")
    
    # Process each conversation
    for i, conversation in enumerate(conversation_items):
        try:
            # Click on conversation to load messages
            driver.execute_script("arguments[0].click();", conversation)
            logging.info(f"Clicked on conversation {i+1} for league {league_id}")
            
            # Wait for message thread to load
            time.sleep(3)
            
            # Scroll through conversation to load all messages
            scroll_conversation(driver)
            
            # Find hidden elements containing message text
            hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
            logging.info(f"Found {len(hidden_elements)} hidden elements in conversation {i+1}")
            
            # Add conversation header to HTML log
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"""
    <h2>Conversation {i+1}</h2>
    <p>Found {len(hidden_elements)} hidden elements</p>
""")
            
            # Extract scores from hidden elements
            wordle_pattern = re.compile(r'Wordle\s+([0-9,]+)\s+([1-6]|X)/6')
            
            # Process each hidden element for scores
            for j, element in enumerate(hidden_elements):
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
                    
                    # Write to HTML log regardless of match (to see all possible content)
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"""
    <div class="element">
        <h3>Element {j+1}</h3>
""")
                        
                        if match:
                            # Extract wordle number and score
                            try:
                                wordle_num = int(match.group(1).replace(',', ''))
                                score_text = match.group(2)
                                
                                f.write(f"""
        <p>Wordle <span class="wordle-num">#{wordle_num}</span> - Score: <span class="score">{score_text}/6</span></p>
""")
                                
                                # Extract phone number from text
                                phone_match = re.search(r'(?:\+?1[-\s]?)?\(?([0-9]{3})\)?[-\s]?([0-9]{3})[-\s]?([0-9]{4})', text)
                                if phone_match:
                                    # Format phone number consistently
                                    element_phone = phone_match.group(1) + phone_match.group(2) + phone_match.group(3)
                                    # Add country code if missing
                                    if len(element_phone) == 10:
                                        element_phone = "1" + element_phone
                                    
                                    player_name = extract_player_name_from_phone(element_phone, league_id)
                                    if player_name:
                                        f.write(f"""
        <p>Player: <span class="player">{player_name}</span> (Phone: {element_phone})</p>
""")
                                    else:
                                        f.write(f"""
        <p>Unknown Player (Phone: {element_phone})</p>
""")
                                
                                # Extract emoji pattern if present
                                if '\u2b1b' in text or '\u2b1c' in text or '\ud83d\udfe8' in text or '\ud83d\udfe9' in text:
                                    pattern_lines = []
                                    for line in text.split('\n'):
                                        if any(emoji in line for emoji in ['\u2b1b', '\u2b1c', '\ud83d\udfe8', '\ud83d\udfe9']):
                                            pattern_lines.append(line.strip())
                                    
                                    if pattern_lines:
                                        emoji_pattern = '\n'.join(pattern_lines)
                                        f.write(f"""
        <p>Emoji Pattern:</p>
        <pre class="emoji">{emoji_pattern}</pre>
""")
                                
                                # Add score to found list if it's recent
                                if wordle_num >= today_wordle - 5:
                                    scores_found.append({
                                        'wordle_num': wordle_num,
                                        'score': score_text,
                                        'element_index': j,
                                        'conversation': i+1,
                                        'league': league_id
                                    })
                                    
                            except ValueError as ve:
                                f.write(f"""
        <p>Invalid Wordle number or score: {ve}</p>
""")
                                
                        # Always include raw text content
                        f.write(f"""
        <details>
            <summary>Raw Text Content</summary>
            <pre>{text}</pre>
        </details>
    </div>
""")
                        
                except Exception as e:
                    logging.error(f"Error processing hidden element {j+1}: {e}")
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"""
    <div class="element">
        <h3>Element {j+1} - ERROR</h3>
        <p>Error processing element: {e}</p>
    </div>
""")
            
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
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"""
    <h2>Conversation {i+1} - ERROR</h2>
    <p>Error: {e}</p>
""")
            # Try to get back to the messages list
            driver.get("https://voice.google.com/messages")
            time.sleep(3)
    
    # Close HTML log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"""
    <h2>Summary of Found Scores</h2>
""")
        if scores_found:
            f.write("""
    <table border="1" cellpadding="5" cellspacing="0">
        <tr>
            <th>Wordle #</th>
            <th>Score</th>
            <th>Conversation</th>
            <th>Element</th>
        </tr>
""")
            for score in sorted(scores_found, key=lambda x: x['wordle_num'], reverse=True):
                f.write(f"""
        <tr>
            <td>{score['wordle_num']}</td>
            <td>{score['score']}/6</td>
            <td>{score['conversation']}</td>
            <td>{score['element_index']}</td>
        </tr>
""")
            f.write("""
    </table>
""")
        else:
            f.write("""
    <p>No Wordle scores found in this league.</p>
""")
            
        f.write("""
</body>
</html>
""")
    
    logging.info(f"DOM elements have been logged to {log_file}")
    print(f"\nDOM elements have been logged to {log_file}")
    print(f"Open this file in a browser to see the full details")
    
    # Print summary to console
    print("\nSummary of Found Scores:")
    if scores_found:
        for score in sorted(scores_found, key=lambda x: x['wordle_num'], reverse=True):
            print(f"Wordle #{score['wordle_num']} - Score: {score['score']}/6 - Conversation: {score['conversation']}")
    else:
        print("No Wordle scores found in this league.")
    
    return True

def main():
    # Set up Chrome driver using function from main script
    driver = setup_chrome_driver(use_profile=True)
    
    try:
        # Navigate to Google Voice using function from main script
        if not navigate_to_google_voice(driver):
            logging.error("Failed to navigate to Google Voice")
            return
        
        # Process leagues
        leagues = [1, 3]  # Main league and PAL league
        
        for league_id in leagues:
            logging.info(f"Processing league ID: {league_id}")
            
            # Extract and log DOM elements for current league
            extract_and_log_elements(driver, league_id)
            
    except Exception as e:
        logging.error(f"Error in main process: {e}")
    finally:
        # Clean up
        driver.quit()
        logging.info("Browser closed")

if __name__ == "__main__":
    main()
