#!/usr/bin/env python3
"""
Repair the Wordle League directories and ensure each league has its proper index.html
"""

import os
import shutil
import logging
from datetime import datetime
import sqlite3
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("league_repair.log"),
        logging.StreamHandler()
    ]
)

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(BASE_DIR, 'website_export')

# League definitions
LEAGUES = {
    "Wordle Warriorz": {
        "dir_name": "",  # Main directory
        "has_days": True
    },
    "Wordle Gang": {
        "dir_name": "wordle-gang",
        "has_days": True
    },
    "Wordle PAL": {
        "dir_name": "wordle-pal",
        "has_days": True
    },
    "Wordle Party": {
        "dir_name": "wordle-party",
        "has_days": True
    },
    "Wordle Vball": {
        "dir_name": "wordle-vball",
        "has_days": True
    }
}

# Find most recent working backup
def find_working_backup():
    backup_dir = os.path.join(EXPORT_DIR, 'backups')
    candidates = []
    
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith('index_') and file.endswith('.html'):
                candidates.append(os.path.join(backup_dir, file))
    
    # Also check website_export_backup
    backup_dir = os.path.join(BASE_DIR, 'website_export_backup', 'backups')
    if os.path.exists(backup_dir):
        for file in os.listdir(backup_dir):
            if file.startswith('index_') and file.endswith('.html'):
                candidates.append(os.path.join(backup_dir, file))
    
    # Return the most recent backup based on modification time
    if candidates:
        return max(candidates, key=os.path.getmtime)
    
    return None

def update_wordle_info(soup):
    """Update the Wordle number and date from the database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT wordle_number, date(date) 
            FROM scores 
            ORDER BY wordle_number DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            wordle_number, wordle_date = result
            
            # Update the Wordle number in the heading
            h2_elements = soup.find_all('h2')
            for h2 in h2_elements:
                if 'Wordle #' in h2.text:
                    h2.string = f"Wordle #{wordle_number} - {wordle_date}"
                    logging.info(f"Updated Wordle number to {wordle_number}")
                    break
    except Exception as e:
        logging.error(f"Error updating Wordle info: {e}")

def ensure_directory_structure():
    """Ensure all league directories exist"""
    for league_name, info in LEAGUES.items():
        dir_path = os.path.join(EXPORT_DIR, info["dir_name"])
        
        # Skip the main directory which already exists
        if info["dir_name"] == "":
            continue
            
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            logging.info(f"Created directory for {league_name}: {dir_path}")

def repair_league_pages():
    """Repair the league pages by using a working template and updating for each league"""
    # Find a working backup template
    template_path = find_working_backup()
    
    if not template_path:
        logging.error("Could not find a working template backup")
        return False
        
    logging.info(f"Using template: {template_path}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Parse the template
        soup = BeautifulSoup(template_content, 'html.parser')
        
        # Update Wordle number and date
        update_wordle_info(soup)
        
        # Make sure tab buttons and content are properly linked
        tab_buttons = soup.select('.tab-button')
        tab_contents = soup.select('.tab-content')
        
        # Ensure the tab navigation works
        for button in tab_buttons:
            button['onclick'] = f"openTab(event, '{button['data-tab']}')"
        
        # Fix any script tags
        script_tag = soup.find('script')
        if not script_tag:
            # Add the tab script if it's missing
            script_tag = soup.new_tag('script')
            script_tag.string = """
            function openTab(evt, tabName) {
                var i, tabcontent, tabbuttons;
                
                tabcontent = document.getElementsByClassName("tab-content");
                for (i = 0; i < tabcontent.length; i++) {
                    tabcontent[i].style.display = "none";
                }
                
                tabbuttons = document.getElementsByClassName("tab-button");
                for (i = 0; i < tabbuttons.length; i++) {
                    tabbuttons[i].className = tabbuttons[i].className.replace(" active", "");
                }
                
                document.getElementById(tabName).style.display = "block";
                evt.currentTarget.className += " active";
            }
            
            // Set default tab to open
            document.addEventListener('DOMContentLoaded', function() {
                document.querySelector('.tab-button').click();
            });
            """
            soup.body.append(script_tag)
        
        # Fix league-specific pages
        for league_name, info in LEAGUES.items():
            league_dir = os.path.join(EXPORT_DIR, info["dir_name"])
            league_file = os.path.join(league_dir, "index.html" if info["dir_name"] else "index.html")
            
            # Create a copy of the soup for this league
            league_soup = BeautifulSoup(str(soup), 'html.parser')
            
            # Update the title
            if league_soup.title:
                league_soup.title.string = f"{league_name} - Wordle League"
            
            # Update any league-specific headings
            h1_tags = league_soup.find_all('h1')
            for h1 in h1_tags:
                if "Wordle League" in h1.text:
                    h1.string = f"{league_name}"
            
            # Save the updated HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create backup of existing file if it exists
            if os.path.exists(league_file):
                backup_path = f"{league_file}.backup_{timestamp}"
                shutil.copy2(league_file, backup_path)
                logging.info(f"Backed up {league_file} to {backup_path}")
            
            # Write the updated file
            with open(league_file, 'w', encoding='utf-8') as f:
                f.write(str(league_soup))
                
            logging.info(f"Updated {league_name} page at {league_file}")
    
        return True
        
    except Exception as e:
        logging.error(f"Error repairing league pages: {e}")
        return False

def main():
    logging.info("Starting league directory repair...")
    
    # Step 1: Ensure all directories exist
    ensure_directory_structure()
    
    # Step 2: Repair league pages
    if repair_league_pages():
        logging.info("Successfully repaired league pages")
        print("Successfully repaired league pages")
    else:
        logging.error("Failed to repair league pages")
        print("Failed to repair league pages")

if __name__ == "__main__":
    main()
