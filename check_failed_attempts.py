#!/usr/bin/env python3
import os
import sqlite3
import json
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define database path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')

# Check for X/6 scores in the database
def check_failed_attempts():
    conn = sqlite3.connect(WORDLE_DATABASE)
    cursor = conn.cursor()
    
    print("Checking for failed attempts (X/6 or 7) in the database...")
    
    # Check league 1 (Wordle Warriorz)
    cursor.execute("""
    SELECT p.name, s.score, s.date, s.wordle_number 
    FROM scores s 
    JOIN players p ON s.player_id = p.id 
    WHERE p.league_id = 1 
    AND (s.score = 'X' OR s.score = '7' OR s.score = 7)
    ORDER BY s.date DESC LIMIT 10;
    """)
    
    rows = cursor.fetchall()
    print(f"\nFound {len(rows)} failed attempts for Wordle Warriorz:")
    for row in rows:
        print(f"Player: {row[0]}, Score: {row[1]}, Date: {row[2]}, Wordle #: {row[3]}")
    
    # Get weekly stats for league 1
    start_wordle = 1500  # Example starting wordle for the current week
    end_wordle = 1506    # Example ending wordle for the current week
    
    print(f"\nGetting weekly stats for Wordle Warriorz with range {start_wordle}-{end_wordle}...")
    
    # Get all players in the league
    cursor.execute("SELECT name FROM players WHERE league_id = 1")
    players = [row[0] for row in cursor.fetchall()]
    
    for name in players:
        # Count failed attempts for this player in the weekly range
        cursor.execute("""
        SELECT COUNT(*) FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.name = ? AND p.league_id = 1
        AND s.wordle_number >= ? AND s.wordle_number <= ?
        AND (s.score = 7 OR s.score = '7' OR s.score = 'X')
        """, (name, start_wordle, end_wordle))
        
        failed_count = cursor.fetchone()[0]
        
        print(f"Player {name}: {failed_count} failed attempts this week")
    
    conn.close()

if __name__ == "__main__":
    check_failed_attempts()
