#!/usr/bin/env python3
import os
import sqlite3
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def extract_weekly_stats():
    """Extract weekly stats like the export script would do"""
    
    # Get all players in league 1
    cursor.execute("SELECT id, name FROM players WHERE league_id = 1")
    players = cursor.fetchall()
    
    # Get the Wordle range for this week (hardcoded for testing)
    start_wordle = 1500
    end_wordle = 1506
    
    for player in players:
        player_id, name = player
        
        # Check for valid scores (not failed attempts)
        cursor.execute("""
        SELECT score, date, wordle_number FROM scores
        WHERE player_id = ?
        AND wordle_number >= ? AND wordle_number <= ?
        AND score NOT IN (7, '7', 'X') 
        AND score IS NOT NULL
        AND score NOT IN ('-', 'None', '')
        """, (player_id, start_wordle, end_wordle))
        
        valid_scores = cursor.fetchall()
        
        # Check for failed attempts
        cursor.execute("""
        SELECT COUNT(*) FROM scores 
        WHERE player_id = ?
        AND wordle_number >= ? AND wordle_number <= ?
        AND (score = 7 OR score = '7' OR score = 'X')
        """, (player_id, start_wordle, end_wordle))
        
        failed_count = cursor.fetchone()[0]
        
        # Print the data as it would be processed by the export script
        logging.info(f"Player: {name}")
        logging.info(f"  Valid scores: {len(valid_scores)}")
        for s in valid_scores:
            logging.info(f"    Score: {s[0]}, Date: {s[1]}, Wordle: {s[2]}")
        logging.info(f"  Failed attempts: {failed_count}")
        
        # Calculate what would go into the weekly_stats object
        weekly_scores = []
        for score_row in valid_scores:
            score = score_row[0]
            try:
                weekly_scores.append(int(score))
            except (ValueError, TypeError):
                pass
        
        weekly_scores.sort()
        top_scores = weekly_scores[:5]
        total_weekly = sum(top_scores) if top_scores else None
        used_scores = len(top_scores)
        
        # Generate the stats object
        if failed_count > 0 and used_scores == 0:
            stats_obj = {
                'name': name,
                'weekly_score': '-',  # No valid scores for weekly total
                'used_scores': 0,     # No used scores
                'failed_attempts': failed_count,
                'failed': failed_count,
                'thrown_out': '-'
            }
        else:
            stats_obj = {
                'name': name,
                'weekly_score': total_weekly,
                'used_scores': used_scores if used_scores > 0 else 0,
                'failed_attempts': failed_count,
                'failed': failed_count,
                'thrown_out': '-'
            }
        
        logging.info(f"  Stats object: {stats_obj}")
        logging.info("  ---------------------------")

if __name__ == "__main__":
    extract_weekly_stats()
    conn.close()
