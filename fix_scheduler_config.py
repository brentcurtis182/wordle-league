#!/usr/bin/env python3
# Script to fix the scheduler configuration to use the improved extraction
import os
import sys
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_scheduler.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Fix the scheduler to use the improved auto update script"""
    logging.info("Starting scheduler configuration fix")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Backup server_auto_update.py
    server_auto_update_path = os.path.join(script_dir, "server_auto_update.py")
    backup_path = os.path.join(script_dir, f"server_auto_update.py.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
    
    logging.info(f"Backing up {server_auto_update_path} to {backup_path}")
    shutil.copy2(server_auto_update_path, backup_path)
    
    # Update the server_auto_update.py script to use integrated_auto_update.py
    with open(server_auto_update_path, 'r') as f:
        content = f.read()
    
    # Replace the extraction script path
    content = content.replace(
        'EXTRACTION_SCRIPT = os.path.join(SCRIPT_DIR, "server_extractor.py")',
        'EXTRACTION_SCRIPT = os.path.join(SCRIPT_DIR, "integrated_auto_update.py")'
    )
    
    # Write the updated content
    with open(server_auto_update_path, 'w') as f:
        f.write(content)
    
    logging.info("Updated server_auto_update.py to use integrated_auto_update.py")
    
    # Check scheduled_update.bat to ensure it's calling server_auto_update.py
    scheduled_update_path = os.path.join(script_dir, "scheduled_update.bat")
    if os.path.exists(scheduled_update_path):
        with open(scheduled_update_path, 'r') as f:
            bat_content = f.read()
        
        if "server_auto_update.py" not in bat_content:
            # Update the batch file
            logging.info("scheduled_update.bat needs to be updated")
            
            backup_bat_path = os.path.join(script_dir, f"scheduled_update.bat.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
            shutil.copy2(scheduled_update_path, backup_bat_path)
            
            # Create a new batch file that calls server_auto_update.py
            with open(scheduled_update_path, 'w') as f:
                f.write('@echo off\n')
                f.write('cd /d "%~dp0"\n')
                f.write('python server_auto_update.py\n')
            
            logging.info("Updated scheduled_update.bat")
    else:
        # Create the batch file if it doesn't exist
        with open(scheduled_update_path, 'w') as f:
            f.write('@echo off\n')
            f.write('cd /d "%~dp0"\n')
            f.write('python server_auto_update.py\n')
        
        logging.info("Created scheduled_update.bat")
    
    logging.info("Scheduler configuration fix completed")
    print("\nScheduler configuration has been updated to use the improved extraction script!")
    print("The scheduler will now use integrated_auto_update.py which has:")
    print("  - Better extraction using .cdk-visually-hidden elements")
    print("  - Proper emoji pattern preservation")
    print("  - Filtering of old scores")

if __name__ == "__main__":
    main()
