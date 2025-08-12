import sqlite3
import os
import sys

def check_database(db_path):
    """Check a database for recent Wordle scores"""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return False
        
    print(f"\nExamining database: {db_path}")
    
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables: {', '.join(tables)}")
        
        # Check for scores table
        if 'scores' in tables:
            # Check columns
            cursor.execute("PRAGMA table_info(scores)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Columns in scores: {', '.join(columns)}")
            
            # Check for recent scores
            player_col = 'player_name' if 'player_name' in columns else 'player'
            try:
                cursor.execute(f"SELECT wordle_num, {player_col}, score FROM scores WHERE wordle_num >= 1500 ORDER BY wordle_num")
                scores = cursor.fetchall()
                print(f"Found {len(scores)} scores for Wordles 1500+:")
                for row in scores[:10]:  # Show first 10
                    print(f"  Wordle #{row[0]}: {row[1]} - {row[2]}")
                if len(scores) > 10:
                    print(f"  ... and {len(scores)-10} more")
            except Exception as e:
                print(f"Error querying scores: {e}")
        
        # Check for score table (singular)
        if 'score' in tables:
            # Check columns
            cursor.execute("PRAGMA table_info(score)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Columns in score: {', '.join(columns)}")
            
            # Check for recent scores
            try:
                cursor.execute("SELECT wordle_num, player, score FROM score WHERE wordle_num >= 1500 ORDER BY wordle_num")
                scores = cursor.fetchall()
                print(f"Found {len(scores)} scores for Wordles 1500+ in 'score' table:")
                for row in scores[:10]:  # Show first 10
                    print(f"  Wordle #{row[0]}: {row[1]} - {row[2]}")
                if len(scores) > 10:
                    print(f"  ... and {len(scores)-10} more")
            except Exception as e:
                print(f"Error querying score table: {e}")
                
        # Check for players table
        if 'players' in tables:
            try:
                cursor.execute("SELECT * FROM players LIMIT 5")
                players = cursor.fetchall()
                print(f"Found {len(players)} players in 'players' table")
            except Exception as e:
                print(f"Error querying players table: {e}")
                
        # Check for leagues table
        if 'leagues' in tables:
            try:
                cursor.execute("SELECT * FROM leagues")
                leagues = cursor.fetchall()
                print(f"Found {len(leagues)} leagues in 'leagues' table")
            except Exception as e:
                print(f"Error querying leagues table: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error examining database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    # Main database files to check
    main_dbs = [
        'wordle_league.db',
        'wordle_scores.db',
        'wordle.db'
    ]
    
    # Check recent backup
    recent_backup = 'wordle_league_backup_20250801_before_revert.db'
    if os.path.exists(recent_backup):
        main_dbs.append(recent_backup)
    
    for db_path in main_dbs:
        check_database(db_path)
    
if __name__ == "__main__":
    main()
