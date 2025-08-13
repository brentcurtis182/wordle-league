import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def check_database():
    """Check Evan's scores in the database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check Evan's scores
        cursor.execute('SELECT id, player, score, wordle_number, date, emoji_pattern FROM scores WHERE player = ? ORDER BY wordle_number DESC', ('Evan',))
        scores = cursor.fetchall()
        
        logging.info(f"Found {len(scores)} scores for Evan:")
        for score in scores:
            logging.info(f"Wordle #{score[3]}, Score: {score[2]}/6, Date: {score[4]}")
            if score[5]:  # If emoji pattern exists
                pattern_lines = score[5].split('\n') if score[5] else []
                logging.info(f"Emoji pattern has {len(pattern_lines)} lines")
        
        # Check today's scores
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT id, player, score, wordle_number, date FROM scores WHERE date = ? ORDER BY score', (today,))
        today_scores = cursor.fetchall()
        
        logging.info(f"\nFound {len(today_scores)} scores for today ({today}):")
        for score in today_scores:
            logging.info(f"Player: {score[1]}, Wordle #{score[3]}, Score: {score[2]}/6")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database()
