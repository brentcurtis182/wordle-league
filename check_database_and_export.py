#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to check both database tables and export files
"""

import sqlite3
import json
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_database_tables():
    """Check scores in both database tables for Wordle #1501"""
    conn = sqlite3.connect('wordle_league.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n=== Checking 'scores' table ===\n")
    cursor.execute("""
        SELECT player_name, wordle_num, score, emoji_pattern
        FROM scores
        WHERE wordle_num = 1501
    """)
    
    scores_results = cursor.fetchall()
    print(f"Found {len(scores_results)} scores for Wordle #1501 in 'scores' table:")
    for row in scores_results:
        print(f"- {row['player_name']}: {row['score']}/6")
    
    print("\n=== Checking 'score' table ===\n")
    cursor.execute("""
        SELECT p.name, s.wordle_number, s.score
        FROM score s
        JOIN player p ON s.player_id = p.id
        WHERE s.wordle_number = 1501
    """)
    
    score_results = cursor.fetchall()
    print(f"Found {len(score_results)} scores for Wordle #1501 in 'score' table:")
    for row in score_results:
        print(f"- {row['name']}: {row['score']}/6")
    
    print("\n=== Checking website export files ===\n")
    try:
        with open('website_export/api/latest.json', 'r') as f:
            data = json.load(f)
            print(f"latest.json wordle number: {data['wordle_number']}")
            print("Scores in latest.json:")
            for score in data['scores']:
                status = f"{score['score']}/6" if score['has_score'] else "No Score"
                print(f"- {score['name']}: {status}")
    except Exception as e:
        print(f"Error reading export file: {e}")
    
    print("\n=== Checking Git Status in Website Export ===\n")
    os.chdir('website_export')
    os.system('git branch')
    os.chdir('..')
    
    conn.close()

if __name__ == "__main__":
    check_database_tables()
