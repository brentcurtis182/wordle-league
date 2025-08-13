import sqlite3
import os
import shutil
import subprocess
import logging
import sys
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('database_fix.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Database paths
MERGED_DB = 'wordle_league_merged.db'
MAIN_DB = 'wordle_league.db'

def backup_current_db():
    """Create a backup of the current database before replacing it"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f'wordle_league_original_{timestamp}.db'
    
    try:
        shutil.copy2(MAIN_DB, backup_path)
        logging.info(f"Created backup of current database: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return False

def replace_database():
    """Replace the main database with the merged database"""
    try:
        if os.path.exists(MERGED_DB):
            if os.path.exists(MAIN_DB):
                os.remove(MAIN_DB)
            shutil.copy2(MERGED_DB, MAIN_DB)
            logging.info(f"Replaced {MAIN_DB} with {MERGED_DB}")
            return True
        else:
            logging.error(f"Merged database {MERGED_DB} not found")
            return False
    except Exception as e:
        logging.error(f"Failed to replace database: {e}")
        return False

def remove_duplicate_scores():
    """Remove duplicate scores from the database, keeping only one per player per Wordle number"""
    conn = None
    try:
        conn = sqlite3.connect(MAIN_DB)
        cursor = conn.cursor()
        
        # Find duplicates
        cursor.execute("""
            SELECT wordle_num, player_name, COUNT(*) as count
            FROM scores 
            GROUP BY wordle_num, player_name
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        logging.info(f"Found {len(duplicates)} players with duplicate scores")
        
        # Remove duplicates, keeping only one score per player per Wordle
        for wordle_num, player_name, count in duplicates:
            logging.info(f"Removing {count-1} duplicate scores for {player_name}, Wordle {wordle_num}")
            
            # Get all score IDs for this player and Wordle
            cursor.execute("""
                SELECT id FROM scores 
                WHERE wordle_num = ? AND player_name = ?
                ORDER BY id
            """, (wordle_num, player_name))
            
            # Keep the first one (lowest ID) and delete the rest
            score_ids = [row[0] for row in cursor.fetchall()]
            keep_id = score_ids[0]
            delete_ids = score_ids[1:]
            
            for delete_id in delete_ids:
                cursor.execute("DELETE FROM scores WHERE id = ?", (delete_id,))
                
        # Commit changes
        conn.commit()
        logging.info("Removed all duplicate scores")
        return True
    except Exception as e:
        logging.error(f"Error removing duplicates: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def check_database_structure():
    """Verify database has necessary tables and structure"""
    conn = None
    try:
        conn = sqlite3.connect(MAIN_DB)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        logging.info(f"Database tables: {', '.join(tables)}")
        
        # Check for required tables
        required_tables = ['scores', 'players', 'leagues']
        missing_tables = [t for t in required_tables if t not in tables]
        if missing_tables:
            logging.warning(f"Missing tables: {', '.join(missing_tables)}")
            
        # Check scores table
        cursor.execute("PRAGMA table_info(scores)")
        columns = [row[1] for row in cursor.fetchall()]
        logging.info(f"Scores table columns: {', '.join(columns)}")
        
        return 'scores' in tables
    except Exception as e:
        logging.error(f"Error checking database structure: {e}")
        return False
    finally:
        if conn:
            conn.close()

def run_fix_export_stats():
    """Run the fix_export_stats.py script to update stats"""
    try:
        logging.info("Running fix_export_stats.py")
        result = subprocess.run(['python', 'fix_export_stats.py'], 
                                capture_output=True, text=True, check=True)
        logging.info("fix_export_stats.py completed successfully")
        logging.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"fix_export_stats.py failed: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error running fix_export_stats.py: {e}")
        return False

def run_clean_emoji_patterns():
    """Run the clean_emoji_patterns.py script to clean emoji patterns"""
    try:
        logging.info("Running clean_emoji_patterns.py")
        result = subprocess.run(['python', 'clean_emoji_patterns.py'], 
                                capture_output=True, text=True, check=True)
        logging.info("clean_emoji_patterns.py completed successfully")
        logging.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"clean_emoji_patterns.py failed: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error running clean_emoji_patterns.py: {e}")
        return False

def main():
    logging.info("Starting database finalization process")
    
    # Step 1: Backup current database
    if not backup_current_db():
        logging.error("Failed to backup current database, aborting")
        return False
    
    # Step 2: Replace database with merged version
    if not replace_database():
        logging.error("Failed to replace database, aborting")
        return False
    
    # Step 3: Remove duplicate scores
    if not remove_duplicate_scores():
        logging.warning("Failed to remove duplicate scores, but continuing")
    
    # Step 4: Check database structure
    if not check_database_structure():
        logging.warning("Database structure check failed, but continuing")
    
    # Step 5: Run fix_export_stats.py
    if not run_fix_export_stats():
        logging.error("Failed to run fix_export_stats.py")
        # Continue anyway since we should still clean emoji patterns
    
    # Step 6: Run clean_emoji_patterns.py
    if not run_clean_emoji_patterns():
        logging.error("Failed to run clean_emoji_patterns.py")
    
    logging.info("Database finalization process completed")
    print("\nDatabase finalization process completed!")
    print("Check database_fix.log for details")
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")
        print("Check database_fix.log for details")
