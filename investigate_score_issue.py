#!/usr/bin/env python3
"""
Script to investigate why Keith is being assigned Joanna's score in League 2 (Wordle Gang)
"""

import sqlite3
import datetime
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("investigation.log"),
        logging.StreamHandler()
    ]
)

def check_database_structure():
    """Check the database structure to understand the tables and columns"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logging.info(f"Tables in database: {tables}")
        
        # Get schema for scores table
        cursor.execute("PRAGMA table_info(scores)")
        scores_schema = cursor.fetchall()
        logging.info(f"Scores table schema: {scores_schema}")
        
        # Get schema for players table
        cursor.execute("PRAGMA table_info(players)")
        players_schema = cursor.fetchall()
        logging.info(f"Players table schema: {players_schema}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error checking database structure: {e}")
        return False

def check_player_records():
    """Check player records for Joanna and Keith"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get player records for Joanna and Keith
        cursor.execute("SELECT * FROM players WHERE name LIKE '%Joanna%' OR name LIKE '%Keith%'")
        player_records = cursor.fetchall()
        logging.info(f"Player records for Joanna and Keith: {player_records}")
        
        # List all players in league 2 (Wordle Gang)
        cursor.execute("SELECT * FROM players WHERE league = 2")
        league2_players = cursor.fetchall()
        logging.info(f"All players in league 2: {league2_players}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error checking player records: {e}")
        return False

def check_recent_scores():
    """Check recent scores for Joanna and Keith"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get recent scores for Joanna
        cursor.execute("SELECT * FROM scores WHERE player LIKE '%Joanna%' ORDER BY date DESC LIMIT 10")
        joanna_scores = cursor.fetchall()
        logging.info(f"Recent scores for Joanna: {joanna_scores}")
        
        # Get recent scores for Keith
        cursor.execute("SELECT * FROM scores WHERE player LIKE '%Keith%' ORDER BY date DESC LIMIT 10")
        keith_scores = cursor.fetchall()
        logging.info(f"Recent scores for Keith: {keith_scores}")
        
        # Get today's scores
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute("SELECT * FROM scores WHERE date = ?", (today,))
        today_scores = cursor.fetchall()
        logging.info(f"Today's scores ({today}): {today_scores}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error checking recent scores: {e}")
        return False

def check_extraction_logic():
    """Check extraction logic in the code files"""
    try:
        # Check key files for phone number mapping logic
        key_files = [
            'direct_hidden_extraction.py',
            'integrated_auto_update_multi_league.py',
            'export_leaderboard_multi_league.py'
        ]
        
        for file in key_files:
            if os.path.exists(file):
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for key patterns in the code that might explain the issue
                phone_mapping = "phone" in content and "mapping" in content
                joanna_specific = "joanna" in content.lower() or "keith" in content.lower()
                
                logging.info(f"File {file}: Contains phone mapping logic: {phone_mapping}, Contains Joanna/Keith specific code: {joanna_specific}")
            else:
                logging.warning(f"File {file} not found")
        
        return True
    except Exception as e:
        logging.error(f"Error checking extraction logic: {e}")
        return False

def check_phone_to_player_mapping():
    """Check how phone numbers are mapped to players"""
    try:
        # Read the player CSV files
        league_files = []
        for i in range(1, 6):
            file = f"league{i}players.csv"
            if os.path.exists(file):
                league_files.append(file)
        
        for file in league_files:
            logging.info(f"Checking player mappings in {file}")
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "joanna" in line.lower() or "keith" in line.lower():
                        logging.info(f"Found relevant mapping in {file}: {line.strip()}")
        
        return True
    except Exception as e:
        logging.error(f"Error checking phone to player mapping: {e}")
        return False

def find_potential_causes():
    """Analyze all data to find potential causes for the score assignment issue"""
    logging.info("Analyzing all data to find potential causes...")
    
    # Check if there might be multiple players with the same phone number
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check for duplicate phone numbers across different players
        cursor.execute("SELECT phone, COUNT(*) as count, GROUP_CONCAT(name) as players FROM players GROUP BY phone HAVING count > 1")
        duplicate_phones = cursor.fetchall()
        
        if duplicate_phones:
            logging.warning(f"Found duplicate phone mappings: {duplicate_phones}")
        else:
            logging.info("No duplicate phone mappings found")
            
        # Check if Joanna's phone might be mapped to Keith in league 2
        cursor.execute("SELECT * FROM players WHERE (name LIKE '%Joanna%' OR name LIKE '%Keith%') AND league = 2")
        league2_joanna_keith = cursor.fetchall()
        logging.info(f"Joanna and Keith records in league 2: {league2_joanna_keith}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error finding potential causes: {e}")

def main():
    logging.info("Starting investigation into Keith's score assignment issue...")
    
    check_database_structure()
    check_player_records()
    check_recent_scores()
    check_extraction_logic()
    check_phone_to_player_mapping()
    find_potential_causes()
    
    logging.info("Investigation completed. Check the log for details.")
    print("\nInvestigation completed. Results have been logged to 'investigation.log'.")
    print("Please check the log file for detailed findings about why Keith might be getting assigned Joanna's score.")

if __name__ == "__main__":
    main()
