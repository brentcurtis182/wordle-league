#!/usr/bin/env python3
# Script to check emoji patterns in the database

import sqlite3
import sys

def check_emoji_patterns(db_path, limit=5):
    """Check emoji patterns in the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query for most recent emoji patterns
        cursor.execute("""
        SELECT player_name, wordle_num, emoji_pattern 
        FROM scores 
        WHERE emoji_pattern IS NOT NULL 
        ORDER BY wordle_num DESC, timestamp DESC
        LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        print(f"\nRECENT EMOJI PATTERNS FROM DATABASE:")
        print("-" * 80)
        
        for row in rows:
            player_name = row[0]
            wordle_num = row[1]
            emoji_pattern = row[2]
            
            print(f"Player: {player_name}, Wordle #{wordle_num}")
            print(f"Pattern:")
            print(emoji_pattern)
            print("-" * 40)
            
        return len(rows)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 0
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_emoji_patterns('wordle_league.db')
