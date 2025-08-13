#!/usr/bin/env python
# Check and restore Evan's Wordle #1500 score

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_evans_score():
    """Check if Evan's Wordle #1500 score exists in database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Find Evan's ID
        cursor.execute("SELECT id FROM player WHERE name = 'Evan'")
        result = cursor.fetchone()
        if not result:
            logging.error("Evan not found in players table")
            conn.close()
            return False, None
        
        evan_id = result[0]
        logging.info(f"Found Evan's ID: {evan_id}")
        
        # Check if score exists
        cursor.execute(
            "SELECT * FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (evan_id,)
        )
        score = cursor.fetchone()
        
        if score:
            logging.info(f"Evan already has a Wordle #1500 score: {score}")
            return True, score
        else:
            logging.warning("❌ Evan's Wordle #1500 score not found in database!")
            return False, None
    except Exception as e:
        logging.error(f"Error checking Evan's score: {e}")
        return False, None
    finally:
        if conn:
            conn.close()

def restore_evans_score():
    """Restore Evan's Wordle #1500 score with proper emoji pattern"""
    has_score, score_data = check_evans_score()
    
    if has_score:
        logging.info("Evan's score already exists, no restoration needed")
        return True
        
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Find Evan's ID
        cursor.execute("SELECT id FROM player WHERE name = 'Evan'")
        result = cursor.fetchone()
        if not result:
            logging.error("Evan not found in players table")
            conn.close()
            return False
        
        evan_id = result[0]
        
        # The emoji pattern for Evan's score (6/6)
        emoji_pattern = "⬛⬛⬛⬛🟨\n🟩⬛🟨⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩"
        
        # Insert the score
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT INTO score (player_id, score, wordle_number, date, emoji_pattern) VALUES (?, ?, ?, ?, ?)",
            (evan_id, 6, 1500, today, emoji_pattern)
        )
        
        conn.commit()
        logging.info("✅ Successfully restored Evan's Wordle #1500 score")
        
        return True
    except Exception as e:
        logging.error(f"Error restoring Evan's score: {e}")
        return False
    finally:
        if conn:
            conn.close()

def check_all_scores_for_today():
    """List all scores for today"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get all scores for today
        cursor.execute("""
            SELECT p.name, s.score, s.wordle_number, s.date, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.date = ?
            ORDER BY s.score
        """, (today,))
        
        scores = cursor.fetchall()
        
        logging.info(f"Found {len(scores)} scores for today ({today}):")
        for score in scores:
            logging.info(f"Player: {score[0]}, Score: {score[1]}/6, Wordle #{score[2]}")
        
        return scores
    except Exception as e:
        logging.error(f"Error checking today's scores: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Checking and restoring Evan's Wordle #1500 score...")
    restore_evans_score()
    logging.info("\nAll scores for today:")
    check_all_scores_for_today()
    logging.info("\nNow running integrated_auto_update to update website...")
    import os
    os.system("python integrated_auto_update.py")
