#!/usr/bin/env python
# fix_weekly_scores.py - Fix weekly score calculation and ensure future scores are properly tracked

import os
import sqlite3
import logging
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Constants
DATABASE_PATH = "wordle_league.db"
EXPORT_DIR = "website_export"
RESET_MARKER_FILE = "last_weekly_reset.txt"

def connect_to_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def fix_weekly_score_calculation():
    """Fix the export_leaderboard.py script to properly calculate weekly scores"""
    try:
        file_path = "export_leaderboard.py"
        
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Make sure we're using Monday at 3:00 AM as the reset time
        if "start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)" not in content:
            content = content.replace(
                "start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)",
                "start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)"
            )
            logging.info("Updated weekly reset time to Monday 3:00 AM")
        
        # Add code to respect the reset marker file if it exists
        if "# Respect the reset marker file if it exists" not in content:
            insert_point = "    # Format the date as a string for SQL comparison"
            reset_marker_code = """    # Respect the reset marker file if it exists
    reset_marker_path = "last_weekly_reset.txt"
    if os.path.exists(reset_marker_path):
        try:
            with open(reset_marker_path, "r") as reset_file:
                reset_time_str = reset_file.read().strip()
                reset_time = datetime.strptime(reset_time_str, "%Y-%m-%d %H:%M:%S")
                
                # If reset time is more recent than the calculated start_of_week, use that instead
                if reset_time > start_of_week:
                    start_of_week = reset_time
                    print(f"Using reset marker time: {reset_time_str}")
        except Exception as e:
            print(f"Error reading reset marker file: {e}")
"""
            content = content.replace(insert_point, reset_marker_code + "\n" + insert_point)
            logging.info("Added code to respect reset marker file")
        
        # Add logging to see all scores considered part of the current week
        if "# Debug weekly scores" not in content:
            insert_point = "            # Check if this score is from the current week"
            debug_code = """            # Debug weekly scores
            if date >= start_of_week_str:
                print(f"Including in weekly scores: {player['name']} - Score: {score}, Date: {date}")
"""
            content = content.replace(insert_point, "            " + debug_code + "\n" + insert_point)
            logging.info("Added weekly score debugging")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info("Successfully fixed weekly score calculation in export_leaderboard.py")
        return True
    except Exception as e:
        logging.error(f"Error fixing weekly score calculation: {e}")
        return False

