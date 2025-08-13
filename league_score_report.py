#!/usr/bin/env python3
# League Score Report - Shows scores by league for verification

import sqlite3
from datetime import datetime, timedelta
import textwrap
import os

def get_todays_wordle_number():
    """Get today's Wordle number based on reference date"""
    # Reference point: Wordle #1503 was on July 31, 2025
    reference_wordle = 1503
    reference_date = datetime(2025, 7, 31)
    
    # Get today's date
    today = datetime.now()
    
    # Calculate days since reference point
    days_diff = (today - reference_date).days
    
    # Calculate today's Wordle number
    today_wordle = reference_wordle + days_diff
    
    return today_wordle

def display_league_info(cursor, league_id, league_name):
    """Display info about a specific league and its players"""
    print(f"\n{'='*70}")
    print(f"LEAGUE {league_id}: {league_name}")
    print(f"{'='*70}")
    
    # Get thread ID for this league
    cursor.execute("SELECT thread_id FROM leagues WHERE league_id = ?", (league_id,))
    thread_id = cursor.fetchone()[0]
    print(f"Thread ID: {thread_id}")
    
    # Get players in this league
    cursor.execute("""
        SELECT id, name, phone_number, nickname 
        FROM players 
        WHERE league_id = ?
        ORDER BY name
    """, (league_id,))
    
    players = cursor.fetchall()
    print(f"\nPlayers in this league ({len(players)}):")
    for player in players:
        player_id, name, phone, nickname = player
        nickname_info = f" ('{nickname}')" if nickname else ""
        print(f"  - {name}{nickname_info} [ID: {player_id}]")
    
    return players

def display_league_scores(cursor, league_id, today_wordle=None):
    """Display scores for a specific league for today's wordle"""
    if not today_wordle:
        today_wordle = get_todays_wordle_number()
    
    print(f"\nWORDLE #{today_wordle} SCORES:")
    print(f"{'-'*30}")
    
    # Get scores for this league and wordle number
    cursor.execute("""
        SELECT p.id, p.name, s.score, s.date, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.league_id = ? AND s.wordle_number = ?
        ORDER BY s.score
    """, (league_id, today_wordle))
    
    scores = cursor.fetchall()
    
    if not scores:
        print("No scores found for today's Wordle in this league.")
        return
    
    print(f"Found {len(scores)} scores:")
    for score_data in scores:
        player_id, name, score, date, pattern = score_data
        print(f"\n  {name}: {score}/6 (submitted: {date})")
        
        if pattern:
            print("  Pattern: [Emoji pattern available but not displayed]")
            # Skip displaying the actual emoji pattern to avoid encoding errors
            # pattern_lines = pattern.strip().split('\n')
            # if pattern_lines:
            #     print("  Pattern:")
            #     for line in pattern_lines:
            #         print(f"    {line}")

def main():
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    # Get all leagues
    cursor.execute("SELECT league_id, name FROM leagues ORDER BY league_id")
    leagues = cursor.fetchall()
    
    # Get today's wordle number
    today_wordle = get_todays_wordle_number()
    
    print(f"\n{'*'*80}")
    print(f"WORDLE LEAGUE SCORE REPORT - WORDLE #{today_wordle} ({datetime.now().strftime('%Y-%m-%d')})")
    print(f"{'*'*80}")
    
    # Process each league
    for league_id, league_name in leagues:
        # Show league info
        players = display_league_info(cursor, league_id, league_name)
        
        # Show today's scores
        display_league_scores(cursor, league_id, today_wordle)
        
        # Get yesterday's wordle number
        yesterday_wordle = today_wordle - 1
        
        # Check yesterday's scores count for reference
        cursor.execute("""
            SELECT COUNT(*)
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE p.league_id = ? AND s.wordle_number = ?
        """, (league_id, yesterday_wordle))
        
        yesterday_count = cursor.fetchone()[0]
        
        print(f"\nFor reference: Wordle #{yesterday_wordle} (yesterday) had {yesterday_count} scores in this league")
        
        print("\n" + "-"*70 + "\n")
    
    # Show some general statistics
    print(f"\n{'*'*80}")
    print("GENERAL STATISTICS")
    print(f"{'*'*80}")
    
    # Count total scores by wordle number
    cursor.execute("""
        SELECT s.wordle_number, COUNT(*) 
        FROM scores s 
        WHERE s.wordle_number >= ? 
        GROUP BY s.wordle_number 
        ORDER BY s.wordle_number DESC
        LIMIT 5
    """, (today_wordle - 4,))
    
    wordle_stats = cursor.fetchall()
    
    print("\nRecent Wordle participation:")
    for wordle_num, count in wordle_stats:
        print(f"  Wordle #{wordle_num}: {count} scores")
    
    conn.close()

if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear screen for better readability
    main()
