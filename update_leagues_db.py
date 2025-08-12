#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to update the database with new leagues (4 and 5)
and add the players from league4players.csv and league5players.csv
"""

import sqlite3
import csv
import os
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_leagues_db.log"),
        logging.StreamHandler()
    ]
)

def load_league_config():
    """Load league configuration from league_config.json"""
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
            return config['leagues']
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return []

def update_leagues_table(conn, leagues_config):
    """Update the leagues table with new leagues"""
    cursor = conn.cursor()
    
    # Get existing leagues
    cursor.execute("SELECT league_id FROM leagues")
    existing_leagues = [row[0] for row in cursor.fetchall()]
    
    # Add new leagues from config if they don't exist
    for league in leagues_config:
        league_id = league['league_id']
        if league_id not in existing_leagues:
            try:
                cursor.execute(
                    """
                    INSERT INTO leagues (league_id, name, thread_id, description)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        league_id,
                        league['name'],
                        league.get('thread_id', f"league_{league_id}_thread"),
                        league.get('description', f"League {league_id}")
                    )
                )
                logging.info(f"Added league {league_id}: {league['name']} to database")
            except Exception as e:
                logging.error(f"Error adding league {league_id}: {e}")
    
    conn.commit()

def add_players_from_csv(conn, league_id, csv_file):
    """Add players from CSV file to the players table"""
    if not os.path.exists(csv_file):
        logging.error(f"CSV file not found: {csv_file}")
        return
    
    cursor = conn.cursor()
    players_added = 0
    
    try:
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header row
            
            # Find the name and phone columns
            name_col = header.index('Name') if 'Name' in header else 0
            phone_col = header.index('Phone') if 'Phone' in header else 1
            
            # Add each player
            for row in reader:
                if len(row) < max(name_col, phone_col) + 1:
                    continue  # Skip incomplete rows
                
                name = row[name_col].strip()
                phone = row[phone_col].strip()
                if not name or not phone:
                    continue  # Skip empty entries
                
                # Clean phone number
                phone = ''.join(c for c in phone if c.isdigit())
                
                # Check if player already exists for this league
                cursor.execute(
                    "SELECT id FROM players WHERE phone_number = ? AND league_id = ?",
                    (phone, league_id)
                )
                if cursor.fetchone():
                    logging.info(f"Player {name} already exists in league {league_id}")
                    continue
                
                # Add player
                cursor.execute(
                    """
                    INSERT INTO players (name, phone_number, league_id, nickname)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, phone, league_id, name)
                )
                players_added += 1
    except Exception as e:
        logging.error(f"Error adding players from {csv_file}: {e}")
        
    conn.commit()
    logging.info(f"Added {players_added} players to league {league_id} from {csv_file}")

def main():
    """Main function to update the database"""
    logging.info("Starting database update for new leagues")
    
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        logging.info("Connected to database")
        
        # Load league config
        leagues_config = load_league_config()
        if not leagues_config:
            logging.error("Failed to load league config, aborting")
            return
        
        # Update leagues table
        update_leagues_table(conn, leagues_config)
        
        # Add players from CSV files for leagues 4 and 5
        for league in leagues_config:
            league_id = league['league_id']
            if league_id in [4, 5]:
                players_csv = league.get('players_csv')
                if players_csv:
                    logging.info(f"Adding players for league {league_id} from {players_csv}")
                    add_players_from_csv(conn, league_id, players_csv)
        
        conn.close()
        logging.info("Database update completed successfully")
        
    except Exception as e:
        logging.error(f"Error updating database: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()
