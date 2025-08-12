#!/usr/bin/env python3
"""
Simple verification script for the unified player_scores table.
Shows basic stats without trying to display emoji patterns.
"""

import os
import sqlite3
import sys

# Define database path
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')

def check_table_stats():
    """Check table statistics"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Count rows in each table
        cursor.execute("SELECT COUNT(*) FROM scores")
        scores_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM score")
        score_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM player_scores")
        unified_count = cursor.fetchone()[0]
        
        print(f"\nOriginal tables: scores={scores_count}, score={score_count}, Total={scores_count+score_count}")
        print(f"Unified table: player_scores={unified_count}")
        
        # Check for any potential duplicates
        cursor.execute("""
        SELECT player_name, wordle_number, league_id, COUNT(*)
        FROM player_scores
        GROUP BY player_name, wordle_number, league_id
        HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("\nWARNING: Potential duplicates found in player_scores:")
            for dup in duplicates:
                print(f"  {dup[0]}, Wordle {dup[1]}, League {dup[2]}: {dup[3]} entries")
        else:
            print("\nNo duplicates found in player_scores table.")
            
        # Get league stats
        print("\nPlayer counts by league:")
        for league_id in [1, 2, 3]:  # League IDs: 1=Warriorz, 2=Gang, 3=PAL
            cursor.execute("""
            SELECT COUNT(DISTINCT player_name) FROM player_scores 
            WHERE league_id = ?
            """, (league_id,))
            count = cursor.fetchone()[0]
            print(f"  League {league_id}: {count} players")
            
        # Latest Wordle numbers
        print("\nLatest Wordle numbers:")
        cursor.execute("""
        SELECT DISTINCT wordle_number 
        FROM player_scores 
        ORDER BY CAST(REPLACE(wordle_number, ',', '') AS INTEGER) DESC
        LIMIT 5
        """)
        wordles = cursor.fetchall()
        print(f"  {[w[0] for w in wordles]}")
        
        # Get sample data without emoji patterns
        print("\nSample scores for latest Wordle by league:")
        if wordles:
            latest_wordle = wordles[0][0]
            for league_id in [1, 2, 3]:
                print(f"  League {league_id} - Wordle {latest_wordle}:")
                cursor.execute("""
                SELECT player_name, score, timestamp
                FROM player_scores
                WHERE league_id = ? AND wordle_number = ?
                ORDER BY player_name
                """, (league_id, latest_wordle))
                
                scores = cursor.fetchall()
                if scores:
                    for score_row in scores:
                        player, score, timestamp = score_row
                        print(f"    {player}: Score={score}, Time={timestamp}")
                else:
                    print("    No scores found")
                    
        return True
        
    except Exception as e:
        print(f"Error checking table stats: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Display information about the unified player_scores table"""
    print("=== Unified Table Check ===")
    
    try:
        check_table_stats()
        print("\nVerification complete!")
    except Exception as e:
        print(f"Error during verification: {e}")
    
if __name__ == "__main__":
    main()
