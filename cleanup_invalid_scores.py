#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cleanup script for removing invalid scores from the database.
Specifically targets:
1. Scores with "X" that don't have valid emoji patterns 
2. Players who have only invalid entries (like Pants in PAL league)

This helps ensure data integrity for leaderboard generation.
"""

import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup_scores.log'),
        logging.StreamHandler()
    ]
)

def connect_to_db():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row  # Return results as dictionary-like objects
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {e}")
        return None

def find_invalid_scores():
    """
    Identify scores that should be considered invalid:
    1. X scores without emoji patterns
    2. Scores with empty emoji patterns that should have them
    """
    conn = connect_to_db()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Query for potentially invalid scores
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, emoji_pattern, league_id
        FROM scores 
        WHERE score = '7' OR score = 'X' OR score = 7 OR emoji_pattern IS NULL OR emoji_pattern = ''
        ORDER BY league_id, player_name
        """)
        
        invalid_scores = []
        for row in cursor.fetchall():
            # Convert Row to dict
            score_data = dict(row)
            
            # Make sure score is an integer for comparison
            try:
                score_value = int(score_data['score'])
            except (ValueError, TypeError):
                score_value = 7  # Default to X for invalid values
                
            # X scores (7) without emoji patterns are suspicious
            if score_value == 7 and (not score_data['emoji_pattern'] or score_data['emoji_pattern'].strip() == ''):
                invalid_scores.append(score_data)
                logging.info(f"Found suspicious X score: {score_data['player_name']}, Wordle {score_data['wordle_num']}")
            
            # Valid scores (1-6) must have emoji patterns
            elif 1 <= score_value <= 6 and (not score_data['emoji_pattern'] or score_data['emoji_pattern'].strip() == ''):
                invalid_scores.append(score_data)
                logging.info(f"Found score without emoji pattern: {score_data['player_name']}, Wordle {score_data['wordle_num']}")
        
        return invalid_scores
        
    except Exception as e:
        logging.error(f"Error finding invalid scores: {e}")
        return []
    finally:
        conn.close()

def check_player_only_has_invalid_scores(player, league_id):
    """Check if a player has only invalid scores in a league."""
    conn = connect_to_db()
    if not conn:
        return True  # Assume the worst if we can't connect
    
    try:
        cursor = conn.cursor()
        
        # Count all scores for the player
        cursor.execute("""
        SELECT COUNT(*) FROM scores 
        WHERE player_name = ? AND league_id = ?
        """, (player, league_id))
        total_scores = cursor.fetchone()[0]
        
        # Count invalid scores (X or empty emoji patterns)
        cursor.execute("""
        SELECT COUNT(*) FROM scores 
        WHERE player_name = ? AND league_id = ?
        AND (score = '7' OR score = 'X' OR score = 7 OR emoji_pattern IS NULL OR emoji_pattern = '')
        """, (player, league_id))
        invalid_scores = cursor.fetchone()[0]
        
        # If all scores are invalid, this player should be cleaned up
        return total_scores > 0 and total_scores == invalid_scores
        
    except Exception as e:
        logging.error(f"Error checking player scores: {e}")
        return False
    finally:
        conn.close()

def delete_invalid_scores():
    """Delete scores that are identified as invalid."""
    invalid_scores = find_invalid_scores()
    if not invalid_scores:
        logging.info("No invalid scores found to delete")
        return
    
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Track players who need all their scores removed
        players_to_clean = {}
        
        # First, check which players only have invalid scores
        for score in invalid_scores:
            player = score['player_name']
            league_id = score['league_id']
            key = f"{player}_{league_id}"
            
            if key not in players_to_clean:
                players_to_clean[key] = check_player_only_has_invalid_scores(player, league_id)
        
        # Now process each invalid score
        deleted_count = 0
        for score in invalid_scores:
            player = score['player_name']
            league_id = score['league_id']
            key = f"{player}_{league_id}"
            
            # If player only has invalid scores or this is specifically a bad entry
            if players_to_clean.get(key, False) or score['score'] == 7:
                cursor.execute("""
                DELETE FROM scores 
                WHERE id = ?
                """, (score['id'],))
                
                deleted_count += 1
                logging.info(f"Deleted invalid score: {player}, Wordle {score['wordle_num']}, League {league_id}")
        
        conn.commit()
        logging.info(f"Deleted {deleted_count} invalid scores in total")
        
    except Exception as e:
        logging.error(f"Error deleting invalid scores: {e}")
        conn.rollback()
    finally:
        conn.close()

def verify_cleanup():
    """Verify that the cleanup was successful."""
    conn = connect_to_db()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Look for players we know should be clean
        cursor.execute("""
        SELECT player_name, league_id, COUNT(*) as count
        FROM scores 
        WHERE player_name = 'Pants' AND league_id = 3
        GROUP BY player_name, league_id
        """)
        
        pants_entries = cursor.fetchone()
        if pants_entries:
            logging.warning(f"Pants still has {pants_entries['count']} entries in PAL league after cleanup!")
        else:
            logging.info("Verification successful: Pants entries have been removed from PAL league")
        
    except Exception as e:
        logging.error(f"Error verifying cleanup: {e}")
    finally:
        conn.close()

def main():
    """Main function to run the cleanup script."""
    logging.info("Starting cleanup of invalid scores")
    delete_invalid_scores()
    verify_cleanup()
    logging.info("Cleanup completed")

if __name__ == "__main__":
    main()
