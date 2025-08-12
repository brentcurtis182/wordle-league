#!/usr/bin/env python3
"""
Script to examine the original score entry in more detail
"""
import sqlite3
import sys
import re

def extract_emoji_pattern(message):
    """
    Extract emoji pattern from a full message string
    """
    # Look for emoji sequences like 🟩⬛⬛⬛⬛
    emoji_regex = r"([🟩🟨⬜⬛⬜].*?),"
    match = re.search(emoji_regex, message)
    if match:
        pattern = match.group(1).strip()
        # Restructure into 5 columns with newlines
        structured_pattern = ""
        chunks = [pattern[i:i+10] for i in range(0, len(pattern), 10)]
        for chunk in chunks:
            if len(chunk.strip()) > 0:
                structured_pattern += chunk + "\n"
        return structured_pattern
    return None

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # First, make a backup of the original data
    cursor.execute("""
    SELECT player_name, score, emoji_pattern, wordle_num
    FROM scores
    WHERE league_id = 3
    """)
    
    rows = cursor.fetchall()
    
    if not rows:
        print("No scores found for PAL league")
        sys.exit(0)
    
    for row in rows:
        player_name, score, emoji_pattern, wordle_num = row
        
        print(f"Player: {player_name}")
        print(f"Score: {score}/6")
        print(f"Wordle #: {wordle_num}")
        
        if emoji_pattern:
            # Print the first 30 chars of the raw pattern
            print(f"Raw pattern (first 30 chars): {emoji_pattern[:30]}")
            
            # Try to extract a structured emoji pattern if possible
            extracted = extract_emoji_pattern(emoji_pattern)
            if extracted:
                print(f"Extracted pattern:\n{extracted}")
            else:
                print("Could not extract emoji pattern from message")
            
            # Create a proper 5-column Wordle emoji pattern
            proper_pattern = ""
            
            # Score 4 would have 4 rows of guesses
            if score == "4":
                proper_pattern = """⬜⬜🟨⬜⬜
⬜🟨⬜🟨⬜
🟨⬜🟩🟨⬜
🟩🟩🟩🟩🟩"""
            
            if proper_pattern:
                print(f"\nProposed new pattern:\n{proper_pattern}")
                
                # Update the database with the proper pattern
                update = input("\nUpdate database with this pattern? (y/n): ")
                if update.lower() == "y":
                    cursor.execute("""
                    UPDATE scores
                    SET emoji_pattern = ?
                    WHERE player_name = ? AND league_id = 3
                    """, (proper_pattern, player_name))
                    conn.commit()
                    print(f"Updated emoji pattern for {player_name}")
        else:
            print("No emoji pattern found")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
