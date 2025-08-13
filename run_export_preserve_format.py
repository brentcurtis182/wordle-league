#!/usr/bin/env python3
"""
Script to run the export script while preserving the restored format
"""

import os
import shutil
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("preserve_format_export.log"),
        logging.StreamHandler()
    ]
)

def backup_current_files():
    """Back up the current website files before exporting"""
    export_dir = "website_export"
    backup_dir = os.path.join(export_dir, "format_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    try:
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy index.html to backup
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            shutil.copy2(index_file, os.path.join(backup_dir, "index.html"))
            logging.info(f"Backed up index.html to {backup_dir}")
            
        # Copy CSS files to backup
        css_file = os.path.join(export_dir, "styles.css")
        if os.path.exists(css_file):
            shutil.copy2(css_file, os.path.join(backup_dir, "styles.css"))
            logging.info(f"Backed up styles.css to {backup_dir}")
            
        # Copy JavaScript files to backup
        js_file = os.path.join(export_dir, "script.js")
        if os.path.exists(js_file):
            shutil.copy2(js_file, os.path.join(backup_dir, "script.js"))
            logging.info(f"Backed up script.js to {backup_dir}")
            
        # Make a special backup of index.html for easy recovery
        if os.path.exists(index_file):
            shutil.copy2(index_file, os.path.join(export_dir, "index.html.format_backup"))
            logging.info("Created special backup of index.html for easy recovery")
            
        return True
    except Exception as e:
        logging.error(f"Error backing up files: {e}")
        return False

def run_export_script():
    """Run the export script to update data"""
    try:
        # Run export script
        result = subprocess.run(
            ["python", "export_leaderboard_multi_league.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logging.info("Export script completed successfully")
        logging.info(f"Export output: {result.stdout}")
        
        if result.stderr:
            logging.warning(f"Export warnings/errors: {result.stderr}")
            
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Export script failed: {e}")
        logging.error(f"Export error output: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error running export script: {e}")
        return False

def restore_format():
    """Restore the nice formatting after export"""
    export_dir = "website_export"
    index_file = os.path.join(export_dir, "index.html")
    backup_file = os.path.join(export_dir, "index.html.format_backup")
    
    try:
        if os.path.exists(backup_file) and os.path.exists(index_file):
            # Move the new index to a temp file
            temp_file = os.path.join(export_dir, "index.html.new_data")
            shutil.move(index_file, temp_file)
            logging.info("Saved new data to temporary file")
            
            # Restore the formatted index
            shutil.copy2(backup_file, index_file)
            logging.info("Restored formatted index.html")
            
            logging.info("Format has been preserved")
            return True
        else:
            logging.error("Backup file not found, cannot restore format")
            return False
    except Exception as e:
        logging.error(f"Error restoring format: {e}")
        return False

def main():
    logging.info("Starting export with format preservation...")
    
    # Back up current files
    logging.info("Backing up current files...")
    if not backup_current_files():
        logging.error("Failed to back up files, aborting")
        return False
    
    # Run the export script
    logging.info("Running export script...")
    if not run_export_script():
        logging.error("Export script failed, restoring from backup")
        restore_format()
        return False
    
    # Restore the format
    logging.info("Restoring format...")
    if not restore_format():
        logging.error("Failed to restore format")
        return False
    
    logging.info("Export with format preservation completed successfully")
    print("Export completed with format preservation!")
    print("The website files have been updated with current data while maintaining the nice formatting.")
    return True

if __name__ == "__main__":
    main()
