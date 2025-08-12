#!/usr/bin/env python3
"""
Fix highlighting in the Season/All-Time Stats tab for all leagues
Ensures that highlighting is consistent across the entire row, including the player column
"""

import os
import logging
import shutil
import sys
import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_highlighting_v3.log"),
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

# The exact highlight style we want to use for consistency
HIGHLIGHT_STYLE = "background-color: rgba(106, 170, 100, 0.3);"

def create_backup(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def fix_highlighting(file_path):
    """Fix highlighting in the Season/All-Time Stats tab for consistent appearance"""
    try:
        # Create backup
        create_backup(file_path)
        
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for the Season/All-Time Stats tab content
        stats_tab = soup.find('div', {'id': 'stats'})
        if not stats_tab:
            logging.warning(f"Could not find stats tab in {file_path}")
            return False
        
        # Find the all-time table
        all_time_container = stats_tab.find('div', {'class': 'all-time-container'})
        if all_time_container:
            all_time_table = all_time_container.find('table')
            
            if all_time_table:
                # Find all rows that need highlighting (those with 5+ games)
                # First, find all rows in the table body
                all_rows = all_time_table.find('tbody').find_all('tr')
                
                fixed_rows = 0
                for row in all_rows:
                    # Check if the row should be highlighted (if it has any background-color style)
                    if 'style' in row.attrs and 'background-color' in row['style']:
                        # Apply consistent style to the row
                        row['style'] = HIGHLIGHT_STYLE
                        
                        # Apply the same background color to ALL cells in the row
                        for cell in row.find_all('td'):
                            if 'style' in cell.attrs:
                                # Keep existing styles and add our background color
                                if 'background-color' not in cell['style']:
                                    cell['style'] += " " + HIGHLIGHT_STYLE
                            else:
                                # Add background color to cells without any style
                                cell['style'] = HIGHLIGHT_STYLE
                        
                        fixed_rows += 1
                
                logging.info(f"Fixed highlighting for {fixed_rows} rows in all-time table")
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
