import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def verify_scores():
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check for Wordle #1500 scores
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE s.wordle_number = 1500
        """)
        scores = cursor.fetchall()
        
        print("\n===== SCORES FOR WORDLE #1500 =====")
        if scores:
            print(f"Found {len(scores)} scores:")
            for score in scores:
                emoji_rows = score['emoji_pattern'].count('\n') + 1 if score['emoji_pattern'] else 0
                score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
                print(f"  {score['name']}: {score_display} with {emoji_rows} rows of emoji")
        else:
            print("No scores found for Wordle #1500")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_scores()
