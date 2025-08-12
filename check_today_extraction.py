#!/usr/bin/env python3
"""
Simple Direct Check of Today's Wordle Scores

This script directly checks the unified scores table to verify if today's
scores (Wordle #1505) were successfully extracted and saved.
"""

import sqlite3
import sys
from datetime import datetime

def check_todays_scores():
    """Check for today's Wordle scores in the unified scores table"""
    # Today's Wordle number
    WORDLE_NUMBER = 1505
    TODAY = "2025-08-02"
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First get the table structure for reference
        cursor.execute("PRAGMA table_info(scores)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Scores table columns: {columns}")
        
        # Check if we have any scores for today's Wordle
        cursor.execute("SELECT COUNT(*) FROM scores WHERE wordle_number = ?", (WORDLE_NUMBER,))
        count = cursor.fetchone()[0]
        
        print(f"\nFOUND {count} SCORES FOR TODAY'S WORDLE #{WORDLE_NUMBER}")
        print("="*60)
        
        if count > 0:
            # Query for today's scores with player names
            cursor.execute("""
            SELECT p.name, s.* 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ?
            ORDER BY s.score
            """, (WORDLE_NUMBER,))
            
            scores = cursor.fetchall()
            
            # Display each score
            for score in scores:
                player_name = score[0]
                score_data = score[1:]
                
                print(f"\nPlayer: {player_name}")
                print(f"Score: {score_data[3]}/6" if score_data[3] != 7 else "Score: X/6")
                print(f"Date: {score_data[4]}")
                
                # Show emoji pattern if available
                pattern = score_data[5]
                if pattern:
                    print("Emoji Pattern: [Available but not displayed due to terminal encoding limitations]")
                    # We'll count the lines instead of printing the actual emojis
                    if pattern:
                        lines = pattern.count('\n') + 1
                        print(f"Pattern has {lines} lines of emoji")
                else:
                    print("No emoji pattern available")
                    
                print("-"*40)
            
            # Now check if we got scores for the main players we're concerned about
            for key_player in ['Malia', 'Evan', 'Fuzwuz', 'Starslider']:
                cursor.execute("""
                SELECT s.score 
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE s.wordle_number = ? AND p.name = ?
                """, (WORDLE_NUMBER, key_player))
                
                result = cursor.fetchone()
                if result:
                    score_val = result[0]
                    score_display = f"{score_val}/6" if score_val != 7 else "X/6"
                    print(f"✓ {key_player}'s score found: {score_display}")
                else:
                    print(f"✗ {key_player}'s score is missing")
        
        else:
            print("No scores found for today's Wordle.")
            print("The extraction may not have worked or no scores were submitted.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}", file=sys.stderr)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print(f"Checking for scores from today ({datetime.now().strftime('%Y-%m-%d')})")
    check_todays_scores()
