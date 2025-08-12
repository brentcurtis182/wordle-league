#!/usr/bin/env python3
"""
Check scores for today in all leagues
"""
import sqlite3
import os
from datetime import datetime, timedelta

def check_todays_scores():
    # Calculate today's Wordle number
    base_date = datetime(2021, 6, 19)  # Wordle #0
    today = datetime.now()
    days_since_base = (today - base_date).days
    today_wordle = days_since_base
    yesterday_wordle = today_wordle - 1
    
    print(f"Today's Wordle #{today_wordle} for date {today.strftime('%Y-%m-%d')}")
    print(f"Yesterday's Wordle #{yesterday_wordle} for date {(today - timedelta(days=1)).strftime('%Y-%m-%d')}")
    
    # Connect to database
    db_path = os.path.join(os.getcwd(), "wordle_league.db")
    print(f"Using database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check both tables
        tables = ["scores", "score"]
        
        for table_name in tables:
            print(f"\n=== SCORES FROM {table_name.upper()} TABLE ===")
            
            # Check the schema first to ensure we use correct column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            if not columns:
                print(f"{table_name} table not found")
                continue
                
            column_dict = {col[1]: col[0] for col in columns}
            
            # Determine column names based on table
            if table_name == "scores":
                player_col = "player_name" 
                wordle_col = "wordle_num"
                league_col = "league_id"
            else:  # score table
                player_col = "player"
                wordle_col = "wordle_number" if "wordle_number" in column_dict else "wordle_num"
                league_col = "league_id"
                
            score_col = "score"
            
            # Main League today's scores
            print(f"\n-- TODAY'S SCORES (#{today_wordle}) IN MAIN LEAGUE (ID: 1) --")
            try:
                cursor.execute(f"""
                SELECT {player_col}, {score_col}
                FROM {table_name}
                WHERE {wordle_col}=? AND {league_col}=1
                ORDER BY {player_col} ASC
                """, (today_wordle,))
                
                rows = cursor.fetchall()
                if not rows:
                    print(f"No scores found for Wordle #{today_wordle} in Main league")
                else:
                    print(f"{'Player':<15} {'Score':<10}")
                    print("-" * 30)
                    for row in rows:
                        player, score = row
                        print(f"{player:<15} {score}/6")
            except Exception as e:
                print(f"Error querying main league: {e}")
                
            # PAL League today's scores
            print(f"\n-- TODAY'S SCORES (#{today_wordle}) IN PAL LEAGUE (ID: 3) --")
            try:
                cursor.execute(f"""
                SELECT {player_col}, {score_col}
                FROM {table_name}
                WHERE {wordle_col}=? AND {league_col}=3
                ORDER BY {player_col} ASC
                """, (today_wordle,))
                
                rows = cursor.fetchall()
                if not rows:
                    print(f"No scores found for Wordle #{today_wordle} in PAL league")
                else:
                    print(f"{'Player':<15} {'Score':<10}")
                    print("-" * 30)
                    for row in rows:
                        player, score = row
                        print(f"{player:<15} {score}/6")
            except Exception as e:
                print(f"Error querying PAL league: {e}")
                
            # Check specifically for Vox in PAL league (all dates)
            print(f"\n-- ALL VOX SCORES IN PAL LEAGUE (ID: 3) --")
            try:
                cursor.execute(f"""
                SELECT {wordle_col}, {score_col}
                FROM {table_name}
                WHERE {player_col}='Vox' AND {league_col}=3
                ORDER BY {wordle_col} DESC
                """)
                
                rows = cursor.fetchall()
                if not rows:
                    print(f"No scores found for Vox in PAL league")
                else:
                    print(f"{'Wordle':<10} {'Score':<10}")
                    print("-" * 25)
                    for row in rows:
                        wordle_num, score = row
                        print(f"#{wordle_num:<9} {score}/6")
            except Exception as e:
                print(f"Error querying Vox's scores: {e}")
        
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_todays_scores()
