#!/usr/bin/env python3
"""
Script to restore the multi-league tab website structure from the backup
and update it with the latest Wordle number and date (August 10th, #1513)
"""

import os
import shutil
import re
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_multi_league.log"),
        logging.StreamHandler()
    ]
)

# Constants
SOURCE_FILE = r"c:\Wordle-League\website_export_backup\index.html"  # This contains the multi-league tabs
TARGET_DIR = r"c:\Wordle-League\website_export"
TARGET_FILE = os.path.join(TARGET_DIR, "index.html")
BACKUP_DIR = os.path.join(TARGET_DIR, f"pre_restore_ml_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

# Latest Wordle information
LATEST_WORDLE_NUMBER = "1513"
LATEST_WORDLE_DATE = "August 10, 2025"

def backup_current_website():
    """Create a backup of the current website before modifying it"""
    try:
        # Create backup directory if it doesn't exist
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
            
        # Backup the current index.html if it exists
        if os.path.exists(TARGET_FILE):
            backup_file = os.path.join(BACKUP_DIR, "index.html")
            shutil.copy2(TARGET_FILE, backup_file)
            logging.info(f"Backed up current index.html to {backup_file}")
        
        return True
    except Exception as e:
        logging.error(f"Error backing up website: {e}")
        return False

def restore_and_update():
    """Restore the website from the backup with multi-league structure and update date/wordle number"""
    try:
        if not os.path.exists(SOURCE_FILE):
            logging.error(f"Source file {SOURCE_FILE} not found")
            return False
            
        # Read the source HTML
        with open(SOURCE_FILE, 'r', encoding='utf-8') as file:
            html_content = file.read()
            
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update the Wordle number and date
        wordle_heading = soup.select_one('h2[style*="color: #6aaa64"]')
        if wordle_heading:
            # Update the Wordle number and date
            old_text = wordle_heading.text
            logging.info(f"Found Wordle heading: {old_text}")
            
            # Replace with new Wordle number and date
            new_text = f"Wordle #{LATEST_WORDLE_NUMBER} - {LATEST_WORDLE_DATE}"
            wordle_heading.string = new_text
            logging.info(f"Updated Wordle heading to: {new_text}")
        else:
            logging.warning("Could not find Wordle heading to update")
        
        # Write the updated HTML to the target file
        with open(TARGET_FILE, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        
        logging.info(f"Successfully restored multi-league structure and updated index.html")
        return True
    
    except Exception as e:
        logging.error(f"Error restoring and updating website: {e}")
        return False

def ensure_league_directories():
    """Make sure all the league directories exist"""
    try:
        # List of league directories that should exist
        league_dirs = ['gang', 'pal', 'party', 'vball']
        
        for league_dir in league_dirs:
            dir_path = os.path.join(TARGET_DIR, league_dir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                # Create a basic index.html in the league directory
                with open(os.path.join(dir_path, 'index.html'), 'w', encoding='utf-8') as f:
                    f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8"/>
    <title>Wordle {league_dir.capitalize()} League</title>
    <meta http-equiv="refresh" content="0;url=../index.html?league={league_dir}">
</head>
<body>
    <p>Redirecting to <a href="../index.html?league={league_dir}">Wordle {league_dir.capitalize()} League</a>...</p>
</body>
</html>
                    """)
                logging.info(f"Created directory and placeholder: {dir_path}")
        
        # Ensure other directories exist in website_export
        required_dirs = ['api', 'days', 'weeks', 'templates']
        for dir_name in required_dirs:
            dir_path = os.path.join(TARGET_DIR, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logging.info(f"Created directory: {dir_path}")
        
        return True
    except Exception as e:
        logging.error(f"Error ensuring league directories: {e}")
        return False

def main():
    """Main function to orchestrate the restoration process"""
    logging.info("Starting website restoration with multi-league structure...")
    
    # Backup current website
    if not backup_current_website():
        logging.error("Failed to backup current website. Aborting.")
        return False
    
    # Restore and update the website
    if not restore_and_update():
        logging.error("Failed to restore and update website. Aborting.")
        return False
    
    # Ensure league directories exist
    if not ensure_league_directories():
        logging.warning("Warning: League directories may not have been created correctly.")
    
    logging.info("Website restoration with multi-league structure completed successfully!")
    print("SUCCESS: Website has been restored with multi-league structure and updated with Wordle #1513 - August 10, 2025")
    return True

if __name__ == "__main__":
    main()
