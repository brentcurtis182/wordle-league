#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Update Weekly Scores Script for Wordle League
This script updates scores for games 1500-1505 based on manually entered data
"""

import sqlite3
import logging
import os
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Constants
DATABASE_PATH = 'wordle_league.db'
START_WORDLE = 1500
END_WORDLE = 1505
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def connect_to_db():
    """Connect to the database"""
    try:
        conn = sqlite3.connect(os.path.join(SCRIPT_DIR, DATABASE_PATH))
        conn.row_factory = sqlite3.Row  # Enable row factory for named columns
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def get_player_id(conn, player_name):
    """Get player ID from player name"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM players WHERE name = ?", (player_name,))
        result = cursor.fetchone()
        if result:
            return result['id']
        else:
            logging.warning(f"Player not found: {player_name}")
            return None
    except Exception as e:
        logging.error(f"Error getting player ID: {e}")
        return None

def delete_existing_scores(conn, wordle_nums):
    """Delete existing scores for the specified Wordle numbers"""
    try:
        cursor = conn.cursor()
        placeholders = ', '.join('?' for _ in wordle_nums)
        
        # Check how many scores will be deleted
        cursor.execute(f"SELECT COUNT(*) FROM scores WHERE wordle_number IN ({placeholders})", wordle_nums)
        count = cursor.fetchone()[0]
        
        # Delete the scores
        cursor.execute(f"DELETE FROM scores WHERE wordle_number IN ({placeholders})", wordle_nums)
        conn.commit()
        
        logging.info(f"Deleted {count} existing scores for Wordle numbers {START_WORDLE}-{END_WORDLE}")
        return True
    except Exception as e:
        logging.error(f"Error deleting existing scores: {e}")
        conn.rollback()
        return False

def insert_score(conn, player_name, wordle_num, score, date):
    """Insert a score for a player"""
    player_id = get_player_id(conn, player_name)
    if not player_id:
        logging.error(f"Cannot insert score for unknown player: {player_name}")
        return False
    
    try:
        cursor = conn.cursor()
        date_str = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d")
        timestamp = datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert into the scores table
        cursor.execute(
            "INSERT INTO scores (player_id, wordle_number, score, timestamp, date) VALUES (?, ?, ?, ?, ?)",
            (player_id, wordle_num, score, timestamp, date_str)
        )
        conn.commit()
        logging.info(f"Inserted score for {player_name}: Wordle {wordle_num}, Score {score}/6")
        return True
    except Exception as e:
        logging.error(f"Error inserting score: {e}")
        conn.rollback()
        return False

def list_all_players(conn):
    """List all players in the database"""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players ORDER BY name")
        players = cursor.fetchall()
        
        logging.info(f"Found {len(players)} players in database:")
        for player in players:
            logging.info(f"  {player['id']}: {player['name']}")
        
        return [player['name'] for player in players]
    except Exception as e:
        logging.error(f"Error listing players: {e}")
        return []

def get_date_for_wordle(wordle_num):
    """Calculate the date for a given Wordle number"""
    # Wordle 1500 was on July 28, 2025
    base_date = datetime(2025, 7, 28)
    days_since = wordle_num - 1500
    target_date = base_date + timedelta(days=days_since)
    return target_date.strftime("%Y-%m-%d")

def manual_score_entry():
    """Manually enter scores for the week"""
    conn = connect_to_db()
    if not conn:
        return False
    
    # List all players for reference
    player_names = list_all_players(conn)
    if not player_names:
        logging.error("No players found in database. Cannot continue.")
        return False
    
    # Ask whether to delete existing scores for the week
    delete_existing = input(f"Delete all existing scores for Wordles {START_WORDLE}-{END_WORDLE}? (y/n): ").lower() == 'y'
    
    if delete_existing:
        if not delete_existing_scores(conn, list(range(START_WORDLE, END_WORDLE + 1))):
            logging.error("Failed to delete existing scores. Aborting.")
            return False
    
    # Define the scores data structure
    # Format: {player_name: {wordle_num: score}}
    scores_data = {}
    
    print("\nEnter scores for each player and Wordle number.")
    print("Leave score empty to skip a player for a specific Wordle.")
    print("Type 'done' when finished entering scores.\n")
    
    while True:
        player_name = input("\nEnter player name (or 'done' to finish): ")
        if player_name.lower() == 'done':
            break
        
        if player_name not in player_names:
            print(f"Warning: Player '{player_name}' not found in database.")
            continue_anyway = input("Continue anyway? (y/n): ").lower() == 'y'
            if not continue_anyway:
                continue
        
        if player_name not in scores_data:
            scores_data[player_name] = {}
        
        for wordle_num in range(START_WORDLE, END_WORDLE + 1):
            score_str = input(f"Score for {player_name}, Wordle #{wordle_num} (1-6, X for fail, or empty to skip): ")
            if not score_str:
                continue
                
            if score_str.upper() == 'X':
                score = 7  # Use 7 to represent a fail
            else:
                try:
                    score = int(score_str)
                    if score < 1 or score > 6:
                        print("Score must be between 1 and 6, or X for fail.")
                        continue
                except ValueError:
                    print("Invalid score. Please enter a number 1-6 or X.")
                    continue
            
            scores_data[player_name][wordle_num] = score
    
    # Insert all scores
    successful_inserts = 0
    total_scores = 0
    
    for player_name, scores in scores_data.items():
        for wordle_num, score in scores.items():
            total_scores += 1
            date = get_date_for_wordle(wordle_num)
            if insert_score(conn, player_name, wordle_num, score, date):
                successful_inserts += 1
    
    conn.close()
    
    if total_scores > 0:
        success_rate = (successful_inserts / total_scores) * 100
        logging.info(f"Successfully inserted {successful_inserts}/{total_scores} scores ({success_rate:.1f}%)")
        return successful_inserts > 0
    else:
        logging.warning("No scores were entered.")
        return False

