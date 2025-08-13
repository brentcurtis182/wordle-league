#!/usr/bin/env python3
"""
Quick script to manually add a Wordle PAL score to the database
This will add your score without needing to use Selenium for extraction
"""

import sqlite3
import logging
import os
import sys
import json
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('pal_score.log', 'w'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Constants
WORDLE_DATABASE = 'wordle_league.db'
LEAGUE_ID = 3  # Wordle PAL League

def get_league_config():
    """Load league configuration from JSON file"""
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found")
        return None
        
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return None

def get_player_names_for_league(league_id):
    """Get all player names in the specified league"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT name, nickname, phone_number FROM players
        WHERE league_id = ?
        """, (league_id,))
        
        players = cursor.fetchall()
        
        result = []
        for name, nickname, phone in players:
            display_name = nickname if nickname else name
            result.append((display_name, phone))
            
        return result
    except Exception as e:
        logging.error(f"Error getting players: {e}")
        return []
    finally:
        if conn:
            conn.close()

def add_score_to_db(phone_number, wordle_num, score, emoji_pattern, league_id):
    """Add a score to the database for a specific league"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Get player name from phone number
        cursor.execute("""
        SELECT name FROM players
        WHERE phone_number = ? AND league_id = ?
        """, (phone_number, league_id))
        
        player_result = cursor.fetchone()
        if not player_result:
            logging.error(f"Player with phone {phone_number} not found in league {league_id}")
            return False
            
        player_name = player_result[0]
        
        # Check if the score already exists
        cursor.execute("""
        SELECT id FROM scores
        WHERE player_name = ? AND wordle_num = ? AND league_id = ?
        """, (player_name, wordle_num, league_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing score
            cursor.execute("""
            UPDATE scores
            SET score = ?, emoji_pattern = ?, timestamp = ?
            WHERE player_name = ? AND wordle_num = ? AND league_id = ?
            """, (score, emoji_pattern, today, player_name, wordle_num, league_id))
            logging.info(f"Updated score for {player_name} in league {league_id}")
        else:
            # Insert new score
            cursor.execute("""
            INSERT INTO scores (player_name, wordle_num, score, emoji_pattern, timestamp, league_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (player_name, wordle_num, score, emoji_pattern, today, league_id))
            logging.info(f"Added new score for {player_name} in league {league_id}")
        
        # Also update the 'score' table for compatibility
        # First get player_id
        cursor.execute("""
        SELECT id FROM players
        WHERE phone_number = ? AND league_id = ?
        """, (phone_number, league_id))
        
        player_id_result = cursor.fetchone()
        if not player_id_result:
            logging.warning(f"Could not find player ID for phone {phone_number} in legacy table update")
            return True  # Still return true since main scores table was updated
            
        player_id = player_id_result[0]
        
        cursor.execute("""
        SELECT id FROM score
        WHERE player_id = ? AND wordle_number = ? AND league_id = ?
        """, (player_id, wordle_num, league_id))
        
        existing_legacy = cursor.fetchone()
        
        if existing_legacy:
            # Update existing legacy score
            cursor.execute("""
            UPDATE score
            SET score = ?, date = ?
            WHERE player_id = ? AND wordle_number = ? AND league_id = ?
            """, (score, today, player_id, wordle_num, league_id))
        else:
            # Insert new legacy score
            cursor.execute("""
            INSERT INTO score (player_id, wordle_number, score, date, league_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (player_id, wordle_num, score, today, league_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        return True
    except Exception as e:
        logging.error(f"Error adding score: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_todays_wordle_number():
    """Get today's Wordle number"""
    # Wordle #1 was released on June 19, 2021
    wordle_start_date = datetime(2021, 6, 19).date()
    today = datetime.now().date()
    
    # Calculate days between start date and today
    days_since_start = (today - wordle_start_date).days
    
    # Wordle number is days since start + 1
    wordle_number = days_since_start + 1
    logging.info(f"Today's Wordle number is {wordle_number}")
    
    return wordle_number

def main():
    logging.info("Starting Wordle PAL score addition")
    
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Find PAL league in config
    pal_league = None
    for league in config['leagues']:
        if league['league_id'] == LEAGUE_ID:
            pal_league = league
            break
    
    if not pal_league:
        logging.error(f"League with ID {LEAGUE_ID} not found in configuration")
        return
        
    logging.info(f"Adding score for {pal_league['name']} league")
    
    # Get players in PAL league
    players = get_player_names_for_league(LEAGUE_ID)
    
    if not players:
        logging.error(f"No players found in league {LEAGUE_ID}")
        return
        
    # Display available players
    logging.info(f"Available players in {pal_league['name']} league:")
    for i, (name, phone) in enumerate(players):
        print(f"{i+1}. {name} ({phone})")
    
    # Select Vox's phone number (assuming Vox is your player)
    # Find Vox's phone number
    vox_phone = None
    for name, phone in players:
        if name.lower() == "vox":
            vox_phone = phone
            break
    
    if not vox_phone:
        logging.error("Could not find Vox in the player list")
        return
    
    # Today's Wordle number
    wordle_num = get_todays_wordle_number()
    
    # Add score for Vox
    score = "4"  # A score of 4/6
    emoji_pattern = "⬜🟩⬜🟨⬜\n⬜🟩🟩🟨⬜\n⬜🟩🟩🟩⬜\n🟩🟩🟩🟩🟩"
    
    if add_score_to_db(vox_phone, wordle_num, score, emoji_pattern, LEAGUE_ID):
        logging.info(f"Successfully added score for Vox: Wordle {wordle_num} - {score}/6")
    else:
        logging.error("Failed to add score")

if __name__ == "__main__":
    main()
