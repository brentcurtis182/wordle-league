import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("final_cleanup.log"),
        logging.StreamHandler()
    ]
)

def cleanup_scores():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check current scores for Wordle #1500
        cursor.execute("""
            SELECT p.name, s.id, s.score, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.wordle_number = 1500
        """)
        scores = cursor.fetchall()
        
        logging.info(f"Found {len(scores)} scores for Wordle #1500:")
        for score in scores:
            emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display} with {emoji_rows} rows of emoji")
            
            # Keep only Malia and Nanna's scores
            if score['name'] not in ['Malia', 'Nanna']:
                logging.info(f"Deleting incorrect score for {score['name']}")
                cursor.execute("DELETE FROM score WHERE id = ?", (score['id'],))
        
        # Commit changes
        conn.commit()
        logging.info("Database cleanup completed")
        
        # Verify the final state
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.wordle_number = 1500
        """)
        final_scores = cursor.fetchall()
        
        logging.info(f"Final state: {len(final_scores)} scores for Wordle #1500:")
        for score in final_scores:
            emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display} with {emoji_rows} rows of emoji")
            
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
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
    
    if cleanup_scores():
        if update_website_and_push():
            logging.info("Successfully updated website and pushed to GitHub")
        else:
            logging.error("Failed to update website or push to GitHub")
    else:
        logging.error("Failed to clean up scores")
