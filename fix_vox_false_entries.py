import sqlite3
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("fix_vox_false_entries.log")
    ]
)

def cleanup_false_entries():
    """Clean up false entries for Vox with Wordle #1503"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First, identify and log all Vox's entries
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE player_name = 'Vox' AND league_id = 3
        ORDER BY wordle_num DESC
        """)
        
        all_scores = cursor.fetchall()
        logging.info(f"Found {len(all_scores)} total scores for Vox in PAL league:")
        
        for score in all_scores:
            score_id, player_name, wordle_num, score_val, timestamp, league_id = score
            logging.info(f"ID: {score_id}, Player: {player_name}, Wordle #{wordle_num}, Score: {score_val}, Date: {timestamp}, League: {league_id}")
        
        # Find false entries for Wordle #1503
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE player_name = 'Vox' AND wordle_num = 1503 AND league_id = 3
        """)
        
        false_entries = cursor.fetchall()
        if false_entries:
            logging.warning(f"Found {len(false_entries)} FALSE entries for Vox with Wordle #1503:")
            for entry in false_entries:
                logging.warning(f"FALSE ENTRY: {entry}")
            
            # Delete false entries
            logging.info(f"Deleting {len(false_entries)} false entries for Vox with Wordle #1503")
            cursor.execute("""
            DELETE FROM scores 
            WHERE player_name = 'Vox' AND wordle_num = 1503 AND league_id = 3
            """)
            
            rows_deleted = cursor.rowcount
            conn.commit()
            logging.info(f"Successfully deleted {rows_deleted} false entries")
            
            return rows_deleted
        else:
            logging.info("No false entries found for Vox with Wordle #1503")
            return 0
            
    except Exception as e:
        logging.error(f"Error cleaning up false entries: {e}")
        if conn:
            conn.rollback()
        return -1
    finally:
        if conn:
            conn.close()

def check_all_wordle_1503_entries():
    """Check all entries for Wordle #1503 to ensure they're legitimate"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all entries for Wordle #1503
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE wordle_num = 1503
        ORDER BY league_id, player_name
        """)
        
        entries = cursor.fetchall()
        logging.info(f"Found {len(entries)} total entries for Wordle #1503:")
        
        for entry in entries:
            score_id, player_name, wordle_num, score, timestamp, league_id = entry
            logging.info(f"ID: {score_id}, Player: {player_name}, Score: {score}, Date: {timestamp}, League: {league_id}")
            
    except Exception as e:
        logging.error(f"Error checking Wordle #1503 entries: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Starting cleanup of false entries for Vox")
    
    # Clean up false entries
    rows_deleted = cleanup_false_entries()
    
    # Check all remaining Wordle #1503 entries
    logging.info("Checking all remaining Wordle #1503 entries")
    check_all_wordle_1503_entries()
    
    if rows_deleted > 0:
        logging.info(f"Successfully cleaned up {rows_deleted} false entries")
    elif rows_deleted == 0:
        logging.info("No false entries found to clean up")
    else:
        logging.error("Error during cleanup")
