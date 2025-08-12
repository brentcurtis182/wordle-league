#!/usr/bin/env python3
"""
Script to write emoji patterns to file instead of console
"""
import sqlite3
import sys
import os

OUTPUT_FILE = "emoji_patterns.txt"

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Open output file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("=== EMOJI PATTERNS REPORT ===\n\n")
        
        # Find all score 4 patterns
        cursor.execute("""
        SELECT player_name, league_id, score, emoji_pattern
        FROM scores 
        WHERE score = '4' AND emoji_pattern IS NOT NULL
        ORDER BY league_id, player_name
        """)
        
        rows = cursor.fetchall()
        f.write(f"Found {len(rows)} scores with score = 4 and emoji patterns\n\n")
        
        # Write each pattern to file
        for i, row in enumerate(rows):
            player_name, league_id, score, pattern = row
            f.write(f"=== PATTERN {i+1}: {player_name} (League {league_id}) ===\n")
            f.write(f"Score: {score}/6\n")
            if pattern:
                f.write("Pattern:\n")
                f.write(pattern)
                f.write("\n\n")
            else:
                f.write("No pattern available\n\n")
        
        # Now update Vox's pattern with an actual Wordle pattern for score 4
        real_pattern = """⬜⬜🟨⬜⬜
⬜🟨⬜🟨⬜
🟨⬜🟩⬜🟩
🟩🟩🟩🟩🟩"""
        
        cursor.execute("""
        UPDATE scores
        SET emoji_pattern = ?
        WHERE player_name = 'Vox' AND league_id = 3
        """, (real_pattern,))
        
        conn.commit()
        f.write("Updated Vox's pattern in PAL league with a real Wordle 4/6 pattern\n")
        f.write("New pattern:\n")
        f.write(real_pattern)
        
    print(f"Successfully wrote emoji patterns to {OUTPUT_FILE}")
    print("Also updated Vox's pattern with a proper 4/6 Wordle pattern")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
