#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to synchronize scores from the 'scores' table to the 'score' table
"""

import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("db_fix.log"),
        logging.StreamHandler()
    ]
)

def sync_scores_between_tables():
    """Copy scores from 'scores' table to 'score' table for missing entries"""
    conn = sqlite3.connect('wordle_league.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Get wordle #1501 scores from the 'scores' table
        cursor.execute("""
            SELECT player_name, wordle_num, score, emoji_pattern, timestamp 
            FROM scores 
            WHERE wordle_num = 1501
        """)
        scores_results = cursor.fetchall()
        
        logging.info(f"Found {len(scores_results)} scores for Wordle #1501 in 'scores' table")
        
        # For each score, check if it exists in 'score' table and add if missing
        for row in scores_results:
            player_name = row['player_name']
            wordle_num = row['wordle_num']
            score = row['score']
            emoji_pattern = row['emoji_pattern']
            timestamp = row['timestamp']
            
            # Convert timestamp to date in YYYY-MM-DD format
            if timestamp:
                try:
                    date_obj = datetime.fromisoformat(timestamp)
                    date_str = date_obj.strftime("%Y-%m-%d")
                except (ValueError, TypeError):
                    date_str = datetime.now().strftime("%Y-%m-%d")
            else:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Get player_id for this player
            cursor.execute("SELECT id FROM player WHERE name = ?", (player_name,))
            player_row = cursor.fetchone()
            
            if not player_row:
                logging.warning(f"Player {player_name} not found in 'player' table. Skipping.")
                continue
                
            player_id = player_row['id']
            
            # Check if score already exists in 'score' table
            cursor.execute("""
                SELECT id FROM score 
                WHERE player_id = ? AND wordle_number = ?
            """, (player_id, wordle_num))
            
            existing = cursor.fetchone()
            
            if existing:
                logging.info(f"Score for {player_name}, Wordle #{wordle_num} already exists in 'score' table. Updating.")
                
                # Update the existing record
                try:
                    cursor.execute("""
                        UPDATE score SET score = ?, emoji_pattern = ?, date = ?
                        WHERE player_id = ? AND wordle_number = ?
                    """, (score, emoji_pattern, date_str, player_id, wordle_num))
                    logging.info(f"Updated score for {player_name}, Wordle #{wordle_num} in 'score' table")
                except sqlite3.OperationalError as e:
                    # If emoji_pattern column doesn't exist
                    if "no such column: emoji_pattern" in str(e):
                        cursor.execute("""
                            UPDATE score SET score = ?, date = ?
                            WHERE player_id = ? AND wordle_number = ?
                        """, (score, date_str, player_id, wordle_num))
                        logging.info(f"Updated score (without emoji pattern) for {player_name}, Wordle #{wordle_num}")
                    else:
                        raise e
            else:
                logging.info(f"Score for {player_name}, Wordle #{wordle_num} missing from 'score' table. Adding.")
                
                # Insert a new record
                try:
                    cursor.execute("""
                        INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date)
                        VALUES (?, ?, ?, ?, ?)
                    """, (player_id, wordle_num, score, emoji_pattern, date_str))
                    logging.info(f"Added score for {player_name}, Wordle #{wordle_num} to 'score' table")
                except sqlite3.OperationalError as e:
                    # If emoji_pattern column doesn't exist
                    if "no such column: emoji_pattern" in str(e):
                        cursor.execute("""
                            INSERT INTO score (player_id, wordle_number, score, date)
                            VALUES (?, ?, ?, ?)
                        """, (player_id, wordle_num, score, date_str))
                        logging.info(f"Added score (without emoji pattern) for {player_name}, Wordle #{wordle_num}")
                    else:
                        raise e
        
        # Commit changes
        conn.commit()
        logging.info("Database sync completed successfully")
        
    except Exception as e:
        logging.error(f"Error synchronizing database tables: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("\n=== Synchronizing Database Tables ===\n")
    sync_scores_between_tables()
    print("\n=== Database Sync Complete ===\n")
    print("Now running website update...\n")
    
    # Import and run update_website_now.py
    try:
        import update_website_now
        print("Website update completed!")
    except Exception as e:
        print(f"Error during website update: {e}")
