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
        logging.FileHandler("check_vox_scores_fix.log")
    ]
)

def check_vox_scores():
    """Check all scores for Vox in the database"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check Vox's scores in PAL league (league_id=3)
        cursor.execute("""
        SELECT id, player_name, wordle_num, score, timestamp, league_id
        FROM scores 
        WHERE player_name = 'Vox' AND league_id = 3
        ORDER BY wordle_num DESC
        """)
        
        rows = cursor.fetchall()
        
        logging.info(f"Found {len(rows)} scores for Vox in PAL league:")
        for row in rows:
            score_id, player_name, wordle_num, score, timestamp, league_id = row
            logging.info(f"ID: {score_id}, Wordle #{wordle_num}, Score: {score}, Date: {timestamp}, League: {league_id}")
        
        # Check if there's a false entry for Wordle #1503
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
            
            return "cleanup_needed", false_entries
        else:
            logging.info("No false entries found for Vox with Wordle #1503")
            return "no_cleanup_needed", []
            
    except Exception as e:
        logging.error(f"Error checking scores: {e}")
        return "error", []
    finally:
        if conn:
            conn.close()

def cleanup_false_entries(entry_ids):
    """Clean up false entries for Vox with Wordle #1503"""
    if not entry_ids:
        logging.info("No false entries to clean up")
        return
        
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Delete entries by ID
        for entry_id in entry_ids:
            logging.info(f"Deleting false entry with ID {entry_id}")
            cursor.execute("DELETE FROM scores WHERE id = ?", (entry_id,))
            
        conn.commit()
        logging.info(f"Successfully deleted {len(entry_ids)} false entries")
        
    except Exception as e:
        logging.error(f"Error cleaning up false entries: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Checking Vox's scores in the database")
    
    # Check if there are false entries
    status, false_entries = check_vox_scores()
    
    # Clean up false entries if needed
    if status == "cleanup_needed":
        logging.info(f"Found {len(false_entries)} false entries that need cleanup")
        
        # Get IDs of false entries
        entry_ids = [entry[0] for entry in false_entries]
        
        # Prompt for confirmation
        confirm = input(f"Do you want to delete {len(entry_ids)} false entries for Vox? (y/n): ")
        if confirm.lower() == 'y':
            cleanup_false_entries(entry_ids)
            logging.info("Cleanup completed")
        else:
            logging.info("Cleanup skipped by user")
    else:
        logging.info("No cleanup needed")
