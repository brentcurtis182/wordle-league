#!/usr/bin/env python3
"""
Adjust the brightness of highlighting in the Season/All-Time Stats tab
Reduces the opacity of the background color to make it less intense
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
        logging.FileHandler("fix_highlighting_brightness.log"),
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

# The exact highlight style we want to use with reduced opacity (0.2 instead of 0.3)
HIGHLIGHT_STYLE = "background-color: rgba(106, 170, 100, 0.2);"

def create_backup(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def adjust_highlighting_brightness(file_path):
    """Adjust the brightness/intensity of highlighting in the All-Time Stats tab"""
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
                # Find all elements with the background-color style
                highlighted_elements = all_time_table.find_all(lambda tag: tag.get('style') and 'background-color: rgba(106, 170, 100,' in tag['style'])
                
                # Adjust the opacity for each element
                for element in highlighted_elements:
                    element['style'] = element['style'].replace(
                        'background-color: rgba(106, 170, 100, 0.3)',
                        'background-color: rgba(106, 170, 100, 0.2)'
                    )
                
                logging.info(f"Adjusted highlighting brightness for {len(highlighted_elements)} elements")
            else:
                logging.warning(f"Could not find all-time table in {file_path}")
        
        # Save the modified HTML
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info(f"Successfully updated highlighting brightness in {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error adjusting highlighting brightness in {file_path}: {e}")
        return False

def main():
    """Adjust highlighting brightness in all league HTML files"""
    logging.info("Starting highlighting brightness adjustment for all leagues")
    
    success_count = 0
    error_count = 0
    
    for league_name, league_dir in LEAGUE_DIRS.items():
        # Construct the path to the league's index.html file
        if league_dir:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
        else:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, "index.html")
            
        if os.path.exists(index_path):
            logging.info(f"Adjusting highlighting brightness for {league_name} league")
            if adjust_highlighting_brightness(index_path):
                success_count += 1
            else:
                error_count += 1
        else:
            logging.warning(f"Could not find index.html for {league_name} league at {index_path}")
            error_count += 1
    
    logging.info(f"Highlighting brightness adjustment completed: {success_count} successful, {error_count} errors")
    print(f"Highlighting brightness adjustment completed: {success_count} successful, {error_count} errors")

if __name__ == "__main__":
    main()
