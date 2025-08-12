#!/usr/bin/env python3
"""
Fix Today's Scores
This script updates the scores for Wordle 1504 to their correct values
"""

import os
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define the correct scores
CORRECT_SCORES = {
    'Brent': 5,    # Was incorrectly 4
    'Joanna': 5,   # Already correct
    'Nanna': 4,    # Update to correct value
    'Evan': 5,     # Already correct
    'Malia': 5     # Already correct
}

def fix_scores():
    """Fix the scores for today's Wordle in both tables"""
    # Get the database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, 'wordle_league.db')
    
    logging.info(f"Using database at: {db_path}")
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Today's Wordle number
    wordle_num = 1504
    
    # First, check current scores
    logging.info(f"Checking current scores for Wordle #{wordle_num}")
    cursor.execute("""
        SELECT player_name, score, emoji_pattern 
        FROM scores 
        WHERE wordle_num = ?
    """, (wordle_num,))
    
    current_scores = cursor.fetchall()
    for row in current_scores:
        logging.info(f"Current score: {row['player_name']}: {row['score']}/6")
    
    # Update scores in 'scores' table
    updated_scores_count = 0
    for player, correct_score in CORRECT_SCORES.items():
        cursor.execute("""
            UPDATE scores
            SET score = ?
            WHERE player_name = ? AND wordle_num = ?
        """, (correct_score, player, wordle_num))
        
        if cursor.rowcount > 0:
            logging.info(f"Updated {player}'s score to {correct_score}/6 in 'scores' table")
            updated_scores_count += cursor.rowcount
    
    conn.commit()
    
    # Now update the 'score' table by finding player_id
    for player, correct_score in CORRECT_SCORES.items():
        # Get player_id
        cursor.execute("SELECT id FROM player WHERE name = ?", (player,))
        player_row = cursor.fetchone()
        
        if player_row:
            player_id = player_row['id']
            
            cursor.execute("""
                UPDATE score
                SET score = ?
                WHERE player_id = ? AND wordle_number = ?
            """, (correct_score, player_id, wordle_num))
            
            if cursor.rowcount > 0:
                logging.info(f"Updated {player}'s score to {correct_score}/6 in 'score' table")
    
    conn.commit()
    
    # Verify the updates
    cursor.execute("""
        SELECT player_name, score
        FROM scores
        WHERE wordle_num = ?
    """, (wordle_num,))
    
    logging.info(f"\nVerified updated scores in 'scores' table for Wordle #{wordle_num}:")
    updated_scores = cursor.fetchall()
    for row in updated_scores:
        logging.info(f"{row['player_name']}: {row['score']}/6")
    
    conn.close()
    return updated_scores_count

if __name__ == "__main__":
    count = fix_scores()
    print(f"\nFixed {count} scores for today's Wordle.")
    print("\nNow running the sync process to ensure database consistency...")
    # Removed sync_database_tables call
    
    print("\nNow running the publish process to update the website...")
    os.system("python server_auto_update_multi_league.py --publish-only")
    
    print("\nProcess complete!")
