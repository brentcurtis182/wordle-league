#!/usr/bin/env python
"""
Very simple script to check if scores match emoji patterns
"""
import sqlite3

# Database path
DATABASE_PATH = 'wordle_league.db'

def verify_scores():
    """Verify if scores match the emoji patterns"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("=== Wordle #1500 Scores ===")
    
    # Get all players for Wordle #1500
    cursor.execute("SELECT player_name FROM scores WHERE wordle_num = 1500")
    players = [row[0] for row in cursor.fetchall()]
    
    for player in players:
        # Get the score for this player
        cursor.execute(
            "SELECT score FROM scores WHERE player_name = ? AND wordle_num = 1500",
            (player,)
        )
        score_row = cursor.fetchone()
        score = score_row[0] if score_row else None
        
        # Get rows in emoji pattern
        cursor.execute(
            "SELECT emoji_pattern FROM scores WHERE player_name = ? AND wordle_num = 1500",
            (player,)
        )
        pattern_row = cursor.fetchone()
        pattern = pattern_row[0] if pattern_row else None
        
        # Count actual rows (not counting blank lines)
        actual_rows = 0
        has_all_green_row = False
        
        if pattern:
            rows = [r for r in pattern.split('\n') if r.strip()]
            actual_rows = len(rows)
            
            # Check if any row is all green (success)
            for row in rows:
                if row.count('🟩') == 5:
                    has_all_green_row = True
                    break
        
        # Determine expected score
        expected_score = None
        if has_all_green_row:
            expected_score = actual_rows
        elif actual_rows >= 6:
            expected_score = 7  # X/6
        
        # Display results
        score_display = "X/6" if score == 7 else f"{score}/6" if score else "Unknown"
        expected_display = "X/6" if expected_score == 7 else f"{expected_score}/6" if expected_score else "Unknown"
        
        print(f"{player}: DB Score = {score_display}, Pattern has {actual_rows} rows")
        print(f"  Expected score based on pattern: {expected_display}")
        
        if expected_score and expected_score != score:
            print(f"  ⚠️ DISCREPANCY DETECTED! Score should be {expected_display}")
        
        print("")
    
    conn.close()

if __name__ == "__main__":
    verify_scores()
