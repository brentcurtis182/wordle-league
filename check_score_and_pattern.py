#!/usr/bin/env python
"""
Check and display scores and emoji patterns for Wordle #1500
"""
import sqlite3
import logging
from datetime import datetime

# Set up logging with UTF-8 encoding to properly display emoji
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("check_scores.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Database path
DATABASE_PATH = 'wordle_league.db'

def count_emoji_rows(pattern):
    """Count how many rows are in an emoji pattern"""
    if not pattern:
        return 0
    return pattern.count('\n') + 1

def calculate_score_from_emoji(pattern):
    """Calculate the score based on the emoji pattern"""
    if not pattern:
        return None
    
    rows = pattern.split('\n')
    num_rows = len(rows)
    
    # If it's not a valid pattern (should have 1-6 rows)
    if num_rows < 1 or num_rows > 6:
        return None
    
    # Check if last row has all green squares (🟩) indicating success
    last_row = rows[-1]
    if '🟩🟩🟩🟩🟩' in last_row:
        return num_rows  # Score is the number of tries (rows)
    else:
        return 7  # X/6 - failed attempt
    
def check_scores():
    """Check and display scores for Wordle #1500 for all players"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check scores table
        cursor.execute(
            "SELECT player_name, score, emoji_pattern FROM scores WHERE wordle_num = 1500 ORDER BY player_name"
        )
        rows = cursor.fetchall()
        
        print("\n=== Scores for Wordle #1500 ===")
        if rows:
            for row in rows:
                player_name = row[0]
                score = row[1]
                emoji_pattern = row[2] if row[2] else "No pattern"
                
                # Calculate expected score from emoji pattern
                calculated_score = calculate_score_from_emoji(emoji_pattern)
                
                score_display = "X/6" if score == 7 else f"{score}/6"
                calculated_score_display = "X/6" if calculated_score == 7 else f"{calculated_score}/6" if calculated_score else "Unknown"
                
                print(f"\n{player_name}:")
                print(f"  Score in DB: {score_display}")
                print(f"  Calculated from emoji: {calculated_score_display}")
                print(f"  Emoji Pattern:")
                if emoji_pattern:
                    print(f"```\n{emoji_pattern}\n```")
                else:
                    print("  No emoji pattern stored")
                
                # Check for discrepancy
                if calculated_score and calculated_score != score:
                    print(f"  ⚠️ DISCREPANCY DETECTED: Stored score ({score_display}) doesn't match emoji pattern!")
        else:
            print("No scores found for Wordle #1500")
            
    except Exception as e:
        logging.error(f"Error checking scores: {e}")
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_scores()
