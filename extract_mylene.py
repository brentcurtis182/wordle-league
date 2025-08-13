#!/usr/bin/env python3
"""
Manual extraction script focused on the Wordle Gang league to extract Mylene's score
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the extraction functions
from integrated_auto_update_multi_league import (
    setup_driver, 
    get_todays_wordle_number, 
    extract_scores_for_league,
    process_scores,
    cleanup_driver
)

def main():
    """Run extraction specifically for Wordle Gang league"""
    
    logging.info("=== Starting manual extraction for Wordle Gang league ===")
    
    # League ID for Wordle Gang
    league_id = 2
    league_name = "Wordle Gang"
    
    # Set up the webdriver
    driver = setup_driver()
    
    if not driver:
        logging.error("Failed to set up WebDriver. Exiting.")
        return
    
    try:
        # Get current Wordle number
        today_wordle = get_todays_wordle_number()
        yesterday_wordle = today_wordle - 1
        logging.info(f"Current Wordle: #{today_wordle}, Yesterday's: #{yesterday_wordle}")
        
        # Extract scores specifically for Wordle Gang league
        logging.info(f"Extracting scores for {league_name} (league_id: {league_id})")
        extracted_scores = extract_scores_for_league(
            driver=driver,
            league_id=league_id, 
            league_name=league_name,
            today_wordle=today_wordle,
            yesterday_wordle=yesterday_wordle
        )
        
        # Process the extracted scores
        if extracted_scores:
            logging.info(f"Found {len(extracted_scores)} score entries to process")
            processed_count = process_scores(extracted_scores, league_id)
            logging.info(f"Successfully processed {processed_count} scores")
        else:
            logging.warning("No scores were extracted")
        
        # Check specifically for Mylene's data
        import sqlite3
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get Mylene's latest scores after extraction
        cursor.execute("""
            SELECT s.score, s.wordle_number, s.timestamp 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.name = 'Mylene' AND p.league_id = ?
            ORDER BY s.timestamp DESC
            LIMIT 3
        """, (league_id,))
        
        scores = cursor.fetchall()
        
        if scores:
            logging.info(f"Found {len(scores)} scores for Mylene:")
            for score_row in scores:
                score, wordle_num, timestamp = score_row
                logging.info(f"Wordle #{wordle_num}: Score: {score}, Timestamp: {timestamp}")
        else:
            logging.warning("No scores found for Mylene after extraction")
            
            # Double check player ID mapping
            cursor.execute("""
                SELECT id, name, phone_number FROM players 
                WHERE name = 'Mylene' AND league_id = ?
            """, (league_id,))
            
            player = cursor.fetchone()
            if player:
                player_id, name, phone = player
                logging.info(f"Mylene is in the database with ID: {player_id}, Phone: {phone}")
            else:
                logging.error("Mylene not found in players table for league 2")
        
        conn.close()
            
    finally:
        # Clean up
        cleanup_driver(driver)
        logging.info("=== Manual extraction completed ===")

if __name__ == "__main__":
    main()
