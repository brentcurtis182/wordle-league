#!/usr/bin/env python3
# Script to check scores in each league for verification

import sqlite3
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("league_verification.log"),
        logging.StreamHandler()
    ]
)

# Connect to the database
conn = sqlite3.connect('wordle_league.db')
cursor = conn.cursor()

def get_todays_wordle_number():
    """Get today's Wordle number"""
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

def check_scores_by_league():
    """Check and display scores for each league"""
    
    # Get today's wordle number
    today_wordle = get_todays_wordle_number()
    yesterday_wordle = today_wordle - 1
    
    # Verify leagues in the database
    cursor.execute("SELECT league_id, name FROM leagues")
    leagues = cursor.fetchall()
    
    print("\n==== LEAGUES IN DATABASE ====")
    for league_id, league_name in leagues:
        print(f"League {league_id}: {league_name}")
    
    # Check scores for today and yesterday by league
    for wordle_num in [today_wordle, yesterday_wordle]:
        print(f"\n==== WORDLE #{wordle_num} SCORES BY LEAGUE ====")
        
        for league_id, league_name in leagues:
            print(f"\n-- LEAGUE {league_id}: {league_name} --")
            
            # Get scores for this league and wordle number
            cursor.execute("""
                SELECT p.name, s.score, s.pattern, s.date_added
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE s.league_id = ? AND s.wordle_num = ?
                ORDER BY s.score
            """, (league_id, wordle_num))
            
            scores = cursor.fetchall()
            
            if scores:
                print(f"Found {len(scores)} scores for Wordle #{wordle_num}:")
                for player, score, pattern, date_added in scores:
                    print(f"  {player}: {score}/6 (added: {date_added})")
                    if pattern:
                        pattern_lines = pattern.split('\n')
                        if len(pattern_lines) > 0:
                            print(f"    Pattern: ({len(pattern_lines)} lines)")
                            for line in pattern_lines[:3]:  # Show first few lines only
                                print(f"    {line}")
                            if len(pattern_lines) > 3:
                                print(f"    ... ({len(pattern_lines) - 3} more lines)")
            else:
                print(f"No scores found for Wordle #{wordle_num}")

def check_player_leagues():
    """Check which leagues each player belongs to"""
    
    print("\n==== PLAYERS AND THEIR LEAGUES ====")
    
    # Get all players
    cursor.execute("SELECT id, name FROM players ORDER BY name")
    players = cursor.fetchall()
    
    for player_id, player_name in players:
        # Find which leagues this player has scores in
        cursor.execute("""
            SELECT DISTINCT l.id, l.name
            FROM leagues l
            JOIN scores s ON s.league_id = l.id
            WHERE s.player_id = ?
        """, (player_id,))
        
        player_leagues = cursor.fetchall()
        
        if player_leagues:
            leagues_str = ", ".join([f"{lid}:{lname}" for lid, lname in player_leagues])
            print(f"{player_name} (ID: {player_id}) - Leagues: {leagues_str}")
        else:
            print(f"{player_name} (ID: {player_id}) - No scores in any league")

if __name__ == "__main__":
    try:
        print("\nVerifying Wordle League Database Scores")
        print("=" * 40)
        
        check_scores_by_league()
        check_player_leagues()
        
    except Exception as e:
        logging.error(f"Error checking scores: {str(e)}")
    finally:
        conn.close()
