import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("manual_score_add.log"),
        logging.StreamHandler()
    ]
)

# Get database path
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')

# Malia's emoji pattern for Wordle #1500
emoji_pattern = """🟨⬛⬛⬛⬛
⬛⬛🟨⬛⬛
⬛🟩⬛⬛🟨
⬛🟩🟨⬛🟩
🟩🟩⬛⬛🟩
🟩🟩⬛⬛🟩"""

def add_malia_score():
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get Malia's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Malia'")
        player_id_result = cursor.fetchone()
        
        if not player_id_result:
            logging.error("Could not find Malia in the player table")
            return False
            
        player_id = player_id_result[0]
        logging.info(f"Found Malia with player_id: {player_id}")
        
        # Check if score already exists for Wordle #1500
        cursor.execute(
            "SELECT id, score FROM score WHERE player_id = ? AND wordle_number = 1500",
            (player_id,)
        )
        existing_score = cursor.fetchone()
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        
        if existing_score:
            score_id = existing_score[0]
            logging.info(f"Found existing score (id: {score_id}, score: {existing_score[1]}) for Wordle #1500")
            
            # Update the existing score to X/6 (score value 7) with the emoji pattern
            cursor.execute(
                "UPDATE score SET score = 7, emoji_pattern = ?, date = ? WHERE id = ?",
                (emoji_pattern, today, score_id)
            )
            logging.info(f"Updated score for Wordle #1500 to X/6 with emoji pattern")
        else:
            # Add a new score for Wordle #1500
            cursor.execute(
                "INSERT INTO score (player_id, score, wordle_number, date, created_at, emoji_pattern) VALUES (?, 7, 1500, ?, ?, ?)",
                (player_id, today, current_time, emoji_pattern)
            )
            logging.info(f"Added new score for Wordle #1500: X/6 with emoji pattern")
        
        # Commit changes
        conn.commit()
        logging.info("Changes committed to database")
        
        # Close connection
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error adding Malia's score: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting manual score addition for Malia")
    if add_malia_score():
        logging.info("Successfully added Malia's score")
        
        # Run export_leaderboard.py to update the website
        logging.info("Running website export to update files")
        import subprocess
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            
            # Run force_update.py to push to GitHub
            logging.info("Running force update to push changes to GitHub")
            try:
                from force_update import force_update
                if force_update():
                    logging.info("Successfully pushed changes to GitHub")
                else:
                    logging.error("Failed to push changes to GitHub")
            except Exception as e:
                logging.error(f"Error running force update: {e}")
        else:
            logging.error(f"Website export failed: {result.stderr}")
    else:
        logging.error("Failed to add Malia's score")
