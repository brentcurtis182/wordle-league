#!/usr/bin/env python3
"""
Display player IDs for specific leagues
"""

import os
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
DB_PATH = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')

def show_players_for_league(league_id, league_name):
    """Show players and their IDs for a specific league"""
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Query players for this league
        cursor.execute("SELECT id, name, phone_number FROM players WHERE league_id = ? ORDER BY name", (league_id,))
        players = cursor.fetchall()
        
        if not players:
            logging.info(f"No players found for league {league_name} (ID: {league_id})")
            return
        
        logging.info(f"Players for league {league_name} (ID: {league_id}):")
        logging.info("-" * 50)
        logging.info(f"{'ID':<6} | {'Name':<20} | {'Phone Number':<15}")
        logging.info("-" * 50)
        
        for player in players:
            player_id, name, phone = player
            logging.info(f"{player_id:<6} | {name:<20} | {phone if phone else 'N/A':<15}")
        
        logging.info("-" * 50)
        conn.close()
        
    except Exception as e:
        logging.error(f"Error retrieving players for league {league_id}: {e}")

def main():
    """Show player IDs for multiple leagues"""
    logging.info("Player IDs for New Leagues")
    
    # League 4: Wordle Party
    show_players_for_league(4, "Wordle Party")
    
    # League 5: Wordle Vball
    show_players_for_league(5, "Wordle Vball")

if __name__ == "__main__":
    main()
