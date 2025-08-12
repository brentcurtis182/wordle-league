import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("final_cleanup_scores.log"),
        logging.StreamHandler()
    ]
)

def cleanup_database():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get player IDs for Malia and Nanna
        cursor.execute("SELECT id FROM player WHERE name = 'Malia'")
        malia_id = cursor.fetchone()['id']
        logging.info(f"Malia's player ID: {malia_id}")
        
        cursor.execute("SELECT id FROM player WHERE name = 'Nanna'")
        nanna_id = cursor.fetchone()['id']
        logging.info(f"Nanna's player ID: {nanna_id}")
        
        # Delete all scores for Wordle #1500 except Malia and Nanna's
        cursor.execute(
            "DELETE FROM score WHERE wordle_number = 1500 AND player_id NOT IN (?, ?)",
            (malia_id, nanna_id)
        )
        deleted_count = cursor.rowcount
        logging.info(f"Deleted {deleted_count} incorrect scores for Wordle #1500")
        
        # Double check that Malia's score is still X/6 (score=7)
        cursor.execute(
            "SELECT score FROM score WHERE wordle_number = 1500 AND player_id = ?",
            (malia_id,)
        )
        malia_score = cursor.fetchone()
        if malia_score and malia_score['score'] != 7:
            logging.info(f"Fixing Malia's score from {malia_score['score']} to 7 (X/6)")
            cursor.execute(
                "UPDATE score SET score = 7 WHERE wordle_number = 1500 AND player_id = ?",
                (malia_id,)
            )
        
        # Double check that Nanna's score is 6/6
        cursor.execute(
            "SELECT score FROM score WHERE wordle_number = 1500 AND player_id = ?",
            (nanna_id,)
        )
        nanna_score = cursor.fetchone()
        if nanna_score and nanna_score['score'] != 6:
            logging.info(f"Fixing Nanna's score from {nanna_score['score']} to 6 (6/6)")
            cursor.execute(
                "UPDATE score SET score = 6 WHERE wordle_number = 1500 AND player_id = ?",
                (nanna_id,)
            )
        
        # Commit changes
        conn.commit()
        logging.info("Database cleanup committed")
        
        # Get final count of scores for Wordle #1500
        cursor.execute(
            "SELECT p.name, s.score FROM score s JOIN player p ON s.player_id = p.id WHERE s.wordle_number = 1500"
        )
        final_scores = cursor.fetchall()
        logging.info(f"Final count of scores for Wordle #1500: {len(final_scores)}")
        for score in final_scores:
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display}")
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error during database cleanup: {e}")
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
    logging.info("Starting final cleanup of Wordle #1500 scores")
    
    if cleanup_database():
        logging.info("Database cleanup successful")
        
        if update_website_and_push():
            logging.info("Website update and GitHub push successful")
        else:
            logging.error("Failed to update website or push to GitHub")
    else:
        logging.error("Database cleanup failed")
