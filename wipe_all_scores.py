#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple script to wipe all scores from both database tables.
"""

import sqlite3
import logging
import os
import shutil
from datetime import datetime

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

def wipe_all_scores():
    """Wipe all scores from all database tables."""
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First, back up the current database state
        backup_db()
        
        # Delete scores from the 'scores' table
        try:
            cursor.execute("DELETE FROM scores")
            logging.info(f"Deleted rows from 'scores' table")
        except sqlite3.OperationalError as e:
            logging.warning(f"Could not delete from 'scores' table: {e}")
        
        # Delete scores from the 'score' table
        try:
            cursor.execute("DELETE FROM score")
            logging.info(f"Deleted rows from 'score' table")
        except sqlite3.OperationalError as e:
            logging.warning(f"Could not delete from 'score' table: {e}")
        
        # Commit changes
        conn.commit()
        logging.info("All scores have been wiped from the database")
        
        print("Database has been wiped clean of all scores")
        print("Now run the integrated_auto_update.py script to extract fresh Wordle #1500 scores")
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Starting database wipe operation...")
    wipe_all_scores()
    logging.info("Database wipe operation completed")
