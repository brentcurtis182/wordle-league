import sqlite3
import subprocess
import os
import sys
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def run_command(command, description):
    """Run a command and log the result"""
    logging.info(f"Running {description}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logging.info(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"✗ {description} failed: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return False

def force_reset():
    """Force both daily and weekly resets"""
    logging.info("Forcing daily and weekly resets")
    
    # Connect to the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    try:
        # Force daily reset by setting last_reset_date to yesterday
        yesterday = (datetime.now().date().replace(day=datetime.now().date().day - 1)).isoformat()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_reset_date', ?)", (yesterday,))
        conn.commit()
        logging.info("✓ Set last_reset_date to yesterday to force daily reset")
        
        # Force weekly reset by setting last_weekly_reset to a month ago
        old_date = "Jul 01"
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_weekly_reset', ?)", (old_date,))
        conn.commit()
        logging.info("✓ Set last_weekly_reset to a month ago to force weekly reset")
        
        return True
    except Exception as e:
        logging.error(f"✗ Error forcing reset: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main function to run the full Monday update process"""
    logging.info("Starting force Monday update process")
    
    # Step 1: Force reset flags in database
    if not force_reset():
        logging.error("Failed to set reset flags in database")
        return False
    
    # Step 2: Run the main update script to execute resets and extract scores
    if not run_command(["python", "integrated_auto_update_multi_league.py"], "integrated auto update with resets"):
        logging.error("Failed to run integrated auto update")
        return False
        
    # Step 3: Update HTML with the reset data
    if not run_command(["python", "export_leaderboard_multi_league.py"], "export leaderboard HTML"):
        logging.error("Failed to export leaderboard")
        return False
        
    # Step 4: Fix tabs for all leagues
    if not run_command(["python", "fix_all_tabs.py"], "fix tabs"):
        logging.warning("Warning: Failed to fix tabs (non-critical)")
        
    # Step 5: Run only the publish step to avoid duplicate extraction
    # Check if server_publish_to_github.py exists
    if os.path.exists('server_publish_to_github.py'):
        if not run_command(["python", "server_publish_to_github.py"], "publish to GitHub"):
            logging.error("Failed to publish to GitHub")
            return False
    else:
        logging.warning("server_publish_to_github.py not found, trying server_auto_update with --skip-extraction")
        # Try to use command-line argument if it exists
        if not run_command(["python", "server_auto_update_multi_league.py", "--skip-extraction"], "server auto update with skip extraction"):
            logging.warning("Failed with --skip-extraction, trying without extraction manually")
            # If that fails, we still need to publish
            if not run_command(["python", "server_auto_update_multi_league.py", "--skip-all-but-publish"], "server publish only"):
                logging.error("Failed to run server publish")
                return False
        
    logging.info("✓ Force Monday update process completed successfully!")
    return True

if __name__ == "__main__":
    main()
