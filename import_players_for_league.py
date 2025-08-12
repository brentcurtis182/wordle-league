#!/usr/bin/env python3
"""
Import Players for Multi-League Support
This script imports players from CSV files into the database with league association.
It ensures players can be in multiple leagues with the same phone number but possibly different names.
"""

import csv
import sqlite3
import json
import os
import sys
import logging
from datetime import datetime

# Set up logging
log_file = 'import_players_league.log'
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

def setup_players_table():
    """Set up the players table with league support if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if players table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Check if league_id column exists
            cursor.execute("PRAGMA table_info(players)")
            columns = cursor.fetchall()
            has_league_id = any(col[1] == 'league_id' for col in columns)
            
            if not has_league_id:
                # Back up existing players
                logging.info("Backing up existing players table")
                cursor.execute("CREATE TABLE players_backup AS SELECT * FROM players")
                
                # Drop and recreate players table with league_id
                cursor.execute("DROP TABLE players")
                table_exists = False
        
        if not table_exists:
            logging.info("Creating players table with league support")
            cursor.execute("""
            CREATE TABLE players (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone_number TEXT NOT NULL,  /* Can be phone number, email, or any identifier */
                league_id INTEGER NOT NULL,
                nickname TEXT,
                UNIQUE(phone_number, league_id)
            )
            """)
            
            # Restore data if we backed it up
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='players_backup'")
            backup_exists = cursor.fetchone() is not None
            
            if backup_exists:
                logging.info("Restoring player data from backup")
                cursor.execute("""
                INSERT INTO players (name, phone_number, league_id, nickname)
                SELECT name, phone_number, 1, name FROM players_backup
                """)
                
                # Clean up backup
                cursor.execute("DROP TABLE players_backup")
            
        conn.commit()
        logging.info("Players table setup complete")
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error setting up players table: {e}")
        return False
        
    finally:
        conn.close()

def import_players_for_league(league_id, csv_file):
    """Import players for a specific league from CSV file"""
    if not os.path.exists(csv_file):
        logging.error(f"CSV file not found: {csv_file}")
        return False
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if league exists
        cursor.execute("SELECT * FROM leagues WHERE league_id = ?", (league_id,))
        league = cursor.fetchone()
        
        if not league:
            logging.error(f"League with ID {league_id} does not exist")
            return False
            
        # Read and import players
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Support multiple identifier column names
                identifier = None
                
                # Try various possible column names for phone/identifier
                for col_name in ['phone_number', 'Phone Number', 'email', 'identifier', 'contact']:
                    if col_name in row and row[col_name].strip():
                        identifier = row[col_name].strip()
                        break
                
                # Try various possible column names for name
                name = None
                for name_col in ['name', 'Player Names', 'Name', 'player']:
                    if name_col in row and row[name_col].strip():
                        name = row[name_col].strip()
                        break
                
                if not name or not identifier:
                    logging.warning(f"Skipping row without proper name or identifier: {row}")
                    continue
                    
                phone_number = identifier  # Use identifier in place of phone_number
                nickname = row.get('nickname', name).strip()
                
                # Check if player already exists in this league
                cursor.execute("""
                SELECT id FROM players 
                WHERE phone_number = ? AND league_id = ?
                """, (phone_number, league_id))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing player
                    cursor.execute("""
                    UPDATE players SET name = ?, nickname = ?
                    WHERE phone_number = ? AND league_id = ?
                    """, (name, nickname, phone_number, league_id))
                    logging.info(f"Updated player {name} ({phone_number}) in league {league_id}")
                else:
                    # Insert new player
                    cursor.execute("""
                    INSERT INTO players (name, phone_number, league_id, nickname)
                    VALUES (?, ?, ?, ?)
                    """, (name, phone_number, league_id, nickname))
                    logging.info(f"Added player {name} ({phone_number}) to league {league_id}")
        
        conn.commit()
        logging.info(f"Successfully imported players for league {league_id} from {csv_file}")
        return True
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error importing players: {e}")
        return False
        
    finally:
        conn.close()

def main():
    """Main function to import players for all leagues"""
    logging.info("Starting player import for multi-league support")
    
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found. Please create it first.")
        return False
        
    # Set up players table with league support
    if not setup_players_table():
        logging.error("Failed to set up players table. Aborting.")
        return False
        
    # Load league configuration
    with open('league_config.json', 'r') as f:
        config = json.load(f)
        
    # Import players for each league
    success = True
    for league in config['leagues']:
        league_id = league['league_id']
        players_csv = league['players_csv']
        
        if os.path.exists(players_csv):
            if not import_players_for_league(league_id, players_csv):
                logging.error(f"Failed to import players for league {league_id}")
                success = False
        else:
            logging.warning(f"CSV file {players_csv} not found for league {league_id}")
    
    if success:
        logging.info("Player import complete for all leagues!")
    else:
        logging.warning("Player import completed with some errors. Check log for details.")
    
    return success

if __name__ == "__main__":
    main()
