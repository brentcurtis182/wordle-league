#!/usr/bin/env python
# Restore Joanna's Wordle #1500 score with proper emoji pattern

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def restore_joanna_score():
    """Restore Joanna's Wordle #1500 score with proper emoji pattern"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Find Joanna's ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.error("Joanna not found in players table")
            conn.close()
            return False
        
        joanna_id = result[0]
        logging.info(f"Found Joanna's ID: {joanna_id}")
        
        # Check if score already exists
        cursor.execute(
            "SELECT * FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (joanna_id,)
        )
        score = cursor.fetchone()
        
        if score:
            logging.info(f"Joanna already has a Wordle #1500 score: {score}")
            return True
        
        # The correct emoji pattern for Joanna's 5/6 score
        emoji_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
        
        # Insert the score
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "INSERT INTO score (player_id, score, wordle_number, date, emoji_pattern) VALUES (?, ?, ?, ?, ?)",
            (joanna_id, 5, 1500, today, emoji_pattern)
        )
        
        conn.commit()
        logging.info("✅ Successfully restored Joanna's Wordle #1500 score")
        
        # Modify check_database.py to prevent future removal
        disable_removal_script()
        
        return True
    except Exception as e:
        logging.error(f"Error restoring Joanna's score: {e}")
        return False
    finally:
        if conn:
            conn.close()

def disable_removal_script():
    """Modify the check_database.py script to prevent automatic removal"""
    try:
        with open("check_database.py", "r") as f:
            content = f.read()
        
        # Create backup
        with open("check_database.py.bak", "w") as f:
            f.write(content)
        
        # Replace the removal code with comments
        new_content = content.replace(
            "if joanna_has_score:\n        logging.info(\"Removing Joanna's score...\")\n        remove_joanna_score()",
            "# DISABLED: Do not remove Joanna's score\n    # if joanna_has_score:\n    #     logging.info(\"Removing Joanna's score...\")\n    #     remove_joanna_score()"
        )
        
        with open("check_database.py", "w") as f:
            f.write(new_content)
        
        logging.info("✅ Modified check_database.py to prevent future removal of Joanna's score")
        return True
    except Exception as e:
        logging.error(f"Error modifying check_database.py: {e}")
        return False

if __name__ == "__main__":
    logging.info("Restoring Joanna's Wordle #1500 score...")
    restore_joanna_score()
