import sqlite3
import logging
import os
from datetime import datetime
import subprocess
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def restore_current_wordle_dates():
    """Update the date for Wordle #1500 scores back to today's date"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime('%Y-%m-%d')
        today_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update the 'score' table
        cursor.execute(
            "UPDATE score SET date = ? WHERE wordle_number = 1500", 
            (today,)
        )
        score_count = cursor.rowcount
        logging.info(f"Updated {score_count} records in 'score' table to today's date")
        
        # Update the 'scores' table
        cursor.execute(
            "UPDATE scores SET timestamp = ? WHERE wordle_num = 1500", 
            (today_timestamp,)
        )
        scores_count = cursor.rowcount
        logging.info(f"Updated {scores_count} records in 'scores' table to today's timestamp")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        logging.error(f"Error restoring dates: {e}")
        return False

def update_website():
    """Update the website with the fixed data"""
    try:
        # Run the export script
        export_script = "export_leaderboard.py"
        if os.path.exists(export_script):
            subprocess.run([sys.executable, export_script], check=True)
            logging.info("Website exported successfully with weekly scores restored")
            
            # Try to push to GitHub
            try:
                from enhanced_functions import push_to_github
                push_to_github()
                logging.info("Changes pushed to GitHub")
            except ImportError:
                logging.warning("Could not import push_to_github function, website not pushed")
            
            return True
        else:
            logging.error(f"Export script {export_script} not found")
            return False
    except Exception as e:
        logging.error(f"Error updating website: {e}")
        return False

def main():
    logging.info("Starting restoration of weekly scores for Wordle League")
    
    # 1. Restore dates for current Wordle scores
    if restore_current_wordle_dates():
        logging.info("✓ Successfully restored dates for Wordle #1500 scores")
    else:
        logging.error("Failed to restore dates")
        return
    
    # 2. Update the website with the fixed data
    if update_website():
        logging.info("✓ Updated website with weekly scores restored")
    else:
        logging.error("Failed to update website")
    
    logging.info("Weekly scores should now be visible on the website")

if __name__ == "__main__":
    main()
