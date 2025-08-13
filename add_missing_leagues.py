#!/usr/bin/env python3
"""
Create missing leagues in the database
This script ensures that all leagues defined in league_config.json exist in the database.
"""

import sqlite3
import json
import os
import logging
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('add_leagues.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Database configuration
DB_PATH = 'wordle_league.db'

def add_missing_leagues():
    """Add any missing leagues from config to the database"""
    # Load league configuration
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found")
        return False
        
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for league in config['leagues']:
            league_id = league['league_id']
            
            # Check if league exists
            cursor.execute("SELECT league_id FROM leagues WHERE league_id = ?", (league_id,))
            exists = cursor.fetchone() is not None
            
            if not exists:
                # Add missing league
                cursor.execute("""
                INSERT INTO leagues (league_id, name, thread_id, description)
                VALUES (?, ?, ?, ?)
                """, (
                    league_id,
                    league['name'],
                    league['thread_id'],
                    league['description']
                ))
                logging.info(f"Added missing league: {league['name']} (ID: {league_id})")
        
        conn.commit()
        conn.close()
        logging.info("All leagues have been added to the database")
        return True
        
    except Exception as e:
        logging.error(f"Error adding leagues: {e}")
        return False

if __name__ == "__main__":
    add_missing_leagues()
