#!/usr/bin/env python
"""
Fix Nanna's Wordle #1500 score from 4/6 to 6/6
"""
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_nanna_score.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Database path
DATABASE_PATH = 'wordle_league.db'

def fix_nannas_score():
    """Fix Nanna's Wordle #1500 score from 4/6 to 6/6"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Update Nanna's score in scores table
        cursor.execute(
            "UPDATE scores SET score = 6 WHERE player_name = 'Nanna' AND wordle_num = 1500"
        )
        
        rows_updated = cursor.rowcount
        if rows_updated > 0:
            logging.info(f"Updated {rows_updated} rows for Nanna's score in scores table")
        else:
            logging.warning("No rows updated for Nanna in scores table")
            
        # Try to update in score table if it exists
        try:
            # Get Nanna's player_id
            cursor.execute("SELECT id FROM player WHERE name = 'Nanna'")
            player_id_row = cursor.fetchone()
            
            if player_id_row:
                player_id = player_id_row[0]
                
                # Update in score table
                cursor.execute(
                    "UPDATE score SET score = 6 WHERE player_id = ? AND wordle_number = 1500",
                    (player_id,)
                )
                
                rows_updated = cursor.rowcount
                if rows_updated > 0:
                    logging.info(f"Updated {rows_updated} rows for Nanna's score in score table")
                else:
                    logging.warning("No rows updated for Nanna in score table")
            else:
                logging.warning("Could not find Nanna's player_id")
                
        except Exception as e:
            logging.warning(f"Error updating score table: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the update
        cursor.execute(
            "SELECT score FROM scores WHERE player_name = 'Nanna' AND wordle_num = 1500"
        )
        updated_score = cursor.fetchone()
        
        if updated_score and updated_score[0] == 6:
            logging.info("✅ Successfully verified Nanna's score is now 6/6")
            return True
        else:
            logging.error("Failed to update Nanna's score correctly")
            return False
            
    except Exception as e:
        logging.error(f"Error fixing Nanna's score: {e}")
        return False
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_website():
    """Update the website with the fixed score"""
    try:
        import subprocess
        logging.info("Running integrated_auto_update.py to update the website...")
        
        # Run the script with skip-extraction flag to avoid overwriting our fixes
        result = subprocess.run(
            ["python", "integrated_auto_update.py", "--skip-extraction", "--publish-only"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Website updated successfully")
            return True
        else:
            logging.error(f"Error updating website: {result.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Exception running website update: {e}")
        return False

if __name__ == "__main__":
    if fix_nannas_score():
        print("Successfully fixed Nanna's score to 6/6")
        if update_website():
            print("Website updated successfully")
        else:
            print("Website update failed, but database was fixed")
    else:
        print("Failed to fix Nanna's score")
