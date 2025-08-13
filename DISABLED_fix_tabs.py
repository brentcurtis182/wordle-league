#!/usr/bin/env python3
"""
Script to fix tab functionality on all Wordle League pages
Adds JavaScript reference to tabs.js in all league HTML files
"""

import os
from bs4 import BeautifulSoup
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_tabs.log"),
        logging.StreamHandler()
    ]
)

# League paths
LEAGUES = {
    "warriorz": "website_export/index.html",
    "gang": "website_export/gang/index.html",
    "pal": "website_export/pal/index.html",
    "party": "website_export/party/index.html",
    "vball": "website_export/vball/index.html"
}

def fix_league_tabs(league_name, file_path):
    """Add tab.js script reference to league HTML file"""
    try:
        # Create backup
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copyfile(file_path, backup_path)
        logging.info(f"Backed up {file_path} to {backup_path}")
        
        # Read HTML
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check if script already exists
        script_exists = False
        for script in soup.find_all('script'):
            if script.get('src') == 'tabs.js' or script.get('src') == '../tabs.js':
                script_exists = True
                break
        
        if not script_exists:
            # Create script tag with proper path
            script = soup.new_tag('script')
            if league_name == "warriorz":
                script['src'] = 'tabs.js'
            else:
                script['src'] = '../tabs.js'
            
            # Add script tag before closing body tag
            body = soup.find('body')
            if body:
                body.append(script)
                
                # Write updated HTML
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logging.info(f"Added tab.js script to {league_name}")
            else:
                logging.error(f"No body tag found in {file_path}")
        else:
            logging.info(f"Script already exists in {league_name}")
            
        # Also fix CSS reference while we're at it
        fix_css_reference(soup, league_name, file_path)
        
        return True
    
    except Exception as e:
        logging.error(f"Error fixing tabs for {league_name}: {e}")
        return False

def fix_css_reference(soup, league_name, file_path):
    """Fix CSS reference in league HTML file"""
    try:
        css_link = soup.find('link', rel='stylesheet')
        if css_link:
            if league_name == "warriorz":
                # Main league should reference styles.css directly
                if css_link.get('href') != 'styles.css':
                    css_link['href'] = 'styles.css'
                    # Write updated HTML
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    logging.info(f"Fixed CSS path for {league_name} to styles.css")
            else:
                # Subdirectory leagues should reference ../styles.css
                if css_link.get('href') != '../styles.css':
                    css_link['href'] = '../styles.css'
                    # Write updated HTML
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    logging.info(f"Fixed CSS path for {league_name} to ../styles.css")
    except Exception as e:
        logging.error(f"Error fixing CSS for {league_name}: {e}")

def main():
    """Fix tabs on all league pages"""
    logging.info("Starting tab fix for all leagues...")
    
    success_count = 0
    for league_name, file_path in LEAGUES.items():
        logging.info(f"Fixing tabs for {league_name}...")
        if fix_league_tabs(league_name, file_path):
            success_count += 1
    
    logging.info(f"Tab fix complete. {success_count}/{len(LEAGUES)} leagues updated successfully")
    
    # Force fix for the landing page
    try:
        # Create landing directory if it doesn't exist
        os.makedirs("website_export/landing", exist_ok=True)
        
        # Copy current landing page to landing directory
        landing_path = "website_export/landing/index.html"
        if os.path.exists("website_export/landing.html"):
            shutil.copyfile("website_export/landing.html", landing_path)
            logging.info("Copied landing.html to landing/index.html")
        
        # Ensure main index.html is the warriorz league
        warriorz_backup = "website_export_backup/backups/index_20250806_131435.html"
        if os.path.exists(warriorz_backup):
            shutil.copyfile(warriorz_backup, "website_export/index.html")
            logging.info("Restored Warriorz league to main index.html")
            
            # Fix CSS and tabs on the restored warriorz page
            fix_league_tabs("warriorz", "website_export/index.html")
    except Exception as e:
        logging.error(f"Error fixing landing page: {e}")
    
    print("Tab functionality has been added to all league pages!")
    print("All leagues should now have working tabs for Latest, Weekly, and All-Time views.")

if __name__ == "__main__":
    main()
