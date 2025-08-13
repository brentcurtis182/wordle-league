#!/usr/bin/env python3
"""
Debug Extraction for Today's Scores

This script adds extensive debugging to the extraction process to diagnose why scores
aren't being properly detected and saved to the unified scores table.
"""

import logging
import sqlite3
import os
import sys
import re
import datetime
from pprint import pprint

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_extraction_today.log"),
        logging.StreamHandler()
    ]
)

# Import extraction modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the fixed extract function from the main script
    from fixed_extract_multi_league import extract_wordle_scores_multi_league
    # Import browser setup function
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    
    def browser_setup():
        """Set up the Chrome browser for automation"""
        try:
            # Configure Chrome options
            chrome_options = Options()
            
            # Use existing Chrome profile to avoid login issues
            profile_dir = os.path.join(os.getcwd(), 'automation_profile')
            logging.info(f"Using existing Chrome profile at {profile_dir}")
            
            if os.path.exists(profile_dir):
                chrome_options.add_argument(f"user-data-dir={profile_dir}")
            else:
                logging.warning(f"Profile directory {profile_dir} not found!")
            
            # Headless option for server environments
            if os.environ.get('HEADLESS', '').lower() == 'true':
                chrome_options.add_argument('--headless')
                logging.info("Running Chrome in headless mode")
                
            # Additional options for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # Start the browser
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_window_size(1200, 800)
            
            return driver
        except Exception as e:
            logging.error(f"Error setting up browser: {e}")
            return None
except ImportError as e:
    logging.error(f"Failed to import extraction modules: {e}")
    exit(1)

def diagnose_extraction():
    """Run a diagnostic extraction with extra logging"""
    logging.info("="*60)
    logging.info("STARTING DIAGNOSTIC EXTRACTION")
    logging.info("="*60)
    
    # Calculate today's expected Wordle number
    ref_date = datetime.date(2025, 7, 31)
    ref_wordle = 1503
    today = datetime.date.today()
    days_diff = (today - ref_date).days
    todays_wordle = ref_wordle + days_diff
    
    logging.info(f"Today is {today} - Expected Wordle number: #{todays_wordle}")
    
    # Check if there's already data for today
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check for scores in unified table
        cursor.execute("""
        SELECT p.name, p.league_id, s.score, s.wordle_number, s.emoji_pattern
        FROM scores s JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number = ?
        """, (todays_wordle,))
        
        existing_scores = cursor.fetchall()
        
        if existing_scores:
            logging.info(f"Found {len(existing_scores)} existing scores for Wordle #{todays_wordle}:")
            for score in existing_scores:
                logging.info(f"  {score[0]} (League {score[1]}): {score[2]}/6")
        else:
            logging.info(f"No existing scores found for Wordle #{todays_wordle}")
            
        # Add a diagnostic function to check Google Voice HTML directly
        
        # Create HTML dump directory if not exists
        os.makedirs('dom_captures', exist_ok=True)
        
        # Setup browser
        driver = browser_setup()
        if not driver:
            logging.error("Failed to set up browser")
            return False
            
        try:
            # Navigate to Google Voice
            logging.info("Navigating to Google Voice...")
            driver.get("https://voice.google.com/messages")
            
            # Wait for page to load
            import time
            time.sleep(5)
            
            # Save full DOM for analysis
            with open(os.path.join('dom_captures', 'diagnostic_full_dom.html'), 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            
            # Look specifically for hidden elements with Wordle data
            from selenium.webdriver.common.by import By
            hidden_elements = driver.find_elements(By.CSS_SELECTOR, ".cdk-visually-hidden")
            
            logging.info(f"Found {len(hidden_elements)} hidden elements")
            
            wordle_pattern = re.compile(r'Wordle\s+(?:#)?(\d[\d,]*)\s+(\d|X)/6', re.IGNORECASE)
            
            # Keep track of all potential Wordle scores in any format
            all_wordle_matches = []
            
            # Save all hidden element text
            with open(os.path.join('dom_captures', 'diagnostic_hidden_elements.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Total hidden elements: {len(hidden_elements)}\n\n")
                
                for i, el in enumerate(hidden_elements):
                    try:
                        el_text = el.get_attribute('textContent')
                        f.write(f"Element {i+1}:\n{el_text}\n{'-'*50}\n")
                        
                        # Check for Wordle score patterns
                        matches = wordle_pattern.findall(el_text)
                        if matches:
                            all_wordle_matches.append((matches[0], el_text))
                            logging.info(f"Found Wordle match: {matches[0]} in hidden element {i+1}")
                    except Exception as e:
                        f.write(f"Error extracting element {i+1}: {e}\n")
                        
            # Check entire page for Wordle mentions
            page_source = driver.page_source
            wordle_mentions = wordle_pattern.findall(page_source)
            
            logging.info(f"Found {len(wordle_mentions)} Wordle mentions in entire page source")
            logging.info(f"Wordle numbers mentioned: {[m[0] for m in wordle_mentions]}")
            
            # Show found Wordle matches from hidden elements
            logging.info("\nWordle scores found in hidden elements:")
            for match, text in all_wordle_matches:
                wordle_num, score = match
                # Clean commas from wordle number
                wordle_num = wordle_num.replace(',', '')
                logging.info(f"Wordle #{wordle_num}: {score}/6")
                
                # Extract emoji pattern if present
                emoji_lines = []
                for line in text.split('\n'):
                    if any(emoji in line for emoji in ['🟩', '⬛', '⬜', '🟨']):
                        emoji_lines.append(line)
                
                if emoji_lines:
                    logging.info(f"  Found emoji pattern with {len(emoji_lines)} lines")
                    for line in emoji_lines:
                        logging.info(f"  {line}")
                else:
                    logging.info("  No emoji pattern found")
            
        finally:
            # Close the browser
            try:
                driver.quit()
            except:
                pass
            
        # Now run the actual extraction
        logging.info("\nRunning the normal extraction process...")
        success = extract_wordle_scores_multi_league()
        
        # Check if new scores were added
        cursor.execute("""
        SELECT p.name, p.league_id, s.score, s.wordle_number, s.date, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number = ?
        ORDER BY p.league_id, p.name
        """, (todays_wordle,))
        
        after_scores = cursor.fetchall()
        
        logging.info(f"After extraction: Found {len(after_scores)} scores for Wordle #{todays_wordle}")
        
        if after_scores:
            logging.info("\nScores in database after extraction:")
            for score in after_scores:
                name, league_id, score_val, wordle_num, date, emoji = score
                display_score = 'X' if score_val == 7 else score_val
                league_name = "Wordle Warriorz" if league_id == 1 else "PAL" if league_id == 3 else "Gang"
                
                logging.info(f"{name} ({league_name}): Wordle #{wordle_num} - {display_score}/6 on {date}")
                if emoji:
                    emoji_lines = emoji.split('\n')
                    for line in emoji_lines:
                        logging.info(f"  {line}")
            
        return True
        
    except Exception as e:
        logging.error(f"Error in diagnostic extraction: {e}", exc_info=True)
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info(f"Starting diagnostic extraction at {datetime.datetime.now()}")
    success = diagnose_extraction()
    if success:
        logging.info("Diagnostic extraction completed successfully!")
    else:
        logging.error("Diagnostic extraction failed!")
