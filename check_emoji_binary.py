#!/usr/bin/env python3
"""
Script to check binary data of emoji patterns in the database
"""
import sqlite3
import binascii
import sys

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Query PAL league scores
    cursor.execute("""
    SELECT player_name, score, emoji_pattern
    FROM scores
    WHERE league_id = 3
    """)
    
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} PAL league scores")
    
    for row in rows:
        player_name = row[0]
        score = row[1]
        emoji_pattern = row[2]
        
        print(f"\nPlayer: {player_name}")
        print(f"Score: {score}")
        
        if emoji_pattern is None:
            print("Emoji pattern: NULL")
        else:
            print(f"Emoji pattern length: {len(emoji_pattern)} characters")
            print("Binary representation:")
            hex_data = binascii.hexlify(emoji_pattern.encode('utf-8')).decode('ascii')
            print(hex_data)
            
            # Try to decode and print the first few characters safely
            try:
                print("First 10 chars:", emoji_pattern[:10])
            except:
                print("Cannot safely display emoji pattern")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
