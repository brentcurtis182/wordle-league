#!/usr/bin/env python3
"""
Clean Slate Database Script

This script:
1. Backs up the current database
2. Wipes all scores while keeping player information
3. Creates a new clean schema for scores with proper relationships
"""

import os
import sqlite3
import logging
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("clean_slate.log"),
        logging.StreamHandler()
    ]
)

# Database paths
DB_PATH = 'wordle_league.db'
BACKUP_PATH = f'wordle_league_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

def backup_database():
    """Create a backup of the current database"""
    try:
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, BACKUP_PATH)
            logging.info(f"Database backed up to {BACKUP_PATH}")
            return True
        else:
            logging.error(f"Database {DB_PATH} not found")
            return False
    except Exception as e:
        logging.error(f"Error backing up database: {e}")
        return False

def get_existing_players():
    """Extract all player information from the existing database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all players from the players table
        cursor.execute("SELECT id, name, league_id, phone_number, nickname FROM players ORDER BY league_id, name")
        players = cursor.fetchall()
        
        logging.info(f"Extracted {len(players)} players from database")
        conn.close()
        
        return players
    except Exception as e:
        logging.error(f"Error getting existing players: {e}")
        return []

def create_clean_schema():
    """Create a clean schema with proper relationships"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Keep the existing players table
        
        # Drop the old scores tables
        cursor.execute("DROP TABLE IF EXISTS scores")
        cursor.execute("DROP TABLE IF EXISTS score")
        
        # Create a new unified scores table with proper relationships
        cursor.execute("""
        CREATE TABLE scores (
            id INTEGER PRIMARY KEY,
            player_id INTEGER NOT NULL,
            wordle_number INTEGER NOT NULL,
            score INTEGER NOT NULL,
            date TEXT NOT NULL,
            emoji_pattern TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE (player_id, wordle_number)
        )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX idx_scores_player_id ON scores (player_id)")
        cursor.execute("CREATE INDEX idx_scores_wordle_number ON scores (wordle_number)")
        cursor.execute("CREATE INDEX idx_scores_date ON scores (date)")
        
        conn.commit()
        logging.info("Created new clean schema for scores table")
        
        # Verify the structure
        cursor.execute("PRAGMA table_info(scores)")
        logging.info("New scores table structure:")
        for column in cursor.fetchall():
            logging.info(f"  {column}")
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error creating clean schema: {e}")
        return False

def normalize_phone_number(phone):
    """Normalize a phone number to standard format"""
    if not phone:
        return "0000000000"  # Placeholder for missing phone numbers
        
    # Strip all non-numeric characters
    clean_phone = ''.join(c for c in phone if c.isdigit())
    
    # Make sure we have 10 or 11 digits
    if len(clean_phone) == 10:
        # Add country code if missing
        clean_phone = '1' + clean_phone
    elif len(clean_phone) > 11:
        # Truncate if too long
        clean_phone = clean_phone[:11]
    elif len(clean_phone) < 10:
        # Too short to be valid
        return "1" + clean_phone.ljust(10, '0')  # Pad with zeros
        
    return clean_phone

def clean_phone_numbers():
    """Normalize all phone numbers in the player table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all players with phone numbers
        cursor.execute("SELECT id, name, phone_number, league_id FROM players")
        players = cursor.fetchall()
        
        updated_count = 0
        for player_id, name, phone, league_id in players:
            # Normalize the phone number
            normalized_phone = normalize_phone_number(phone)
            
            # Always store a valid phone number (original or normalized)
            cursor.execute(
                "UPDATE players SET phone_number = ? WHERE id = ?", 
                (normalized_phone, player_id)
            )
            
            if normalized_phone != phone:
                updated_count += 1
                logging.info(f"Updated phone for {name} (league {league_id}): {phone} -> {normalized_phone}")
        
        conn.commit()
        logging.info(f"Normalized {updated_count} phone numbers")
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error normalizing phone numbers: {e}")
        return False

def verify_player_table():
    """Verify the player table has all required leagues and players"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check leagues are properly set up
        cursor.execute("SELECT DISTINCT league_id FROM players ORDER BY league_id")
        leagues = [row[0] for row in cursor.fetchall()]
        
        logging.info(f"Found leagues with IDs: {leagues}")
        
        # Get player counts by league
        cursor.execute("""
        SELECT league_id, COUNT(*) 
        FROM players 
        GROUP BY league_id 
        ORDER BY league_id
        """)
        
        league_counts = cursor.fetchall()
        for league_id, count in league_counts:
            league_name = "Unknown"
            if league_id == 1:
                league_name = "Wordle Warriorz"
            elif league_id == 2:
                league_name = "Wordle Gang"
            elif league_id == 3:
                league_name = "PAL"
                
            logging.info(f"League {league_id} ({league_name}): {count} players")
            
            # Log players in each league
            cursor.execute("SELECT name, phone_number FROM players WHERE league_id = ? ORDER BY name", (league_id,))
            players = cursor.fetchall()
            
            logging.info(f"Players in league {league_id}:")
            for name, phone in players:
                logging.info(f"  - {name}: {phone}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error verifying player table: {e}")
        return False

def main():
    """Main function to create a clean slate database"""
    logging.info("Starting clean slate database creation")
    
    # Step 1: Backup the current database
    if not backup_database():
        logging.error("Database backup failed. Aborting.")
        return False
    
    # Step 2: Clean up phone numbers
    if not clean_phone_numbers():
        logging.error("Phone number cleanup failed. Aborting.")
        return False
    
    # Step 3: Get existing players
    players = get_existing_players()
    if not players:
        logging.error("Failed to extract players. Aborting.")
        return False
    
    # Step 4: Create clean schema
    if not create_clean_schema():
        logging.error("Failed to create clean schema. Aborting.")
        return False
    
    # Step 5: Verify player table
    if not verify_player_table():
        logging.warning("Issues found in player table. Please review.")
    
    logging.info("Clean slate database successfully created!")
    logging.info(f"The database has been backed up to {BACKUP_PATH}")
    logging.info("All score data has been wiped, player data is preserved.")
    logging.info("Phone numbers have been normalized across all leagues.")
    logging.info("Ready for fresh extraction with the new schema.")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Clean slate database created!")
        print(f"Backup created at: {BACKUP_PATH}")
        print("\nNext steps:")
        print("1. Run extraction script to get fresh scores")
        print("2. Check that scores are saved correctly in the new schema")
    else:
        print("\nERROR: Failed to create clean slate database.")
        print("Check the log file for details.")
