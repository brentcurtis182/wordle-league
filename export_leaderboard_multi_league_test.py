#!/usr/bin/env python3
# Test version of export script using test database

import os
import sys
import sqlite3
import jinja2
import subprocess
import logging
import shutil
from datetime import datetime, timedelta

# Import the original export script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import export_leaderboard_multi_league

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("export_test_script.log"),
        logging.StreamHandler()
    ]
)

def main():
    """Run export using test database"""
    logging.info("Starting test export with test database")
    
    # Override the database path in the export script
    # Store the original database URI
    original_db = export_leaderboard_multi_league.WORDLE_DATABASE
    export_leaderboard_multi_league.WORDLE_DATABASE = 'wordle_league_test.db'
    
    # Override export directory to a test directory
    original_export_dir = export_leaderboard_multi_league.EXPORT_DIR
    test_export_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'website_export_test')
    export_leaderboard_multi_league.EXPORT_DIR = test_export_dir
    
    # Create test export directory if it doesn't exist
    if not os.path.exists(test_export_dir):
        os.makedirs(test_export_dir)
    
    try:
        # Run the export
        export_result = export_leaderboard_multi_league.main()
        
        logging.info(f"Test export completed with result: {export_result}")
        
        # Restore original values
        export_leaderboard_multi_league.DATABASE_URI = original_db
        export_leaderboard_multi_league.EXPORT_DIR = original_export_dir
        
        return export_result
    except Exception as e:
        logging.error(f"Error during test export: {e}")
        # Restore original values
        export_leaderboard_multi_league.DATABASE_URI = original_db
        export_leaderboard_multi_league.EXPORT_DIR = original_export_dir
        return False

if __name__ == "__main__":
    main()
    logging.info("Test export script completed")
