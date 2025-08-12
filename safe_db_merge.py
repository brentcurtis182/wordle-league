import sqlite3
import os
import shutil
import datetime
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('safe_db_merge.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Source and destination database paths
CURRENT_DB = 'wordle_league.db'  # Our current working database with clean emoji patterns
BACKUP_DB = 'wordle_league_backup_20250801_before_revert.db'  # More complete database with recent scores
OUTPUT_DB = 'wordle_league_merged.db'  # New merged database

def create_backup():
    """Create another backup of our current database"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f'wordle_league_pre_merge_{timestamp}.db'
    
    try:
        shutil.copy2(CURRENT_DB, backup_path)
        logging.info(f"Created backup of current database: {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create backup: {e}")
        return False

def get_clean_emoji_patterns():
    """Get clean emoji patterns from the current database"""
    conn = None
    patterns = {}
    
    try:
        conn = sqlite3.connect(CURRENT_DB)
        cursor = conn.cursor()
        
        # Get emoji patterns from the current database
        cursor.execute("""
            SELECT wordle_num, player_name, emoji_pattern
            FROM scores
            WHERE emoji_pattern IS NOT NULL AND emoji_pattern != ''
        """)
        
        for row in cursor.fetchall():
            wordle_num, player_name, emoji_pattern = row
            key = (wordle_num, player_name)
            patterns[key] = emoji_pattern
            
        logging.info(f"Found {len(patterns)} clean emoji patterns in current database")
        return patterns
    except Exception as e:
        logging.error(f"Error getting clean emoji patterns: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def create_merged_db():
    """Create a new database by copying the complete backup database"""
    try:
        # First make sure the backup exists
        if not os.path.exists(BACKUP_DB):
            logging.error(f"Backup database not found: {BACKUP_DB}")
            return False
            
        # Copy the backup to our new merged database
        shutil.copy2(BACKUP_DB, OUTPUT_DB)
        logging.info(f"Created merged database from backup: {OUTPUT_DB}")
        return True
    except Exception as e:
        logging.error(f"Error creating merged database: {e}")
        return False

def update_emoji_patterns(patterns):
    """Update emoji patterns in the merged database"""
    conn = None
    updated = 0
    
    try:
        conn = sqlite3.connect(OUTPUT_DB)
        cursor = conn.cursor()
        
        # Update each pattern
        for (wordle_num, player_name), emoji_pattern in patterns.items():
            try:
                # Only update main league (league_id=1) patterns to avoid breaking PAL league
                cursor.execute("""
                    UPDATE scores 
                    SET emoji_pattern = ? 
                    WHERE wordle_num = ? AND player_name = ? AND (league_id = 1 OR league_id IS NULL)
                """, (emoji_pattern, wordle_num, player_name))
                
                if cursor.rowcount > 0:
                    updated += 1
            except Exception as e:
                logging.error(f"Error updating pattern for {player_name}, Wordle {wordle_num}: {e}")
        
        # Commit changes
        conn.commit()
        logging.info(f"Updated {updated} emoji patterns in merged database")
        
        return updated
    except Exception as e:
        logging.error(f"Error updating emoji patterns: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def verify_merged_db():
    """Verify the merged database has expected structure and data"""
    conn = None
    try:
        conn = sqlite3.connect(OUTPUT_DB)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = ['player', 'score', 'scores', 'leagues', 'players']
        
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            logging.warning(f"Missing tables in merged database: {', '.join(missing_tables)}")
        
        # Check for recent scores
        cursor.execute("""
            SELECT wordle_num, player_name, score 
            FROM scores 
            WHERE wordle_num >= 1503
            ORDER BY wordle_num
        """)
        recent_scores = cursor.fetchall()
        logging.info(f"Found {len(recent_scores)} scores for Wordle 1503+")
        for row in recent_scores:
            logging.info(f"  Wordle #{row[0]}: {row[1]} - {row[2]}")
            
        # Check emoji patterns
        cursor.execute("""
            SELECT COUNT(*) 
            FROM scores 
            WHERE emoji_pattern IS NOT NULL AND emoji_pattern != ''
        """)
        pattern_count = cursor.fetchone()[0]
        logging.info(f"Found {pattern_count} emoji patterns in merged database")
        
        # All checks passed
        return len(recent_scores) > 0 and pattern_count > 0
    except Exception as e:
        logging.error(f"Error verifying merged database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def update_current_db_symlink():
    """Update the wordle_league.db to point to our merged database"""
    try:
        # First backup the current database again
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        final_backup = f'wordle_league_final_pre_switch_{timestamp}.db'
        shutil.copy2(CURRENT_DB, final_backup)
        logging.info(f"Created final backup before switch: {final_backup}")
        
        # Replace current database with merged database
        os.remove(CURRENT_DB)
        shutil.copy2(OUTPUT_DB, CURRENT_DB)
        logging.info(f"Replaced current database with merged database")
        
        return True
    except Exception as e:
        logging.error(f"Error updating current database: {e}")
        return False

def main():
    logging.info("Starting safe database merge process")
    
    # Step 1: Create another backup of our current database
    if not create_backup():
        logging.error("Failed to create backup, aborting")
        return False
    
    # Step 2: Get clean emoji patterns from current database
    patterns = get_clean_emoji_patterns()
    if not patterns:
        logging.error("Failed to get clean emoji patterns, aborting")
        return False
    
    # Step 3: Create merged database from backup
    if not create_merged_db():
        logging.error("Failed to create merged database, aborting")
        return False
    
    # Step 4: Update emoji patterns in merged database
    updated = update_emoji_patterns(patterns)
    if updated == 0:
        logging.warning("No emoji patterns were updated")
    
    # Step 5: Verify merged database
    if not verify_merged_db():
        logging.error("Failed to verify merged database, aborting final switch")
        logging.info(f"Merged database is available at {OUTPUT_DB} for manual inspection")
        return False
    
    # Display info about the merged database
    print("\nMerged database created and verified successfully.")
    print(f"Merged database is available at: {OUTPUT_DB}")
    print("\nNOTICE: This automated run will NOT replace the current database.")
    print(f"To use the merged database, manually rename {OUTPUT_DB} to {CURRENT_DB}")
    logging.info("Auto-run completed without replacing current database")
    return True
    
    # Step 6: Update current database
    if update_current_db_symlink():
        logging.info("Database merge completed successfully")
        print("\nDatabase merge completed successfully!")
        print(f"The current database ({CURRENT_DB}) has been updated with all scores and clean emoji patterns.")
        return True
    else:
        logging.error("Failed to update current database")
        print(f"\nError updating current database. The merged database is still available at {OUTPUT_DB}.")
        return False

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"An unexpected error occurred: {e}")
        print("Check safe_db_merge.log for details")
