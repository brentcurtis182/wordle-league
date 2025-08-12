#!/usr/bin/env python3
"""
Script to delete Nanna's incomplete score for today's Wordle so it can be 
properly re-extracted with the complete emoji pattern.
"""
import sqlite3
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def delete_nannas_score():
    """Delete Nanna's incomplete score for today's Wordle"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's Wordle number
        ref_date = datetime(2025, 7, 31).date()
        ref_wordle = 1503
        today = datetime.now().date()
        days_since_ref = (today - ref_date).days
        todays_wordle = ref_wordle + days_since_ref
        
        logging.info(f"Today's Wordle number: {todays_wordle}")
        
        # Get Nanna's player ID from the Wordle Warriorz league (league_id 1)
        cursor.execute("""
        SELECT id FROM players 
        WHERE name = 'Nanna' AND league_id = 1
        """)
        result = cursor.fetchone()
        if not result:
            logging.error("Could not find Nanna in the Wordle Warriorz league")
            return False
            
        nanna_id = result[0]
        logging.info(f"Nanna's player ID: {nanna_id}")
        
        # Check if Nanna has a score for today
        cursor.execute("""
        SELECT id, score, emoji_pattern FROM scores 
        WHERE player_id = ? AND wordle_number = ?
        """, (nanna_id, todays_wordle))
        
        result = cursor.fetchone()
        if result:
            score_id, score, emoji_pattern = result
            logging.info(f"Found Nanna's score for Wordle {todays_wordle}: {score}/6")
            
            if emoji_pattern:
                emoji_lines = emoji_pattern.strip().split('\n')
                logging.info(f"Current emoji pattern has {len(emoji_lines)} lines")
                logging.info(f"Current emoji pattern:\n{emoji_pattern}")
            
            # Delete the score
            cursor.execute("DELETE FROM scores WHERE id = ?", (score_id,))
            conn.commit()
            
            logging.info(f"Successfully deleted Nanna's score (ID: {score_id})")
            return True
        else:
            logging.info(f"No score found for Nanna for Wordle {todays_wordle}")
            return False
            
    except Exception as e:
        logging.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def verify_score_deleted():
    """Verify that Nanna's score has been deleted"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's Wordle number
        ref_date = datetime(2025, 7, 31).date()
        ref_wordle = 1503
        today = datetime.now().date()
        days_since_ref = (today - ref_date).days
        todays_wordle = ref_wordle + days_since_ref
        
        # Get Nanna's player ID from the Wordle Warriorz league (league_id 1)
        cursor.execute("""
        SELECT id FROM players 
        WHERE name = 'Nanna' AND league_id = 1
        """)
        result = cursor.fetchone()
        if not result:
            logging.error("Could not find Nanna in the Wordle Warriorz league")
            return False
            
        nanna_id = result[0]
        
        # Check if Nanna has a score for today
        cursor.execute("""
        SELECT id FROM scores 
        WHERE player_id = ? AND wordle_number = ?
        """, (nanna_id, todays_wordle))
        
        result = cursor.fetchone()
        if result:
            logging.error(f"Nanna's score still exists for Wordle {todays_wordle}")
            return False
        else:
            logging.info(f"Confirmed: Nanna has no score for Wordle {todays_wordle}")
            return True
            
    except Exception as e:
        logging.error(f"Error during verification: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def run_update():
    """Run the script to update the website with Nanna's score removed"""
    try:
        import subprocess
        logging.info("Running integrated_auto_update_multi_league.py to update the website...")
        
        # Use subprocess to run the update script
        result = subprocess.run(
            ["python", "integrated_auto_update_multi_league.py"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Successfully ran update script")
            logging.info(result.stdout[:200] + "..." if len(result.stdout) > 200 else result.stdout)
            return True
        else:
            logging.error(f"Error running update script: {result.returncode}")
            logging.error(result.stderr)
            return False
            
    except Exception as e:
        logging.error(f"Error running update: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting script to delete Nanna's incomplete score...")
    
    if delete_nannas_score():
        if verify_score_deleted():
            logging.info("Score successfully deleted and verified")
            
            # Automatically run the update script
            logging.info("Running update script to re-extract scores...")
            if run_update():
                logging.info("Update completed successfully")
            else:
                logging.error("Update failed")
        else:
            logging.error("Failed to verify score deletion")
            sys.exit(1)
    else:
        logging.info("No action needed or deletion failed")
        
    logging.info("Script completed")
