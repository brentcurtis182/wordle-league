#!/usr/bin/env python
# Direct SQL fix for Evan's score to ensure it shows as X/6 (7)

import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def fix_evan_score():
    """Directly update Evan's score to X/6 (7) in the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get Evan's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Evan'")
        result = cursor.fetchone()
        if not result:
            logging.error("Evan not found in player table")
            return False
            
        evan_id = result[0]
        logging.info(f"Found Evan's ID: {evan_id}")
        
        # Check current score
        cursor.execute(
            "SELECT id, score FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (evan_id,)
        )
        score_row = cursor.fetchone()
        
        if score_row:
            score_id, current_score = score_row
            logging.info(f"Current score for Evan's Wordle #1500: {current_score}")
            
            # Update to X/6 (7)
            cursor.execute(
                "UPDATE score SET score = 7 WHERE id = ?",
                (score_id,)
            )
            conn.commit()
            
            # Verify the update
            cursor.execute(
                "SELECT score FROM score WHERE id = ?", 
                (score_id,)
            )
            new_score = cursor.fetchone()[0]
            logging.info(f"Updated score: {new_score} (should be 7 for X/6)")
            
            conn.close()
            return True
        else:
            logging.error("No score found for Evan's Wordle #1500")
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Error updating score: {e}")
        return False

if __name__ == "__main__":
    logging.info("Fixing Evan's score to X/6...")
    success = fix_evan_score()
    
    if success:
        logging.info("✅ Successfully updated Evan's score to X/6")
        logging.info("Now running integrated_auto_update.py to update the website...")
        
        import os
        os.system("python integrated_auto_update.py")
    else:
        logging.error("Failed to update Evan's score")
