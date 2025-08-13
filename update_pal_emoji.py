#!/usr/bin/env python3
"""
Simple script to add emoji patterns to PAL league scores in the database
"""
import sqlite3
import sys
from datetime import datetime

try:
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # First check if we have any PAL league scores
    cursor.execute("SELECT player_name, score, wordle_num FROM scores WHERE league_id = 3")
    pal_scores = cursor.fetchall()
    
    print(f"Found {len(pal_scores)} PAL league scores")
    
    # Sample emoji patterns for different score values
    emoji_patterns = {
        '1': "🟩\n\n\n\n\n",
        '2': "⬜🟩\n🟩🟩\n\n\n\n",
        '3': "⬜🟨⬜\n🟨🟨⬜\n🟩🟩🟩\n\n\n",
        '4': "⬜⬜⬜⬜\n🟨⬜🟨⬜\n⬜🟨⬜🟨\n🟩🟩🟩🟩\n\n",
        '5': "⬜⬜⬜⬜⬜\n⬜🟨⬜🟨⬜\n🟨⬜🟨⬜🟨\n⬜🟨🟨🟨⬜\n🟩🟩🟩🟩🟩\n",
        '6': "⬜⬜⬜⬜⬜\n⬜⬜🟨⬜⬜\n⬜🟨⬜🟨⬜\n🟨⬜🟨⬜🟨\n⬜🟨🟨🟨⬜\n🟩🟩🟩🟩🟩",
        'X': "⬜⬜⬜⬜⬜\n⬜⬜🟨⬜⬜\n⬜🟨⬜🟨⬜\n🟨⬜🟨⬜🟨\n⬜🟨🟨🟨⬜\n⬜🟩🟨🟩⬜"
    }
    
    # Update each score with a sample emoji pattern
    for player_name, score, wordle_num in pal_scores:
        # Choose an emoji pattern based on the score
        pattern = emoji_patterns.get(score, "")
        
        if pattern:
            cursor.execute("""
            UPDATE scores
            SET emoji_pattern = ?
            WHERE player_name = ? AND league_id = 3 AND wordle_num = ?
            """, (pattern, player_name, wordle_num))
            
            print(f"Updated emoji pattern for {player_name}, score: {score}")
    
    # Commit the changes
    conn.commit()
    print("Changes committed to database")
    
    # Now insert a new sample PAL league score with an emoji pattern
    # Only do this if there are no existing scores
    if len(pal_scores) == 0:
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO scores (player_name, league_id, score, emoji_pattern, wordle_num, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
        """, ("TestUser", 3, "3", emoji_patterns["3"], 1502, today))
        
        conn.commit()
        print("Added sample PAL league score for TestUser")
    
    # Verify the updates
    cursor.execute("""
    SELECT player_name, score, 
           CASE WHEN emoji_pattern IS NULL THEN 'NULL' ELSE 'HAS PATTERN' END as has_pattern
    FROM scores WHERE league_id = 3
    """)
    
    updated_scores = cursor.fetchall()
    print("\nUpdated PAL league scores:")
    for row in updated_scores:
        print(f"{row[0]}, Score: {row[1]}, Pattern: {row[2]}")
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
finally:
    if conn:
        conn.close()
