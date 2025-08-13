import os
import sys
import logging
import subprocess
from datetime import datetime

# Import the improved extraction functions
from improved_extraction_fix import validate_database_scores

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run_with_improvements.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def run_main_script():
    """Run the main integrated_auto_update.py script"""
    logging.info("Running integrated_auto_update.py to extract new scores")
    
    try:
        # Run the script and capture output
        result = subprocess.run(
            ["python", "Wordle_League_Codebase/integrated_auto_update.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Main script executed successfully")
            # Log stdout for diagnostics
            logging.info("Main script output:")
            for line in result.stdout.splitlines():
                logging.info(f"  {line}")
            return True
        else:
            logging.error(f"Main script failed with return code {result.returncode}")
            logging.error(f"Error output: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running main script: {e}")
        return False

def run_database_validation():
    """Validate database and clean up any issues"""
    logging.info("Running database validation")
    result = validate_database_scores()
    return result

def update_website():
    """Update the website files"""
    logging.info("Running export_leaderboard.py to update website")
    
    try:
        result = subprocess.run(
            ["python", "export_leaderboard.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error exporting website: {e}")
        return False

def push_to_github():
    """Push website updates to GitHub"""
    logging.info("Running force_update.py to push to GitHub")
    
    try:
        result = subprocess.run(
            ["python", "force_update.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("GitHub push successful")
            return True
        else:
            logging.error(f"GitHub push failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def verify_scores():
    """Verify current scores in database"""
    logging.info("Verifying current scores")
    
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get today's Wordle number (this should match your system's logic)
        today_wordle = 1500  # For July 28, 2025
        
        # Get today's scores
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.wordle_number = ?
        """, (today_wordle,))
        
        scores = cursor.fetchall()
        
        logging.info(f"Found {len(scores)} scores for Wordle #{today_wordle}:")
        for score in scores:
            emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display} with {emoji_rows} rows of emoji")
            
        conn.close()
        return scores
    except Exception as e:
        logging.error(f"Error verifying scores: {e}")
        return []

def main():
    logging.info("Starting improved Wordle League update process")
    
    # Step 1: Run the main script to extract new scores
    main_success = run_main_script()
    
    # Step 2: Validate and clean the database
    db_success = run_database_validation()
    
    # Step 3: Export the website files
    export_success = update_website()
    
    # Step 4: Push to GitHub
    if export_success:
        push_success = push_to_github()
    else:
        push_success = False
        logging.error("Skipped GitHub push due to export failure")
    
    # Log overall status
    if main_success and db_success and export_success and push_success:
        logging.info("All steps completed successfully")
    else:
        logging.warning("Some steps failed - check logs for details")
    
    # Verify the final state of scores
    import sqlite3
    verify_scores()
    
    logging.info("Process completed")

if __name__ == "__main__":
    main()
