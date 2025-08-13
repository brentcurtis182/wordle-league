#!/usr/bin/env python3
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime

# Set up logging with more verbose output
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("debug_extract.log"),
                        logging.StreamHandler()
                    ])

# Import the main extraction function
sys.path.insert(0, os.path.abspath('.'))
from integrated_auto_update_multi_league import extract_wordle_scores_multi_league

def main():
    logging.debug("Starting debug extraction process")
    try:
        # Call the extraction function 
        logging.debug("Calling extract_wordle_scores_multi_league")
        results = extract_wordle_scores_multi_league()
        
        logging.debug(f"Extraction results: {results}")
        
        # Log any found scores from the browser's window._foundScores
        logging.debug("Checking for window._foundScores in extraction results")
        if results and 'scores' in results:
            logging.debug(f"Found {len(results['scores'])} scores")
            for score in results['scores']:
                logging.debug(f"SCORE FOUND: {score}")
        else:
            logging.debug("No scores found in extraction results")
            
    except Exception as e:
        logging.exception(f"Error in debug extraction: {e}")

if __name__ == "__main__":
    main()
