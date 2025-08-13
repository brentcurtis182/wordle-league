#!/usr/bin/env python3
"""
Simple wrapper script to update all leagues using update_correct_structure.py
This script will update all leagues in one go with proper HTML structure,
including days of the week columns and without duplicate descriptions.
"""

import sys
import subprocess
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_all_leagues.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Define all league keys
LEAGUES = ['warriorz', 'gang', 'pal', 'party', 'vball']

def main():
    """Update all leagues using update_correct_structure.py"""
    start_time = time.time()
    logger.info("Starting update for all Wordle leagues")
    
    successful = 0
    failed = 0
    
    for league in LEAGUES:
        logger.info(f"Updating {league} league...")
        try:
            # Run update_correct_structure.py for this league
            result = subprocess.run(
                ['python', 'update_correct_structure.py', league], 
                check=True,
                capture_output=True, 
                text=True
            )
            logger.info(f"Successfully updated {league} league")
            logger.debug(result.stdout)
            successful += 1
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update {league} league: {e}")
            logger.error(f"Error output: {e.stderr}")
            failed += 1
    
    # Run additional scripts
    try:
        logger.info("Updating API JSON data...")
        subprocess.run(['python', 'export_api_json.py'], check=True)
        # Don't overwrite index.html with landing page
        # logger.info("Fixing landing page...")
        # subprocess.run(['python', 'fix_landing_page.py'], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run additional scripts: {e}")
        failed += 1
    
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"Update complete in {duration:.2f} seconds")
    logger.info(f"Results: {successful} leagues updated successfully, {failed} failures")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
