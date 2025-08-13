#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct PAL League Wordle #1505 Score Fix

This script bypasses the extraction system completely and directly adds
the missing Wordle #1505 scores for the PAL league to both database tables.
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_pal_scores_1505():
    """Add PAL league scores for Wordle #1505 directly to both tables"""
    logging.info("Starting direct PAL Wordle #1505 score fix")
    
    # Wordle number to fix
    wordle_num = 1505
    
    # Today's date
    today = datetime.now().strftime('%Y-%m-%d')
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # PAL league ID
    league_id = 3
    
    # PAL player scores to add - manually specified
    # Format: (player_name, score)
    # Note: X/6 is recorded as 7
    pal_scores = [
        ("Vox", 4),
        ("Fuzwuz", 5),
        ("Starslider", 4)
    ]
    
    # Connect to database
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        scores_added = 0
        
        for player_name, score in pal_scores:
            # Check if score already exists in scores table
            cursor.execute(
                "SELECT id FROM scores WHERE player_name = ? AND wordle_num = ? AND league_id = ?",
                (player_name, wordle_num, league_id)
            )
            if cursor.fetchone():
                logging.info(f"Score for {player_name}, Wordle #{wordle_num} already exists in scores table")
                continue
                
            # Get player_id for score table
            cursor.execute(
                "SELECT id FROM players WHERE name = ? AND league_id = ?",
                (player_name, league_id)
            )
            player_row = cursor.fetchone()
            if not player_row:
                logging.error(f"Player {player_name} not found in players table for league {league_id}")
                continue
            
            player_id = player_row[0]
            
            # Add to scores table (plural)
            logging.info(f"Adding score to scores table: {player_name}, {score}/6, Wordle #{wordle_num}")
            cursor.execute(
                "INSERT INTO scores (player_name, score, wordle_num, league_id) VALUES (?, ?, ?, ?)",
                (player_name, score, wordle_num, league_id)
            )
            
            # Add to score table (singular)
            logging.info(f"Adding score to score table: player_id={player_id}, {score}/6, Wordle #{wordle_num}")
            cursor.execute(
                "INSERT INTO score (player_id, score, wordle_number, date, created_at, league_id) VALUES (?, ?, ?, ?, ?, ?)",
                (player_id, score, wordle_num, today, timestamp, league_id)
            )
            
            scores_added += 1
        
        # Commit changes
        conn.commit()
        logging.info(f"Successfully added {scores_added} PAL league scores for Wordle #{wordle_num}")
        
        return scores_added
        
    except Exception as e:
        logging.error(f"Error adding PAL scores: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
        return 0
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    scores_added = fix_pal_scores_1505()
    print(f"\nPAL League Wordle #1505 Fix Complete")
    print(f"Added {scores_added} new scores to the database")
    
    # Suggest next steps
    if scores_added > 0:
        print("\nNext steps:")
        print("1. Run 'python export_leaderboard_multi_league.py' to update the website")
        print("2. Check that scores appear on the PAL leaderboard")
