#!/usr/bin/env python3
"""
Script to restore the website from the website_export_backup directory
which contains the complete August 10th data including Wordle #1513
"""

import os
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_from_backup.log"),
        logging.StreamHandler()
    ]
)

def backup_current_website():
    """Backup the current website before replacing it"""
    try:
        current_dir = "website_export"
        backup_dir = f"website_export_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create a full backup of the current website
        if os.path.exists(current_dir):
            shutil.copytree(current_dir, backup_dir)
            logging.info(f"Created backup of current website at {backup_dir}")
        return True
    except Exception as e:
        logging.error(f"Failed to backup current website: {e}")
        return False

def restore_from_backup():
    """Restore the website from the backup directory"""
    try:
        source_dir = "website_export_backup"
        target_dir = "website_export"
        
        # Verify the backup has the latest data
        wordle1513_path = os.path.join(source_dir, "daily", "wordle-1513.html")
        if not os.path.exists(wordle1513_path):
            logging.error(f"Backup does not contain Wordle #1513 data at {wordle1513_path}")
            print("ERROR: The backup doesn't seem to have today's Wordle data (Wordle #1513).")
            return False
        
        logging.info(f"Verified backup contains Wordle #1513 data")
        
        # Check if the backup contains index.html
        index_path = os.path.join(source_dir, "index.html")
        if not os.path.exists(index_path):
            logging.error(f"Backup does not contain index.html at {index_path}")
            print("ERROR: The backup doesn't contain index.html.")
            return False
            
        logging.info(f"Verified backup contains index.html")
        
        # Copy all files from backup to website_export
        for item in os.listdir(source_dir):
            source_path = os.path.join(source_dir, item)
            target_path = os.path.join(target_dir, item)
            
            if item == '.git':
                # Skip .git directory to avoid git issues
                continue
                
            if os.path.isdir(source_path):
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
                logging.info(f"Copied directory {item} to {target_dir}")
            else:
                if os.path.exists(target_path):
                    os.remove(target_path)
                shutil.copy2(source_path, target_path)
                logging.info(f"Copied file {item} to {target_dir}")
                
        return True
    except Exception as e:
        logging.error(f"Failed to restore from backup: {e}")
        return False

def verify_restoration():
    """Verify that the restoration was successful"""
    try:
        # Check key files exist
        website_dir = "website_export"
        index_path = os.path.join(website_dir, "index.html")
        if not os.path.exists(index_path):
            logging.error(f"Restoration failed: index.html not found at {index_path}")
            return False
            
        # Check wordle-1513.html exists
        wordle1513_path = os.path.join(website_dir, "daily", "wordle-1513.html")
        if not os.path.exists(wordle1513_path):
            logging.error(f"Restoration failed: wordle-1513.html not found at {wordle1513_path}")
            return False
            
        # Check all league directories exist
        required_leagues = ["gang", "pal", "party", "vball"]
        for league in required_leagues:
            league_dir = os.path.join(website_dir, league)
            if not os.path.exists(league_dir):
                logging.error(f"Restoration failed: league directory {league} not found at {league_dir}")
                return False
                
        logging.info("Restoration verification passed: All key files and directories exist")
        return True
    except Exception as e:
        logging.error(f"Verification failed: {e}")
        return False

def main():
    """Main function to orchestrate the restoration"""
    logging.info("Starting website restoration from backup...")
    
    # First, backup the current website
    logging.info("Backing up current website...")
    if not backup_current_website():
        print("ERROR: Failed to backup current website. Aborting restoration.")
        return False
        
    # Restore from backup
    logging.info("Restoring from backup...")
    if not restore_from_backup():
        print("ERROR: Failed to restore from backup.")
        return False
        
    # Verify restoration
    logging.info("Verifying restoration...")
    if not verify_restoration():
        print("WARNING: Restoration verification failed. The website may not be fully restored.")
        return False
        
    logging.info("Website successfully restored from backup!")
    print("SUCCESS: Website has been successfully restored from the backup.")
    print("The website should now show correct data for all leagues through August 10th (Wordle #1513).")
    return True
    
if __name__ == "__main__":
    main()
