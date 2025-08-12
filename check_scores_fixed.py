#!/usr/bin/env python
"""
Check and display scores and emoji patterns for Wordle #1500
"""
import sqlite3
import logging
import sys

# Set up logging with basic configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database path
DATABASE_PATH = 'wordle_league.db'

def check_scores():
    """Check and display scores for Wordle #1500 for all players"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check scores table
        cursor.execute(
            "SELECT player_name, score FROM scores WHERE wordle_num = 1500 ORDER BY player_name"
        )
        rows = cursor.fetchall()
        
        print("\n=== Scores for Wordle #1500 ===")
        if rows:
            for row in rows:
                player_name = row[0]
                score = row[1]
                
                score_display = "X/6" if score == 7 else f"{score}/6"
                
                print(f"{player_name}: {score_display}")
                
                # Get emoji pattern but don't try to print it directly
                cursor.execute(
                    "SELECT emoji_pattern FROM scores WHERE wordle_num = 1500 AND player_name = ?",
                    (player_name,)
                )
                pattern_row = cursor.fetchone()
                
                if pattern_row and pattern_row[0]:
                    # Count rows in the pattern
                    pattern = pattern_row[0]
                    row_count = pattern.count('\n') + 1
                    print(f"  Emoji pattern has {row_count} rows")
                    
                    # Check if last row is all greens
                    rows = pattern.split('\n')
                    last_row = rows[-1] if rows else ""
                    
                    if "🟩🟩🟩🟩🟩" in last_row:
                        print(f"  Last row is all green - successful solve")
                        expected_score = row_count
                    else:
                        print(f"  Last row is NOT all green - likely a failed attempt")
                        expected_score = 7
                        
                    if expected_score != score:
                        print(f"  ⚠️ DISCREPANCY: Pattern suggests {expected_score}/6 but score is {score_display}")
                else:
                    print("  No emoji pattern stored")
        else:
            print("No scores found for Wordle #1500")
            
    except Exception as e:
        logging.error(f"Error checking scores: {e}")
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    check_scores()
