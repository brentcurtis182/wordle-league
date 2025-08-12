#!/usr/bin/env python
# Fix Evan's Wordle score to show X/6 instead of 6/6

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def fix_evans_score():
    """Update Evan's Wordle #1500 score to X/6 (value 7) instead of 6/6"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Find Evan's ID and score entry
        cursor.execute("SELECT id FROM player WHERE name = 'Evan'")
        result = cursor.fetchone()
        if not result:
            logging.error("Evan not found in players table")
            conn.close()
            return False
        
        evan_id = result[0]
        logging.info(f"Found Evan's ID: {evan_id}")
        
        # First, check the scores table structure
        cursor.execute("PRAGMA table_info(scores)")
        columns = [row[1] for row in cursor.fetchall()]
        logging.info(f"Scores table columns: {columns}")
        
        # Check if score exists in scores table
        cursor.execute(
            "SELECT id, score, wordle_number FROM scores WHERE player = ? AND wordle_number = 1500", 
            ('Evan',)
        )
        score = cursor.fetchone()
        
        if score:
            score_id, current_score, wordle_num = score
            logging.info(f"Found score in scores table: ID={score_id}, Score={current_score}, Wordle#{wordle_num}")
            
            # Update to X/6 (value 7)
            cursor.execute(
                "UPDATE scores SET score = 7 WHERE id = ?",
                (score_id,)
            )
            conn.commit()
            logging.info("✅ Updated Evan's score to X/6 (value 7) in scores table")
        else:
            logging.warning("Could not find Evan's score in scores table")
        
        # Also check the score table (singular) which might be used
        try:
            cursor.execute("PRAGMA table_info(score)")
            columns = [row[1] for row in cursor.fetchall()]
            logging.info(f"Score table columns: {columns}")
            
            cursor.execute(
                "SELECT id, score, wordle_number FROM score WHERE player_id = ? AND wordle_number = 1500", 
                (evan_id,)
            )
            score = cursor.fetchone()
            
            if score:
                score_id, current_score, wordle_num = score
                logging.info(f"Found score in score table: ID={score_id}, Score={current_score}, Wordle#{wordle_num}")
                
                # Update to X/6 (value 7)
                cursor.execute(
                    "UPDATE score SET score = 7 WHERE id = ?",
                    (score_id,)
                )
                conn.commit()
                logging.info("✅ Updated Evan's score to X/6 (value 7) in score table")
            else:
                logging.warning("Could not find Evan's score in score table")
        except sqlite3.OperationalError as e:
            logging.info(f"Score table check error (may not exist): {e}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error fixing Evan's score: {e}")
        if conn:
            conn.close()
        return False

def check_database():
    """Check all scores for Evan"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Check for scores table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if cursor.fetchone():
            cursor.execute("SELECT id, player, score, wordle_number, date FROM scores WHERE player = 'Evan'")
            scores = cursor.fetchall()
            if scores:
                logging.info("\nEvan's scores in scores table:")
                for score in scores:
                    score_display = "X/6" if score[2] == 7 else f"{score[2]}/6"
                    logging.info(f"ID: {score[0]}, Score: {score_display}, Wordle #{score[3]}, Date: {score[4]}")
        
        # Check for score table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score'")
        if cursor.fetchone():
            # First find Evan's player ID
            cursor.execute("SELECT id FROM player WHERE name = 'Evan'")
            result = cursor.fetchone()
            if result:
                evan_id = result[0]
                cursor.execute("SELECT id, score, wordle_number, date FROM score WHERE player_id = ?", (evan_id,))
                scores = cursor.fetchall()
                if scores:
                    logging.info("\nEvan's scores in score table:")
                    for score in scores:
                        score_display = "X/6" if score[1] == 7 else f"{score[1]}/6"
                        logging.info(f"ID: {score[0]}, Score: {score_display}, Wordle #{score[2]}, Date: {score[3]}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error checking database: {e}")

if __name__ == "__main__":
    logging.info("Fixing Evan's Wordle #1500 score to X/6...")
    fix_evans_score()
    logging.info("\nChecking database after fix:")
    check_database()
    logging.info("\nRunning integrated_auto_update.py to update website...")
    import os
    os.system("python integrated_auto_update.py")
