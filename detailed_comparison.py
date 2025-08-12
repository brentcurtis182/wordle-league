#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Perform a detailed comparison between latest scores and weekly stats
to show clear evidence that our fix worked.
"""

import os
import sqlite3
import logging
from datetime import datetime
import tabulate  # For nice table output

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_db(db_path='wordle_league.db'):
    """Connect to the SQLite database and return connection and cursor"""
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

def calculate_wordle_number():
    """Calculate today's Wordle number"""
    # Wordle #0 was on June 19, 2021
    base_date = datetime.strptime("2021-06-19", "%Y-%m-%d")
    today = datetime.now()
    days_since_base = (today - base_date).days
    return days_since_base

def get_weekly_range():
    """Calculate the current week's Wordle number range"""
    today_wordle = calculate_wordle_number()
    # Calculate start and end of week (Monday-Sunday)
    today_weekday = datetime.now().weekday()  # Monday is 0, Sunday is 6
    start_wordle = today_wordle - today_weekday
    end_wordle = start_wordle + 6
    return start_wordle, end_wordle

def get_league_name(league_id):
    """Get league name based on ID"""
    league_names = {
        1: "Wordle Warriorz",
        2: "Wordle Gang",
        3: "Wordle PAL"
    }
    return league_names.get(league_id, f"League {league_id}")

def compare_league_data(league_id):
    """Compare latest scores with weekly stats for a league"""
    conn, cursor = connect_to_db()
    
    league_name = get_league_name(league_id)
    today_wordle = calculate_wordle_number()
    start_wordle, end_wordle = get_weekly_range()
    
    logging.info(f"\n{'='*80}\nComparing data for {league_name} (ID: {league_id})")
    logging.info(f"Today's Wordle: {today_wordle}")
    logging.info(f"Weekly range: {start_wordle} to {end_wordle}\n")
    
    # Get all players in the league
    cursor.execute("SELECT id, name FROM players WHERE league_id = ?", (league_id,))
    players_data = cursor.fetchall()
    players = {row['id']: row['name'] for row in players_data}
    
    # Table header
    headers = ["Player", "Latest Score", "In Weekly Stats", "Used in Weekly Total", "In All-time Stats"]
    rows = []
    
    # For each player, collect data
    for player_id, player_name in players.items():
        # Get latest score for this player (today's Wordle)
        cursor.execute("""
        SELECT s.score, s.emoji_pattern 
        FROM scores s 
        WHERE s.player_id = ? AND s.wordle_number = ?
        """, (player_id, today_wordle))
        latest_score_row = cursor.fetchone()
        latest_score = latest_score_row['score'] if latest_score_row else "-"
        
        # Get all weekly scores for this player
        cursor.execute("""
        SELECT s.score, s.wordle_number
        FROM scores s
        WHERE s.player_id = ? AND s.wordle_number >= ? AND s.wordle_number <= ?
        ORDER BY s.score
        """, (player_id, start_wordle, end_wordle))
        weekly_scores = [row['score'] for row in cursor.fetchall()]
        
        # Check if latest score is in weekly scores
        has_in_weekly = "Yes" if latest_score in weekly_scores and latest_score != "-" else "N/A"
        
        # Check if score is used in weekly total (top 5 non-failed scores)
        valid_weekly_scores = [s for s in weekly_scores if s < 7]  # Failed attempts = 7
        top_scores = sorted(valid_weekly_scores)[:5]
        used_in_weekly = "Yes" if latest_score in top_scores and latest_score != "-" else "N/A"
        
        # Get all-time scores for this player
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM scores s
        WHERE s.player_id = ?
        """, (player_id,))
        all_time_count = cursor.fetchone()['count']
        
        # Check if player has any all-time scores
        in_all_time = "Yes" if all_time_count > 0 else "No"
        
        # Add to table rows
        rows.append([player_name, latest_score, has_in_weekly, used_in_weekly, in_all_time])
    
    # Display table
    print("\n" + tabulate.tabulate(rows, headers=headers, tablefmt="pipe"))
    
    # Also get the actual weekly stats from the calculation
    print("\nWeekly Stats Calculation:")
    print(f"{'Player':<15} {'Weekly Score':<15} {'Used Scores':<15}")
    
    # Calculate weekly stats
    for player_id, player_name in players.items():
        # Get all weekly scores for this player
        cursor.execute("""
        SELECT s.score
        FROM scores s
        WHERE s.player_id = ? AND s.wordle_number >= ? AND s.wordle_number <= ?
        ORDER BY s.score
        """, (player_id, start_wordle, end_wordle))
        
        all_scores = [row['score'] for row in cursor.fetchall()]
        valid_scores = [s for s in all_scores if s < 7]  # Exclude failed attempts
        weekly_score = sum(sorted(valid_scores)[:5]) if valid_scores else "-"
        used_scores = len(valid_scores)
        
        print(f"{player_name:<15} {str(weekly_score):<15} {str(used_scores):<15}")
    
    # Get scores that only appear in 'scores' table
    cursor.execute("""
    SELECT p.name, s.score, s.wordle_number
    FROM scores s
    JOIN players p ON s.player_id = p.id
    WHERE p.league_id = ? AND s.wordle_number >= ? AND s.wordle_number <= ?
    ORDER BY p.name, s.wordle_number
    """, (league_id, start_wordle, end_wordle))
    
    scores_table_results = {}
    for row in cursor.fetchall():
        if row['name'] not in scores_table_results:
            scores_table_results[row['name']] = []
        scores_table_results[row['name']].append((row['wordle_number'], row['score']))
    
    print("\nScores in 'scores' table for this week:")
    for player_name, scores in scores_table_results.items():
        if scores:
            score_str = ", ".join([f"Wordle #{wn}: {s}" for wn, s in scores])
            print(f"  {player_name}: {score_str}")
        else:
            print(f"  {player_name}: No scores")
    
    conn.close()

def main():
    """Run comparisons for all leagues"""
    conn, cursor = connect_to_db()
    
    # Get all leagues
    cursor.execute("SELECT DISTINCT league_id FROM players ORDER BY league_id")
    league_ids = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    # Run comparison for each league
    for league_id in league_ids:
        compare_league_data(league_id)
    
    print("\n✅ Comparison complete! Check the results above to confirm consistency.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Error during comparison: {e}")
        import traceback
        traceback.print_exc()
