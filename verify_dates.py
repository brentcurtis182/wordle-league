import sqlite3
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def verify_dates():
    """Verify that each Wordle number has the correct date in the database"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check all scores, grouped by Wordle number
        cursor.execute("""
        SELECT wordle_num, MIN(timestamp), MAX(timestamp), COUNT(*)
        FROM scores 
        GROUP BY wordle_num
        ORDER BY wordle_num DESC
        """)
        
        results = cursor.fetchall()
        
        print("\n===== WORDLE NUMBER TO DATE MAPPING =====")
        print(f"{'Wordle #':<10} {'Min Date':<15} {'Max Date':<15} {'Count':<5}")
        print("-" * 45)
        
        for wordle_num, min_date, max_date, count in results:
            # Extract just the date part
            min_date_str = min_date.split()[0] if min_date else "N/A"
            max_date_str = max_date.split()[0] if max_date else "N/A"
            print(f"{wordle_num:<10} {min_date_str:<15} {max_date_str:<15} {count:<5}")
        
        # Specifically check Wordle #1503 (today)
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1503
        ORDER BY league_id, player_name
        """)
        
        today_scores = cursor.fetchall()
        
        print("\n===== WORDLE #1503 (TODAY, July 31, 2025) =====")
        if today_scores:
            for player, wordle_num, score, timestamp, league_id in today_scores:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                date_str = timestamp.split()[0] if timestamp else "N/A"
                print(f"{league_name}: {player} - {score}/6 on {date_str}")
        else:
            print("No scores found for today's Wordle #1503")
        
        # Check yesterday's scores (Wordle #1502)
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1502
        ORDER BY league_id, player_name
        """)
        
        yesterday_scores = cursor.fetchall()
        
        print("\n===== WORDLE #1502 (YESTERDAY, July 30, 2025) =====")
        if yesterday_scores:
            for player, wordle_num, score, timestamp, league_id in yesterday_scores:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                date_str = timestamp.split()[0] if timestamp else "N/A"
                print(f"{league_name}: {player} - {score}/6 on {date_str}")
        else:
            print("No scores found for yesterday's Wordle #1502")
            
    except Exception as e:
        logging.error(f"Error verifying dates: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    verify_dates()
