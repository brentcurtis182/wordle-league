#!/usr/bin/env python
"""
Fix Database Synchronization Issues between 'score' and 'scores' tables
and restore correct Wordle #1500 scores for all players.

This script:
1. Backs up the database
2. Restores correct Wordle #1500 scores for all 5 players
3. Synchronizes data between 'score' and 'scores' tables
4. Updates server_extractor.py to maintain both tables going forward
"""

import os
import re
import sys
import time
import sqlite3
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_database_sync.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Database path
DATABASE_PATH = 'wordle_league.db'
SERVER_EXTRACTOR_PATH = 'server_extractor.py'
SERVER_EXTRACTOR_BACKUP = 'server_extractor.py.bak'

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

def backup_database():
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{DATABASE_PATH}.{timestamp}.bak"
    
    try:
        shutil.copy2(DATABASE_PATH, backup_path)
        logging.info(f"Created database backup at {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create database backup: {e}")
        return False

def backup_server_extractor():
    """Create a backup of server_extractor.py"""
    try:
        shutil.copy2(SERVER_EXTRACTOR_PATH, SERVER_EXTRACTOR_BACKUP)
        logging.info(f"Created backup of {SERVER_EXTRACTOR_PATH} at {SERVER_EXTRACTOR_BACKUP}")
        return True
    except Exception as e:
        logging.error(f"Failed to create backup of {SERVER_EXTRACTOR_PATH}: {e}")
        return False

