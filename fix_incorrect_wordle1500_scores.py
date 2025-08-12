#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix incorrect Wordle #1500 scores in the database.

This script corrects any wrong scores for Wordle #1500, particularly
Nanna's score which should be 6/6 rather than the incorrectly saved 4/6.
It also updates the website with the corrected data.
"""

import sqlite3
import logging
import os
import sys
import subprocess

# Configure logging
logging.basicConfig(
    filename='fix_wordle1500_scores.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # Use UTF-8 encoding to avoid issues with emoji characters
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def fix_wordle1500_scores():
    """
    Fix incorrect scores for Wordle #1500 in both score and scores tables.
    """
    # Known correct scores for Wordle #1500
    correct_scores = {
        'Nanna': 6,  # Nanna's correct score is 6/6, not 4/6
        # Add other players here if needed
    }
    
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, back up the current database state
        backup_db()
        
        # Fix scores in 'scores' table
        for player_name, correct_score in correct_scores.items():
            logging.info(f"Fixing {player_name}'s Wordle #1500 score to {correct_score}/6")
            
            # Check if the player exists in the scores table
            cursor.execute(
                "SELECT id, score, emoji_pattern FROM scores WHERE wordle_num = ? AND player_name = ?", 
                (1500, player_name)
            )
            result = cursor.fetchone()
            
            if result:
                current_score = result['score']
                if current_score != correct_score:
                    cursor.execute(
                        "UPDATE scores SET score = ? WHERE id = ?",
                        (correct_score, result['id'])
                    )
                    logging.info(f"Updated {player_name}'s score from {current_score}/6 to {correct_score}/6 in 'scores' table")
                else:
                    logging.info(f"{player_name}'s score is already correct ({correct_score}/6) in 'scores' table")
            else:
                logging.warning(f"No record found for {player_name} in 'scores' table")
        
        # Also check for the 'score' table which may be used by the website
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score'")
            if cursor.fetchone():
                # Fix scores in 'score' table if it exists
                for player_name, correct_score in correct_scores.items():
                    # Check different column name combinations that might exist
                    possible_queries = [
                        "SELECT id, score FROM score WHERE wordle_number = ? AND player = ?",
                        "SELECT id, score FROM score WHERE wordle_num = ? AND player_name = ?",
                        "SELECT id, score FROM score WHERE wordle_num = ? AND player = ?",
                        "SELECT id, score FROM score WHERE wordle_number = ? AND player_name = ?"
                    ]
                    
                    record_found = False
                    for query in possible_queries:
                        try:
                            cursor.execute(query, (1500, player_name))
                            result = cursor.fetchone()
                            if result:
                                record_found = True
                                current_score = result['score']
                                if current_score != correct_score:
                                    cursor.execute(
                                        "UPDATE score SET score = ? WHERE id = ?",
                                        (correct_score, result['id'])
                                    )
                                    logging.info(f"Updated {player_name}'s score from {current_score}/6 to {correct_score}/6 in 'score' table")
                                else:
                                    logging.info(f"{player_name}'s score is already correct ({correct_score}/6) in 'score' table")
                                break
                        except sqlite3.OperationalError:
                            # This query pattern didn't work, try the next one
                            continue
                    
                    if not record_found:
                        logging.warning(f"No record found for {player_name} in 'score' table")
        except sqlite3.Error as e:
            logging.error(f"Error checking 'score' table: {e}")
        
        # Commit changes
        conn.commit()
        logging.info("All Wordle #1500 scores have been corrected in the database")
        
        # Update the website to reflect the changes
        update_website()
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def backup_db():
    """Create a backup of the database before making changes."""
    try:
        import shutil
        from datetime import datetime
        
        backup_dir = 'db_backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'wordle_league_{timestamp}.db')
        
        # Copy the database to the backup location
        shutil.copy2('wordle_league.db', backup_path)
        logging.info(f"Database backed up to {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create database backup: {e}")
        return False

def update_website():
    """Update the website to reflect the corrected scores."""
    try:
        logging.info("Updating website with corrected scores...")
        
        # This assumes you have a script to update your website
        # Replace with the actual command you use to update your website
        if os.path.exists('update_website.py'):
            subprocess.run(['python', 'update_website.py'], check=True)
            logging.info("Website updated successfully")
        elif os.path.exists('publish_to_github.py'):
            subprocess.run(['python', 'publish_to_github.py'], check=True)
            logging.info("Website published to GitHub successfully")
        else:
            logging.warning("No website update script found. Please manually update the website.")
    except subprocess.SubprocessError as e:
        logging.error(f"Failed to update website: {e}")

if __name__ == "__main__":
    logging.info("Starting Wordle #1500 score correction script...")
    fix_wordle1500_scores()
    logging.info("Wordle #1500 score correction completed!")
