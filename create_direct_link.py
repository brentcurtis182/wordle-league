#!/usr/bin/env python
# Create a direct link with unique timestamp query parameter to bypass all caches

import os
import sqlite3
import logging
import webbrowser
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def verify_joanna_pattern():
    """Verify Joanna's pattern in the database"""
    conn = sqlite3.connect("wordle_league.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get Joanna's player ID
    cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
    joanna_id = cursor.fetchone()["id"]
    logging.info(f"Joanna's player ID: {joanna_id}")
    
    # Get her current score for Wordle 1500
    cursor.execute("""
        SELECT id, score, emoji_pattern 
        FROM score 
        WHERE player_id = ? AND wordle_number = 1500
    """, (joanna_id,))
    
    score_record = cursor.fetchone()
    if score_record:
        score_id = score_record["id"]
        score = score_record["score"]
        pattern = score_record["emoji_pattern"]
        
        logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}")
        
        # Count rows in pattern
        rows = 0
        if pattern:
            rows = pattern.count('\n') + 1
            logging.info(f"Pattern has {rows} rows")
            logging.info(f"Pattern: {pattern}")
            
            return rows
    
    conn.close()
    return 0

def main():
    # Verify the database has the correct pattern
    rows = verify_joanna_pattern()
    if rows == 5:
        logging.info("Joanna's pattern is correctly showing 5 rows in the database")
    else:
        logging.error(f"Joanna's pattern is showing {rows} rows in the database - expected 5 rows")
    
    # Create a unique timestamped URL
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    direct_url = f"https://brentcurtis182.github.io/wordle-league/daily/wordle-1500.html?nocache={timestamp}"
    index_url = f"https://brentcurtis182.github.io/wordle-league/index.html?nocache={timestamp}"
    
    print("\n====== CACHE-BUSTING DIRECT LINKS =======")
    print(f"Main page with no cache: {index_url}")
    print(f"Wordle 1500 page with no cache: {direct_url}")
    print("==========================================")
    print("\nTry opening these links in an incognito/private window")
    print("If you still don't see the updated pattern, GitHub Pages might be experiencing delays")

if __name__ == "__main__":
    main()
