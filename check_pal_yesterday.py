import sqlite3
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def check_pal_scores():
    """Check PAL league scores for yesterday (July 30, 2025)"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Yesterday's date
        yesterday_date = datetime(2025, 7, 30).date()
        yesterday_str = yesterday_date.strftime("%Y-%m-%d")
        
        # Get all PAL league scores for yesterday
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp
        FROM scores
        WHERE league_id = 3 AND date(timestamp) = date(?)
        ORDER BY player_name
        """, (yesterday_str,))
        
        yesterday_scores = cursor.fetchall()
        
        print(f"===== PAL LEAGUE SCORES FOR {yesterday_str} =====")
        if yesterday_scores:
            for player, wordle_num, score, timestamp in yesterday_scores:
                print(f"{player} - Wordle #{wordle_num} - {score}/6 on {timestamp}")
            print(f"\nTotal: {len(yesterday_scores)} scores for {yesterday_str}")
        else:
            print(f"No PAL league scores found for {yesterday_str}!")
        
        # Check if any scores for Wordle #1502 (yesterday's Wordle) in PAL league
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp
        FROM scores
        WHERE league_id = 3 AND (wordle_num = 1502 OR wordle_num = '1,502')
        ORDER BY player_name
        """)
        
        wordle_1502_scores = cursor.fetchall()
        
        print(f"\n===== PAL LEAGUE SCORES FOR WORDLE #1502 =====")
        if wordle_1502_scores:
            for player, wordle_num, score, timestamp in wordle_1502_scores:
                date_str = timestamp.split()[0] if timestamp else "N/A"
                print(f"{player} - Wordle #{wordle_num} - {score}/6 on {date_str}")
            print(f"\nTotal: {len(wordle_1502_scores)} scores for Wordle #1502")
        else:
            print(f"No PAL league scores found for Wordle #1502!")
            
    except Exception as e:
        logging.error(f"Error checking PAL scores: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_pal_scores()
