#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to check current Wordle #1500 scores in the database
"""

import sqlite3
import logging
import sys

# Configure logging to avoid Unicode errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("check_scores.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def check_scores():
    """Check current scores for Wordle #1500 in both tables"""
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== Scores for Wordle #1500 in 'scores' table ===\n")
        cursor.execute("""
            SELECT player_name, score, emoji_pattern 
            FROM scores 
            WHERE wordle_num = 1500
            ORDER BY player_name
        """)
        
        scores_results = cursor.fetchall()
        if scores_results:
            for row in scores_results:
                player = row['player_name']
                score = row['score']
                score_display = "X/6" if score == 7 else f"{score}/6"
                
                # Count rows in emoji pattern if it exists
                emoji_pattern = row['emoji_pattern']
                pattern_rows = 0
                if emoji_pattern:
                    pattern_rows = emoji_pattern.count('\n') + 1
                
                # Safe print to avoid Unicode errors
                try:
                    print(f"{player}: {score_display} - Pattern has {pattern_rows} rows")
                except UnicodeEncodeError:
                    print(f"{player}: {score_display} - Pattern has {pattern_rows} rows [Unicode error]")
        else:
            print("No scores found for Wordle #1500 in 'scores' table")
        
        # Check if 'score' table exists and check it too
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score'")
        if cursor.fetchone():
            print("\n=== Scores for Wordle #1500 in 'score' table ===\n")
            
            # Try different column combinations
            try:
                cursor.execute("""
                    SELECT player, score 
                    FROM score 
                    WHERE wordle_number = 1500
                    ORDER BY player
                """)
            except sqlite3.OperationalError:
                try:
                    cursor.execute("""
                        SELECT player_name as player, score 
                        FROM score 
                        WHERE wordle_num = 1500
                        ORDER BY player_name
                    """)
                except sqlite3.OperationalError:
                    print("Could not query 'score' table due to schema differences")
                    return
            
            score_results = cursor.fetchall()
            if score_results:
                for row in score_results:
                    player = row['player']
                    score = row['score']
                    score_display = "X/6" if score == 7 else f"{score}/6"
                    
                    # Safe print to avoid Unicode errors
                    try:
                        print(f"{player}: {score_display}")
                    except UnicodeEncodeError:
                        print(f"{player}: {score_display} [Unicode error]")
            else:
                print("No scores found for Wordle #1500 in 'score' table")
        
    except Exception as e:
        logging.error(f"Error checking scores: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("\n=== Checking Wordle #1500 Scores ===\n")
    check_scores()
