import sqlite3
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_database_scores():
    """Check all scores in the database and their dates"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check score table
        logging.info("==== SCORE TABLE ====")
        cursor.execute("SELECT DISTINCT wordle_number FROM score ORDER BY wordle_number DESC")
        wordles = cursor.fetchall()
        logging.info(f"Found {len(wordles)} distinct Wordle numbers in score table")
        
        for wordle in wordles[:5]:  # Show most recent 5
            wordle_num = wordle['wordle_number']
            cursor.execute("SELECT player_id, score, date FROM score WHERE wordle_number = ?", (wordle_num,))
            scores = cursor.fetchall()
            logging.info(f"Wordle #{wordle_num}: {len(scores)} scores")
            
            for score in scores:
                player_id = score['player_id']
                cursor.execute("SELECT name FROM player WHERE id = ?", (player_id,))
                player = cursor.fetchone()
                player_name = player['name'] if player else "Unknown"
                logging.info(f"  {player_name}: {score['score']}/6 on {score['date']}")
        
        # Check scores table
        logging.info("\n==== SCORES TABLE ====")
        cursor.execute("SELECT DISTINCT wordle_num FROM scores ORDER BY wordle_num DESC")
        wordles = cursor.fetchall()
        logging.info(f"Found {len(wordles)} distinct Wordle numbers in scores table")
        
        for wordle in wordles[:5]:  # Show most recent 5
            wordle_num = wordle['wordle_num']
            cursor.execute("SELECT player_name, score, timestamp FROM scores WHERE wordle_num = ?", (wordle_num,))
            scores = cursor.fetchall()
            logging.info(f"Wordle #{wordle_num}: {len(scores)} scores")
            
            for score in scores:
                logging.info(f"  {score['player_name']}: {score['score']}/6 on {score['timestamp']}")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error checking scores: {e}")

def fix_weekly_scores():
    """Update the database to only show today's scores in the weekly view"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get today's date
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Check how many scores we have for today
        cursor.execute("SELECT COUNT(*) as count FROM score WHERE date = ?", (today,))
        today_count = cursor.fetchone()['count']
        logging.info(f"Found {today_count} scores for today ({today})")
        
        if today_count > 0:
            # Remove all scores except today's
            cursor.execute("DELETE FROM score WHERE date != ?", (today,))
            deleted = cursor.rowcount
            logging.info(f"Deleted {deleted} old scores from score table")
            
            # Also remove from scores table - based on timestamp
            cursor.execute("DELETE FROM scores WHERE date(timestamp) != ?", (today,))
            deleted = cursor.rowcount
            logging.info(f"Deleted {deleted} old scores from scores table")
            
            # Commit changes
            conn.commit()
            logging.info("Changes committed to database")
        else:
            logging.warning("No scores found for today, not deleting anything")
        
        conn.close()
    except Exception as e:
        logging.error(f"Error fixing weekly scores: {e}")

def should_delete_old_scores():
    """Ask if we should delete old scores"""
    print("\nThe weekly and all-time pages are showing scores from multiple days.")
    print("Do you want to delete all scores except today's? (y/n)")
    response = input("Enter your choice: ")
    return response.lower() == 'y'

if __name__ == "__main__":
    check_database_scores()
    
    if should_delete_old_scores():
        fix_weekly_scores()
        
        # Run the update script to update the website with only today's scores
        print("\nRunning update_with_correct_patterns.py to refresh the website...")
        import update_with_correct_patterns
        update_with_correct_patterns.main()
    else:
        print("No changes made to the database.")
