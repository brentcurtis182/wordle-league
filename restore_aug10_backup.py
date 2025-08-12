#!/usr/bin/env python3
"""
Script to restore website files from the August 10, 2025 11:34 PM backup
which had proper working tabs for all leagues
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
        logging.FileHandler("restore_backup.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def restore_from_backup():
    """Restore website files from August 10, 2025 11:34 PM backup"""
    # Base paths
    website_dir = "website_export"
    backup_dir = os.path.join(website_dir, "backups")
    
    # Timestamp for the backup we want to restore
    backup_timestamp = "20250810_233451"
    
    # League directories to process
    leagues = [
        "",               # Main index (Wordle Warriorz)
        "gang",           # Wordle Gang 
        "pal",            # Wordle PAL
        "party",          # Wordle Party
        "vball"           # Wordle Vball
    ]
    
    restore_count = 0
    error_count = 0
    
    # First create backups of current files
    current_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for league_dir in leagues:
        # Source and destination paths
        target_dir = os.path.join(website_dir, league_dir)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            
        current_file = os.path.join(target_dir, "index.html")
        
        # Backup current file if it exists
        if os.path.exists(current_file):
            current_backup = f"{current_file}_before_restore_{current_timestamp}"
            try:
                shutil.copy2(current_file, current_backup)
                logger.info(f"Backed up current {current_file} to {current_backup}")
            except Exception as e:
                logger.error(f"Failed to backup {current_file}: {e}")
    
    # Now restore from the Aug 10 backup
    for league_dir in leagues:
        # Target file (where we'll restore to)
        target_dir = os.path.join(website_dir, league_dir)
        target_file = os.path.join(target_dir, "index.html")
        
        # Source backup file
        if league_dir == "":
            # Main index file
            source_file = os.path.join(backup_dir, f"index.html_{backup_timestamp}")
        else:
            # League-specific file
            source_file = os.path.join(backup_dir, f"{league_dir}_index.html_{backup_timestamp}")
        
        if os.path.exists(source_file):
            try:
                # Ensure the target directory exists
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                
                # Copy the backup file to the target location
                shutil.copy2(source_file, target_file)
                restore_count += 1
                logger.info(f"Restored {target_file} from {source_file}")
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to restore {target_file}: {e}")
        else:
            logger.warning(f"Backup file not found: {source_file}")
    
    logger.info(f"Restore completed. Successfully restored {restore_count} files with {error_count} errors.")
    return restore_count, error_count

if __name__ == "__main__":
    logger.info("Starting website restoration from August 10, 2025 11:34 PM backup")
    restore_count, error_count = restore_from_backup()
    
    if restore_count > 0 and error_count == 0:
        print("\nRestore successful! Website files have been reverted to the August 10th backup with working tabs.")
        print("You should verify the website locally before publishing to GitHub.")
    else:
        print("\nRestore completed with some issues. Please check the log file for details.")
