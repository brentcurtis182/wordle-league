import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_extraction.log"),
        logging.StreamHandler()
    ]
)

def check_database():
    """Check current state of the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, get player IDs
        cursor.execute("SELECT id, name FROM player")
        players = {row['name']: row['id'] for row in cursor.fetchall()}
        logging.info(f"Found players: {list(players.keys())}")
        
        # Check for today's scores (Wordle #1500)
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.wordle_number = 1500
        """)
        scores = cursor.fetchall()
        
        if scores:
            logging.info(f"Found {len(scores)} scores for Wordle #1500:")
            for score in scores:
                emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
                logging.info(f"  {score['name']}: {score['score']}/6 with {emoji_rows} rows of emoji")
        else:
            logging.info("No scores found for Wordle #1500")
            
        # Check specifically for Joanna's score
        if 'Joanna' in players:
            cursor.execute("""
                SELECT s.id, s.score, s.emoji_pattern, s.date
                FROM score s
                WHERE s.player_id = ? AND s.wordle_number = 1500
            """, (players['Joanna'],))
            joanna_score = cursor.fetchone()
            
            if joanna_score:
                logging.info(f"Joanna's score for #1500: {joanna_score['score']}/6")
                logging.info(f"Date: {joanna_score['date']}")
                if joanna_score['emoji_pattern']:
                    logging.info(f"Emoji pattern: {joanna_score['emoji_pattern']}")
                    logging.info(f"Pattern has {joanna_score['emoji_pattern'].count('\n') + 1} rows")
                
                # Delete Joanna's incorrect score
                logging.info("Deleting Joanna's incorrect score for Wordle #1500")
                cursor.execute("DELETE FROM score WHERE id = ?", (joanna_score['id'],))
                conn.commit()
                logging.info("Deleted Joanna's score")
        
        # Check specifically for Malia's score
        if 'Malia' in players:
            cursor.execute("""
                SELECT s.id, s.score, s.emoji_pattern, s.date
                FROM score s
                WHERE s.player_id = ? AND s.wordle_number = 1500
            """, (players['Malia'],))
            malia_score = cursor.fetchone()
            
            if malia_score:
                logging.info(f"Malia already has a score for #1500: {malia_score['score']}/6")
                if malia_score['emoji_pattern']:
                    logging.info(f"Pattern has {malia_score['emoji_pattern'].count('\n') + 1} rows")
            else:
                # Malia's emoji pattern for Wordle #1500
                emoji_pattern = """🟨⬛⬛⬛⬛
⬛⬛🟨⬛⬛
⬛🟩⬛⬛🟨
⬛🟩🟨⬛🟩
🟩🟩⬛⬛🟩
🟩🟩⬛⬛🟩"""

                # Add Malia's score
                today = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                
                cursor.execute(
                    "INSERT INTO score (player_id, score, wordle_number, date, created_at, emoji_pattern) VALUES (?, 7, 1500, ?, ?, ?)",
                    (players['Malia'], today, current_time, emoji_pattern)
                )
                conn.commit()
                logging.info("Added Malia's score for Wordle #1500")
        
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return False

def update_website():
    """Run export_leaderboard.py to update website files"""
    try:
        import subprocess
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error running website export: {e}")
        return False

def push_to_github():
    """Run force_update.py to push changes to GitHub"""
    try:
        import subprocess
        logging.info("Running force_update.py...")
        result = subprocess.run(["python", "force_update.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("GitHub push successful")
            return True
        else:
            logging.error(f"GitHub push failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting database fix for Wordle #1500 scores")
    
    # Step 1: Check and fix the database
    if check_database():
        # Step 2: Update the website files
        if update_website():
            # Step 3: Push to GitHub
            if push_to_github():
                logging.info("All steps completed successfully")
            else:
                logging.error("Failed to push to GitHub")
        else:
            logging.error("Failed to update website")
    else:
        logging.error("Database check/fix failed")
