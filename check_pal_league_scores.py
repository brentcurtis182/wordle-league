#!/usr/bin/env python3
"""
Quick check for PAL league scores including Vox's scores
"""
import sqlite3
import os
from datetime import datetime, timedelta

def check_pal_league_scores():
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
        
        # Check database schema first
        print("\n=== DATABASE SCHEMA ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {', '.join(t[0] for t in tables)}")
        
        # Check scores table schema
        print("\n=== SCORES TABLE SCHEMA ===")
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        if not columns:
            print("Scores table not found")
        else:
            column_names = [col[1] for col in columns]
            print(f"Columns: {', '.join(column_names)}")
            
            # Also check score table (singular) as there might be two tables
            try:
                cursor.execute("PRAGMA table_info(score)")
                columns2 = cursor.fetchall()
                if columns2:
                    column_names2 = [col[1] for col in columns2]
                    print(f"\nAlternate 'score' table found with columns: {', '.join(column_names2)}")
            except:
                pass
        
        # Check for all PAL league scores (league_id=3)
        print("\n=== ALL PAL LEAGUE SCORES ===")
        cursor.execute("""
            SELECT player_name, wordle_num, score, emoji_pattern, timestamp 
            FROM scores 
            WHERE league_id=3
            ORDER BY wordle_num DESC, player_name ASC
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        if not rows:
            print("No scores found for PAL league")
        else:
            print(f"{'Player':<15} {'Wordle':<10} {'Score':<10} {'Date Added':<20}")
            print("-" * 60)
            for row in rows:
                player, wordle_num, score, pattern, date_added = row
                print(f"{player:<15} #{wordle_num:<9} {score}/6{' ':<9} {date_added}")
        
        # Check specifically for Vox's scores
        print("\n=== VOX'S SCORES ===")
        cursor.execute("""
            SELECT wordle_num, score, emoji_pattern, timestamp 
            FROM scores 
            WHERE player_name='Vox' AND league_id=3
            ORDER BY wordle_num DESC
            LIMIT 5
        """)
        
        rows = cursor.fetchall()
        if not rows:
            print("No scores found for Vox")
        else:
            print(f"{'Wordle':<10} {'Score':<10} {'Date Added':<20}")
            print("-" * 50)
            for row in rows:
                wordle_num, score, pattern, date_added = row
                print(f"#{wordle_num:<9} {score}/6{' ':<9} {date_added}")
        
        # Check for today's scores in PAL league
        print(f"\n=== TODAY'S SCORES (#{today_wordle}) IN PAL LEAGUE ===")
        cursor.execute("""
            SELECT player_name, score, emoji_pattern, timestamp 
            FROM scores 
            WHERE wordle_num=? AND league_id=3
            ORDER BY player_name ASC
        """, (today_wordle,))
        
        rows = cursor.fetchall()
        if not rows:
            print(f"No scores found for Wordle #{today_wordle} in PAL league")
        else:
            print(f"{'Player':<15} {'Score':<10} {'Date Added':<20}")
            print("-" * 50)
            for row in rows:
                player, score, pattern, date_added = row
                print(f"{player:<15} {score}/6{' ':<9} {date_added}")
        
        print("\nNOTE: If Vox has submitted a score but it's not showing up, check:")
        print("1. The score format in Google Voice (should be 'Wordle 1503 X/6' format)")
        print("2. The phone number mapping in the script (should map (858) 735-9353 to Vox in league 3)")
        print("3. If the score was sent with correct emoji pattern")
        
    except Exception as e:
        print(f"Error checking scores: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_pal_league_scores()
