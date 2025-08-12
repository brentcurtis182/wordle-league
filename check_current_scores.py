#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to check current Wordle scores in both database tables
"""

import sqlite3

def check_scores():
    """Check current scores in both database tables"""
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print("\n=== Scores in 'scores' table ===\n")
        cursor.execute("""
            SELECT player_name, wordle_num, score, emoji_pattern 
            FROM scores 
            ORDER BY wordle_num DESC, player_name
        """)
        
        scores_results = cursor.fetchall()
        if scores_results:
            for row in scores_results:
                player = row['player_name']
                wordle_num = row['wordle_num']
                score = row['score']
                score_display = "X/6" if score == 7 else f"{score}/6"
                
                # Count rows in emoji pattern if it exists
                emoji_pattern = row['emoji_pattern']
                pattern_rows = 0
                if emoji_pattern:
                    pattern_rows = emoji_pattern.count('\n') + 1
                
                # Safe print to avoid Unicode errors
                try:
                    print(f"{player}: Wordle {wordle_num} - {score_display} - Pattern has {pattern_rows} rows")
                except UnicodeEncodeError:
                    print(f"{player}: Wordle {wordle_num} - {score_display} - Pattern has {pattern_rows} rows [Unicode error]")
        else:
            print("No scores found in 'scores' table")
        
        # Check 'score' table too
        print("\n=== Scores in 'score' table ===\n")
        cursor.execute("""
            SELECT p.name as player_name, s.wordle_number, s.score 
            FROM score s
            JOIN player p ON s.player_id = p.id
            ORDER BY s.wordle_number DESC, p.name
        """)
        
        score_results = cursor.fetchall()
        if score_results:
            for row in score_results:
                player = row['player_name']
                wordle_num = row['wordle_number']
                score = row['score']
                score_display = "X/6" if score == 7 else f"{score}/6"
                
                # Safe print to avoid Unicode errors
                try:
                    print(f"{player}: Wordle {wordle_num} - {score_display}")
                except UnicodeEncodeError:
                    print(f"{player}: Wordle {wordle_num} - {score_display} [Unicode error]")
        else:
            print("No scores found in 'score' table")
        
    except Exception as e:
        print(f"Error checking scores: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("\n=== Checking Current Wordle Scores ===\n")
    check_scores()
