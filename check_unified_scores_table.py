#!/usr/bin/env python3
"""
Check Unified Scores Table Schema
This script checks the unified scores table schema and displays samples of
today's scores for all leagues to help with migration debugging
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta

def check_table_schema(db_path, table_name):
    """Check the schema of a database table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\nTABLE SCHEMA: {table_name}")
        print("-" * 50)
        
        for col in columns:
            print(f"{col[0]}: {col[1]} ({col[2]})")
        
        return columns
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return []
    finally:
        if conn:
            conn.close()

def check_today_scores(db_path):
    """Check scores from today in the unified scores table for all leagues"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the current Wordle number
        cursor.execute("""
            SELECT MAX(wordle_number) FROM scores
        """)
        latest_wordle = cursor.fetchone()[0]
        
        print(f"\nLatest Wordle Number: {latest_wordle}")
        
        # Get scores for this wordle for all leagues
        cursor.execute("""
            SELECT s.id, s.player_id, p.name, p.league_id, s.score, s.wordle_number, 
                   s.date, LENGTH(s.emoji_pattern) as emoji_length
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ?
            ORDER BY p.league_id, s.score
        """, (latest_wordle,))
        
        results = cursor.fetchall()
        
        print(f"\nFOUND {len(results)} SCORES FOR WORDLE #{latest_wordle}")
        print("-" * 50)
        print("ID  | Player (ID) | League | Score | Date | Emoji Length")
        print("-" * 50)
        
        for row in results:
            score_id, player_id, player_name, league_id, score, wordle_num, date, emoji_len = row
            print(f"{score_id:<4}| {player_name} ({player_id:<2}) | {league_id:<6} | {score:<5} | {date} | {emoji_len} chars")
            
        return len(results)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 0
    finally:
        if conn:
            conn.close()

def check_players_table(db_path):
    """Check the players table for league information"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get player counts by league
        cursor.execute("""
            SELECT league_id, COUNT(*) as player_count 
            FROM players 
            GROUP BY league_id
            ORDER BY league_id
        """)
        
        league_counts = cursor.fetchall()
        
        print(f"\nPLAYER COUNTS BY LEAGUE")
        print("-" * 30)
        
        for league_id, count in league_counts:
            print(f"League {league_id}: {count} players")
            
        # Sample players from each league
        for league_id, _ in league_counts:
            cursor.execute("""
                SELECT id, name, nickname, league_id 
                FROM players 
                WHERE league_id = ?
                LIMIT 3
            """, (league_id,))
            
            players = cursor.fetchall()
            
            print(f"\nSAMPLE PLAYERS FOR LEAGUE {league_id}")
            print("-" * 40)
            
            for player in players:
                print(f"ID: {player[0]}, Name: {player[1]}, Nickname: {player[2]}")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
    finally:
        if conn:
            conn.close()

def main():
    """Main function"""
    # Database path - get from environment or use default
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_db_path = os.path.join(script_dir, 'wordle_league.db')
    db_path = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')
    
    print(f"Using database at: {db_path}")
    
    # Check the scores table schema
    check_table_schema(db_path, 'scores')
    
    # Check the players table schema
    check_table_schema(db_path, 'players')
    
    # Check players by league
    check_players_table(db_path)
    
    # Check today's scores for all leagues
    check_today_scores(db_path)
    
if __name__ == "__main__":
    main()
