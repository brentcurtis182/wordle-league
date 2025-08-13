#!/usr/bin/env python3
"""
Simplified script to fix league pages structure while preserving content
"""

import os
import sqlite3
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_leagues.log"),
        logging.StreamHandler()
    ]
)

def update_league_page(league_path, league_name):
    """Update a league's HTML with correct structure and current data"""
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{league_path}.backup_{timestamp}"
        shutil.copy2(league_path, backup_file)
        logging.info(f"Backed up {league_path} to {backup_file}")
        
        # Get latest Wordle info from database
        try:
            conn = sqlite3.connect('wordle_league.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wordle_number, date(date) as wordle_date 
                FROM scores 
                ORDER BY wordle_number DESC
                LIMIT 1
            """)
            result = cursor.fetchone()
            conn.close()
            
            if result:
                latest_wordle = result[0]
                latest_date = result[1]
            else:
                latest_wordle = 1513  # Fallback
                latest_date = "August 10, 2025"  # Fallback
        except Exception as e:
            logging.error(f"Database error: {e}")
            latest_wordle = 1513  # Fallback
            latest_date = "August 10, 2025"  # Fallback
        
        # Read the current index.html
        with open(league_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Update Wordle number and date
        wordle_heading = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if wordle_heading:
            wordle_heading.string = f"Wordle #{latest_wordle} - {latest_date}"
            logging.info(f"Updated Wordle number to #{latest_wordle} - {latest_date}")
        
        # Set the page title
        if soup.title:
            soup.title.string = f"{league_name} - Wordle League"
        
        # Write updated content back to file
        with open(league_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Successfully updated {league_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating {league_path}: {e}")
        return False

def main():
    logging.info("Starting league page fixes...")
    
    # Define leagues and their paths
    leagues = {
        "website_export/index.html": "Wordle Warriorz",
        "website_export/wordle-gang/index.html": "Wordle Gang",
        "website_export/wordle-pal/index.html": "Wordle PAL",
        "website_export/wordle-party/index.html": "Wordle Party",
        "website_export/wordle-vball/index.html": "Wordle Vball"
    }
    
    success_count = 0
    
    for league_path, league_name in leagues.items():
        if not os.path.exists(league_path):
            logging.warning(f"League file not found: {league_path}, skipping")
            continue
            
        logging.info(f"Processing {league_name}...")
        
        # Update the league's HTML
        if update_league_page(league_path, league_name):
            logging.info(f"Successfully fixed {league_name}")
            success_count += 1
        else:
            logging.error(f"Failed to fix {league_name}")
    
    logging.info(f"Update complete. Successfully fixed {success_count} of {len(leagues)} leagues.")
    print(f"Successfully fixed {success_count} of {len(leagues)} league pages.")
    return success_count == len(leagues)

if __name__ == "__main__":
    main()
