#!/usr/bin/env python3
"""
Script to check emoji patterns for specific players
"""
import sqlite3
import sys

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Check Brent's patterns
    cursor.execute("""
    SELECT player_name, score, wordle_num, emoji_pattern 
    FROM scores 
    WHERE player_name = 'Brent' AND score = '4'
    ORDER BY wordle_num DESC
    LIMIT 1
    """)
    
    brent_row = cursor.fetchone()
    print("\n=== BRENT'S PATTERN ===")
    if brent_row:
        print(f"Wordle #{brent_row[2]}, Score: {brent_row[1]}/6")
        if brent_row[3]:
            print("Pattern (as stored):")
            print(brent_row[3])
            print("\nPattern (line by line):")
            for line in brent_row[3].split('\n'):
                print(f"Line: '{line}'")
        else:
            print("No emoji pattern found")
    else:
        print("No matching score found for Brent")
        
    # Check Vox's pattern in PAL league
    cursor.execute("""
    SELECT player_name, score, wordle_num, emoji_pattern 
    FROM scores 
    WHERE player_name = 'Vox' AND league_id = 3
    LIMIT 1
    """)
    
    vox_row = cursor.fetchone()
    print("\n=== VOX'S PATTERN (PAL League) ===")
    if vox_row:
        print(f"Wordle #{vox_row[2]}, Score: {vox_row[1]}/6")
        if vox_row[3]:
            print("Pattern (as stored):")
            print(vox_row[3])
            print("\nPattern (line by line):")
            for line in vox_row[3].split('\n'):
                print(f"Line: '{line}'")
        else:
            print("No emoji pattern found")
    else:
        print("No matching score found for Vox in PAL league")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
