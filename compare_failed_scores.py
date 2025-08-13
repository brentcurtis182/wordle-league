#!/usr/bin/env python
# Compare failed scores (X/6) processing for different players

import sqlite3
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def check_player_scores(player_names):
    """Check scores for the given players"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        for player_name in player_names:
            # Get player ID
            cursor.execute("SELECT id FROM player WHERE name = ?", (player_name,))
            result = cursor.fetchone()
            
            if not result:
                logging.warning(f"{player_name} not found in player table")
                continue
                
            player_id = result[0]
            
            # Get all scores for this player
            cursor.execute(
                "SELECT wordle_number, score, emoji_pattern FROM score WHERE player_id = ? ORDER BY wordle_number DESC", 
                (player_id,)
            )
            scores = cursor.fetchall()
            
            logging.info(f"\n{player_name} has {len(scores)} scores:")
            for score_row in scores:
                wordle_num, score_val, emoji_pattern = score_row
                score_display = "X/6" if score_val == 7 else f"{score_val}/6"
                has_pattern = "with emoji pattern" if emoji_pattern else "no pattern"
                logging.info(f"  Wordle #{wordle_num}: {score_display} ({has_pattern})")
                
                # If this is an X/6 score or Wordle #1500, show the emoji pattern
                if score_val == 7 or wordle_num == 1500:
                    if emoji_pattern:
                        logging.info(f"  Pattern: {emoji_pattern}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error checking scores: {e}")

def analyze_message_formats():
    """Check recent logs for message formats that might be causing issues"""
    try:
        with open("integrated_auto_update.log", "r", encoding="utf-8", errors="ignore") as f:
            log_lines = f.readlines()
        
        # Look for failed attempt pattern matches
        failed_pattern_lines = [line for line in log_lines if "Found failed matches" in line]
        logging.info(f"\nFound {len(failed_pattern_lines)} log lines with failed match patterns:")
        for line in failed_pattern_lines[:10]:  # Show up to 10 examples
            logging.info(f"  {line.strip()}")
            
        # Look for successful score extractions
        score_lines = [line for line in log_lines if "Found score: Wordle" in line or "Found failed attempt: Wordle" in line]
        logging.info(f"\nFound {len(score_lines)} log lines with score extractions:")
        for line in score_lines[:10]:  # Show up to 10 examples
            logging.info(f"  {line.strip()}")
    except Exception as e:
        logging.error(f"Error analyzing log files: {e}")

if __name__ == "__main__":
    logging.info("Comparing failed scores (X/6) for different players")
    check_player_scores(['Evan', 'Malia', 'Joanna'])
    
    logging.info("\nAnalyzing message format patterns")
    analyze_message_formats()
