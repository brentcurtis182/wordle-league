#!/usr/bin/env python3
import sqlite3
from datetime import datetime, timedelta

# Database path
WORDLE_DATABASE = 'wordle_league.db'

def check_pants_data():
    """Check data for player Pants in the database"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Check for any entries for Pants
        cursor.execute("""
        SELECT id, wordle_num, score, timestamp, emoji_pattern, league_id 
        FROM scores 
        WHERE player_name = 'Pants'
        """)
        
        pants_entries = cursor.fetchall()
        print(f"Found {len(pants_entries)} entries for player 'Pants':")
        for entry in pants_entries:
            id, wordle_num, score, timestamp, pattern, league_id = entry
            print(f"ID: {id}, Wordle: {wordle_num}, Score: {score}, Date: {timestamp}, League: {league_id}")
            
        # Check for entries that might be causing the incorrect display
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id 
        FROM scores 
        WHERE player_name = 'Pants' AND league_id = 3
        """)
        
        pal_pants_entries = cursor.fetchall()
        print(f"\nFound {len(pal_pants_entries)} entries for player 'Pants' in PAL league (ID: 3):")
        for entry in pal_pants_entries:
            id, name, wordle_num, score, timestamp, league_id = entry
            print(f"ID: {id}, Wordle: {wordle_num}, Score: {score}, Date: {timestamp}")
            
        return True
        
    except Exception as e:
        print(f"Error checking Pants data: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_pants_data()
