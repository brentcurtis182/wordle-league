import sqlite3
import logging
import os
import sys
import subprocess
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def backup_database():
    """Create a backup of the database before cleaning"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"wordle_league_cleanup_{timestamp}.db.bak"
        
        # Copy the database file
        import shutil
        shutil.copy2('wordle_league.db', backup_file)
        logging.info(f"Database backup created: {backup_file}")
        return True
    except Exception as e:
        logging.error(f"Error creating database backup: {e}")
        return False

def cleanup_old_wordle_scores():
    """Remove all scores except Wordle #1500"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Keep only Wordle #1500 in score table
        cursor.execute("DELETE FROM score WHERE wordle_number != 1500")
        score_deleted = cursor.rowcount
        logging.info(f"Deleted {score_deleted} non-1500 scores from score table")
        
        # Keep only Wordle #1500 in scores table
        cursor.execute("DELETE FROM scores WHERE wordle_num != 1500")
        scores_deleted = cursor.rowcount
        logging.info(f"Deleted {scores_deleted} non-1500 scores from scores table")
        
        # Remove any unknown player scores for 1500
        cursor.execute("DELETE FROM score WHERE player_id NOT IN (SELECT id FROM player WHERE name IN ('Brent', 'Evan', 'Joanna', 'Malia', 'Nanna')) AND wordle_number = 1500")
        unknown_deleted = cursor.rowcount
        logging.info(f"Deleted {unknown_deleted} unknown player scores from score table")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logging.info("Database cleaned - only Wordle #1500 scores remain")
        return True
    except Exception as e:
        logging.error(f"Error cleaning database: {e}")
        return False

def export_website():
    """Export the website with updated data"""
    try:
        logging.info("Exporting website...")
        export_script = "export_leaderboard.py"
        
        if os.path.exists(export_script):
            subprocess.run([sys.executable, export_script], check=True)
            logging.info("Website exported successfully")
            return True
        else:
            logging.error(f"Export script {export_script} not found")
            return False
    except Exception as e:
        logging.error(f"Error exporting website: {e}")
        return False

def push_to_github():
    """Push changes to GitHub Pages"""
    try:
        logging.info("Pushing changes to GitHub...")
        
        # Use the existing enhanced_functions module if available
        try:
            from enhanced_functions import push_to_github as push_function
            result = push_function()
            return result
        except ImportError:
            # Fallback to direct git commands
            website_dir = "website_export"
            if not os.path.isdir(website_dir):
                logging.error(f"Website directory {website_dir} not found")
                return False
                
            # Change to website directory
            os.chdir(website_dir)
            
            # Add changes
            subprocess.run(["git", "add", "."], check=True)
            
            # Commit changes
            commit_msg = "Cleanup - keep only Wordle 1500 scores"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            # Push changes
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            logging.info("Changes pushed to GitHub successfully")
            return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting database cleanup to keep only Wordle #1500 scores")
    
    # Step 1: Backup the database
    if not backup_database():
        logging.error("Failed to create database backup, aborting")
        return
    
    # Step 2: Clean up the database
    if not cleanup_old_wordle_scores():
        logging.error("Failed to clean up database, aborting")
        return
    
    # Step 3: Export website
    if not export_website():
        logging.error("Failed to export website")
        return
    
    # Step 4: Push to GitHub
    if not push_to_github():
        logging.error("Failed to push to GitHub")
        return
    
    logging.info("All operations completed successfully")

if __name__ == "__main__":
    main()
