#!/usr/bin/env python3
# Enhanced script to check PAL league stats in the database
import sqlite3
import sys
from datetime import datetime, timedelta
import traceback

def check_scores(db_path, league_id=3, limit=100):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get today's date and the start of the week (Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        print(f"Today: {today.strftime('%Y-%m-%d')}")
        print(f"Start of week: {start_date}")
        
        # Get column names for scores table
        cursor.execute("PRAGMA table_info(scores)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\nScores table columns: {columns}")
        
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
            print(f"ID: {id}, Player: {player}, Wordle: {wordle}, Score: {score}, Date: {timestamp}")
        
        print(f"\nFound {len(rows)} recent scores for league {league_id}")
        
        # Check unique players
        print(f"\nPLAYERS IN LEAGUE {league_id}:")
        print("-" * 80)
        
        cursor.execute("""
        SELECT DISTINCT player_name
        FROM scores
        WHERE league_id = ?
        """, (league_id,))
        
        all_players = cursor.fetchall()
        print(f"Found {len(all_players)} total players in league {league_id}:")
        for player in all_players:
            print(f"- {player[0]}")
        
        # Check players with scores this week
        cursor.execute("""
        SELECT DISTINCT player_name
        FROM scores
        WHERE league_id = ? AND timestamp >= ?
        """, (league_id, start_date))
        
        weekly_players = cursor.fetchall()
        print(f"\nFound {len(weekly_players)} players with scores this week:")
        for player in weekly_players:
            print(f"- {player[0]}")
            
        # Check each player's scores this week in detail
        print(f"\nWEEKLY SCORES DETAILS:")
        print("-" * 80)
        
        for player_row in all_players:
            name = player_row[0]
            
            # Get weekly scores
            cursor.execute("""
            SELECT score, date(timestamp) as score_date, wordle_num
            FROM scores
            WHERE player_name = ? AND league_id = ? AND timestamp >= ?
            ORDER BY score_date
            """, (name, league_id, start_date))
            
            weekly_scores = cursor.fetchall()
            
            # Get all scores (for all-time stats)
            cursor.execute("""
            SELECT score, date(timestamp) as score_date, wordle_num
            FROM scores
            WHERE player_name = ? AND league_id = ?
            ORDER BY score_date
            """, (name, league_id))
            
            all_scores = cursor.fetchall()
            
            print(f"\n{name}:")
            print(f"  Total scores in database: {len(all_scores)}")
            print(f"  Scores this week: {len(weekly_scores)}")
            
            print("  Weekly scores:")
            for score, date, wordle in weekly_scores:
                print(f"    Wordle {wordle} ({date}): {score}")
            
            print("  All-time scores:")
            for score, date, wordle in all_scores:
                print(f"    Wordle {wordle} ({date}): {score}")
        
        # Debug weekly stats calculation
        print(f"\nDEBUG WEEKLY STATS CALCULATION:")
        print("-" * 80)
        
        for player_row in all_players:
            name = player_row[0]
            
            cursor.execute("""
            SELECT DISTINCT score, timestamp, date(timestamp) as score_date
            FROM scores
            WHERE player_name = ? AND league_id = ? AND timestamp >= ?
            GROUP BY date(timestamp)
            ORDER BY 
                CASE 
                    WHEN score = 'X' THEN 7
                    WHEN score = '-' THEN 8
                    ELSE CAST(score AS INTEGER)
                END
            """, (name, league_id, start_date))
            
            scores_this_week = cursor.fetchall()
            print(f"\nPlayer {name}: {len(scores_this_week)} unique scores this week")
            
            weekly_scores = []
            for score_row in scores_this_week:
                score = score_row[0]
                date = score_row[1][:10] if len(score_row) > 1 and score_row[1] else 'Unknown date'
                score_date = score_row[2] if len(score_row) > 2 else 'Unknown date'
                print(f"  Score: {score}, Date: {date}, Score Date: {score_date}")
                
                try:
                    if score not in ['X', '-']:
                        weekly_scores.append(int(score))
                except ValueError as e:
                    print(f"  ERROR: Could not convert score '{score}' to integer: {e}")
            
            # Calculate weekly stats as the export script would
            weekly_scores.sort()
            top_scores = weekly_scores[:5]
            total_weekly = sum(top_scores) if top_scores else None
            used_scores = len(top_scores)
            
            print(f"  Weekly scores after processing: {weekly_scores}")
            print(f"  Top scores (max 5): {top_scores}")
            print(f"  Weekly total: {total_weekly}")
            print(f"  Used scores: {used_scores}")
            
        return True
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        traceback.print_exc()
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_scores('wordle_league.db')
