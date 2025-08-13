#!/usr/bin/env python
# Database fix script for Vox's PAL league score
# This script normalizes the Wordle number format by removing commas

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database location
WORDLE_DATABASE = "wordle_league.db"

def fix_wordle_number_format():
    """Fix Wordle number format by removing commas in PAL league scores"""
    conn = None
    
    try:
        logging.info("Starting database fix for PAL league Wordle number formats")
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # First, backup the scores table
        logging.info("Creating backup of scores table")
        cursor.execute("CREATE TABLE IF NOT EXISTS scores_backup AS SELECT * FROM scores")
        conn.commit()
        
        # Get all PAL league scores with comma format
        logging.info("Finding PAL league scores with comma format")
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, emoji_pattern, league_id
        FROM scores
        WHERE league_id = 3 AND wordle_num LIKE '%,%'
        """)
        
        comma_scores = cursor.fetchall()
        logging.info(f"Found {len(comma_scores)} scores with comma format in PAL league")
        
        # Update each score to remove commas
        for score in comma_scores:
            score_id = score[0]
            player_name = score[1]
            wordle_with_comma = score[2]
            wordle_without_comma = wordle_with_comma.replace(",", "")
            
            logging.info(f"Updating score ID {score_id} for player {player_name}: {wordle_with_comma} -> {wordle_without_comma}")
            
            cursor.execute("""
            UPDATE scores
            SET wordle_num = ?
            WHERE id = ?
            """, (wordle_without_comma, score_id))
        
        # Commit the changes
        conn.commit()
        logging.info(f"Successfully updated {len(comma_scores)} scores")
        
        # Verify the fix
        cursor.execute("""
        SELECT player_name, wordle_num, score
        FROM scores
        WHERE league_id = 3
        """)
        
        updated_scores = cursor.fetchall()
        logging.info("Updated PAL league scores:")
        for score in updated_scores:
            logging.info(f"  Player: {score[0]}, Wordle #: {score[1]}, Score: {score[2]}")
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logging.error(f"Exception: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    
    logging.info("Database fix script completed")

if __name__ == "__main__":
    fix_wordle_number_format()
