#!/usr/bin/env python3
"""
Simple script to check PAL league score data in the database
"""
import sqlite3
import sys

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Query PAL league scores
    cursor.execute("""
    SELECT player_name, score, emoji_pattern, wordle_num, timestamp
    FROM scores
    WHERE league_id = 3
    """)
    
    rows = cursor.fetchall()
    
    # Display the results
    print("PAL League Scores:")
    print("=" * 50)
    print("Player\tScore\tEmoji Pattern\tWordle #\tTimestamp")
    print("-" * 50)
    
    for row in rows:
        player_name = row[0]
        score = row[1]
        emoji_pattern = row[2] if row[2] is not None else "NULL"
        wordle_num = row[3]
        timestamp = row[4]
        
        print(f"{player_name}\t{score}\t{emoji_pattern}\t{wordle_num}\t{timestamp}")
    
    # Check if emoji_pattern column exists in the scores table
    cursor.execute("PRAGMA table_info(scores)")
    columns = cursor.fetchall()
    
    print("\nScores Table Schema:")
    print("=" * 50)
    for col in columns:
        print(f"{col[0]}: {col[1]} ({col[2]})")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
