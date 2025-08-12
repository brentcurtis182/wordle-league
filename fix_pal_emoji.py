#!/usr/bin/env python3
"""
Script to fix PAL league emoji patterns with properly formatted data
"""
import sqlite3
import sys

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Create a properly formatted emoji pattern for score 4
    proper_emoji_pattern = "⬜⬜⬜⬜\n🟨⬜🟨⬜\n⬜🟨⬜🟨\n🟩🟩🟩🟩\n\n"
    
    # Update the Vox entry
    cursor.execute("""
    UPDATE scores
    SET emoji_pattern = ?
    WHERE player_name = 'Vox' AND league_id = 3
    """, (proper_emoji_pattern,))
    
    conn.commit()
    print("Updated Vox emoji pattern with properly formatted data")
    
    # Verify the update
    cursor.execute("""
    SELECT player_name, score, emoji_pattern
    FROM scores
    WHERE player_name = 'Vox' AND league_id = 3
    """)
    
    row = cursor.fetchone()
    if row:
        print(f"\nVerified update for {row[0]}")
        print(f"Score: {row[1]}")
        print(f"Emoji pattern format: {row[2][:20]}...")
    else:
        print("No Vox score found in PAL league")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
