#!/usr/bin/env python3
# Script to verify emoji patterns for specific players in the production database

import sqlite3
import logging
import sys
from datetime import datetime

# Configure logging with UTF-8 encoding for emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify_emoji_patterns.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Reconfigure sys.stdout for proper emoji display on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_emoji_patterns():
    """Check emoji patterns for specific players"""
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Players to check
        players_to_check = ['Malia', 'Evan']
        
        for player in players_to_check:
            # Get all emoji patterns for this player
            cursor.execute("""
                SELECT player_name, wordle_num, score, emoji_pattern 
                FROM scores 
                WHERE player_name = ? 
                AND emoji_pattern IS NOT NULL 
                AND league_id = 1
                ORDER BY wordle_num DESC
                LIMIT 10
            """, (player,))
            
            rows = cursor.fetchall()
            
            print(f"\n{'=' * 40}")
            print(f"Verified patterns for {player} ({len(rows)} entries):")
            print(f"{'=' * 40}")
            
            for row in rows:
                player_name, wordle_num, score, pattern = row
                print(f"Wordle #{wordle_num}, Score: {score}")
                print(f"Pattern:\n{pattern}")
                print('-' * 40)
                
                # Check if the pattern contains any non-emoji content
                non_emoji_lines = []
                for line in pattern.split('\n'):
                    # Check if this line has emoji but also other content
                    has_emoji = any(char in line for char in ['🟩', '⬛', '⬜', '🟨'])
                    has_invalid = any(char.isalpha() or char.isdigit() for char in line)
                    
                    if has_emoji and has_invalid:
                        non_emoji_lines.append(line)
                
                if non_emoji_lines:
                    print("⚠️ WARNING: Found potential date/time text in pattern:")
                    for line in non_emoji_lines:
                        print(f"  {line}")
                else:
                    print("✅ Pattern looks clean")
            
        conn.close()
        
    except Exception as e:
        logging.error(f"Error checking emoji patterns: {e}")

if __name__ == "__main__":
    check_emoji_patterns()
