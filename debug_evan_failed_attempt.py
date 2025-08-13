#!/usr/bin/env python3
import os
import sqlite3
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def check_evan_failed_attempt():
    """Check Evan's failed attempt in the database and debug the extraction for weekly stats"""
    
    # Check if Evan exists in the players table
    cursor.execute("SELECT id, name FROM players WHERE name = 'Evan' AND league_id = 1")
    player = cursor.fetchone()
    
    if not player:
        logging.error("Evan not found in players table for league 1")
        return
        
    player_id = player[0]
    logging.info(f"Found Evan with player_id={player_id}")
    
    # Look for failed attempts by Evan
    cursor.execute("""
    SELECT s.id, s.score, s.date, s.wordle_number
    FROM scores s
    WHERE s.player_id = ? AND (s.score = '7' OR s.score = 7 OR s.score = 'X')
    ORDER BY s.date DESC
    """, (player_id,))
    
    failed_attempts = cursor.fetchall()
    logging.info(f"Found {len(failed_attempts)} failed attempts for Evan:")
    for attempt in failed_attempts:
        logging.info(f"ID: {attempt[0]}, Score: {attempt[1]}, Date: {attempt[2]}, Wordle: {attempt[3]}")
    
    # Get the weekly Wordle range
    # Hardcode for testing - assuming same as in the export script
    start_wordle = 1500
    end_wordle = 1506
    logging.info(f"Using weekly Wordle range: {start_wordle}-{end_wordle}")
    
    # Count failed attempts specifically in this weekly range
    cursor.execute("""
    SELECT COUNT(*) FROM scores s
    WHERE s.player_id = ? 
    AND s.wordle_number >= ? AND s.wordle_number <= ?
    AND (s.score = 7 OR s.score = '7' OR s.score = 'X')
    """, (player_id, start_wordle, end_wordle))
    
    failed_count = cursor.fetchone()[0]
    logging.info(f"Evan has {failed_count} failed attempts in this weekly range")
    
    # Print the raw data that would go into weekly stats
    cursor.execute("""
    SELECT name, score, date, wordle_number
    FROM scores s
    JOIN players p ON s.player_id = p.id
    WHERE p.name = 'Evan' AND p.league_id = 1 
    AND s.wordle_number >= ? AND s.wordle_number <= ?
    ORDER BY s.date DESC
    """, (start_wordle, end_wordle))
    
    evan_scores = cursor.fetchall()
    logging.info(f"All of Evan's scores for this week ({start_wordle}-{end_wordle}):")
    for score in evan_scores:
        logging.info(f"Name: {score[0]}, Score: {score[1]}, Date: {score[2]}, Wordle: {score[3]}")
    
    # Check if the wordle number for the failed attempt is in the current weekly range
    if failed_attempts and len(failed_attempts) > 0:
        for attempt in failed_attempts:
            wordle_num = attempt[3]
            if wordle_num is not None and start_wordle <= int(wordle_num) <= end_wordle:
                logging.info(f"CONFIRMED: Evan's failed attempt (Wordle #{wordle_num}) is in the current weekly range")
            else:
                logging.warning(f"Evan's failed attempt (Wordle #{wordle_num}) is NOT in the current weekly range {start_wordle}-{end_wordle}")

if __name__ == "__main__":
    check_evan_failed_attempt()
    conn.close()
