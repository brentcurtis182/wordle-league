#!/usr/bin/env python3
"""
Database Schema Update for Multi-League Support
This script updates the database schema to support multiple leagues
while preserving all existing data and functionality.
"""

import sqlite3
import json
import os
import sys
import logging
from datetime import datetime

# Set up logging
log_file = 'update_database_leagues.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Database configuration
DB_PATH = 'wordle_league.db'
BACKUP_PATH = f'wordle_league_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

def backup_database():
    """Create a backup of the database before making changes"""
    import shutil
    if os.path.exists(DB_PATH):
        logging.info(f"Creating backup of database to {BACKUP_PATH}")
        shutil.copy2(DB_PATH, BACKUP_PATH)
        return True
    else:
        logging.error(f"Database file {DB_PATH} not found!")
        return False

def check_if_league_tables_exist():
    """Check if the leagues table already exists"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leagues'")
    leagues_table_exists = cursor.fetchone() is not None
    
    conn.close()
    return leagues_table_exists

def update_schema():
    """Update the database schema to support multiple leagues"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Create leagues table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS leagues (
            league_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            thread_id TEXT NOT NULL,
            description TEXT
        )
        """)
        
        # Check if the scores table has a league_id column
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        has_league_id = any(col[1] == 'league_id' for col in columns)
        
        if not has_league_id:
            logging.info("Adding league_id column to scores table")
            cursor.execute("ALTER TABLE scores ADD COLUMN league_id INTEGER DEFAULT 1")
            
        # Check if the score table has a league_id column
        cursor.execute("PRAGMA table_info(score)")
        columns = cursor.fetchall()
        has_league_id = any(col[1] == 'league_id' for col in columns)
        
        if not has_league_id:
            logging.info("Adding league_id column to score table")
            cursor.execute("ALTER TABLE score ADD COLUMN league_id INTEGER DEFAULT 1")
            
        # Set up the default league
        cursor.execute("SELECT * FROM leagues WHERE league_id = 1")
        if cursor.fetchone() is None:
            with open('league_config.json', 'r') as f:
                config = json.load(f)
                default_league = next(l for l in config['leagues'] if l['league_id'] == 1)
                
            cursor.execute("""
            INSERT INTO leagues (league_id, name, thread_id, description)
            VALUES (?, ?, ?, ?)
            """, (
                default_league['league_id'],
                default_league['name'],
                default_league['thread_id'],
                default_league['description']
            ))
            logging.info(f"Added default league: {default_league['name']}")
        
        conn.commit()
        logging.info("Database schema successfully updated!")
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error updating schema: {e}")
        return False
        
    finally:
        conn.close()

def main():
    """Main function to update the database schema"""
    logging.info("Starting database schema update for multi-league support")
    
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found. Please create it first.")
        return False
    
    # Check if we've already updated the schema
    if check_if_league_tables_exist():
        logging.info("League tables already exist. No update needed.")
        return True
        
    # Create a backup first
    if not backup_database():
        logging.error("Failed to create backup. Aborting.")
        return False
        
    # Update the schema
    success = update_schema()
    
    if success:
        logging.info("Database schema updated successfully for multi-league support!")
        logging.info(f"A backup was created at {BACKUP_PATH}")
    else:
        logging.error("Failed to update database schema.")
        logging.info(f"You can restore from backup at {BACKUP_PATH} if needed.")
    
    return success

if __name__ == "__main__":
    main()
