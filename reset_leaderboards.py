#!/usr/bin/env python3
# Reset Leaderboards Script
# This script resets the All-Time and Weekly leaderboards, keeping only today's scores

import os
import sqlite3
import logging
from datetime import datetime, timedelta
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Today's Wordle number (August 11, 2025)
CURRENT_WORDLE = 1513

def backup_database():
    """Create a backup of the database before making changes"""
    try:
        db_path = 'wordle_league.db'
        backup_path = f'wordle_league_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}.db'
        
        # Copy the database file
        with open(db_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        
        logging.info(f"Created database backup at {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Error creating database backup: {e}")
        return False

def reset_scores():
    """Reset scores keeping only current week's data"""
    try:
        # Calculate the start of the current week (Monday)
        today = datetime.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute("SELECT COUNT(*) FROM score")
        total_scores = cursor.fetchone()[0]
        
        # Keep only scores from this week's Wordle (1500)
        cursor.execute("""
            DELETE FROM score 
            WHERE wordle_number != ?
        """, (CURRENT_WORDLE,))
        
        deleted_count = total_scores - cursor.fetchone()[0] if cursor.rowcount == -1 else cursor.rowcount
        
        # Commit the changes
        conn.commit()
        conn.close()
        
        logging.info(f"Reset complete. Removed {deleted_count} historical scores.")
        logging.info(f"Kept all scores for Wordle #{CURRENT_WORDLE} (today).")
        
        return True
    except Exception as e:
        logging.error(f"Error resetting scores: {e}")
        return False

def export_and_publish():
    """Run the export and publish scripts to update the website"""
    try:
        # Run the export script
        subprocess.run(["python", "export_leaderboard.py"], check=True)
        logging.info("Successfully exported updated leaderboards")
        
        # Run the git push script
        subprocess.run(["python", "repair_git_and_push.py"], check=True)
        logging.info("Successfully published updated leaderboards to GitHub")
        
        return True
    except Exception as e:
        logging.error(f"Error exporting and publishing: {e}")
        return False

def main():
    print("\n" + "=" * 70)
    print(" WORDLE LEAGUE LEADERBOARD RESET ")
    print("=" * 70)
    
    print("\nThis script will:")
    print("1. Create a backup of the current database")
    print("2. Delete ALL historical scores except for today's (Wordle #1500)")
    print("3. Re-export the leaderboard with only today's scores")
    print("4. Publish the updated leaderboard to GitHub")
    
    # Running automatically without confirmation
    
    # Create a backup first
    print("\nCreating database backup...")
    if not backup_database():
        print("Failed to create backup. Aborting reset.")
        return
    
    # Reset the scores
    print("\nResetting scores...")
    if not reset_scores():
        print("Failed to reset scores. Your database backup can be used to restore.")
        return
    
    # Export and publish
    print("\nExporting and publishing updated leaderboards...")
    if not export_and_publish():
        print("Failed to export or publish. Database has been reset, but website may not be updated.")
        return
    
    print("\n" + "=" * 70)
    print(" RESET COMPLETED SUCCESSFULLY ")
    print("=" * 70)
    print("\nThe leaderboards have been reset with only today's scores.")
    print("The website should update within a few minutes.")
    print("All-Time and Weekly leaderboards now only contain data from today.")
    print("\nYou can check the website at: https://brentcurtis182.github.io/wordle-league/")

if __name__ == "__main__":
    main()
