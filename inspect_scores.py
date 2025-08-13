import sqlite3
import os
import sys

def inspect_scores_table():
    """Inspect the scores table specifically to understand where fake scores might be coming from"""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check the structure of the scores table
        print("\n=== Scores Table Structure ===")
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Count total scores
        cursor.execute("SELECT COUNT(*) FROM scores")
        total_count = cursor.fetchone()[0]
        print(f"\nTotal scores in database: {total_count}")
        
        # Count scores by league
        print("\n=== Scores by League ===")
        cursor.execute("""
        SELECT p.league_id, COUNT(*) 
        FROM scores s
        JOIN players p ON s.player_id = p.id
        GROUP BY p.league_id
        """)
        for row in cursor.fetchall():
            league_id, count = row
            print(f"  League {league_id}: {count} scores")
        
        # Look at distribution of scores by Wordle number
        print("\n=== Scores by Wordle Number (recent) ===")
        cursor.execute("""
        SELECT wordle_number, COUNT(*) 
        FROM scores 
        WHERE wordle_number >= 1500
        GROUP BY wordle_number
        ORDER BY wordle_number DESC
        """)
        for row in cursor.fetchall():
            wordle_num, count = row
            print(f"  Wordle {wordle_num}: {count} scores")
        
        # Check for Pants scores specifically
        print("\n=== Pants Scores (League 3) ===")
        cursor.execute("""
        SELECT s.id, s.wordle_number, s.score, s.emoji_pattern, s.timestamp
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.name = 'Pants' AND p.league_id = 3
        ORDER BY s.wordle_number DESC
        """)
        pants_scores = cursor.fetchall()
        for score in pants_scores[:10]:  # Limit to first 10
            score_id, wordle_num, score_val, emoji, timestamp = score
            print(f"  ID {score_id}: Wordle {wordle_num}, Score {score_val}, Timestamp: {timestamp}")
        
        # Look at Gang League scores (league 2)
        print("\n=== Gang League Players with Scores (League 2) ===")
        cursor.execute("""
        SELECT p.name, s.wordle_number, s.score, s.timestamp
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.league_id = 2
        ORDER BY p.name, s.wordle_number DESC
        """)
        gang_scores = cursor.fetchall()
        for score in gang_scores[:20]:  # Limit to first 20
            name, wordle_num, score_val, timestamp = score
            print(f"  {name}: Wordle {wordle_num}, Score {score_val}, Timestamp: {timestamp}")
        
        # Create a report on possibly fake or duplicate scores
        print("\n=== Potential Issues ===")
        
        # Check for duplicate scores for same player, same wordle
        cursor.execute("""
        SELECT p.name, p.league_id, s.wordle_number, COUNT(*) as cnt
        FROM scores s
        JOIN players p ON s.player_id = p.id
        GROUP BY p.name, p.league_id, s.wordle_number
        HAVING COUNT(*) > 1
        ORDER BY cnt DESC
        """)
        dupes = cursor.fetchall()
        if dupes:
            print("Duplicate scores found (same player, same wordle):")
            for dupe in dupes:
                name, league_id, wordle_num, count = dupe
                print(f"  {name} (League {league_id}): Wordle {wordle_num} has {count} entries")
        else:
            print("No duplicate scores found.")
        
        # Find players that have scores but shouldn't according to what we know
        print("\nPlayers who should not have scores but do:")
        # Check Pants in League 3
        cursor.execute("""
        SELECT COUNT(*) FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.name = 'Pants' AND p.league_id = 3
        """)
        pants_count = cursor.fetchone()[0]
        if pants_count > 0:
            print(f"  Pants (League 3): {pants_count} scores - SUSPICIOUS (should be 0)")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_scores_table()
