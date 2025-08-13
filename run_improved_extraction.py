#!/usr/bin/env python3
"""
Improved Wordle League Multi-League Extraction Runner

This script runs the improved extraction process with enhanced thread clicking
and identification specifically targeting the PAL league issue.

When run directly, this script:
1. Uses the enhanced thread clicking and identification
2. Falls back to the original extraction if needed
3. Can be called by server_auto_update_multi_league.py
"""

import os
import sys
import time
import logging
import traceback
import subprocess
from datetime import datetime

# Configure logging
log_file = f"improved_extraction_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def run_improved_extraction():
    """
    Run the improved extraction with enhanced thread clicking
    
    Returns:
        bool: True if extraction was successful, False otherwise
    """
    logging.info("=== STARTING IMPROVED EXTRACTION ===")
    
    try:
        # Import our direct implementation
        from direct_thread_fix import improved_extract_wordle_scores_multi_league
        
        # Run the improved extraction
        success = improved_extract_wordle_scores_multi_league()
        
        if success:
            logging.info("Improved extraction completed successfully!")
        else:
            logging.warning("Improved extraction found no scores, falling back to original method")
            
            # Fall back to original method if improved method found no scores
            from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
            success = extract_wordle_scores_multi_league()
            
            if success:
                logging.info("Original extraction method found scores")
            else:
                logging.warning("Neither extraction method found scores")
        
        return success
        
    except Exception as e:
        logging.error(f"Error during improved extraction: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Try original method as fallback
        try:
            logging.info("Attempting original extraction method as fallback")
            from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
            success = extract_wordle_scores_multi_league()
            return success
        except Exception as e2:
            logging.error(f"Original extraction also failed: {str(e2)}")
            return False

def run_post_extraction_steps():
    """
    Run the post-extraction steps from the integrated script
    
    Returns:
        bool: True if post-extraction was successful, False otherwise
    """
    logging.info("=== RUNNING POST-EXTRACTION STEPS ===")
    
    try:
        # Import and run the post-extraction function
        from integrated_auto_update_multi_league import run_after_extraction
        run_after_extraction()
        return True
        
    except Exception as e:
        logging.error(f"Error during post-extraction steps: {str(e)}")
        logging.error(traceback.format_exc())
        return False

def run_with_improved_extraction():
    """
    Run the full extraction and update process with improved extraction
    
    Returns:
        int: 0 if successful, 1 otherwise
    """
    start_time = datetime.now()
    logging.info(f"Starting improved multi-league extraction process at {start_time}")
    
    # Step 1: Run improved extraction
    extraction_success = run_improved_extraction()
    
    # Step 2: Run post-extraction steps
    if extraction_success:
        post_success = run_post_extraction_steps()
        if post_success:
            logging.info("Full process completed successfully")
            return 0
        else:
            logging.error("Post-extraction steps failed")
            return 1
    else:
        logging.error("Extraction failed")
        return 1

def create_batch_file():
    """
    Create a batch file to run this script
    """
    batch_content = """@echo off
echo Starting Wordle League Multi-League Update with improved extraction...
cd /d %~dp0
python run_improved_extraction.py
echo Complete.
"""

    with open("run_improved_extraction.bat", "w") as f:
        f.write(batch_content)
    
    logging.info("Created batch file: run_improved_extraction.bat")
    
if __name__ == "__main__":
    # Create batch file for easy scheduling
    create_batch_file()
    
    # Run the full process
    exit_code = run_with_improved_extraction()
    
    # Log completion
    end_time = datetime.now()
    duration = end_time - datetime.strptime(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
    logging.info(f"Process completed in {duration.total_seconds()} seconds with exit code {exit_code}")
    
    # Exit with appropriate code
    sys.exit(exit_code)
