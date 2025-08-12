#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to force update the website with today's scores by ensuring database consistency
"""

import sqlite3
import logging
import os
import subprocess
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_dates_and_update_website():
    """
    1. Update the date field in the score table to today's date for all Wordle #1501 entries
    2. Force update the website files
    3. Commit and push changes to GitHub
    """
    conn = sqlite3.connect('wordle_league.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get today's date in YYYY-MM-DD format
    today_date = datetime.now().strftime("%Y-%m-%d")
    wordle_number = 1501  # Current Wordle number
    
    print(f"\n=== Fixing Dates for Wordle #{wordle_number} ===\n")
    
    # 1. Update date field for all Wordle #1501 entries in score table
    cursor.execute("UPDATE score SET date = ? WHERE wordle_number = ?", (today_date, wordle_number))
    conn.commit()
    
    # Verify the update worked
    cursor.execute("""
        SELECT p.name, s.wordle_number, s.score, s.date
        FROM score s
        JOIN player p ON s.player_id = p.id
        WHERE s.wordle_number = ?
    """, (wordle_number,))
    
    rows = cursor.fetchall()
    print(f"Found {len(rows)} scores for Wordle #{wordle_number}:")
    for row in rows:
        print(f"- {row['name']}: {row['score']}/6 (Date: {row['date']})")
    
    conn.close()
    
    print("\n=== Running Website Update ===\n")
    
    # 2. Run the export_leaderboard.py script to generate website files
    try:
        subprocess.run(["python", "export_leaderboard.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running export_leaderboard.py: {e}")
        return False
    
    print("\n=== Committing and Pushing Changes ===\n")
    
    # 3. Commit and push changes to GitHub with cache-busting commit message
    os.chdir('website_export')
    
    try:
        # Add all files
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit with timestamp for cache busting
        commit_message = f"Update with latest scores for Wordle #{wordle_number} (timestamp: {datetime.now().timestamp()})"
        subprocess.run(["git", "commit", "-m", commit_message], check=False)
        
        # Force push to override any conflicts
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], check=True)
        
        print("\nWebsite updated and pushed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error committing/pushing changes: {e}")
        return False

if __name__ == "__main__":
    fix_dates_and_update_website()
