#!/usr/bin/env python3
# Diagnostic script that uses the existing extract_wordle_scores_multi_league function
# to open Google Voice threads and capture what's found

import os
import sys
import time
import logging
import subprocess

# Import the function from the integrated file
from integrated_auto_update_multi_league import extract_wordle_scores_multi_league, get_todays_wordle_number, kill_chrome_processes

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("diagnostic_capture.log"),
        logging.StreamHandler()
    ]
)

def run_diagnostic():
    """Run the diagnostic to capture thread DOM elements"""
    logging.info("Running diagnostic capture")
    
    # Make sure Chrome processes are killed
    kill_chrome_processes()
    
    # Get today's Wordle number
    today_wordle = get_todays_wordle_number()
    logging.info(f"Looking for Wordle #{today_wordle} scores")
    
    # Create results directory if it doesn't exist
    results_dir = "thread_capture_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Call the existing function that opens threads
    logging.info("Calling extract_wordle_scores_multi_league function")
    extract_wordle_scores_multi_league()
    
    logging.info("Diagnostic complete. Check screenshots and logs for results.")

if __name__ == "__main__":
    run_diagnostic()