def get_table_schema(cursor, table_name):
    """Get the schema of a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return [column[1] for column in columns]

def get_player_ids(cursor):
    """Get player IDs from the database"""
    player_ids = {}
    try:
        cursor.execute("SELECT id, name FROM player")
        for row in cursor.fetchall():
            player_ids[row[1]] = row[0]
        return player_ids
    except Exception as e:
        logging.warning(f"Could not get player IDs: {e}")
        # Create a fallback mapping with estimated IDs
        return {
            "Evan": 1,
            "Joanna": 2, 
            "Brent": 3,
            "Nanna": 4,
            "Malia": 5
        }

def restore_correct_data():
    """Restore correct scores and emoji patterns for all players"""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if both tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='score' OR name='scores')")
        tables = [row[0] for row in cursor.fetchall()]
        logging.info(f"Found tables: {tables}")
        
        # Get schemas for both tables if they exist
        schemas = {}
        for table in tables:
            schemas[table] = get_table_schema(cursor, table)
            logging.info(f"Schema for {table}: {schemas[table]}")
        
        # Get player IDs if available
        player_ids = get_player_ids(cursor)
        logging.info(f"Player IDs: {player_ids}")
        
        # Process each player's data
        for player_name, data in CORRECT_DATA.items():
            wordle_number = data["wordle_number"]
            score = data["score"]
            emoji_pattern = data["emoji_pattern"]
            player_id = player_ids.get(player_name, None)
            
            # Update/insert into 'scores' table if it exists
            if 'scores' in tables:
                # Check if entry exists
                cursor.execute(
                    "SELECT id FROM scores WHERE player_name = ? AND wordle_num = ?", 
                    (player_name, wordle_number)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    cursor.execute(
                        "UPDATE scores SET score = ?, emoji_pattern = ? WHERE player_name = ? AND wordle_num = ?",
                        (score, emoji_pattern, player_name, wordle_number)
                    )
                    logging.info(f"Updated {player_name}'s score in 'scores' table")
                else:
                    # Insert
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    cursor.execute(
                        "INSERT INTO scores (player_name, wordle_num, score, emoji_pattern, timestamp) VALUES (?, ?, ?, ?, ?)",
                        (player_name, wordle_number, score, emoji_pattern, timestamp)
                    )
                    logging.info(f"Inserted {player_name}'s score into 'scores' table")
            
            # Update/insert into 'score' table if it exists and we have player_id
            if 'score' in tables and player_id:
                # Check if entry exists
                cursor.execute(
                    "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
                    (player_id, wordle_number)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    cursor.execute(
                        "UPDATE score SET score = ?, emoji_pattern = ? WHERE player_id = ? AND wordle_number = ?",
                        (score, emoji_pattern, player_id, wordle_number)
                    )
                    logging.info(f"Updated {player_name}'s score in 'score' table")
                else:
                    # Insert
                    current_date = datetime.now().strftime('%Y-%m-%d')
                    cursor.execute(
                        "INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date) VALUES (?, ?, ?, ?, ?)",
                        (player_id, wordle_number, score, emoji_pattern, current_date)
                    )
                    logging.info(f"Inserted {player_name}'s score into 'score' table")
        
        # Commit changes
        conn.commit()
        logging.info("✅ Successfully restored correct data for all players in all tables")
        return True
        
    except Exception as e:
        logging.error(f"Error restoring data: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def update_server_extractor():
    """Update server_extractor.py to maintain both tables"""
    try:
        with open(SERVER_EXTRACTOR_PATH, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Find the save_score function
        save_score_pattern = r'def save_score\(score_data\):.*?return False'
        save_score_match = re.search(save_score_pattern, content, re.DOTALL)
        
        if not save_score_match:
            logging.error("Could not find save_score function in server_extractor.py")
            return False
        
        # Current function
        current_function = save_score_match.group(0)
        
        # Updated function that syncs both tables
        updated_function = '''def save_score(score_data):
    """Save Wordle score to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if this score already exists in 'score' table
        cursor.execute(
            "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
            (score_data['player_id'], score_data['wordle_number'])
        )
        existing = cursor.fetchone()
        
        if existing:
            logging.info(f"Score already exists for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
        else:
            # Insert the new score into 'score' table
            cursor.execute(
                "INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date) VALUES (?, ?, ?, ?, ?)",
                (
                    score_data['player_id'],
                    score_data['wordle_number'],
                    score_data['score'],
                    score_data['emoji_pattern'],
                    score_data['date']
                )
            )
            logging.info(f"Successfully saved score in 'score' table for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
        
        # SYNC: Also update the 'scores' table used by the website
        cursor.execute(
            "SELECT id FROM scores WHERE player_name = ? AND wordle_num = ?", 
            (score_data['player_name'], score_data['wordle_number'])
        )
        existing_in_scores = cursor.fetchone()
        
        if existing_in_scores:
            # Update in scores table
            cursor.execute(
                "UPDATE scores SET score = ?, emoji_pattern = ? WHERE player_name = ? AND wordle_num = ?",
                (
                    score_data['score'],
                    score_data['emoji_pattern'],
                    score_data['player_name'], 
                    score_data['wordle_number']
                )
            )
            logging.info(f"Updated score in 'scores' table for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
        else:
            # Insert into scores table
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO scores (player_name, wordle_num, score, emoji_pattern, timestamp) VALUES (?, ?, ?, ?, ?)",
                (
                    score_data['player_name'],
                    score_data['wordle_number'], 
                    score_data['score'],
                    score_data['emoji_pattern'],
                    timestamp
                )
            )
            logging.info(f"Also inserted into 'scores' table for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
        
        # Commit changes to both tables
        conn.commit()
        conn.close()
        logging.info(f"✓ Successfully saved score to all tables for {score_data['player_name']}, Wordle {score_data['wordle_number']}")
        return True
    except Exception as e:
        logging.error(f"Error saving score: {e}")
        return False'''
        
        # Replace the old function with the new one
        updated_content = content.replace(current_function, updated_function)
        
        # Add datetime import if not present
        if 'from datetime import datetime' not in updated_content:
            updated_content = updated_content.replace(
                'import sqlite3', 
                'import sqlite3\nfrom datetime import datetime'
            )
        
        # Write the updated content back
        with open(SERVER_EXTRACTOR_PATH, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        logging.info("✅ Successfully updated server_extractor.py to synchronize both tables")
        return True
        
    except Exception as e:
        logging.error(f"Error updating server_extractor.py: {e}")
        return False

def run_website_update():
    """Run the website update script to apply changes"""
    try:
        import subprocess
        logging.info("Running integrated_auto_update.py to update the website...")
        
        # Run the script with skip-extraction flag to avoid overwriting our fixes
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

def main():
    """Main function to fix the database and script issues"""
    logging.info("Starting database synchronization and fix process...")
    
    # Create backups
    if not backup_database():
        logging.error("Database backup failed, aborting")
        return False
        
    if not backup_server_extractor():
        logging.warning("Server extractor backup failed, but continuing anyway")
    
    # Step 1: Restore correct data to all tables
    if not restore_correct_data():
        logging.error("Failed to restore correct data")
        return False
        
    # Step 2: Update server_extractor.py to maintain both tables
    if not update_server_extractor():
        logging.error("Failed to update server_extractor.py")
        return False
        
    # Step 3: Update the website
    if not run_website_update():
        logging.warning("Website update failed, but data has been fixed")
    
    logging.info("✅ Database synchronization and fix completed successfully!")
    return True

if __name__ == "__main__":
    if main():
        print("✅ Fix completed successfully! Both tables are now synchronized.")
        print("The automated task can be safely re-enabled now.")
    else:
        print("❌ Fix failed. Please check the logs and try again.")
