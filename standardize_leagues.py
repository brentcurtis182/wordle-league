#!/usr/bin/env python3
"""
Standardize Wordle League Pages
--------------------------------
This script ensures consistency across all league pages by:
1. Standardizing tab functionality
2. Fixing CSS references
3. Ensuring Wordle Warriorz is at the main URL

Run this script after any website update to ensure all leagues
have consistent structure and functionality.
"""

import os
import sys
import logging
import shutil
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("standardize_leagues.log"),
        logging.StreamHandler()
    ]
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(SCRIPT_DIR, "website_export")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "website_export_backup", "backups")

# League paths (relative to EXPORT_DIR)
LEAGUES = {
    "warriorz": "index.html",  # Main league at root
    "gang": "gang/index.html",
    "pal": "pal/index.html",
    "party": "party/index.html",
    "vball": "vball/index.html"
}

# League display names
LEAGUE_NAMES = {
    "warriorz": "Wordle Warriorz",
    "gang": "Wordle Gang",
    "pal": "Wordle Pal",
    "party": "Wordle Party",
    "vball": "Wordle Vball"
}

def create_tabs_js():
    """Create tab functionality JavaScript file if it doesn't exist"""
    tabs_js_path = os.path.join(EXPORT_DIR, "tabs.js")
    
    if not os.path.exists(tabs_js_path):
        logging.info("Creating tabs.js file...")
        tabs_js_content = """// Tab functionality for Wordle League pages
document.addEventListener('DOMContentLoaded', function() {
    // Get all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    
    // Add click event listener to each button
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Get the data-tab attribute value (tab id to show)
            const tabToShow = this.getAttribute('data-tab');
            
            // Remove active class from all tab buttons and content
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Add active class to clicked button and corresponding content
            this.classList.add('active');
            document.getElementById(tabToShow).classList.add('active');
        });
    });
});"""

        with open(tabs_js_path, 'w', encoding='utf-8') as f:
            f.write(tabs_js_content)
        logging.info(f"Created {tabs_js_path}")
    else:
        logging.info("tabs.js already exists")

def backup_file(file_path):
    """Create backup of file with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"{os.path.basename(file_path)}.backup_{timestamp}"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # Create backup directory if it doesn't exist
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    
    # Create backup
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backed up {file_path} to {backup_path}")
    
    return backup_path

def restore_main_league():
    """Restore Wordle Warriorz to main index.html if needed"""
    main_index = os.path.join(EXPORT_DIR, "index.html")
    
    # Read current index.html
    with open(main_index, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if it's the Wordle Warriorz league page (look for specific indicators)
    soup = BeautifulSoup(content, 'html.parser')
    title = soup.title.string if soup.title else ""
    
    if "Welcome" in title:
        logging.info("Main index.html is currently the landing page, restoring Wordle Warriorz...")
        
        # Look for the most recent backup of index.html
        backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith("index_")]
        if backups:
            # Sort by timestamp (newest first)
            backups.sort(reverse=True)
            newest_backup = os.path.join(BACKUP_DIR, backups[0])
            
            # Backup current index.html
            backup_file(main_index)
            
            # Restore from backup
            shutil.copy2(newest_backup, main_index)
            logging.info(f"Restored Wordle Warriorz from {newest_backup}")
            return True
        else:
            logging.error("No backup found for Wordle Warriorz league")
            return False
    else:
        logging.info("Main index.html is already the Wordle Warriorz league page")
        return True

def standardize_league(league_name, file_path):
    """Standardize a league HTML file"""
    full_path = os.path.join(EXPORT_DIR, file_path)
    if not os.path.exists(full_path):
        logging.error(f"League file not found: {full_path}")
        return False
    
    # Backup current file
    backup_path = backup_file(full_path)
    
    # Read HTML
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Set the league name in the title and heading
    if league_name in LEAGUE_NAMES:
        display_name = LEAGUE_NAMES[league_name]
        
        # Update page title
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = f"{display_name} - Wordle League"
            logging.info(f"Updated title for {league_name} to '{title_tag.string}'")
        
        # Update main heading (h1)
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_tag.string = display_name
            logging.info(f"Updated heading for {league_name} to '{display_name}'")
        else:
            logging.warning(f"No h1 tag found in {league_name} league")
    else:
        logging.warning(f"No display name defined for {league_name}")
    
    
    # 1. Fix CSS reference
    css_link = soup.find('link', rel='stylesheet')
    if css_link:
        if league_name == "warriorz":
            # Main league should reference styles.css directly
            if css_link.get('href') != 'styles.css':
                css_link['href'] = 'styles.css'
                logging.info(f"Fixed CSS path for {league_name} to styles.css")
        else:
            # Subdirectory leagues should reference ../styles.css
            if css_link.get('href') != '../styles.css':
                css_link['href'] = '../styles.css'
                logging.info(f"Fixed CSS path for {league_name} to ../styles.css")
    
    # 2. Add tab script reference if missing
    tab_script_exists = False
    for script in soup.find_all('script'):
        src = script.get('src', '')
        if 'tabs.js' in src:
            tab_script_exists = True
            break
    
    if not tab_script_exists:
        # Create new script tag
        script = soup.new_tag('script')
        if league_name == "warriorz":
            script['src'] = 'tabs.js'
        else:
            script['src'] = '../tabs.js'
        
        # Find body tag and append script
        body = soup.find('body')
        if body:
            body.append(script)
            logging.info(f"Added tabs.js script to {league_name}")
        else:
            logging.error(f"No body tag found in {league_name}")
    
    # Write updated HTML
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    logging.info(f"Standardized {league_name} league")
    return True

def main():
    """Main function to standardize all leagues"""
    logging.info("Starting league standardization process...")
    
    # 1. Create tabs.js if needed
    create_tabs_js()
    
    # 2. Ensure Wordle Warriorz is at main URL
    if not restore_main_league():
        logging.error("Failed to restore Wordle Warriorz to main URL")
    
    # 3. Standardize all leagues
    success_count = 0
    for league_name, file_path in LEAGUES.items():
        logging.info(f"Standardizing {league_name} league...")
        if standardize_league(league_name, file_path):
            success_count += 1
    
    logging.info(f"Standardization complete. {success_count}/{len(LEAGUES)} leagues updated successfully")
    
    print(f"All {success_count} leagues have been standardized with consistent:")
    print("  - CSS references")
    print("  - Tab functionality")
    print("  - HTML structure")
    print("\nWordle Warriorz is now at the main URL")

if __name__ == "__main__":
    main()
