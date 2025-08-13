#!/usr/bin/env python3
"""
Make All-Time Stats highlighting match Weekly Totals highlighting exactly
Changes the opacity from 0.2 to 0.15 and adds font-weight: bold to match Weekly table
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
        logging.FileHandler("fix_highlighting_match_weekly.log"),
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

# The exact highlight style used in the Weekly Totals table
HIGHLIGHT_STYLE = "background-color: rgba(106, 170, 100, 0.15); font-weight: bold;"

def create_backup(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def match_highlighting(file_path):
    """Make All-Time Stats highlighting match Weekly Totals highlighting exactly"""
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
                # Find all rows that need highlighting
                # First, find all rows in the table body that already have some kind of background color
                all_rows = all_time_table.find('tbody').find_all('tr', style=lambda s: s and 'background-color' in s)
                
                fixed_rows = 0
                for row in all_rows:
                    # Apply the exact highlighting style from Weekly table
                    row['style'] = HIGHLIGHT_STYLE
                    
                    # Apply the same style to ALL cells in the row for consistency
                    for cell in row.find_all('td'):
                        if 'style' in cell.attrs:
                            # Remove any existing style from the cell
                            cell_style = cell['style']
                            if 'background-color' in cell_style:
                                # Replace with the exact Weekly table style
                                cell['style'] = HIGHLIGHT_STYLE
                        else:
                            # Add the Weekly table style
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
    """Match highlighting across all league HTML files"""
    logging.info("Starting to match highlighting styles across all leagues")
    
    success_count = 0
    error_count = 0
    
    for league_name, league_dir in LEAGUE_DIRS.items():
        # Construct the path to the league's index.html file
        if league_dir:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
        else:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, "index.html")
            
        if os.path.exists(index_path):
            logging.info(f"Matching highlighting for {league_name} league")
            if match_highlighting(index_path):
                success_count += 1
            else:
                error_count += 1
        else:
            logging.warning(f"Could not find index.html for {league_name} league at {index_path}")
            error_count += 1
    
    logging.info(f"Highlighting matching completed: {success_count} successful, {error_count} errors")
    print(f"Highlighting matching completed: {success_count} successful, {error_count} errors")

if __name__ == "__main__":
    main()
