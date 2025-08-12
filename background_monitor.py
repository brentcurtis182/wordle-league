#!/usr/bin/env python
"""
Background monitor script to run scheduled_update.bat every minute
This bypasses Task Scheduler permission issues
"""

import subprocess
import time
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("background_monitor.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    update_script = os.path.join(script_dir, "scheduled_update.bat")
    
    logging.info("Starting Wordle League background monitor")
    logging.info(f"Will run {update_script} every minute")
    logging.info("Press Ctrl+C to stop")
    
    # Run once immediately
    run_update(update_script)
    
    # Then run every minute
    try:
        while True:
            # Wait for 60 seconds
            time.sleep(60)
            run_update(update_script)
    except KeyboardInterrupt:
        logging.info("Monitor stopped by user")
        
def run_update(update_script):
    """Run the update script and log results"""
    try:
        start_time = datetime.now()
        logging.info(f"Running update at {start_time}")
        
        # Run the batch file and capture output
        process = subprocess.Popen(
            update_script, 
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Get output with a timeout
        try:
            stdout, stderr = process.communicate(timeout=30)
            exit_code = process.returncode
            
            if exit_code == 0:
                logging.info("Update completed successfully")
            else:
                logging.error(f"Update failed with exit code {exit_code}")
                logging.error(f"Error output: {stderr}")
                
        except subprocess.TimeoutExpired:
            process.kill()
            logging.warning("Update process timed out after 30 seconds")
            
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        logging.info(f"Update took {duration:.2f} seconds")
        
    except Exception as e:
        logging.error(f"Error running update: {e}")

if __name__ == "__main__":
    main()
