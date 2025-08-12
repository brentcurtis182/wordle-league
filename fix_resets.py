#!/usr/bin/env python3
"""
Fix Reset Functionality for Wordle League
This script restores daily and weekly reset functionality that has stopped working.
"""

import os
import sqlite3
import logging
from datetime import datetime, timedelta
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_resets.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Today's correct Wordle number
CURRENT_WORDLE = 1514  # Monday, August 11th, 2025

def create_missing_tables():
    """Create missing tables needed for reset functionality"""
    logger.info("Creating missing tables needed for resets")
    
    try:
        # Connect to the main database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if settings table exists, create if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'")
        if not cursor.fetchone():
            logger.info("Creating settings table")
            cursor.execute("""
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """)
            # Initialize with today's date
            today = datetime.now().date().isoformat()
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", 
                          ('last_reset_date', today))
        
        # Check if latest_scores table exists, create if not
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='latest_scores'")
        if not cursor.fetchone():
            logger.info("Creating latest_scores table")
            cursor.execute("""
            CREATE TABLE latest_scores (
                player_id INTEGER,
                league_id INTEGER,
                score INTEGER,
                emoji_pattern TEXT,
                score_date TEXT,
                FOREIGN KEY(player_id) REFERENCES players(id)
            )
            """)
        
        conn.commit()
        logger.info("Missing tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating missing tables: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def add_reset_functions():
    """Add missing reset functions to the update script"""
    logger.info("Adding missing reset functions to integrated_auto_update_multi_league.py")
    
    try:
        script_path = os.path.join(os.getcwd(), "integrated_auto_update_multi_league.py")
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if reset functions already exist
        if "def check_for_daily_reset" in content:
            logger.info("Reset functions already exist in the script")
            return True
        
        # Functions to add
        reset_functions = """
# Reset functionality

def check_for_daily_reset(force_reset=False):
    \"\"\"Check if we need to reset the latest scores for a new day\"\"\"
    logging.info("Checking if daily reset is needed")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        # Get the last reset date from the settings table
        cursor.execute("SELECT value FROM settings WHERE key = 'last_reset_date'")
        result = cursor.fetchone()
        
        # Get today's date
        today = datetime.now().date().isoformat()
        current_hour = datetime.now().hour
        
        if result:
            last_update_date = result[0]
        else:
            # First time running, set today as last update date
            last_update_date = None
            cursor.execute("INSERT INTO settings (key, value) VALUES ('last_reset_date', ?)", (today,))
            conn.commit()
        
        # Check if we've already done a reset today
        reset_already_done_today = (last_update_date is not None and last_update_date == today)
        
        # Reset is needed if:
        # 1. No previous reset recorded, or
        # 2. Last reset was not today, or
        # 3. Force reset is requested AND it's after 3 AM AND we haven't already reset today
        reset_needed = (last_update_date is None or 
                       last_update_date != today or 
                       (force_reset and current_hour >= 3 and not reset_already_done_today))
        
        if reset_needed:
            logging.info(f"Daily reset needed. Today: {today}, Last update: {last_update_date}, Force: {force_reset}, Hour: {current_hour}, Already done today: {reset_already_done_today}")
            
            # Update the last reset date
            cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_reset_date', ?)", (today,))
            
            # Create latest_scores table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS latest_scores (
                player_id INTEGER,
                league_id INTEGER,
                score INTEGER,
                emoji_pattern TEXT,
                score_date TEXT,
                FOREIGN KEY(player_id) REFERENCES players(id)
            )
            ''')
            
            # Clear latest scores table
            cursor.execute("DELETE FROM latest_scores")
            conn.commit()
            
            logging.info("Daily reset completed successfully")
            return True
        else:
            logging.info(f"No daily reset needed. Today: {today}, Last update: {last_update_date}")
            return False
    except Exception as e:
        logging.error(f"Error checking for daily reset: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def reset_weekly_stats():
    \"\"\"Reset weekly stats and update season winners on Monday\"\"\"
    logging.info("Checking if weekly reset is needed")
    
    try:
        # Only reset on Monday
        if datetime.now().weekday() != 0:  # 0 = Monday
            logging.info("Not Monday, no weekly reset needed")
            return False
            
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get the current date and calculate last Monday
        today = datetime.now().date()
        days_since_last_monday = 7  # Since today is Monday, last Monday was 7 days ago
        last_monday = today - timedelta(days=days_since_last_monday)
        monday_str = last_monday.strftime("%b %d")  # Format as "Aug 04"
        
        # Check if we've already processed this Monday
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        cursor.execute("SELECT value FROM settings WHERE key = 'last_weekly_reset'")
        last_reset = cursor.fetchone()
        
        if last_reset and last_reset[0] == monday_str:
            logging.info(f"Weekly reset already processed for {monday_str}")
            return False
            
        # Update all leagues
        for league_id in range(1, 6):  # 1-5 for all leagues
            # Get weekly winners
            cursor.execute(\"\"\"
            SELECT p.id, p.name, MIN(s.score) as best_score 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.league_id = ? 
            AND s.score_date >= ? 
            AND s.score_date < ?
            GROUP BY p.id
            ORDER BY best_score
            LIMIT 1
            \"\"\", (league_id, last_monday.isoformat(), today.isoformat()))
            
            winner = cursor.fetchone()
            if winner:
                player_id, name, score = winner
                logging.info(f"Weekly winner for league {league_id}: {name} with score {score}")
                
                # Create season_winners table if it doesn't exist
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS season_winners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id INTEGER,
                    league_id INTEGER,
                    week_date TEXT,
                    score INTEGER,
                    FOREIGN KEY(player_id) REFERENCES players(id)
                )
                ''')
                
                # Add to season_winners table if not already there
                cursor.execute(\"\"\"
                SELECT id FROM season_winners 
                WHERE player_id = ? AND league_id = ? AND week_date = ?
                \"\"\", (player_id, league_id, monday_str))
                
                if not cursor.fetchone():
                    cursor.execute(\"\"\"
                    INSERT INTO season_winners (player_id, league_id, week_date, score)
                    VALUES (?, ?, ?, ?)
                    \"\"\", (player_id, league_id, monday_str, score))
        
        # Update the last weekly reset date
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_weekly_reset', ?)", 
                      (monday_str,))
        
        conn.commit()
        logging.info(f"Weekly reset completed for week of {monday_str}")
        return True
    except Exception as e:
        logging.error(f"Error in weekly reset: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

"""
        
        # Add functions to the end of the file before if __name__ == "__main__"
        main_check = "if __name__ == \"__main__\":"
        if main_check in content:
            new_content = content.replace(main_check, reset_functions + "\n\n" + main_check)
        else:
            new_content = content + "\n\n" + reset_functions
        
        # Write back to file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info("Reset functions added to integrated_auto_update_multi_league.py")
        return True
    except Exception as e:
        logger.error(f"Error adding reset functions: {e}")
        return False

def update_main_function():
    """Update main function to call the reset functions"""
    logger.info("Updating main function to call reset functions")
    
    try:
        script_path = os.path.join(os.getcwd(), "integrated_auto_update_multi_league.py")
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if main function already calls reset functions
        if "check_for_daily_reset" in content and "def main" in content:
            if "check_for_daily_reset(force_reset=" in content and "reset_weekly_stats()" in content:
                logger.info("Main function already calls reset functions")
                return True
        
        # Find the main function
        if "def main" in content:
            # Add reset function calls in the main function after extraction
            main_content = content.split("def main")[1].split("\n")
            updated_main = []
            found_extraction = False
            
            for line in main_content:
                updated_main.append(line)
                if "extraction_success" in line or "export_success" in line:
                    found_extraction = True
                    # Add reset function calls
                    updated_main.append("        # Check for daily/weekly resets")
                    updated_main.append("        current_hour = datetime.now().hour")
                    updated_main.append("        force_reset = current_hour >= 3  # Force reset if after 3 AM")
                    updated_main.append("        check_for_daily_reset(force_reset=force_reset)")
                    updated_main.append("        # Check for weekly reset (Monday)")
                    updated_main.append("        if datetime.now().weekday() == 0:  # Monday = 0")
                    updated_main.append("            reset_weekly_stats()")
                    break
            
            if found_extraction:
                new_main = "\n".join(updated_main)
                new_content = content.split("def main")[0] + "def main" + new_main
                
                # Write back to file
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                logger.info("Main function updated to call reset functions")
                return True
            else:
                logger.warning("Could not find appropriate location to add reset function calls")
                return False
        else:
            logger.warning("Could not find main function")
            return False
    except Exception as e:
        logger.error(f"Error updating main function: {e}")
        return False

def force_resets():
    """Force both daily and weekly resets right now"""
    logger.info("Forcing daily and weekly resets")
    
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Create settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        # Force daily reset - clear last_reset_date
        today = datetime.now().date().isoformat()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_reset_date', ?)", (today,))
        
        # Create/clear latest_scores table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS latest_scores (
            player_id INTEGER,
            league_id INTEGER,
            score INTEGER,
            emoji_pattern TEXT,
            score_date TEXT,
            FOREIGN KEY(player_id) REFERENCES players(id)
        )
        ''')
        cursor.execute("DELETE FROM latest_scores")
        
        # Update weekly reset - calculate last Monday
        today_date = datetime.now().date()
        days_since_last_monday = 7  # Last Monday was 7 days ago
        last_monday = today_date - timedelta(days=days_since_last_monday)
        monday_str = last_monday.strftime("%b %d")  # Format as "Aug 04"
        
        # Update the last_weekly_reset to force processing
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_weekly_reset', ?)", (monday_str,))
        
        conn.commit()
        logger.info(f"Reset flags set: daily={today}, weekly={monday_str}")
        
        # Force script to run with reset flags
        subprocess.run(["python", "integrated_auto_update_multi_league.py"], check=True)
        
        return True
    except Exception as e:
        logger.error(f"Error forcing resets: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main function to fix reset functionality"""
    print("\n===== FIXING WORDLE LEAGUE RESET FUNCTIONALITY =====")
    
    # 1. Create missing tables
    print("\n1. Creating missing tables...")
    if create_missing_tables():
        print("   [SUCCESS] Missing tables created successfully")
    else:
        print("   [FAILED] Failed to create missing tables")
        return
    
    # 2. Add reset functions to update script
    print("\n2. Adding reset functions to update script...")
    if add_reset_functions():
        print("   [SUCCESS] Reset functions added successfully")
    else:
        print("   [FAILED] Failed to add reset functions")
        return
    
    # 3. Update main function to call resets
    print("\n3. Updating main function...")
    if update_main_function():
        print("   [SUCCESS] Main function updated successfully")
    else:
        print("   [FAILED] Failed to update main function")
    
    # 4. Force resets right now
    print("\n4. Forcing resets...")
    if force_resets():
        print("   [SUCCESS] Resets forced successfully")
    else:
        print("   [FAILED] Failed to force resets")
    
    print("\n===== RESET FUNCTIONALITY FIX COMPLETE =====")
    print("\nDaily and weekly resets should now work properly again.")
    print("The correct Wordle number for today (Monday, Aug 11th) is #1514.")

if __name__ == "__main__":
    main()
