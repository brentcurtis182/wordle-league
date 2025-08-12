#!/usr/bin/env python3
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_mylene_score():
    """Check if Mylene's score has been extracted for the Wordle Gang league"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get Mylene's player ID in the Gang league (league_id = 2)
        cursor.execute("SELECT id FROM players WHERE name = 'Mylene' AND league_id = 2")
        player_id_result = cursor.fetchone()
        
        if not player_id_result:
            logging.info("Mylene not found in the Wordle Gang league (league_id = 2)")
            return
        
        player_id = player_id_result[0]
        logging.info(f"Found Mylene with player ID: {player_id} in league 2")
        
        # Get her recent scores
        cursor.execute("""
            SELECT score, wordle_number, timestamp 
            FROM scores 
            WHERE player_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (player_id,))
        
        scores = cursor.fetchall()
        
        if not scores:
            logging.info("No scores found for Mylene in the database")
            return
        
        logging.info(f"Found {len(scores)} recent scores for Mylene:")
        for score_row in scores:
            score, wordle_num, timestamp = score_row
            logging.info(f"Wordle #{wordle_num}: Score: {score}, Timestamp: {timestamp}")
        
        # Check the thread ID being used for Wordle Gang
        cursor.execute("""
            SELECT value FROM config WHERE key = 'league_2_thread_id'
        """)
        thread_id_result = cursor.fetchone()
        thread_id = thread_id_result[0] if thread_id_result else "Not found in config table"
        
        logging.info(f"Current thread ID being used for Wordle Gang: {thread_id}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logging.error(f"Error checking Mylene's score: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting Mylene score check...")
    check_mylene_score()
    logging.info("Finished checking.")
