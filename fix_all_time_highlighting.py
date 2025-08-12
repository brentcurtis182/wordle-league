#!/usr/bin/env python3
"""
Fix highlighting in the Season/All-Time Stats tab for all leagues
Ensures that highlighting applies to the entire row including the player name column
"""

import os
import re
import logging
import shutil
import sys
import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_highlighting.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Constants
WEBSITE_EXPORT_DIR = "website_export"
LEAGUE_DIRS = {
    "Wordle Warriorz": "",
    "Wordle Gang": "gang",
    "Wordle PAL": "pal",
    "Wordle Party": "party",
    "Wordle Vball": "vball"
}

def create_backup(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def fix_highlighting(file_path):
    """Fix highlighting in the Season/All-Time Stats tab"""
    try:
        # Create backup
        create_backup(file_path)
        
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # First attempt: Look for the Season/All-Time Stats tab content
        stats_tab = soup.find('div', {'id': 'stats'})
        if not stats_tab:
            logging.warning(f"Could not find stats tab in {file_path}")
            return False
        
        # Find all tables in the stats tab
        season_table = stats_tab.find('table', {'class': 'season-table'})
        all_time_container = stats_tab.find('div', {'class': 'all-time-container'})
        
        if all_time_container:
            all_time_table = all_time_container.find('table')
            
            if all_time_table:
                # Find all rows with highlighting
                highlighted_rows = all_time_table.find_all('tr', style=lambda s: s and "background-color" in s)
                
                # Fix highlighting for each row
                for row in highlighted_rows:
                    # Make sure all cells in the row have the highlighting class
                    for cell in row.find_all('td'):
                        if 'style' not in cell.attrs or "background-color" not in cell['style']:
                            # Only add specific CSS to player name cell (first td)
                            if cell == row.find('td'):
                                if 'style' in cell.attrs:
                                    cell['style'] = cell['style'] + "; background-color: rgba(106, 170, 100, 0.3);"
                                else:
                                    cell['style'] = "background-color: rgba(106, 170, 100, 0.3);"
                
                logging.info(f"Fixed highlighting for {len(highlighted_rows)} rows in all-time table")
            else:
                logging.warning(f"Could not find all-time table in {file_path}")
        
        # Save the modified HTML
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info(f"Successfully updated highlighting in {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error fixing highlighting in {file_path}: {e}")
        return False

def main():
    """Fix highlighting in all league HTML files"""
    logging.info("Starting highlighting fix for all leagues")
    
    success_count = 0
    error_count = 0
    
    for league_name, league_dir in LEAGUE_DIRS.items():
        # Construct the path to the league's index.html file
        if league_dir:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
        else:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, "index.html")
            
        if os.path.exists(index_path):
            logging.info(f"Fixing highlighting for {league_name} league")
            if fix_highlighting(index_path):
                success_count += 1
            else:
                error_count += 1
        else:
            logging.warning(f"Could not find index.html for {league_name} league at {index_path}")
            error_count += 1
    
    logging.info(f"Highlighting fix completed: {success_count} successful, {error_count} errors")
    print(f"Highlighting fix completed: {success_count} successful, {error_count} errors")

if __name__ == "__main__":
    main()
