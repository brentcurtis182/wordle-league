#!/usr/bin/env python3
"""
Script to update Vox's pattern with the correct one provided by the user
"""
import sqlite3
import sys

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # The correct pattern with black squares (dark mode)
    correct_pattern = """🟨⬛⬛⬛⬛
⬛⬛🟨🟨⬛
⬛🟨🟩🟩⬛
🟩🟩🟩🟩🟩"""
    
    # Update Vox's pattern
    cursor.execute("""
    UPDATE scores
    SET emoji_pattern = ?
    WHERE player_name = 'Vox' AND league_id = 3
    """, (correct_pattern,))
    
    conn.commit()
    print("Updated Vox's pattern with the correct dark mode pattern")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
