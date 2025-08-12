#!/usr/bin/env python
# fix_joanna_and_weekly_reset.py - Combined script to fix Joanna's score and handle weekly reset

import os
import sqlite3
import logging
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"wordle_fixes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

# Constants
DATABASE_PATH = "wordle_league.db"
WORDLE_NUMBER = 1500  # Target Wordle number
PLAYER_NAME = "Joanna"  # Player name to check
RESET_MARKER_FILE = "last_weekly_reset.txt"

def connect_to_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def check_joanna_score():
    """Check if Joanna has a score for Wordle #1500 and print all scores for this Wordle"""
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get player_id for Joanna
        cursor.execute("SELECT id FROM player WHERE name = ?", (PLAYER_NAME,))
        player_row = cursor.fetchone()
        
        if not player_row:
            logging.error(f"Player '{PLAYER_NAME}' not found in database")
            return False
        
        player_id = player_row['id']
        logging.info(f"Found player: {PLAYER_NAME}, ID: {player_id}")
        
        # Check all scores for Wordle #1500
        logging.info(f"Current scores for Wordle #{WORDLE_NUMBER}:")
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern, s.date
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.wordle_number = ?
            ORDER BY p.name
        """, (WORDLE_NUMBER,))
        
        scores = cursor.fetchall()
        if not scores:
            logging.info(f"No scores found for Wordle #{WORDLE_NUMBER}")
            return False
        
        for score in scores:
            emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display} ({emoji_rows} rows) on {score['date']}")
        
        # Check specifically for Joanna's score
        cursor.execute("""
            SELECT s.id, s.score, s.emoji_pattern, s.date 
            FROM score s
            WHERE s.player_id = ? AND s.wordle_number = ?
        """, (player_id, WORDLE_NUMBER))
        
        joanna_score = cursor.fetchone()
        if joanna_score:
            score_display = "X/6" if joanna_score['score'] == 7 else f"{joanna_score['score']}/6"
            logging.info(f"Found Joanna's score for Wordle #{WORDLE_NUMBER}: {score_display}")
            if joanna_score['emoji_pattern']:
                logging.info(f"Emoji pattern:\n{joanna_score['emoji_pattern']}")
                emoji_rows = joanna_score['emoji_pattern'].count('\n') + 1
                logging.info(f"Pattern has {emoji_rows} rows but score is {score_display}")
            return True
        else:
            logging.info(f"Joanna has no score for Wordle #{WORDLE_NUMBER}")
            return False
    
    finally:
        conn.close()

def remove_joanna_score():
    """Remove Joanna's score for Wordle #1500"""
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get player_id for Joanna
        cursor.execute("SELECT id FROM player WHERE name = ?", (PLAYER_NAME,))
        player_row = cursor.fetchone()
        
        if not player_row:
            logging.error(f"Player '{PLAYER_NAME}' not found in database")
            return False
        
        player_id = player_row['id']
        
        # Delete Joanna's score for this Wordle
        cursor.execute("""
            DELETE FROM score
            WHERE player_id = ? AND wordle_number = ?
        """, (player_id, WORDLE_NUMBER))
        
        if cursor.rowcount > 0:
            logging.info(f"Removed {cursor.rowcount} score entry for {PLAYER_NAME}, Wordle #{WORDLE_NUMBER}")
            conn.commit()
            return True
        else:
            logging.info(f"No scores found to remove for {PLAYER_NAME}, Wordle #{WORDLE_NUMBER}")
            return False
    
    except sqlite3.Error as e:
        logging.error(f"Database error during score removal: {e}")
        return False
    
    finally:
        conn.close()

def check_if_reset_needed():
    """Check if the weekly reset is needed (Monday after 3:00am)"""
    now = datetime.now()
    
    # Check if it's Monday
    is_monday = (now.weekday() == 0)  # 0 = Monday, 1 = Tuesday, etc.
    
    # Check if it's after 3:00am
    is_after_3am = (now.hour >= 3)
    
    # Determine the start of this week (Monday 3:00am)
    start_of_week = now - timedelta(days=now.weekday())  # Beginning of Monday
    start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
    
    # If today is not Monday or it's before 3:00am, adjust to the previous week's Monday
    if not (is_monday and is_after_3am):
        start_of_week = start_of_week - timedelta(days=7)
    
    # Check if we've already done a reset since the start_of_week
    if os.path.exists(RESET_MARKER_FILE):
        with open(RESET_MARKER_FILE, 'r') as f:
            try:
                last_reset_str = f.read().strip()
                last_reset = datetime.strptime(last_reset_str, '%Y-%m-%d %H:%M:%S')
                
                # If we've already reset after this week's start, no need to reset again
                if last_reset >= start_of_week:
                    logging.info(f"Weekly reset already performed on {last_reset_str}")
                    return False
            except ValueError:
                # If the file content is invalid, proceed with reset
                logging.warning("Invalid last reset timestamp, will perform reset")
    
    # Either we have never reset or it's time for a new reset
    if is_monday and is_after_3am:
        logging.info(f"Weekly reset needed. It's Monday {now.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    else:
        logging.info(f"No weekly reset needed. It's {now.strftime('%A')}, not Monday after 3:00am")
        return False

def mark_reset_complete():
    """Mark that we've completed the weekly reset"""
    with open(RESET_MARKER_FILE, 'w') as f:
        reset_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        f.write(reset_time)
    logging.info(f"Marked weekly reset as completed at {reset_time}")

def update_website_and_push():
    """Update website and push to GitHub"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            
            logging.info("Running force_update.py...")
            force_result = subprocess.run(["python", "force_update.py"], capture_output=True, text=True)
            
            if force_result.returncode == 0:
                logging.info("Force update successful")
                return True
            else:
                logging.error(f"Force update failed: {force_result.stderr}")
                return False
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error in update_website_and_push: {e}")
        return False

def main():
    """Main function to run all fixes"""
    logging.info("Starting Wordle League fix process")
    
    # PART 1: Fix Joanna's incorrect score
    logging.info("STEP 1: Checking for Joanna's score")
    
    # Check if Joanna has a score
    has_score = check_joanna_score()
    
    if has_score:
        # Remove the score if it exists
        logging.info("Found incorrect score for Joanna, removing...")
        if remove_joanna_score():
            # Verify the score was removed
            if not check_joanna_score():
                logging.info("Successfully removed Joanna's score")
            else:
                logging.error("Failed to remove Joanna's score")
        else:
            logging.error("Error removing Joanna's score")
    else:
        logging.info("No action needed, Joanna doesn't have a score for this Wordle")
    
    # PART 2: Weekly Reset Check
    logging.info("\nSTEP 2: Checking for weekly reset")
    
    # Check if reset is needed
    if check_if_reset_needed():
        logging.info("Weekly reset needed, performing reset...")
        
        # Mark reset as complete (to prevent duplicate resets)
        mark_reset_complete()
    else:
        logging.info("No weekly reset needed at this time")
    
    # PART 3: Update website with all changes
    logging.info("\nSTEP 3: Updating website and pushing to GitHub")
    
    if update_website_and_push():
        logging.info("Website update and GitHub push completed successfully")
    else:
        logging.error("Failed to update website or push to GitHub")
    
    logging.info("\nAll fixes completed!")

if __name__ == "__main__":
    main()
