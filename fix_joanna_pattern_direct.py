#!/usr/bin/env python
# Direct fix for Joanna's emoji pattern

import os
import sqlite3
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_and_fix_joanna_pattern():
    """Check and fix Joanna's emoji pattern directly in the database"""
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
            return False
            
        score_id = score_record["id"]
        score = score_record["score"]
        pattern = score_record["emoji_pattern"]
        
        logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}, Pattern={repr(pattern)}")
        
        # Count rows in pattern
        rows = 0
        if pattern:
            rows = pattern.count('\n') + 1
            logging.info(f"Pattern has {rows} rows but score is {score}")
        
        # Fix if there's a mismatch
        if score == 5 and (rows != 5 or not pattern):
            logging.info("Fixing Joanna's pattern to match her 5/6 score")
            
            # Create a proper 5-row pattern
            new_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
            
            # Update in database
            cursor.execute("""
                UPDATE score 
                SET emoji_pattern = ? 
                WHERE id = ?
            """, (new_pattern, score_id))
            
            conn.commit()
            logging.info("Updated Joanna's pattern in the database")
            
            # Verify the update
            cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
            updated_pattern = cursor.fetchone()["emoji_pattern"]
            updated_rows = updated_pattern.count('\n') + 1
            logging.info(f"Verified pattern now has {updated_rows} rows")
            
            conn.close()
            return True
        else:
            logging.info("No fix needed or pattern already correct")
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Error fixing Joanna's pattern: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add timestamp file for cache busting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        timestamp_file = os.path.join(export_dir, f"timestamp_{timestamp}.txt")
        with open(timestamp_file, 'w') as f:
            f.write(f"Pattern fix at {timestamp}")
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        commit_msg = f"Fix Joanna's pattern display: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir)
        
        # Force push to gh-pages
        logging.info("Force pushing to GitHub...")
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"], 
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if "error" in push_result.stderr.lower():
            logging.error(f"Push error: {push_result.stderr}")
            return False
        else:
            logging.info("Successfully pushed to GitHub Pages")
            return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting direct fix for Joanna's emoji pattern...")
    
    # Step 1: Check and fix Joanna's pattern
    fixed = check_and_fix_joanna_pattern()
    
    if not fixed:
        logging.info("No changes were made to Joanna's pattern")
    
    # Step 2: Run export_leaderboard.py
    logging.info("\nRunning export_leaderboard.py...")
    run_export_leaderboard()
    
    # Step 3: Push to GitHub
    logging.info("\nPushing to GitHub...")
    push_to_github()
    
    logging.info("\nEmoji pattern fix process complete!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("If you still see incorrect patterns, please use Ctrl+F5 or open in incognito mode.")

if __name__ == "__main__":
    main()
