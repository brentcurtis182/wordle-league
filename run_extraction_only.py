#!/usr/bin/env python3
"""
Run Extraction Only

This script runs only the extraction part of the Wordle League update process,
using the improved multi-league extraction methods.
"""

import sys
import logging
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"extraction_run_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Run extraction only"""
    logging.info("=" * 50)
    logging.info("STARTING EXTRACTION ONLY")
    logging.info("=" * 50)
    
    try:
        # Import the extract function
        from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
        
        # Run extraction
        success = extract_wordle_scores_multi_league()
        
        logging.info(f"Extraction completed with success: {success}")
        return success
    except Exception as e:
        logging.error(f"Error during extraction: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    print(f"Extraction only completed with success: {success}")
    sys.exit(0 if success else 1)
