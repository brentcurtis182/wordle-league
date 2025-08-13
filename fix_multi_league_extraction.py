#!/usr/bin/env python3
"""
Fix for the multi-league extraction issue in Wordle League

This script adds the missing extract_wordle_scores_multi_league function to
integrated_auto_update_multi_league.py and fixes the issue where threads
were being opened twice for different leagues.

Usage: python fix_multi_league_extraction.py
"""

import os
import sys
import re
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_extraction.log"),
        logging.StreamHandler()
    ]
)

def add_extract_wordle_scores_multi_league_function():
    """Add the missing extract_wordle_scores_multi_league function to the file"""
    
    source_file = "integrated_auto_update_multi_league.py"
    backup_file = f"integrated_auto_update_multi_league.py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    logging.info(f"Creating backup of {source_file} to {backup_file}")
    
    try:
        # Create backup
        with open(source_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
            
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_content)
            
        logging.info("Backup created successfully")
        
        # Look for where to insert the new function
        # We'll insert it right before the run_extraction_only function
        insertion_point = original_content.find("def run_extraction_only()")
        
        if insertion_point == -1:
            logging.error("Could not find insertion point (run_extraction_only function)")
            return False
            
        # Get the content before and after the insertion point
        before = original_content[:insertion_point]
        after = original_content[insertion_point:]
        
        # Create the new function to insert
        new_function = """def extract_wordle_scores_multi_league():
    \"\"\"Extract Wordle scores from all leagues
    
    This function handles the extraction process for multiple leagues,
    ensuring each thread is opened only once per league.
    
    Returns:
        bool: True if extraction was successful, False otherwise
    \"\"\"
    logging.info("Starting multi-league extraction process")
    
    # Set up the driver
    driver = setup_driver()
    if not driver:
        logging.error("Failed to set up WebDriver")
        return False
        
    try:
        # Navigate to Google Voice
        logging.info("Navigating to Google Voice")
        driver.get("https://voice.google.com/messages")
        
        # Take screenshot for verification
        driver.save_screenshot("google_voice_navigation.png")
        
        # Wait for conversations to load
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
            )
            logging.info("Successfully loaded Google Voice conversations")
        except TimeoutException:
            logging.error("Timed out waiting for Google Voice conversations")
            driver.quit()
            return False
            
        # Find all conversation threads
        logging.info("Finding conversation threads")
        try:
            conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list gv-text-thread")
            if not conversation_items:
                logging.warning("No conversation threads found")
            else:
                logging.info(f"Found {len(conversation_items)} conversation threads")
        except Exception as e:
            logging.error(f"Error finding conversation threads: {e}")
            driver.quit()
            return False
            
        # Get today's and yesterday's Wordle numbers
        today_wordle = get_todays_wordle_number()
        yesterday_wordle = get_yesterdays_wordle_number()
        
        # Create a mapping of threads to their leagues
        thread_league_map = {}
        
        # Process each thread to identify which league it belongs to
        for i, thread in enumerate(conversation_items[:10]):  # Check first 10 threads
            try:
                # Get thread text
                thread_text = thread.text
                
                # Check if this thread contains any known phone numbers for specific leagues
                if is_league_thread(thread_text, 1):
                    thread_league_map[i] = 1  # League 1: Wordle Warriorz
                    logging.info(f"Thread {i+1} identified as League 1 (Wordle Warriorz)")
                elif is_league_thread(thread_text, 3):
                    thread_league_map[i] = 3  # League 3: PAL
                    logging.info(f"Thread {i+1} identified as League 3 (PAL)")
                # Note: We don't currently handle League 2
            except Exception as e:
                logging.error(f"Error identifying league for thread {i+1}: {e}")
        
        # Now extract scores from each league thread separately
        total_scores = 0
        
        # First, extract scores from League 1 (Wordle Warriorz)
        league_1_threads = [conversation_items[idx] for idx, league in thread_league_map.items() if league == 1]
        if league_1_threads:
            logging.info("Extracting scores from League 1 (Wordle Warriorz)")
            league_1_scores = extract_scores_from_conversations(
                driver, league_1_threads, today_wordle, yesterday_wordle, league_id=1
            )
            total_scores += league_1_scores
        else:
            logging.warning("No threads found for League 1 (Wordle Warriorz)")
        
        # Reset driver to get fresh page for League 3
        driver.get("https://voice.google.com/messages")
        time.sleep(5)
        
        # Wait for conversations to load again
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "gv-conversation-list"))
            )
            logging.info("Successfully reloaded Google Voice conversations")
        except TimeoutException:
            logging.error("Timed out waiting for Google Voice conversations reload")
            driver.quit()
            return total_scores > 0
        
        # Get fresh conversation items
        try:
            conversation_items = driver.find_elements(By.CSS_SELECTOR, "gv-conversation-list gv-text-thread")
            logging.info(f"Found {len(conversation_items)} conversation threads after reload")
        except Exception as e:
            logging.error(f"Error finding conversation threads after reload: {e}")
            driver.quit()
            return total_scores > 0
        
        # Rebuild thread_league_map for fresh threads
        thread_league_map = {}
        for i, thread in enumerate(conversation_items[:10]):
            try:
                thread_text = thread.text
                if is_league_thread(thread_text, 1):
                    thread_league_map[i] = 1
                elif is_league_thread(thread_text, 3):
                    thread_league_map[i] = 3
            except Exception as e:
                logging.error(f"Error identifying league after reload for thread {i+1}: {e}")
        
        # Now extract scores from League 3 (PAL)
        league_3_threads = [conversation_items[idx] for idx, league in thread_league_map.items() if league == 3]
        if league_3_threads:
            logging.info("Extracting scores from League 3 (PAL)")
            league_3_scores = extract_scores_from_conversations(
                driver, league_3_threads, today_wordle, yesterday_wordle, league_id=3
            )
            total_scores += league_3_scores
        else:
            logging.warning("No threads found for League 3 (PAL)")
        
        # Clean up
        driver.quit()
        
        # Return success if we found at least one score
        logging.info(f"Total scores extracted across all leagues: {total_scores}")
        return total_scores > 0
        
    except Exception as e:
        logging.error(f"Error in extract_wordle_scores_multi_league: {e}")
        if driver:
            driver.quit()
        return False

def is_league_thread(thread_text, league_id):
    \"\"\"Determine if a thread belongs to a specific league based on its text
    
    Args:
        thread_text: The text of the thread
        league_id: League ID to check for
        
    Returns:
        bool: True if thread belongs to this league, False otherwise
    \"\"\"
    # League-specific phone numbers
    league_phones = {
        1: ["3109263555", "7603341190", "9713024781"],  # Wordle Warriorz
        3: ["8587359353", "4698345364", "7604206113"]   # PAL league
    }
    
    # If we don't have info for this league, return False
    if league_id not in league_phones:
        return False
        
    # Check if any of the league's phone numbers are in the thread text
    for phone in league_phones[league_id]:
        if phone in thread_text.replace(" ", "").replace("-", "").replace("(", "").replace(")", ""):
            return True
            
    return False

"""
        
        # Combine everything
        new_content = before + new_function + after
        
        # Write the updated file
        with open(source_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        logging.info("Successfully added extract_wordle_scores_multi_league function")
        return True
        
    except Exception as e:
        logging.error(f"Error adding extract_wordle_scores_multi_league function: {e}")
        return False

def fix_league_assignments():
    """Fix incorrect league assignments in the database"""
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check the current schema
        cursor.execute("PRAGMA table_info(scores)")
        columns = [column[1] for column in cursor.fetchall()]
        logging.info(f"Database columns: {columns}")
        
        # Fix Joanna and Nanna - move from League 3 to League 1
        # For the current wordle number
        cursor.execute("SELECT wordle_num FROM scores ORDER BY CAST(REPLACE(wordle_num, ',', '') AS INTEGER) DESC LIMIT 1")
        latest_wordle = cursor.fetchone()
        
        if latest_wordle:
            latest_wordle = latest_wordle[0]
            logging.info(f"Latest Wordle number: {latest_wordle}")
            
            # Fix Joanna's scores
            cursor.execute("""
                UPDATE scores SET league_id = 1
                WHERE player_name = 'Joanna' AND league_id = 3 AND wordle_num = ?
            """, (latest_wordle,))
            joanna_rows = cursor.rowcount
            logging.info(f"Fixed {joanna_rows} rows for Joanna (League 3 -> League 1)")
            
            # Fix Nanna's scores
            cursor.execute("""
                UPDATE scores SET league_id = 1
                WHERE player_name = 'Nanna' AND league_id = 3 AND wordle_num = ?
            """, (latest_wordle,))
            nanna_rows = cursor.rowcount
            logging.info(f"Fixed {nanna_rows} rows for Nanna (League 3 -> League 1)")
            
            # Fix Keith's scores
            cursor.execute("""
                UPDATE scores SET league_id = 2
                WHERE player_name = 'Keith' AND league_id = 1 AND wordle_num = ?
            """, (latest_wordle,))
            keith_rows = cursor.rowcount
            logging.info(f"Fixed {keith_rows} rows for Keith (League 1 -> League 2)")
            
            # Commit changes
            conn.commit()
            
            logging.info(f"Total rows fixed: {joanna_rows + nanna_rows + keith_rows}")
        else:
            logging.warning("No Wordle numbers found in database")
        
        # Close connection
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error fixing league assignments: {e}")
        return False

def main():
    """Main function to apply all fixes"""
    
    logging.info("Starting multi-league extraction fix")
    
    # Step 1: Add the missing extract_wordle_scores_multi_league function
    function_added = add_extract_wordle_scores_multi_league_function()
    
    if function_added:
        logging.info("Successfully added missing function to integrated_auto_update_multi_league.py")
    else:
        logging.error("Failed to add missing function")
        return False
        
    # Step 2: Fix league assignments in the database
    assignments_fixed = fix_league_assignments()
    
    if assignments_fixed:
        logging.info("Successfully fixed league assignments in the database")
    else:
        logging.error("Failed to fix league assignments")
        
    logging.info("All fixes applied. Please run the extraction script to verify.")
    return True

if __name__ == "__main__":
    main()
