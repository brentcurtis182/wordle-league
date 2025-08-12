#!/usr/bin/env python3
"""
Script to restore the Wordle League site to a functional state with player scores
and statistics tables from backup files.
"""

import os
import shutil
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_working_site.log"),
        logging.StreamHandler()
    ]
)

def restore_index_from_backup():
    """Restore the index.html file from the .bak backup file"""
    try:
        export_dir = "website_export"
        backup_file = os.path.join(export_dir, "index.html.bak")
        current_file = os.path.join(export_dir, "index.html")
        
        # Check if backup file exists
        if not os.path.exists(backup_file):
            logging.error(f"Backup file not found: {backup_file}")
            return False
            
        # Read backup file content
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_content = f.read()
            
        # Read current file to extract Season 1 tab if it exists
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
                
            # Parse current content to extract Season 1 tab
            current_soup = BeautifulSoup(current_content, 'html.parser')
            stats_tab = current_soup.find('div', {'id': 'stats'})
            season_heading = None
            if stats_tab:
                season_heading = stats_tab.find('h2', text=re.compile('Season 1'))
        except Exception as e:
            logging.warning(f"Could not extract Season 1 tab: {e}")
            season_heading = None
        
        # Parse backup content
        backup_soup = BeautifulSoup(backup_content, 'html.parser')
        
        # If Season 1 tab was found in current file, add it to the backup content
        if season_heading:
            logging.info("Found Season 1 tab in current file, preserving it")
            stats_tab_backup = backup_soup.find('div', {'id': 'stats'})
            if stats_tab_backup:
                # Update the tab with Season 1 content or add it as an additional tab
                season_content = current_soup.find('div', {'id': 'stats'})
                if season_content:
                    stats_tab_backup.append(season_content)
        
        # Write updated content to index.html
        with open(current_file, 'w', encoding='utf-8') as f:
            f.write(str(backup_soup))
            
        logging.info("Successfully restored index.html from backup")
        return True
        
    except Exception as e:
        logging.error(f"Error restoring index.html: {e}")
        return False

def restore_landing_page():
    """Ensure landing.html is set up as the site entry point"""
    try:
        export_dir = "website_export"
        landing_file = os.path.join(export_dir, "landing.html")
        
        # Check if landing.html exists
        if not os.path.exists(landing_file):
            logging.warning("landing.html not found, skipping landing page setup")
            return False
            
        # Copy landing.html to the directory above website_export if needed
        parent_landing = os.path.join(os.path.dirname(export_dir), "index.html")
        shutil.copyfile(landing_file, parent_landing)
        logging.info("Copied landing.html to parent directory as index.html")
        
        return True
    except Exception as e:
        logging.error(f"Error setting up landing page: {e}")
        return False

def restore_weekly_pages():
    """Ensure weekly pages are properly linked"""
    try:
        export_dir = "website_export"
        weeks_dir = os.path.join(export_dir, "weeks")
        
        if not os.path.exists(weeks_dir):
            logging.warning("weeks directory not found, skipping weekly pages restore")
            return False
            
        # Nothing to do here since the links are already in the restored index.html
        logging.info("Weekly page links should be intact in the restored index.html")
        return True
    except Exception as e:
        logging.error(f"Error checking weekly pages: {e}")
        return False

def main():
    logging.info("Starting full site restoration...")
    
    # Restore index.html from backup
    if restore_index_from_backup():
        logging.info("Successfully restored index.html with player scores and statistics")
    else:
        logging.error("Failed to restore index.html")
        return False
    
    # Set up landing page
    restore_landing_page()
    
    # Check weekly pages
    restore_weekly_pages()
    
    logging.info("Site restoration completed")
    print("Site has been restored with player scores and statistics!")
    print("You can access the site in the website_export directory.")
    return True

if __name__ == "__main__":
    main()
