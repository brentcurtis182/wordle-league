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

def verify_todays_scores():
    """Verify scores for today's date and yesterday's date"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Today and yesterday
        today_date = datetime.now().date()
        yesterday_date = today_date - timedelta(days=1)
        
        today_str = today_date.strftime("%Y-%m-%d")
        yesterday_str = yesterday_date.strftime("%Y-%m-%d")
        
        print(f"===== SCORE VERIFICATION FOR {today_str} =====")
        print(f"Today is {today_str}")
        print(f"Yesterday was {yesterday_str}")
        
        # Get the max Wordle number to determine today's Wordle number
        cursor.execute("""
        SELECT MAX(CAST(REPLACE(wordle_num, ',', '') AS INTEGER)) 
        FROM scores
        """)
        result = cursor.fetchone()
        if result[0]:
            likely_today_wordle = result[0]
            likely_yesterday_wordle = likely_today_wordle - 1
            print(f"Latest Wordle number in database: #{likely_today_wordle}")
            print(f"Yesterday's Wordle number was likely: #{likely_yesterday_wordle}")
        else:
            print("No Wordle numbers found in database!")
            return
            
        # Check scores for today's date
        cursor.execute("""
        SELECT league_id, COUNT(*) as count
        FROM scores
        WHERE date(timestamp) = date(?)
        GROUP BY league_id
        """, (today_str,))
        
        results = cursor.fetchall()
        
        if results:
            print(f"\nScores found for TODAY ({today_str}):")
            for league_id, count in results:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                print(f"  {league_name}: {count} score(s)")
                
            # Show details of today's scores
            cursor.execute("""
            SELECT player_name, wordle_num, score, timestamp, league_id
            FROM scores
            WHERE date(timestamp) = date(?)
            ORDER BY league_id, player_name
            """, (today_str,))
            
            scores = cursor.fetchall()
            print("\nDetails of TODAY's scores:")
            for player, wordle_num, score, timestamp, league_id in scores:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                print(f"  {league_name}: {player} - Wordle #{wordle_num} - {score}/6")
        else:
            print(f"\nWARNING: No scores found for today ({today_str})!")
        
        # Check scores for yesterday's date
        cursor.execute("""
        SELECT league_id, COUNT(*) as count
        FROM scores
        WHERE date(timestamp) = date(?)
        GROUP BY league_id
        """, (yesterday_str,))
        
        results = cursor.fetchall()
        
        if results:
            print(f"\nScores found for YESTERDAY ({yesterday_str}):")
            for league_id, count in results:
                league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
                print(f"  {league_name}: {count} score(s)")
        else:
            print(f"\nNo scores found for yesterday ({yesterday_str})!")
            
        # Check for potential date issues
        print("\nChecking for potential date mismatches...")
        cursor.execute("""
        SELECT wordle_num, MIN(date(timestamp)) as min_date, MAX(date(timestamp)) as max_date, COUNT(*) as count
        FROM scores
        WHERE CAST(REPLACE(wordle_num, ',', '') AS INTEGER) >= ?
        GROUP BY wordle_num
        ORDER BY CAST(REPLACE(wordle_num, ',', '') AS INTEGER) DESC
        LIMIT 5
        """, (likely_today_wordle - 3,))
        
        wordle_dates = cursor.fetchall()
        
        if wordle_dates:
            for wordle_num, min_date, max_date, count in wordle_dates:
                if min_date != max_date:
                    print(f"⚠️ WARNING: Wordle #{wordle_num} has dates ranging from {min_date} to {max_date} ({count} entries)")
                else:
                    print(f"✓ Wordle #{wordle_num}: All {count} entries have consistent date {min_date}")
        
    except Exception as e:
        logging.error(f"Error verifying scores: {e}")
    finally:
        if conn:
            conn.close()
    
    print("\nVerification complete!")

if __name__ == "__main__":
    verify_todays_scores()
