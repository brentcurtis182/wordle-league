#!/usr/bin/env python
# Final fix for Joanna's pattern, with database verification and website update

import os
import sqlite3
import logging
import subprocess
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def fix_joanna_pattern():
    """Fix Joanna's emoji pattern in the database with verification"""
    try:
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
        if not score_record:
            logging.error("No score found for Joanna for Wordle 1500")
            conn.close()
            return False
            
        score_id = score_record["id"]
        score = score_record["score"]
        pattern = score_record["emoji_pattern"]
        
        logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}")
        
        # Count rows in pattern
        rows = 0
        if pattern:
            rows = pattern.count('\n') + 1
            logging.info(f"Pattern has {rows} rows but score is {score}")
            logging.info(f"Current pattern: {pattern}")
        
        # Fix if there's a mismatch
        if score == 5 and rows != 5:
            logging.info("Fixing Joanna's pattern to match her 5/6 score")
            
            # Create a proper 5-row pattern
            new_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
            
            # Update in database with IMMEDIATE transaction for durability
            conn.execute("BEGIN IMMEDIATE")
            cursor.execute("""
                UPDATE score 
                SET emoji_pattern = ? 
                WHERE id = ?
            """, (new_pattern, score_id))
            
            conn.commit()
            logging.info("Updated Joanna's pattern in the database")
            
            # Double verify the update with a new connection
            verify_conn = sqlite3.connect("wordle_league.db")
            verify_conn.row_factory = sqlite3.Row
            verify_cursor = verify_conn.cursor()
            verify_cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
            updated_pattern = verify_cursor.fetchone()["emoji_pattern"]
            updated_rows = updated_pattern.count('\n') + 1
            logging.info(f"Verified pattern now has {updated_rows} rows")
            logging.info(f"New pattern: {updated_pattern}")
            verify_conn.close()
            
            conn.close()
            return updated_rows == 5
        else:
            if rows == 5:
                logging.info("Pattern already has 5 rows, no fix needed")
            else:
                logging.warning(f"Unexpected pattern rows: {rows} for score: {score}")
            conn.close()
            return rows == 5
    except Exception as e:
        logging.error(f"Error fixing Joanna's pattern: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def push_website_changes():
    """Push website changes using repair_git_and_push.py"""
    try:
        logging.info("Running repair_git_and_push.py...")
        result = subprocess.run(["python", "repair_git_and_push.py"], 
                              capture_output=True, text=True, check=False)
        
        if result.returncode == 0:
            logging.info("GitHub push successful")
            return True
        else:
            logging.error(f"GitHub push failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running repair_git_and_push.py: {e}")
        return False

def main():
    logging.info("Starting final pattern fix and website update...")
    
    # Step 1: Fix Joanna's pattern in the database
    logging.info("\nStep 1: Fixing Joanna's pattern in database...")
    if not fix_joanna_pattern():
        logging.error("Failed to fix Joanna's pattern in database")
        return
    
    # Step 2: Generate website files
    logging.info("\nStep 2: Generating website files...")
    if not run_export_leaderboard():
        logging.error("Failed to generate website files")
        return
    
    # Step 3: Push changes to GitHub
    logging.info("\nStep 3: Pushing changes to GitHub...")
    if not push_website_changes():
        logging.error("Failed to push changes to GitHub")
        return
    
    # Generate cache-busting URLs
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    direct_url = f"https://brentcurtis182.github.io/wordle-league/daily/wordle-1500.html?nocache={timestamp}"
    index_url = f"https://brentcurtis182.github.io/wordle-league/index.html?nocache={timestamp}"
    
    logging.info("\nProcess completed!")
    logging.info("Please wait 1-2 minutes for GitHub Pages to update")
    print("\n====== CACHE-BUSTING DIRECT LINKS =======")
    print(f"Main page with no cache: {index_url}")
    print(f"Wordle 1500 page with no cache: {direct_url}")
    print("==========================================")
    print("\nTry opening these links in an incognito/private window in 1-2 minutes")

if __name__ == "__main__":
    main()
