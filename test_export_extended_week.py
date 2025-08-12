import sys
import os
import sqlite3
import logging
import datetime
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('test_export_extended_week.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def adjust_weekly_stats_query():
    """
    Update the scores table to ensure this week's scores (including Monday) are included
    in the weekly stats calculation by extending the date range.
    """
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Define date range to include (go back 8 days to ensure we catch Monday)
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday() + 1)  # Monday of current week, plus one day buffer
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        logging.info(f"Using extended date range starting from: {start_date}")
        
        # Get all scores that should be included in this week's stats
        cursor.execute("""
            SELECT player_name, score, wordle_number, timestamp, date(timestamp) as score_date
            FROM scores
            WHERE timestamp >= ?
            ORDER BY player_name, timestamp
        """, (start_date,))
        
        weekly_scores = cursor.fetchall()
        logging.info(f"Found {len(weekly_scores)} scores in the extended weekly range")
        
        for score in weekly_scores:
            player, score_val, wordle_num, timestamp, date = score
            logging.info(f"Score in extended range: {player} - Wordle {wordle_num} - Score {score_val} - Date {date}")
        
        return len(weekly_scores)
            
    except Exception as e:
        logging.error(f"Error adjusting weekly stats: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def run_export():
    """Run the regular export script after checking the scores"""
    try:
        logging.info("Running export script...")
        # Use os.system to run the export script
        result = os.system("python export_leaderboard_multi_league.py")
        logging.info(f"Export script completed with result: {result}")
        return result == 0
    except Exception as e:
        logging.error(f"Error running export script: {e}")
        return False

if __name__ == "__main__":
    print("Starting extended weekly stats test...")
    count = adjust_weekly_stats_query()
    print(f"Found {count} scores in the extended weekly range")
    
    # Run the regular export
    success = run_export()
    print(f"Export {'succeeded' if success else 'failed'}")
    print("Check test_export_extended_week.log for details")
