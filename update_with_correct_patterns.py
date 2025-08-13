import os
import sys
import sqlite3
import shutil
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# The correct patterns we extracted from the HTML files
WORDLE_1500_PATTERNS = {
    'Joanna': '🟩⬛🟨⬛⬛\n⬛⬛⬛⬛⬛\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩🟩🟩🟩',
    'Brent': '🟩⬛⬛⬛⬛\n🟩⬛🟨⬛⬛\n🟩🟩⬛⬛⬛\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩🟩🟩🟩',
    'Evan': '⬛⬛⬛⬛🟨\n🟩⬛🟨⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩',
    'Malia': '🟨⬛⬛⬛⬛\n⬛⬛🟨⬛⬛\n⬛🟩⬛⬛🟨\n⬛🟩🟨⬛🟩\n🟩🟩⬛⬛🟩\n🟩🟩⬛⬛🟩',
    'Nanna': '⬜🟩⬜⬜🟩\n⬜🟩⬜⬜🟩\n⬜🟩⬜⬜🟩\n⬜🟩🟨⬜🟩\n🟩🟩⬜⬜🟩\n🟩🟩🟩🟩🟩'
}

# Corresponding scores (numeric value)
WORDLE_1500_SCORES = {
    'Joanna': 5,  # 5/6
    'Brent': 6,   # 6/6
    'Evan': 7,    # X/6 (represented as 7)
    'Malia': 7,   # X/6 (represented as 7)
    'Nanna': 6    # 6/6
}

def backup_database():
    """Create a backup of the database before making changes"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"wordle_league_{timestamp}.db.bak"
        
        # Copy the database file
        shutil.copy2('wordle_league.db', backup_file)
        logging.info(f"Database backup created: {backup_file}")
        return True
    except Exception as e:
        logging.error(f"Error creating database backup: {e}")
        return False

def update_database_tables():
    """Update both database tables with the correct patterns"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get player IDs
        cursor.execute("SELECT id, name FROM player")
        player_ids = {row['name']: row['id'] for row in cursor.fetchall()}
        
        updates_made = 0
        
        # Update both tables for each player
        for player_name, pattern in WORDLE_1500_PATTERNS.items():
            if player_name not in player_ids:
                logging.warning(f"Player {player_name} not found in database")
                continue
                
            player_id = player_ids[player_name]
            score_value = WORDLE_1500_SCORES[player_name]
            
            # Update 'score' table
            cursor.execute(
                "UPDATE score SET score = ?, emoji_pattern = ? WHERE player_id = ? AND wordle_number = 1500",
                (score_value, pattern, player_id)
            )
            score_updates = cursor.rowcount
            
            # Update 'scores' table
            cursor.execute(
                "UPDATE scores SET score = ?, emoji_pattern = ? WHERE player_name = ? AND wordle_num = 1500",
                (score_value, pattern, player_name)
            )
            scores_updates = cursor.rowcount
            
            logging.info(f"Updated {player_name}: {score_updates} rows in 'score' table, {scores_updates} rows in 'scores' table")
            updates_made += score_updates + scores_updates
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logging.info(f"Total updates made: {updates_made}")
        return updates_made > 0
    except Exception as e:
        logging.error(f"Error updating database: {e}")
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
            commit_msg = "Update Wordle 1500 with correct emoji patterns"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            
            # Push changes
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            logging.info("Changes pushed to GitHub successfully")
            return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting update process with correct patterns")
    
    # Step 1: Backup database
    if not backup_database():
        if input("Database backup failed. Continue anyway? (y/n): ").lower() != 'y':
            logging.info("Update aborted by user")
            return
    
    # Step 2: Update database tables
    update_success = update_database_tables()
    if not update_success:
        logging.error("Database update failed")
        return
    
    # Step 3: Export website
    export_success = export_website()
    if not export_success:
        if input("Website export failed. Continue to GitHub push anyway? (y/n): ").lower() != 'y':
            logging.info("GitHub push aborted by user")
            return
    
    # Step 4: Push to GitHub
    push_success = push_to_github()
    if push_success:
        logging.info("Update process completed successfully!")
    else:
        logging.error("Failed to push changes to GitHub")

if __name__ == "__main__":
    main()
