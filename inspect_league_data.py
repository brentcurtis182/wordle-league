#!/usr/bin/env python3
"""
Diagnostic script to inspect league data from the database
"""

import sqlite3
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# League definitions
LEAGUES = {
    "warriorz": {"id": 1, "name": "Wordle Warriorz"},
    "gang": {"id": 2, "name": "Wordle Gang"},
    "pal": {"id": 3, "name": "Wordle PAL"},
    "party": {"id": 4, "name": "Wordle Party"},
    "vball": {"id": 5, "name": "Wordle Vball"}
}

def inspect_league_data(league_id):
    """Get and inspect raw data from the database for a specific league"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        logging.info(f"Inspecting data for league ID {league_id}")
        
        # Get latest Wordle number and date
        cursor.execute("""
            SELECT wordle_number, date(date) as wordle_date 
            FROM scores 
            ORDER BY wordle_number DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        if not result:
            logging.error("No Wordle data found in database")
            return None
        
        latest_wordle = result[0]
        latest_date = result[1]
        
        logging.info(f"Latest Wordle: #{latest_wordle} ({latest_date})")
        
        # Check schema for players table
        cursor.execute("PRAGMA table_info(players)")
        columns = cursor.fetchall()
        logging.info("Players table schema:")
        for col in columns:
            logging.info(f"  {col}")
        
        # Check league_id values in players table
        cursor.execute("SELECT DISTINCT league_id FROM players")
        league_ids = cursor.fetchall()
        logging.info(f"Distinct league_id values in players table: {league_ids}")
        
        # Get all players for this league
        cursor.execute("""
            SELECT id, name, league_id
            FROM players
            WHERE league_id = ?
        """, (league_id,))
        players = cursor.fetchall()
        logging.info(f"Players for league {league_id}:")
        for player in players:
            logging.info(f"  {player}")
        
        # Get player scores for the latest Wordle for this league
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ? AND p.league_id = ?
        """, (latest_wordle, league_id))
        latest_scores = cursor.fetchall()
        logging.info(f"Latest scores for league {league_id} (Wordle #{latest_wordle}):")
        for score in latest_scores:
            logging.info(f"  {score}")
        
        # Get weekly stats directly without transformation
        cursor.execute("""
            SELECT p.name, 
                   SUM(CASE WHEN s.score BETWEEN '1' AND '6' THEN CAST(SUBSTRING(s.score, 1, 1) AS INTEGER) ELSE 0 END) AS weekly_score,
                   COUNT(CASE WHEN s.score BETWEEN '1' AND '6' THEN 1 END) AS used_scores,
                   COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id 
                AND s.wordle_number >= (? - 6) AND s.wordle_number <= ?
            WHERE p.league_id = ?
            GROUP BY p.name
        """, (latest_wordle, latest_wordle, league_id))
        weekly_stats_raw = cursor.fetchall()
        logging.info(f"Raw weekly stats for league {league_id}:")
        for i, stat in enumerate(weekly_stats_raw):
            logging.info(f"  Row {i}: {stat}")
            logging.info(f"    Type: {type(stat)}")
            for j, value in enumerate(stat):
                logging.info(f"      Item {j}: {value} (Type: {type(value)})")
        
        # Get all-time stats directly without transformation
        cursor.execute("""
            SELECT p.name, 
                   COUNT(CASE WHEN s.score BETWEEN '1' AND '6' THEN 1 END) AS games_played,
                   ROUND(AVG(CASE WHEN s.score BETWEEN '1' AND '6' THEN CAST(SUBSTRING(s.score, 1, 1) AS INTEGER) 
                           WHEN s.score = 'X/6' THEN 7
                           ELSE NULL END), 2) AS average,
                   COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id
            WHERE p.league_id = ?
            GROUP BY p.name
        """, (league_id,))
        alltime_stats_raw = cursor.fetchall()
        logging.info(f"Raw all-time stats for league {league_id}:")
        for i, stat in enumerate(alltime_stats_raw):
            logging.info(f"  Row {i}: {stat}")
            logging.info(f"    Type: {type(stat)}")
            for j, value in enumerate(stat):
                logging.info(f"      Item {j}: {value} (Type: {type(value)})")
        
        conn.close()
        return {
            'latest_wordle': latest_wordle,
            'latest_date': latest_date,
            'players': players,
            'latest_scores': latest_scores,
            'weekly_stats_raw': weekly_stats_raw,
            'alltime_stats_raw': alltime_stats_raw
        }
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return None

def main():
    for league_code, league_info in LEAGUES.items():
        league_id = league_info["id"]
        league_name = league_info["name"]
        
        print(f"\n{'='*80}\n{league_name} (ID: {league_id})\n{'='*80}")
        
        data = inspect_league_data(league_id)
        if not data:
            print(f"Failed to inspect data for {league_name}")

if __name__ == "__main__":
    main()
