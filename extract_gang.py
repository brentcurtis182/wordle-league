#!/usr/bin/env python3
"""
Script to run the extraction process for just the Wordle Gang league
"""

import subprocess
import sys
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Run the integrated extraction script focusing on the Gang league"""
    try:
        logging.info("Running extraction for Wordle Gang league...")
        
        # Call the integrated script with league_id=2 argument
        result = subprocess.run(
            [sys.executable, "integrated_auto_update_multi_league.py", "--league", "2"],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Output the results
        logging.info("Extraction completed")
        logging.info(f"STDOUT: {result.stdout}")
        
        if result.stderr:
            logging.warning(f"STDERR: {result.stderr}")
        
        # Now check if Mylene's score was extracted
        logging.info("Checking for Mylene's scores...")
        check_scores()
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running extraction: {e}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
    except Exception as e:
        logging.error(f"Error: {str(e)}")

def check_scores():
    """Check if Mylene's scores were extracted"""
    import sqlite3
    
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get Mylene's player ID
        cursor.execute("""
            SELECT id, phone_number FROM players 
            WHERE name = 'Mylene' AND league_id = 2
        """)
        
        player = cursor.fetchone()
        if not player:
            logging.error("Mylene not found in the players table for Wordle Gang")
            return
            
        player_id, phone = player
        logging.info(f"Found Mylene with ID: {player_id}, Phone: {phone}")
        
        # Get her scores
        cursor.execute("""
            SELECT score, wordle_number, timestamp 
            FROM scores 
            WHERE player_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (player_id,))
        
        scores = cursor.fetchall()
        
        if not scores:
            logging.warning("No scores found for Mylene")
            return
            
        logging.info(f"Found {len(scores)} scores for Mylene:")
        for score_row in scores:
            score, wordle_num, timestamp = score_row
            logging.info(f"Wordle #{wordle_num}: Score: {score}, Timestamp: {timestamp}")
            
        conn.close()
    except Exception as e:
        logging.error(f"Error checking scores: {str(e)}")

if __name__ == "__main__":
    main()