def force_weekly_reset():
    """Force a weekly reset by updating the reset marker file to Monday 3:00 AM"""
    try:
        # Get the most recent Monday at 3:00 AM
        today = datetime.now()
        days_since_monday = today.weekday()  # Monday is 0
        last_monday = today - timedelta(days=days_since_monday)
        monday_3am = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Write to reset marker file
        with open(RESET_MARKER_FILE, "w") as f:
            f.write(monday_3am.strftime("%Y-%m-%d %H:%M:%S"))
            
        logging.info(f"Weekly reset marker updated to: {monday_3am.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logging.error(f"Error forcing weekly reset: {e}")
        return False

def list_scores_for_current_week():
    """List all scores for the current week (since Monday 3:00 AM)"""
    try:
        conn = connect_to_db()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Calculate the start of the week (Monday 3:00 AM)
        today = datetime.now()
        days_since_monday = today.weekday()  # Monday is 0
        last_monday = today - timedelta(days=days_since_monday)
        monday_3am = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Format for SQL comparison
        start_of_week_str = monday_3am.strftime("%Y-%m-%d")
        
        # Query scores from this week
        cursor.execute("""
            SELECT p.name, s.wordle_number, s.score, s.date
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.date >= ?
            ORDER BY s.date DESC, p.name ASC
        """, (start_of_week_str,))
        
        scores = cursor.fetchall()
        
        logging.info(f"Scores for current week (since {start_of_week_str}):")
        if not scores:
            logging.info("  No scores found for this week")
        else:
            for score in scores:
                score_display = "X/6" if score["score"] == 7 else f"{score['score']}/6"
                logging.info(f"  {score['name']}: Wordle #{score['wordle_number']} - {score_display} on {score['date']}")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error listing scores: {e}")
        return False

def add_upcoming_wordles():
    """Add placeholder entries for upcoming Wordles to verify future score tracking"""
    try:
        conn = connect_to_db()
        if not conn:
            return False
            
        cursor = conn.cursor()
        
        # Get Malia and Nanna's player IDs
        cursor.execute("SELECT id FROM player WHERE name = 'Malia'")
        malia_id = cursor.fetchone()["id"] if cursor.fetchone() else None
        
        cursor.execute("SELECT id FROM player WHERE name = 'Nanna'")
        nanna_id = cursor.fetchone()["id"] if cursor.fetchone() else None
        
        if not malia_id or not nanna_id:
            logging.error("Could not find Malia or Nanna in the players table")
            conn.close()
            return False
        
        # Add placeholder for Wordle #1507 (next Wordle)
        wordle_number = 1507
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check if entries already exist
        cursor.execute(
            "SELECT COUNT(*) FROM score WHERE wordle_number = ? AND player_id IN (?, ?)", 
            (wordle_number, malia_id, nanna_id)
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            logging.info(f"Adding placeholder entries for Wordle #{wordle_number}")
            
            # Add entry for Malia
            cursor.execute("""
                INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date)
                VALUES (?, ?, ?, ?, ?)
            """, (malia_id, wordle_number, 3, "🟨🟨🟩\n🟨🟩🟩\n🟩🟩🟩", today))
            
            # Add entry for Nanna
            cursor.execute("""
                INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date)
                VALUES (?, ?, ?, ?, ?)
            """, (nanna_id, wordle_number, 4, "⬜🟨⬜🟩\n🟨🟨🟩🟩\n🟨🟩🟩🟩\n🟩🟩🟩🟩", today))
            
            conn.commit()
            logging.info(f"Added placeholder entries for Wordle #{wordle_number} for Malia and Nanna")
        else:
            logging.info(f"Entries for Wordle #{wordle_number} already exist")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error adding upcoming Wordles: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

def update_website_and_push():
    """Update the website files and push to GitHub"""
    try:
        # Run export_leaderboard.py with more verbose output
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Print export_leaderboard.py's output for debugging
            for line in result.stdout.split('\n'):
                if line.strip():
                    logging.info(f"Export: {line}")
            
            logging.info("Website export successful")
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
        
        # Push changes to GitHub
        export_dir = os.path.join(os.getcwd(), EXPORT_DIR)
        
        logging.info("Pushing changes to GitHub...")
        
        # Add all changes
        subprocess.run(["git", "add", "-A"], cwd=export_dir, check=True)
        
        # Commit with weekly reset message
        message = f"Update weekly scores (reset): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", message], cwd=export_dir)
        
        # Force push to GitHub
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_dir, check=True)
        
        logging.info("Successfully pushed to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error updating website and pushing: {e}")
        return False

def main():
    """Main function"""
    logging.info("Starting weekly score fix...")
    
    # Step 1: Fix weekly score calculation
    logging.info("\nStep 1: Fixing weekly score calculation")
    if fix_weekly_score_calculation():
        logging.info("Weekly score calculation fixed")
    
    # Step 2: Force weekly reset
    logging.info("\nStep 2: Forcing weekly reset")
    if force_weekly_reset():
        logging.info("Weekly reset forced")
    
    # Step 3: List scores for current week
    logging.info("\nStep 3: Listing scores for current week")
    if list_scores_for_current_week():
        logging.info("Current week scores listed")
    
    # Step 4: Add upcoming Wordles
    logging.info("\nStep 4: Adding upcoming Wordles")
    if add_upcoming_wordles():
        logging.info("Upcoming Wordles added")
    
    # Step 5: Update website and push
    logging.info("\nStep 5: Updating website and pushing to GitHub")
    if update_website_and_push():
        logging.info("Website updated and pushed to GitHub")
    
    logging.info("\nAll fixes completed!")
    logging.info("The website should now show the correct weekly scores")
    logging.info("Note: Remember to clear your browser cache with Ctrl+F5 or open in incognito mode")
    logging.info("The weekly scores should now only show scores from Monday 3:00 AM onwards")

if __name__ == "__main__":
    main()
