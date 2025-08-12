import os
import sys
import time
import sqlite3
import logging
from datetime import datetime
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("force_extraction.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Force a new extraction run"""
    logging.info("Starting forced extraction for Wordle #1501")
    
    # Check the database first
    conn = sqlite3.connect('wordle_league.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Check if we have any Wordle #1501 scores
    cursor.execute("SELECT * FROM scores WHERE wordle_num = 1501")
    existing_scores = cursor.fetchall()
    print(f"Found {len(existing_scores)} existing Wordle #1501 scores before extraction")
    
    # Run the integrated auto update script
    try:
        print("Running integrated_auto_update.py with debug output...")
        result = subprocess.run(
            ["python", "integrated_auto_update.py"], 
            check=True,
            capture_output=True,
            text=True
        )
        print("\nOutput from extraction:")
        print(result.stdout)
        
        if result.stderr:
            print("\nErrors from extraction:")
            print(result.stderr)
    except Exception as e:
        print(f"Error running extraction: {e}")
    
    # Check the database again
    cursor.execute("SELECT * FROM scores WHERE wordle_num = 1501")
    new_scores = cursor.fetchall()
    print(f"\nFound {len(new_scores)} Wordle #1501 scores after extraction")
    
    if len(new_scores) > 0:
        print("\nWordle #1501 scores found:")
        for score in new_scores:
            print(f"Player: {score['player_name']}, Score: {score['score']}/6, Date: {score['timestamp']}")
    
    conn.close()
    
    # Force a website update
    try:
        print("\nForcing website update...")
        update_result = subprocess.run(
            ["python", "update_website_now.py"],
            check=True,
            capture_output=True,
            text=True
        )
        print("Website update complete")
    except Exception as e:
        print(f"Error updating website: {e}")

if __name__ == "__main__":
    main()
