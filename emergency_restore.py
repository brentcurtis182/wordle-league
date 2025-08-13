#!/usr/bin/env python3
"""
Emergency restore script to fix the corrupted index.html file
"""

import os
import shutil
import logging
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emergency_restore.log"),
        logging.StreamHandler()
    ]
)

def restore_from_backup():
    """Restore the website from the .bak file and update to current date"""
    export_dir = "website_export"
    current_file = os.path.join(export_dir, "index.html")
    backup_file = os.path.join(export_dir, "index.html.bak")
    
    # Create a backup of the current file (even if it's broken)
    broken_backup = os.path.join(export_dir, f"index.html.broken_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    shutil.copy2(current_file, broken_backup)
    logging.info(f"Backed up broken file to {broken_backup}")
    
    try:
        # Read the backup content
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_content = f.read()
            
        # Parse with BeautifulSoup
        backup_soup = BeautifulSoup(backup_content, 'html.parser')
        
        # Update the date to August 10, 2025 (Wordle #1513)
        latest_tab = backup_soup.find('div', {'id': 'latest'})
        if latest_tab:
            h2 = latest_tab.find('h2')
            if h2:
                h2.string = "Wordle #1513 - August 10, 2025"
                logging.info("Updated Wordle number to #1513 and date to August 10, 2025")
                
        # Keep the weekly and stats tabs from the current file if they have newer data
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
                
            current_soup = BeautifulSoup(current_content, 'html.parser')
            
            # Check if weekly tab has content
            current_weekly_tab = current_soup.find('div', {'id': 'weekly'})
            backup_weekly_tab = backup_soup.find('div', {'id': 'weekly'})
            
            if current_weekly_tab and backup_weekly_tab:
                current_weekly_table = current_weekly_tab.find('table')
                if current_weekly_table:
                    # Replace weekly tab content in backup with current content
                    backup_weekly_tab.clear()
                    for child in current_weekly_tab.children:
                        backup_weekly_tab.append(child)
                    logging.info("Preserved weekly tab content from current file")
            
            # Check if stats tab has content
            current_stats_tab = current_soup.find('div', {'id': 'stats'})
            backup_stats_tab = backup_soup.find('div', {'id': 'stats'})
            
            if current_stats_tab and backup_stats_tab:
                current_stats_table = current_stats_tab.find('table')
                if current_stats_table:
                    # Replace stats tab content in backup with current content
                    backup_stats_tab.clear()
                    for child in current_stats_tab.children:
                        backup_stats_tab.append(child)
                    logging.info("Preserved stats tab content from current file")
                    
        except Exception as e:
            logging.warning(f"Could not preserve weekly/stats content: {e}")
                
        # Write the restored content back to the file
        with open(current_file, 'w', encoding='utf-8') as f:
            f.write(str(backup_soup))
            
        logging.info("Successfully restored website from backup")
        
        # Make a special backup of the restored file for safety
        restored_backup = os.path.join(export_dir, f"index.html.restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(current_file, restored_backup)
        logging.info(f"Created backup of restored file at {restored_backup}")
        
        return True
    except Exception as e:
        logging.error(f"Error restoring from backup: {e}")
        return False
        
def main():
    logging.info("Starting emergency restoration...")
    if restore_from_backup():
        print("Successfully restored website from backup!")
        print("The website should now show correct data with proper formatting.")
        return True
    else:
        print("Failed to restore website from backup.")
        return False
        
if __name__ == "__main__":
    main()
