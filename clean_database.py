import sqlite3
import os
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("database_clean.log")
    ]
)

def backup_database():
    """Create a backup of the database before making changes"""
    try:
        # Get timestamp for backup file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"wordle_league_backup_{timestamp}.db"
        
        # Read the database content
        with open("wordle_league.db", "rb") as src:
            data = src.read()
            
        # Write to backup file
        with open(backup_file, "wb") as dest:
            dest.write(data)
            
        logging.info(f"Backup created: {backup_file}")
        return True
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        return False

def clean_scores_table():
    """Clean the scores table by removing all scores"""
    conn = None
    try:
        # Create backup first
        if not backup_database():
            return False
            
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM scores")
        before_count = cursor.fetchone()[0]
        logging.info(f"Before cleaning: {before_count} scores in database")
        
        # Delete all scores
        cursor.execute("DELETE FROM scores")
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT COUNT(*) FROM scores")
        after_count = cursor.fetchone()[0]
        logging.info(f"After cleaning: {after_count} scores in database")
        
        if after_count == 0:
            logging.info("Successfully cleaned scores table")
            return True
        else:
            logging.error("Failed to clean scores table completely")
            return False
            
    except Exception as e:
        logging.error(f"Error cleaning scores table: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main function to execute the cleaning process"""
    print("=== Wordle League Database Cleanup ===")
    print("WARNING: This will delete ALL scores from the database.")
    print("A backup will be created before proceeding.")
    
    response = input("Are you sure you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cleanup canceled.")
        return
        
    success = clean_scores_table()
    if success:
        print("\nDatabase cleaned successfully!")
        print("All scores have been removed from the database.")
        print("New scores will be added as they come in through the extraction process.")
    else:
        print("\nCleaning failed. Check the log file for details.")
        
if __name__ == "__main__":
    main()
