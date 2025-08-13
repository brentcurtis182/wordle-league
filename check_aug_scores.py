#!/usr/bin/env python3
"""
Check recent scores in the database
"""

import sqlite3
import datetime

def check_recent_scores():
    """Check scores for August in the database"""
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    print("Checking scores in wordle_league.db...\n")
    
    # Get column names first to avoid errors
    cursor.execute("PRAGMA table_info(scores)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Available columns in scores table: {columns}")
    
    # Adapt our query based on column availability
    date_col = "date" if "date" in columns else "score_date"
    player_id_col = "player_id" if "player_id" in columns else "id"
    league_id_col = "league_id" if "league_id" in columns else None
    
    # Get most recent scores (adapt query based on schema)
    if league_id_col:
        query = f"""
        SELECT p.name, s.wordle_number, s.score, s.{date_col}, s.{league_id_col}
        FROM scores s
        JOIN players p ON s.{player_id_col} = p.id
        WHERE s.{date_col} >= '2025-08-01'
        ORDER BY s.{date_col} DESC, p.name
        LIMIT 50
        """
    else:
        query = f"""
        SELECT p.name, s.wordle_number, s.score, s.{date_col}
        FROM scores s
        JOIN players p ON s.{player_id_col} = p.id
        WHERE s.{date_col} >= '2025-08-01'
        ORDER BY s.{date_col} DESC, p.name
        LIMIT 50
        """
    
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        if rows:
            print(f"\nFound {len(rows)} scores since August 1st:")
            for row in rows:
                if league_id_col:
                    print(f"{row[0]}: Wordle #{row[1]} - Score: {row[2]} - Date: {row[3]} - League: {row[4]}")
                else:
                    print(f"{row[0]}: Wordle #{row[1]} - Score: {row[2]} - Date: {row[3]}")
        else:
            print("No scores found since August 1st")
            
        # Get the latest Wordle number
        cursor.execute("SELECT MAX(wordle_number) FROM scores")
        max_wordle = cursor.fetchone()[0]
        print(f"\nLatest Wordle number in database: {max_wordle}")
        
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    
    conn.close()

if __name__ == "__main__":
    check_recent_scores()
