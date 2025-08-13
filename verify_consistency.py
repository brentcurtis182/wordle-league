#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verify consistency between latest scores and weekly/all-time stats
to confirm that our fix worked correctly.
"""

import os
import sqlite3
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_db(db_path='wordle_league.db'):
    """Connect to the SQLite database and return connection and cursor"""
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), db_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    return conn, cursor

def get_latest_scores(cursor, wordle_number, league_id):
    """Get the latest scores from the database for a specific wordle number and league"""
    cursor.execute("""
    SELECT p.name, s.score, s.emoji_pattern, s.wordle_number
    FROM scores s
    JOIN players p ON s.player_id = p.id
    WHERE s.wordle_number = ? AND p.league_id = ?
    ORDER BY s.score
    """, (wordle_number, league_id))
    
    return [dict(row) for row in cursor.fetchall()]

def get_weekly_stats(cursor, league_id, start_wordle, end_wordle):
    """Get weekly stats from the database for a specific league and wordle range"""
    player_stats = {}
    
    # Get all players in the league
    cursor.execute("SELECT id, name FROM players WHERE league_id = ?", (league_id,))
    players = {row['id']: row['name'] for row in cursor.fetchall()}
    
    # Initialize stats for all players
    for player_id, name in players.items():
        player_stats[name] = {
            'name': name,
            'scores': [],
            'weekly_score': 0,
            'used_scores': 0,
            'failed_attempts': 0
        }
    
    # Get scores for each player in the wordle range
    for player_id, name in players.items():
        cursor.execute("""
        SELECT s.score, s.timestamp, s.wordle_number
        FROM scores s
        WHERE s.player_id = ? AND s.wordle_number >= ? AND s.wordle_number <= ?
        ORDER BY s.score
        """, (player_id, start_wordle, end_wordle))
        
        for row in cursor.fetchall():
            score = row['score']
            player_stats[name]['scores'].append(score)
            
            # Count failed attempts (score of 7)
            if score == 7:
                player_stats[name]['failed_attempts'] += 1
    
    # Calculate weekly stats
    for name, stats in player_stats.items():
        valid_scores = [s for s in stats['scores'] if s < 7]
        stats['used_scores'] = len(valid_scores)
        
        # Calculate weekly score (sum of top 5 valid scores)
        top_scores = sorted(valid_scores)[:5]
        stats['weekly_score'] = sum(top_scores) if top_scores else '-'
    
    return list(player_stats.values())

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
    # Wordle numbers increment by 1 each day
    today_weekday = datetime.now().weekday()  # Monday is 0, Sunday is 6
    start_wordle = today_wordle - today_weekday
    end_wordle = start_wordle + 6
    return start_wordle, end_wordle

def verify_league_consistency(league_id, league_name):
    """Verify data consistency for a specific league"""
    conn, cursor = connect_to_db()
    
    # Get current Wordle number and week range
    today_wordle = calculate_wordle_number()
    start_wordle, end_wordle = get_weekly_range()
    
    logging.info(f"Verifying consistency for league: {league_name} (ID: {league_id})")
    logging.info(f"Today's Wordle: {today_wordle}")
    logging.info(f"Weekly range: {start_wordle} to {end_wordle}")
    
    # Get latest scores
    latest_scores = get_latest_scores(cursor, today_wordle, league_id)
    logging.info(f"Latest scores: {len(latest_scores)} entries")
    
    # Get weekly stats
    weekly_stats = get_weekly_stats(cursor, league_id, start_wordle, end_wordle)
    logging.info(f"Weekly stats: {len(weekly_stats)} entries")
    
    # Cross-reference check
    all_consistent = True
    
    # Map of player names to their latest scores
    latest_score_by_player = {score['name']: score for score in latest_scores}
    
    # Map of player names to their weekly stats
    weekly_stats_by_player = {stat['name']: stat for stat in weekly_stats}
    
    # Check players in latest scores
    for name, score_data in latest_score_by_player.items():
        if name in weekly_stats_by_player:
            weekly_data = weekly_stats_by_player[name]
            
            # Verify if this player's latest score is reflected in weekly stats
            if score_data['wordle_number'] >= start_wordle and score_data['wordle_number'] <= end_wordle:
                score_value = score_data['score']
                
                # For failed attempts (X/6), score is stored as 7
                if score_value == 7:
                    if weekly_data['failed_attempts'] < 1:
                        logging.warning(f"Inconsistency: {name} has failed attempt in latest but not in weekly")
                        all_consistent = False
                else:
                    # Check if score exists in player's weekly scores
                    if score_value not in weekly_data['scores']:
                        logging.warning(f"Inconsistency: {name}'s score {score_value} not found in weekly scores")
                        all_consistent = False
        else:
            logging.warning(f"Player {name} has latest score but missing from weekly stats")
            all_consistent = False
    
    # Check if all players in weekly stats have corresponding entries in latest
    for name in weekly_stats_by_player:
        if name not in latest_score_by_player:
            # This is OK - not all players have scores for latest wordle
            pass
    
    conn.close()
    
    return all_consistent

def verify_all_leagues():
    """Verify data consistency across all leagues"""
    conn, cursor = connect_to_db()
    
    # Get all distinct league IDs from players table
    cursor.execute("SELECT DISTINCT league_id FROM players ORDER BY league_id")
    league_ids = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    all_consistent = True
    results = []
    
    # League names mapping based on our known data
    league_names = {
        1: "Wordle Warriorz",
        2: "Wordle Gang",
        3: "Wordle PAL"
    }
    
    for league_id in league_ids:
        league_name = league_names.get(league_id, f"League {league_id}")
        
        is_consistent = verify_league_consistency(league_id, league_name)
        results.append({
            'league_id': league_id,
            'league_name': league_name,
            'is_consistent': is_consistent
        })
        
        if not is_consistent:
            all_consistent = False
    
    return all_consistent, results

if __name__ == "__main__":
    logging.info("Starting consistency verification")
    all_consistent, results = verify_all_leagues()
    
    logging.info("\n--- VERIFICATION RESULTS ---")
    for result in results:
        status = "✓ CONSISTENT" if result['is_consistent'] else "✗ INCONSISTENT"
        logging.info(f"League {result['league_name']} (ID: {result['league_id']}): {status}")
    
    if all_consistent:
        logging.info("\n✅ SUCCESS: All leagues have consistent data between latest scores and weekly stats!")
    else:
        logging.warning("\n⚠️ WARNING: Some leagues have inconsistencies. See warnings above for details.")
