#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to wipe all scores from the database and prepare for a fresh extraction of only Wordle #1500.
This creates a clean slate to avoid any confusion between database tables and ensure consistent data.
"""

import sqlite3
import logging
import os
import shutil
from datetime import datetime
import sys

# Configure logging with UTF-8 encoding
logging.basicConfig(
    filename='wipe_and_reset.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Add console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

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
        return backup_path
    except Exception as e:
        logging.error(f"Failed to create database backup: {e}")
        return None

def wipe_all_scores():
    """Wipe all scores from all database tables."""
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, back up the current database state
        backup_path = backup_db()
        if not backup_path:
            logging.error("Backup failed. Aborting wipe operation.")
            return False
        
        # Check if the user wants to proceed
        print("\n⚠️ WARNING: This will DELETE ALL SCORES from the database!")
        print("A backup has been created at:", backup_path)
        confirm = input("Type 'YES' to continue or anything else to cancel: ")
        if confirm.strip().upper() != "YES":
            print("Operation cancelled.")
            logging.info("Wipe operation cancelled by user")
            return False
        
        # Delete scores from the 'scores' table
        try:
            cursor.execute("DELETE FROM scores")
            logging.info(f"Deleted {cursor.rowcount} rows from 'scores' table")
        except sqlite3.OperationalError as e:
            logging.warning(f"Could not delete from 'scores' table: {e}")
        
        # Delete scores from the 'score' table
        try:
            cursor.execute("DELETE FROM score")
            logging.info(f"Deleted {cursor.rowcount} rows from 'score' table")
        except sqlite3.OperationalError as e:
            logging.warning(f"Could not delete from 'score' table: {e}")
        
        # Commit changes
        conn.commit()
        logging.info("All scores have been wiped from the database")
        
        print("\n✅ Database has been wiped clean of all scores")
        print("Next steps:")
        print("1. Run the integrated_auto_update.py script to extract fresh Wordle #1500 scores")
        print("2. The script will use the fixed logic to properly save scores and emoji patterns")
        print("3. Run the export_leaderboard.py script to update the website with the new data")
        
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Starting database wipe operation...")
    success = wipe_all_scores()
    if success:
        logging.info("Database wipe completed successfully")
    else:
        logging.error("Database wipe failed or was cancelled")
        print("\n❌ Operation failed or was cancelled. See log file for details.")
