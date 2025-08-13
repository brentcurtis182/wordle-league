#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct fix for emoji patterns using exact patterns provided by the user
"""

import sqlite3
import os
import logging
import shutil
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_exact_patterns.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def backup_db():
    """Create a backup of the database before making changes."""
    try:
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

def fix_patterns():
    """Update database with exact emoji patterns"""
    # The exact patterns as provided
    exact_patterns = {
        'Joanna': "⬛🟨⬛⬛⬛\n⬛🟨🟨⬛⬛\n🟨🟩⬛🟨⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩",
        'Brent': "⬛⬛⬛⬛⬛\n⬛🟨⬛⬛🟨\n🟨⬛🟨⬛🟨\n🟨⬛🟩🟨🟨\n🟩🟩⬛🟩⬛\n🟩🟩🟩🟩🟩",
        'Nanna': "🟩⬛⬛⬛⬛\n🟩⬛🟨⬛⬛\n🟩🟩⬛⬛⬛\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩🟩🟩🟩",
        'Evan': "⬛⬛⬛⬛🟨\n🟩⬛🟨⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩",
        'Malia': "⬛⬛⬛⬛⬛\n⬛⬛🟨⬛⬛\n🟨🟨⬛⬛🟨\n🟩🟩⬛🟩⬛\n🟩🟩⬛🟩🟩\n🟩🟩⬛🟩🟩"
    }
    
    wordle_num = 1500
    
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        for player, pattern in exact_patterns.items():
            # Update scores table
            cursor.execute(
                "SELECT id, emoji_pattern FROM scores WHERE player_name = ? AND wordle_num = ?",
                (player, wordle_num)
            )
            scores_result = cursor.fetchone()
            
            if scores_result:
                cursor.execute(
                    "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                    (pattern, scores_result['id'])
                )
                logging.info(f"Updated {player}'s pattern in scores table to exact pattern")
            else:
                logging.warning(f"No record found for {player} in scores table")
                
            # Update score table (get player_id first)
            cursor.execute("SELECT id FROM player WHERE name = ?", (player,))
            player_row = cursor.fetchone()
            
            if player_row:
                player_id = player_row['id']
                
                cursor.execute(
                    "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?",
                    (player_id, wordle_num)
                )
                score_result = cursor.fetchone()
                
                if score_result:
                    cursor.execute(
                        "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                        (pattern, score_result['id'])
                    )
                    logging.info(f"Updated {player}'s pattern in score table to exact pattern")
                else:
                    logging.warning(f"No record found for {player} in score table")
            else:
                logging.warning(f"Player {player} not found in player table")
        
        conn.commit()
        logging.info(f"All patterns updated to exact patterns")
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
    
    return True

def export_website():
    """Export the website with updated data"""
    try:
        logging.info("Exporting website files")
        result = subprocess.run(
            ["python", "export_leaderboard.py"], 
            capture_output=True, 
            text=True
        )
        if result.returncode == 0:
            logging.info("Website exported successfully")
            return True
        else:
            logging.error(f"Website export error: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Export error: {e}")
        return False

def publish_to_github():
    """Push changes to GitHub with cache-busting commit message"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"Update website with EXACT emoji patterns for Wordle #1500 - {timestamp}"
        
        # Use subprocess to run git commands
        logging.info("Publishing to GitHub")
        subprocess.run(
            ["python", "server_publish_to_github.py"],
            check=True
        )
        
        logging.info("Changes pushed to GitHub")
        return True
    except Exception as e:
        logging.error(f"GitHub publish error: {e}")
        return False

def main():
    """Main function to coordinate all steps"""
    logging.info("Starting exact pattern fix")
    
    # Backup the database
    if not backup_db():
        logging.error("Database backup failed. Aborting.")
        return
    
    # Fix the patterns
    if not fix_patterns():
        logging.error("Pattern fix failed. Aborting.")
        return
    
    # Export the website
    if not export_website():
        logging.error("Website export failed. Continuing anyway...")
    
    # Publish to GitHub
    if not publish_to_github():
        logging.error("GitHub publish failed.")
    else:
        logging.info("Fix completed successfully. Website should be updated with exact patterns.")
        logging.info("Note: It may take a few minutes for GitHub Pages to update.")

if __name__ == "__main__":
    main()
