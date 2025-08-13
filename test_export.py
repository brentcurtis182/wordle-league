#!/usr/bin/env python3
# Test script for exporting with clean emoji patterns

import os
import sys
import sqlite3
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_export.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Run a test export using the test database"""
    logging.info("Starting test export with test database")
    
    # Store the original database path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    original_db = os.path.join(script_dir, 'wordle_league.db')
    test_db = os.path.join(script_dir, 'wordle_league_test.db')
    
    # Create a backup of the original database
    if not os.path.exists(test_db):
        logging.error("Test database not found. Please run the emoji pattern test first.")
        return False
    
    # Override environment variables for the export script
    os.environ['DATABASE_URI'] = test_db
    os.environ['EXPORT_DIR'] = os.path.join(script_dir, 'website_export_test')
    
    # Create the test export directory if it doesn't exist
    if not os.path.exists(os.environ['EXPORT_DIR']):
        os.makedirs(os.environ['EXPORT_DIR'])
    
    try:
        # Import and run the export script
        sys.path.insert(0, script_dir)
        import export_leaderboard_multi_league
        export_result = export_leaderboard_multi_league.main()
        
        logging.info(f"Test export completed with result: {export_result}")
        
        # Check for files that should have been created
        test_dir = os.environ['EXPORT_DIR']
        index_file = os.path.join(test_dir, 'warriorz', 'index.html')
        daily_dir = os.path.join(test_dir, 'warriorz', 'daily')
        
        if os.path.exists(index_file):
            logging.info(f"Success! Generated index file: {index_file}")
        else:
            logging.error(f"Failed to generate index file: {index_file}")
        
        if os.path.exists(daily_dir) and os.listdir(daily_dir):
            logging.info(f"Success! Generated daily files in: {daily_dir}")
            logging.info(f"Daily files: {os.listdir(daily_dir)}")
        else:
            logging.error(f"Failed to generate daily files in: {daily_dir}")
        
        return export_result
    except Exception as e:
        logging.error(f"Error during test export: {e}")
        return False
    finally:
        # Clean up environment variables
        if 'DATABASE_URI' in os.environ:
            del os.environ['DATABASE_URI']
        if 'EXPORT_DIR' in os.environ:
            del os.environ['EXPORT_DIR']

if __name__ == "__main__":
    success = main()
    logging.info(f"Test export script completed: {'Success' if success else 'Failed'}")
