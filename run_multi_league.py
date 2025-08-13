#!/usr/bin/env python3
# Direct Multi-League Extraction Script
# This script can be called directly by server_auto_update_multi_league.py

import logging
import sys
import os
from datetime import datetime

# Configure logging
log_file = f"multi_league_extraction_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def main():
    logging.info("Starting improved multi-league extraction")
    
    try:
        # Use the patched runner
        import run_patched_extraction
        success = run_patched_extraction.main()
        
        # If that fails, fall back to original
        if not success:
            logging.warning("Patched extraction failed, falling back to original method")
            from integrated_auto_update_multi_league import extract_wordle_scores_multi_league
            success = extract_wordle_scores_multi_league()
        
        return success
        
    except Exception as e:
        logging.error(f"Error in direct run script: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit_code = 0 if success else 1
    print(f"Extraction completed with success: {success}")
    sys.exit(exit_code)