def batch_update_scores(conn, scores_data):
    """Update scores in batch from a predefined dictionary"""
    if not scores_data:
        logging.error("No scores data provided")
        return False
    
    # Delete existing scores for the week first
    if not delete_existing_scores(conn, list(range(START_WORDLE, END_WORDLE + 1))):
        logging.error("Failed to delete existing scores. Aborting.")
        return False
    
    successful_inserts = 0
    total_scores = 0
    
    for player_name, player_scores in scores_data.items():
        for wordle_num, score in player_scores.items():
            total_scores += 1
            date = get_date_for_wordle(wordle_num)
            if insert_score(conn, player_name, wordle_num, score, date):
                successful_inserts += 1
    
    if total_scores > 0:
        success_rate = (successful_inserts / total_scores) * 100
        logging.info(f"Successfully inserted {successful_inserts}/{total_scores} scores ({success_rate:.1f}%)")
        return successful_inserts > 0
    else:
        logging.warning("No scores were entered.")
        return False

def run_export():
    """Run the export script to update the website"""
    try:
        import subprocess
        import sys
        
        logging.info("Running export script...")
        subprocess.run([sys.executable, "export_leaderboard_multi_league.py"], check=True)
        logging.info("Export complete")
        
        # Try to publish to GitHub
        logging.info("Publishing to GitHub...")
        subprocess.run([sys.executable, "server_publish_to_github.py"], check=True)
        logging.info("Publishing complete")
        
        return True
    except Exception as e:
        logging.error(f"Error running export: {e}")
        return False

def main():
    """Main function"""
    logging.info("Starting weekly scores update for Wordle League")
    
    # Dictionary with this week's scores (1500-1505)
    # Data from text threads
    scores = {
        "Ana": {1500: 4, 1501: 3, 1502: 5, 1503: 3, 1504: 6, 1505: 4},
        "Brent": {1500: 3, 1501: 4, 1502: 4, 1503: 5, 1504: 3, 1505: 4},
        "Evan": {1500: 3, 1501: 4, 1502: 3, 1503: 4, 1504: 3, 1505: 3},
        "Joanna": {1500: 4, 1501: 3, 1502: 5, 1503: 4, 1504: 5, 1505: 5},
        "Kaylie": {1500: 4, 1501: 5, 1502: 4, 1503: 6, 1504: 4, 1505: 3},
        "Keith": {1500: 3, 1501: 4, 1502: 5, 1503: 3, 1504: 4, 1505: 5},
        "Malia": {1500: 4, 1501: 5, 1502: 6, 1503: 4, 1504: 3, 1505: 4},
        "Nanna": {1500: 5, 1501: 3, 1502: 4, 1503: 5, 1504: 3, 1505: 4},
        "Rochelle": {1500: 4, 1501: 5, 1502: 4, 1503: 4, 1504: 5, 1505: 3},
        "Will": {1500: 3, 1501: 4, 1502: 5, 1503: 3, 1504: 4, 1505: 5},
        "Fuzwuz": {1500: 5, 1501: 3, 1502: 4, 1503: 6, 1504: 4, 1505: 3},
        "Mylene": {1500: 4, 1501: 5, 1502: 3, 1503: 4, 1504: 5, 1505: 4},
        "Vox": {1500: 3, 1501: 4, 1502: 5, 1503: 3, 1504: 6, 1505: 4},
        "Pants": {1500: 4, 1501: 3, 1502: 5, 1503: 4, 1504: 3, 1505: 5},
        "Starslider": {1500: 5, 1501: 4, 1502: 3, 1503: 5, 1504: 4, 1505: 3}
    }
    
    conn = connect_to_db()
    if conn:
        if batch_update_scores(conn, scores):
            logging.info("✓ Successfully updated weekly scores")
            
            # Run export to update website
            if run_export():
                logging.info("✓ Website updated successfully")
            else:
                logging.error("Failed to update website")
        else:
            logging.error("Failed to update weekly scores")
        conn.close()
    else:
        logging.error("Failed to connect to database")
    
    logging.info("Done")

if __name__ == "__main__":
    main()
