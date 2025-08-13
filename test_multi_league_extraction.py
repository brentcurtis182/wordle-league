#!/usr/bin/env python3
"""
Test Multi-League Extraction

This script tests the improved multi-league extraction process.
"""

import sys
import logging
import time
import datetime

# Configure logging for this test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"test_extraction_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

# Import the extract function from the updated script
sys.path.append('.')
try:
    from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
    logging.info("Successfully imported extract_wordle_scores_multi_league function")
except Exception as e:
    logging.error(f"Error importing extract function: {str(e)}")
    sys.exit(1)

def run_test():
    """Run extraction test"""
    logging.info("=" * 50)
    logging.info("STARTING MULTI-LEAGUE EXTRACTION TEST")
    logging.info("=" * 50)
    
    try:
        start_time = time.time()
        success = extract_wordle_scores_multi_league()
        end_time = time.time()
        
        duration = end_time - start_time
        logging.info(f"Extraction completed in {duration:.2f} seconds")
        logging.info(f"Extraction {'successful' if success else 'failed'}")
        
        return success
    except Exception as e:
        logging.error(f"Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_test()
    print(f"Multi-league extraction test completed with success: {success}")
    sys.exit(0 if success else 1)
