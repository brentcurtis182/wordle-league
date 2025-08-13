#!/usr/bin/env python
# restore_website.py - Restore website while fixing Joanna's score only

import os
import sqlite3
import subprocess
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def remove_joanna_score():
    """Remove Joanna's incorrect score for Wordle #1500"""
    try:
        # Connect to database
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # First find Joanna's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.info("Joanna not found in players table")
            conn.close()
            return False
            
        joanna_id = result[0]
        logging.info(f"Found Joanna's player ID: {joanna_id}")
        
        # Delete Joanna's score for Wordle #1500
        cursor.execute(
            "DELETE FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (joanna_id,)
        )
        
        if cursor.rowcount > 0:
            logging.info(f"Removed {cursor.rowcount} score(s) for Joanna, Wordle #1500")
        else:
            logging.info("No scores found for Joanna, Wordle #1500")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error removing Joanna's score: {e}")
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
            logging.error(f"Output: {result.stdout}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Change to export directory
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        message = f"Fix Joanna's score: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", message], cwd=export_dir)
        
        # Push to GitHub
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_dir, check=True)
        
        logging.info("Successfully pushed to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    """Main function to restore the website"""
    logging.info("Starting website restoration...")
    
    # Step 1: Remove Joanna's score
    logging.info("\nStep 1: Removing Joanna's score")
    if remove_joanna_score():
        logging.info("Successfully removed Joanna's score")
    
    # Step 2: Run export_leaderboard.py
    logging.info("\nStep 2: Running export_leaderboard.py")
    if run_export_leaderboard():
        logging.info("Successfully exported website files")
    else:
        logging.error("Failed to export website files. Stopping restoration.")
        return
    
    # Step 3: Push to GitHub
    logging.info("\nStep 3: Pushing to GitHub")
    if push_to_github():
        logging.info("Successfully pushed to GitHub")
    
    logging.info("\nWebsite restoration complete!")
    logging.info("The website should be available at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("Note: GitHub Pages may take a few minutes to update. Try using a private/incognito window to check.")

if __name__ == "__main__":
    main()
