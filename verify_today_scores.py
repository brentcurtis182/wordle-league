#!/usr/bin/env python3
"""
Verify Today's Wordle Scores in Database

This script checks if today's scores (Wordle #1505) were properly saved
in the unified scores table for both leagues.
"""

import sqlite3
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_todays_scores(db_path='wordle_league.db'):
    """Check if today's scores were correctly saved in the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Today's Wordle number
        today_wordle = 1505
        
        # Get column names
        cursor.execute("PRAGMA table_info(scores)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Check today's scores for each league
        for league_id in [1, 3]:  # Wordle Warriorz = 1, PAL = 3
            league_name = "Wordle Warriorz" if league_id == 1 else "PAL"
            
            # Query for today's scores in this league
            query = """
            SELECT s.*, p.name 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ? AND s.league_id = ?
            ORDER BY s.score
            """
            
            cursor.execute(query, (today_wordle, league_id))
            scores = cursor.fetchall()
            
            # Display results
            print(f"\n{league_name.upper()} SCORES FOR TODAY (WORDLE #{today_wordle}):")
            print("-" * 80)
            
            # Add player name to columns for display
            display_columns = columns + ["player_name"]
            print(", ".join(display_columns))
            print("-" * 80)
            
            if scores:
                for score in scores:
                    print(score)
                print(f"Total: {len(scores)} scores found")
            else:
                print(f"No scores found for {league_name} today (Wordle #{today_wordle})")
                
            # Check for any failed attempts (score = 7)
            cursor.execute("""
            SELECT p.name 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ? AND s.league_id = ? AND s.score = 7
            """, (today_wordle, league_id))
            
            failed = cursor.fetchall()
            if failed:
                print(f"\nPlayers who failed today's Wordle in {league_name}:")
                for player in failed:
                    print(f"- {player[0]}")
                    
            # Check emoji patterns
            cursor.execute("""
            SELECT p.name, s.emoji_pattern
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ? AND s.league_id = ? AND s.emoji_pattern IS NOT NULL
            """, (today_wordle, league_id))
            
            patterns = cursor.fetchall()
            if patterns:
                print(f"\nEmoji patterns for {league_name}:")
                for player, pattern in patterns:
                    print(f"\n{player}'s pattern:")
                    print(pattern)
            else:
                print(f"\nNo emoji patterns found for {league_name} today")
            
        # Check overall status across all leagues
        cursor.execute("SELECT COUNT(*) FROM scores WHERE wordle_number = ?", (today_wordle,))
        total_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 40)
        print(f"OVERALL: Found {total_count} total scores for Wordle #{today_wordle}")
        print("=" * 40)
        
        return total_count > 0
        
    except Exception as e:
        logging.error(f"Error checking scores: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print(f"Verifying scores for today's Wordle (#1505)")
    success = check_todays_scores()
    
    if success:
        print("\nSuccess! Today's scores were found in the database.")
    else:
        print("\nWarning: No scores found for today's Wordle.")
