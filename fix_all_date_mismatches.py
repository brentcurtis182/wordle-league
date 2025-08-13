import sqlite3
import sys
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_all_date_mismatches.log")
    ]
)

def fix_date_mismatches():
    """Find and fix all date mismatches in the database"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Calculate the correct date for each Wordle number
        # Wordle #1 was released on June 19, 2021
        wordle_start_date = datetime(2021, 6, 19).date()
        
        # Get all scores
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        ORDER BY wordle_num DESC, league_id, player_name
        """)
        
        all_scores = cursor.fetchall()
        logging.info(f"Found {len(all_scores)} total scores in the database")
        
        # Check each score for date mismatches
        mismatches = []
        false_scores = []
        
        today_wordle = 1503  # Current Wordle number (July 31, 2025)
        yesterday_wordle = 1502
        
        for score in all_scores:
            score_id, player_name, wordle_num, score_val, timestamp, league_id = score
            
            # Calculate correct date for this Wordle number
            # Handle comma-formatted Wordle numbers
            wordle_num_clean = str(wordle_num).replace(',', '')
            score_date = wordle_start_date + timedelta(days=(int(wordle_num_clean) - 1))
            score_date_str = score_date.strftime("%Y-%m-%d")
            
            # Get actual date from timestamp
            actual_date = timestamp.split()[0]  # Get just the date part
            
            # Check if dates match
            if actual_date != score_date_str:
                logging.warning(f"Date mismatch: ID {score_id}, {player_name}, Wordle #{wordle_num}, "
                               f"Score date should be {score_date_str} but is {actual_date}")
                mismatches.append((score_id, player_name, wordle_num, score_val, timestamp, league_id, 
                                 score_date_str))
            
            # Check for false scores for today's Wordle
            wordle_num_clean = str(wordle_num).replace(',', '')
            if int(wordle_num_clean) == today_wordle:
                # Known false scores based on user information
                if (player_name == "Vox" and league_id == 3) or (player_name == "Evan" and league_id == 1):
                    logging.warning(f"FALSE SCORE: ID {score_id}, {player_name}, Wordle #{wordle_num}, "
                                   f"Score: {score_val}, Date: {timestamp}, League: {league_id}")
                    false_scores.append(score_id)
        
        # Fix date mismatches
        for mismatch in mismatches:
            score_id, player_name, wordle_num, score_val, timestamp, league_id, correct_date = mismatch
            
            # Keep the time part but replace the date
            time_part = timestamp.split()[1]
            corrected_timestamp = f"{correct_date} {time_part}"
            
            logging.info(f"Fixing date for ID {score_id}: {timestamp} -> {corrected_timestamp}")
            
            cursor.execute("""
            UPDATE scores
            SET timestamp = ?
            WHERE id = ?
            """, (corrected_timestamp, score_id))
        
        # Delete false scores
        for score_id in false_scores:
            logging.info(f"Deleting false score with ID {score_id}")
            cursor.execute("DELETE FROM scores WHERE id = ?", (score_id,))
        
        # Commit changes
        conn.commit()
        
        logging.info(f"Fixed {len(mismatches)} date mismatches")
        logging.info(f"Deleted {len(false_scores)} false scores")
        
        # Verify fixes
        check_today_scores(conn)
        
        return len(mismatches), len(false_scores)
            
    except Exception as e:
        logging.error(f"Error fixing date mismatches: {e}")
        if conn:
            conn.rollback()
        return 0, 0
    finally:
        if conn:
            conn.close()

def check_today_scores(conn=None):
    """Check all scores for today's and yesterday's Wordle after fixes"""
    close_conn = False
    try:
        if not conn:
            conn = sqlite3.connect('wordle_league.db')
            close_conn = True
            
        cursor = conn.cursor()
        
        # Check today's Wordle scores
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1503
        ORDER BY league_id, player_name
        """)
        
        today_scores = cursor.fetchall()
        
        logging.info(f"\nFinal scores for TODAY (Wordle #1503):")
        for player, wordle_num, score, timestamp, league_id in today_scores:
            league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
            logging.info(f"{league_name}: {player} - {score}/6 ({timestamp})")
        
        # Check yesterday's Wordle scores
        cursor.execute("""
        SELECT player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1502
        ORDER BY league_id, player_name
        """)
        
        yesterday_scores = cursor.fetchall()
        
        logging.info(f"\nFinal scores for YESTERDAY (Wordle #1502):")
        for player, wordle_num, score, timestamp, league_id in yesterday_scores:
            league_name = "Warriorz" if league_id == 1 else "PAL" if league_id == 3 else f"League {league_id}"
            logging.info(f"{league_name}: {player} - {score}/6 ({timestamp})")
            
    except Exception as e:
        logging.error(f"Error checking scores: {e}")
    finally:
        if close_conn and conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Starting comprehensive fix for date mismatches and false scores")
    
    mismatches_fixed, false_scores_deleted = fix_date_mismatches()
    
    logging.info(f"Summary: Fixed {mismatches_fixed} date mismatches and deleted {false_scores_deleted} false scores")
