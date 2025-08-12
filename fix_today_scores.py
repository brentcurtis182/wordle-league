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

def fix_wordle_1503_dates():
    """Fix dates for Wordle #1503 - set to July 31, 2025 (today)"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Reference point
        today_date = datetime(2025, 7, 31).date()
        today_str = today_date.strftime("%Y-%m-%d")
        yesterday_date = datetime(2025, 7, 30).date()
        yesterday_str = yesterday_date.strftime("%Y-%m-%d")
        
        # First, see all scores for Wordle #1503
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp, league_id 
        FROM scores 
        WHERE wordle_num = 1503 OR wordle_num = '1,503'
        ORDER BY league_id, player_name
        """)
        
        print("===== CURRENT WORDLE #1503 SCORES =====")
        scores = cursor.fetchall()
        for player, wordle_num, score, timestamp, league_id in scores:
            league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
            date_str = timestamp.split()[0] if timestamp else "N/A"
            print(f"{league_name}: {player} - {score}/6 on {date_str}")
            
        # Special case handling for Vox's score
        cursor.execute("""
        UPDATE scores
        SET timestamp = ?
        WHERE wordle_num IN (1503, '1,503') 
        AND player_name != 'Vox' 
        AND timestamp LIKE ?
        """, (f"{today_str} 12:00:00", f"{yesterday_str}%"))
        
        non_vox_updates = cursor.rowcount
        logging.info(f"Updated {non_vox_updates} non-Vox scores to {today_str}")
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp, league_id 
        FROM scores 
        WHERE wordle_num = 1503 OR wordle_num = '1,503'
        ORDER BY league_id, player_name
        """)
        
        print("\n===== UPDATED WORDLE #1503 SCORES =====")
        scores = cursor.fetchall()
        for player, wordle_num, score, timestamp, league_id in scores:
            league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
            date_str = timestamp.split()[0] if timestamp else "N/A"
            print(f"{league_name}: {player} - {score}/6 on {date_str}")
        
    except Exception as e:
        logging.error(f"Error fixing dates: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_wordle_1503_dates()
