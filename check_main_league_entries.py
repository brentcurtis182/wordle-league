import sqlite3
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("check_main_league.log")
    ]
)

def check_main_league_entries():
    """Check all entries for today's Wordle in the main league (league_id=1)"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check today's Wordle entries for main league
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1503 AND league_id = 1
        ORDER BY player_name
        """)
        
        entries = cursor.fetchall()
        
        logging.info(f"Found {len(entries)} entries for Wordle #1503 in the main league:")
        
        for entry in entries:
            score_id, player_name, wordle_num, score, timestamp, league_id = entry
            logging.info(f"ID: {score_id}, Player: {player_name}, Score: {score}, Date: {timestamp}")
        
        # Check for false entries - any players not expected to have a score
        # According to user, there should be exactly 3 scores
        expected_count = 3
        if len(entries) != expected_count:
            logging.warning(f"WARNING: Found {len(entries)} entries but expected {expected_count}!")
            logging.warning("This may indicate some false entries")
        else:
            logging.info(f"✓ Number of entries matches expected count ({expected_count})")
        
        # Check yesterday's entries for reference
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1502 AND league_id = 1
        ORDER BY player_name
        """)
        
        yesterday_entries = cursor.fetchall()
        
        logging.info(f"\nFound {len(yesterday_entries)} entries for Wordle #1502 (yesterday) in the main league:")
        
        for entry in yesterday_entries:
            score_id, player_name, wordle_num, score, timestamp, league_id = entry
            logging.info(f"ID: {score_id}, Player: {player_name}, Score: {score}, Date: {timestamp}")
            
        return entries
            
    except Exception as e:
        logging.error(f"Error checking main league entries: {e}")
        return []
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Checking main league entries for today's Wordle #1503")
    entries = check_main_league_entries()
    
    if entries:
        logging.info(f"Main league has {len(entries)} entries for today:")
        for entry in entries:
            _, player, _, score, timestamp, _ = entry
            logging.info(f"- {player}: {score}/6 ({timestamp})")
    else:
        logging.error("Error retrieving main league entries")
