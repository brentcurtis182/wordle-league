#!/usr/bin/env python3
"""
Check the reset status of the Wordle League database.
This script will examine the database to determine if daily/weekly resets are occurring.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_exists(db_name):
    """Check if the database file exists"""
    if os.path.exists(db_name):
        logger.info(f"Found database: {db_name}")
        return True
    else:
        logger.error(f"Database file not found: {db_name}")
        return False

def check_db_tables(conn):
    """Check what tables exist in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    logger.info(f"Database contains {len(tables)} tables:")
    for table in tables:
        logger.info(f"- {table[0]}")
    
    # Check for specific tables
    required_tables = ['scores', 'players', 'latest_scores', 'season_winners']
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
        if cursor.fetchone():
            logger.info(f"✓ Required table exists: {table}")
        else:
            logger.warning(f"✗ Required table missing: {table}")
    
    return tables

def check_settings_table(conn):
    """Check if the settings table exists and contains reset information"""
    cursor = conn.cursor()
    
    # Check if settings table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings';")
    if not cursor.fetchone():
        logger.warning("Settings table does not exist - this may be why resets aren't working")
        return False
    
    # Check for last reset date
    try:
        cursor.execute("SELECT key, value FROM settings WHERE key LIKE '%reset%';")
        reset_settings = cursor.fetchall()
        
        if reset_settings:
            logger.info("Found reset settings:")
            for key, value in reset_settings:
                logger.info(f"  {key}: {value}")
        else:
            logger.warning("No reset settings found in settings table")
        
        return True
    except sqlite3.Error as e:
        logger.error(f"Error querying settings table: {e}")
        return False

def check_latest_scores(conn):
    """Check the latest scores table for recent entries"""
    cursor = conn.cursor()
    
    try:
        # Check if latest_scores table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='latest_scores';")
        if not cursor.fetchone():
            logger.warning("Latest scores table does not exist")
            return False
        
        # Check latest score entries
        cursor.execute("SELECT COUNT(*) FROM latest_scores;")
        count = cursor.fetchone()[0]
        logger.info(f"Latest scores table contains {count} entries")
        
        # Get most recent scores
        cursor.execute("SELECT * FROM latest_scores ORDER BY ROWID DESC LIMIT 5;")
        recent_scores = cursor.fetchall()
        
        if recent_scores:
            for score in recent_scores:
                logger.info(f"Recent score: {score}")
        
        return True
    except sqlite3.Error as e:
        logger.error(f"Error checking latest scores: {e}")
        return False

def check_season_winners(conn):
    """Check the season winners table for weekly winners"""
    cursor = conn.cursor()
    
    try:
        # Check if season_winners table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='season_winners';")
        if not cursor.fetchone():
            logger.warning("Season winners table does not exist")
            return False
        
        # Check season winners entries
        cursor.execute("SELECT COUNT(*) FROM season_winners;")
        count = cursor.fetchone()[0]
        logger.info(f"Season winners table contains {count} entries")
        
        # Get most recent winners
        cursor.execute("""
        SELECT p.name, sw.week_date, sw.score 
        FROM season_winners sw
        JOIN players p ON sw.player_id = p.id
        ORDER BY sw.ROWID DESC LIMIT 5;
        """)
        recent_winners = cursor.fetchall()
        
        if recent_winners:
            logger.info("Recent weekly winners:")
            for name, week, score in recent_winners:
                logger.info(f"  {name} won for week of {week} with score {score}")
        else:
            logger.warning("No weekly winners found in season_winners table")
        
        return True
    except sqlite3.Error as e:
        logger.error(f"Error checking season winners: {e}")
        return False

def calculate_wordle_number():
    """Calculate today's Wordle number based on the start date"""
    # Wordle #1 was on June 19, 2021
    start_date = datetime(2021, 6, 19).date()
    today = datetime.now().date()
    
    # Calculate the difference in days
    days_since_start = (today - start_date).days
    
    return days_since_start + 1  # +1 because Wordle #1 was on day 0

def check_reset_functions():
    """Check for the presence of reset functions in key Python files"""
    reset_functions = {
        "integrated_auto_update_multi_league.py": ["check_for_daily_reset", "reset_weekly_stats"],
        "update_correct_structure.py": ["get_player_weekly_wins", "rebuild_stats_tab"]
    }
    
    for filename, functions in reset_functions.items():
        filepath = os.path.join(os.getcwd(), filename)
        if not os.path.exists(filepath):
            logger.warning(f"File not found: {filepath}")
            continue
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for function in functions:
            if f"def {function}" in content:
                logger.info(f"✓ Function found in {filename}: {function}")
            else:
                logger.warning(f"✗ Function missing in {filename}: {function}")

def main():
    """Main function to check reset status"""
    print("\n===== WORDLE LEAGUE RESET STATUS CHECK =====")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current weekday: {datetime.now().strftime('%A')}")
    print(f"Calculated Wordle number: #{calculate_wordle_number()}")
    print("===========================================\n")
    
    # Try both potential database files
    db_files = ["wordle_league.db", "wordle_scores.db"]
    
    for db_file in db_files:
        if check_database_exists(db_file):
            try:
                conn = sqlite3.connect(db_file)
                conn.row_factory = sqlite3.Row  # This allows accessing columns by name
                
                print(f"\n----- Database: {db_file} -----")
                
                # Check tables
                check_db_tables(conn)
                
                # Check settings
                print("\n-- Settings Table --")
                check_settings_table(conn)
                
                # Check latest scores
                print("\n-- Latest Scores Table --")
                check_latest_scores(conn)
                
                # Check season winners
                print("\n-- Season Winners Table --")
                check_season_winners(conn)
                
                conn.close()
            except sqlite3.Error as e:
                logger.error(f"Database error with {db_file}: {e}")
    
    # Check reset functions
    print("\n-- Reset Functions in Python Files --")
    check_reset_functions()
    
    print("\n===== CHECK COMPLETE =====")

if __name__ == "__main__":
    main()
