import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nanna_score_fix.log"),
        logging.StreamHandler()
    ]
)

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

# Nanna's emoji pattern for Wordle #1500
emoji_pattern = """⬜🟩⬜⬜🟩
⬜🟩⬜⬜🟩
⬜🟩⬜⬜🟩
⬜🟩🟨⬜🟩
🟩🟩⬜⬜🟩
🟩🟩🟩🟩🟩"""

def fix_scores():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First, get player IDs
        cursor.execute("SELECT id, name FROM player")
        players = {row['name']: row['id'] for row in cursor.fetchall()}
        logging.info(f"Found players: {list(players.keys())}")
        
        # Check for today's scores (Wordle #1500)
        cursor.execute("""
            SELECT p.name, s.id, s.score, s.emoji_pattern 
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
                
                # Check for Joanna's incorrect score
                if score['name'] == 'Joanna':
                    logging.info(f"Deleting Joanna's incorrect score for Wordle #1500")
                    cursor.execute("DELETE FROM score WHERE id = ?", (score['id'],))
                    conn.commit()
                    logging.info("Deleted Joanna's score")
        
        # Add Nanna's score if not already present
        if 'Nanna' in players:
            cursor.execute("""
                SELECT s.id, s.score, s.emoji_pattern
                FROM score s
                WHERE s.player_id = ? AND s.wordle_number = 1500
            """, (players['Nanna'],))
            nanna_score = cursor.fetchone()
            
            if nanna_score:
                logging.info(f"Nanna already has a score for #1500: {nanna_score['score']}/6")
                if nanna_score['emoji_pattern']:
                    logging.info(f"Pattern has {nanna_score['emoji_pattern'].count('\n') + 1} rows")
            else:
                # Add Nanna's score
                today = datetime.now().strftime('%Y-%m-%d')
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
                
                cursor.execute(
                    "INSERT INTO score (player_id, score, wordle_number, date, created_at, emoji_pattern) VALUES (?, 6, 1500, ?, ?, ?)",
                    (players['Nanna'], today, current_time, emoji_pattern)
                )
                conn.commit()
                logging.info("Added Nanna's score for Wordle #1500: 6/6")
        else:
            logging.error("Could not find Nanna in the player table")
        
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return False

def update_website_and_push():
    try:
        import subprocess
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            
            logging.info("Running force_update.py...")
            force_result = subprocess.run(["python", "force_update.py"], capture_output=True, text=True)
            
            if force_result.returncode == 0:
                logging.info("Force update successful")
                return True
            else:
                logging.error(f"Force update failed: {force_result.stderr}")
                return False
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Error in update_website_and_push: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting fix for Wordle #1500 scores")
    
    if fix_scores():
        logging.info("Successfully fixed scores in database")
        
        if update_website_and_push():
            logging.info("Successfully updated website and pushed to GitHub")
        else:
            logging.error("Failed to update website or push to GitHub")
    else:
        logging.error("Failed to fix scores")
