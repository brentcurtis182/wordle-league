#!/usr/bin/env python3
# Script to check PAL league stats in the database
import sqlite3
import sys
from datetime import datetime, timedelta

def check_scores(db_path, league_id=3, limit=50):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get today's date and the start of the week (Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        print(f"Today: {today.strftime('%Y-%m-%d')}")
        print(f"Start of week: {start_date}")
        
        # Display recent scores for PAL league
        print(f"\nRECENT SCORES FOR LEAGUE {league_id} (PAL):")
        print("-" * 80)
        
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, emoji_pattern
        FROM scores
        WHERE league_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """, (league_id, limit))
        
        rows = cursor.fetchall()
        
        for row in rows:
            id, player, wordle, score, timestamp, pattern = row
            pattern_preview = pattern[:20] + "..." if pattern and len(pattern) > 20 else pattern
            print(f"ID: {id}, Player: {player}, Wordle: {wordle}, Score: {score}, Date: {timestamp}, Pattern: {pattern_preview}")
        
        print(f"\nFound {len(rows)} recent scores for league {league_id}")
        
        # Check unique players
        print(f"\nPLAYERS IN LEAGUE {league_id} WITH SCORES THIS WEEK:")
        print("-" * 80)
        
        cursor.execute("""
        SELECT DISTINCT player_name
        FROM scores
        WHERE league_id = ? AND timestamp >= ?
        """, (league_id, start_date))
        
        players = cursor.fetchall()
        print(f"Found {len(players)} players with scores this week:")
        for player in players:
            print(f"- {player[0]}")
            
        # Check each player's scores this week
        print(f"\nWEEKLY SCORES PER PLAYER:")
        print("-" * 80)
        
        for player_row in players:
            name = player_row[0]
            cursor.execute("""
            SELECT score, date(timestamp) as score_date
            FROM scores
            WHERE player_name = ? AND league_id = ? AND timestamp >= ?
            ORDER BY score_date
            """, (name, league_id, start_date))
            
            scores = cursor.fetchall()
            print(f"{name}: {len(scores)} scores this week")
            for score, date in scores:
                print(f"  {date}: {score}")
                
        return True
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_scores('wordle_league.db')
