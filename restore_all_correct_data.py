#!/usr/bin/env python
"""
Restore all correct data for Wordle #1500 and fix weekly scores calculation
This will:
1. Restore correct emoji patterns for all players
2. Ensure scores are correctly represented (including X/6 for failed attempts)
3. Fix weekly totals calculation
"""

import sqlite3
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_data.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Database path
DATABASE_PATH = 'wordle_league.db'

# Backup the database first
def backup_database():
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{DATABASE_PATH}.{timestamp}.bak"
    
    try:
        import shutil
        shutil.copy2(DATABASE_PATH, backup_path)
        logging.info(f"Created database backup at {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create database backup: {e}")
        return False

# Correct data for all players
CORRECT_DATA = {
    "Evan": {
        "wordle_number": 1500,
        "score": 7,  # X/6 is stored as 7
        "emoji_pattern": "Wordle 1500 X/6\n\n⬜⬜⬜🟨⬜\n🟨⬜⬜🟨⬜\n⬜🟨🟩⬜⬜\n⬜🟩🟩🟨⬜\n⬜🟩🟩⬜🟨\n🟩🟩🟩⬜⬜"
    },
    "Joanna": {
        "wordle_number": 1500,
        "score": 5,
        "emoji_pattern": "Wordle 1500 5/6\n\n⬜⬜⬜🟨⬜\n⬜⬜⬜🟨🟩\n⬜🟨⬜⬜🟩\n⬜🟩🟩⬜🟩\n🟩🟩🟩🟩🟩"
    },
    "Brent": {
        "wordle_number": 1500,
        "score": 6, 
        "emoji_pattern": "Wordle 1500 6/6\n\n⬜⬜⬜🟨⬜\n⬜⬜⬜🟨🟩\n⬜⬜⬜⬜🟩\n⬜🟩🟩⬜🟩\n⬜🟩🟩⬜🟩\n🟩🟩🟩🟩🟩"
    },
    "Nanna": {
        "wordle_number": 1500,
        "score": 4,
        "emoji_pattern": "Wordle 1500 4/6\n\n⬜⬜🟨⬜⬜\n⬜🟨🟨⬜🟨\n🟩🟩🟩⬜⬜\n🟩🟩🟩🟩🟩"
    },
    "Malia": {
        "wordle_number": 1500,
        "score": 7,  # X/6 is stored as 7
        "emoji_pattern": "Wordle 1500 X/6\n\n⬜⬜🟨⬜⬜\n🟨🟨⬜⬜⬜\n⬜🟩🟩⬜⬜\n⬜🟩🟩⬜⬜\n⬜🟩🟩🟨⬜\n🟩🟩🟩⬜🟩"
    }
}

def restore_correct_data():
    """Restore correct scores and emoji patterns for all players"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Update each player's data directly by name
        for player_name, data in CORRECT_DATA.items():
            wordle_number = data["wordle_number"]
            score = data["score"]
            emoji_pattern = data["emoji_pattern"]
            
            # Check if entry exists
            cursor.execute(
                "SELECT id FROM scores WHERE player_name = ? AND wordle_num = ?", 
                (player_name, wordle_number)
            )
            existing_entry = cursor.fetchone()
            
            if existing_entry:
                # Update existing entry
                cursor.execute(
                    "UPDATE scores SET score = ?, emoji_pattern = ? WHERE player_name = ? AND wordle_num = ?",
                    (score, emoji_pattern, player_name, wordle_number)
                )
                logging.info(f"Updated existing entry for {player_name}, Wordle #{wordle_number}, score: {score}")
            else:
                # Insert new entry
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute(
                    "INSERT INTO scores (player_name, wordle_num, score, emoji_pattern, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (player_name, wordle_number, score, emoji_pattern, current_time)
                )
                logging.info(f"Inserted new entry for {player_name}, Wordle #{wordle_number}, score: {score}")
            
        # Fix weekly totals calculation
        fix_weekly_totals(cursor)
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logging.info("✅ Successfully restored correct data for all players")
        return True
        
    except Exception as e:
        logging.error(f"Error restoring data: {e}")
        return False

def fix_weekly_totals(cursor):
    """Fix weekly totals calculation - make sure it counts only 1 game for each player"""
    try:
        # First, make sure there's only one score per player for Wordle #1500
        cursor.execute(
            """
            SELECT player_name, COUNT(*) as count 
            FROM scores 
            WHERE wordle_num = 1500 
            GROUP BY player_name 
            HAVING count > 1
            """
        )
        
        duplicates = cursor.fetchall()
        for player_name, count in duplicates:
            logging.warning(f"Found {count} duplicate scores for player {player_name}, Wordle #1500. Fixing...")
            
            # Keep only the most recently updated score
            cursor.execute(
                """
                DELETE FROM scores 
                WHERE id IN (
                    SELECT id FROM scores 
                    WHERE player_name = ? AND wordle_num = 1500
                    ORDER BY timestamp DESC
                    LIMIT -1 OFFSET 1
                )
                """, 
                (player_name,)
            )
        
        # Now verify weekly totals are correct
        logging.info("Weekly totals should now show correctly with exactly one game per player")
        
    except Exception as e:
        logging.error(f"Error fixing weekly totals: {e}")

def run_website_update():
    """Run the website update script to apply changes"""
    try:
        import subprocess
        logging.info("Running integrated_auto_update.py to update the website...")
        
        # Run the script
        result = subprocess.run(
            ["python", "integrated_auto_update.py", "--skip-extraction", "--publish-only"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Website updated successfully")
            return True
        else:
            logging.error(f"Error updating website: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Exception running website update: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting data restoration process...")
    
    # Create a backup first
    if not backup_database():
        logging.error("Aborting due to backup failure")
        exit(1)
    
    # Restore correct data
    if restore_correct_data():
        # Update the website
        run_website_update()
    else:
        logging.error("Data restoration failed")
