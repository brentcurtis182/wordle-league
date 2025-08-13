import sqlite3
import os
import sys

def inspect_database_tables():
    """Inspect the database tables to understand the data structure and content"""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== Database Tables ===")
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get column info for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("Columns:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # Count rows in the table
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # Get a sample of data from each table
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            if rows:
                print("Sample data:")
                for row in rows:
                    print(f"  {row}")
        
        # Check for players with scores in multiple leagues
        print("\n=== Players in Multiple Leagues ===")
        cursor.execute("""
        SELECT p1.name, p1.league_id, p2.league_id 
        FROM players p1 
        JOIN players p2 ON p1.name = p2.name AND p1.league_id != p2.league_id
        GROUP BY p1.name
        ORDER BY p1.name
        """)
        multi_league_players = cursor.fetchall()
        for player in multi_league_players:
            name, league1, league2 = player
            print(f"Player: {name} - Leagues: {league1}, {league2}")
        
        # Check for scores in the database for players who shouldn't have any
        print("\n=== Pants score check (Should have none) ===")
        cursor.execute("""
        SELECT s.wordle_number, s.score, s.timestamp
        FROM scores s 
        JOIN players p ON s.player_id = p.id
        WHERE p.name = 'Pants' AND p.league_id = 3
        ORDER BY s.wordle_number
        """)
        pants_scores = cursor.fetchall()
        print(f"Pants (league 3) has {len(pants_scores)} scores")
        for score in pants_scores[:10]:  # Show first 10 scores
            print(f"  Wordle {score[0]}: {score[1]} - {score[2]}")
        
        # Check Gang league players who shouldn't have scores
        print("\n=== Gang League score check ===")
        cursor.execute("""
        SELECT p.name, COUNT(s.id) as score_count
        FROM players p
        LEFT JOIN scores s ON p.id = s.player_id
        WHERE p.league_id = 2
        GROUP BY p.name
        ORDER BY score_count DESC
        """)
        gang_players = cursor.fetchall()
        for player in gang_players:
            name, count = player
            print(f"  {name}: {count} scores")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    inspect_database_tables()
