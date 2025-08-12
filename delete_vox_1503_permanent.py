#!/usr/bin/env python3
import sqlite3
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def delete_vox_scores():
    """Delete Vox's erroneous Wordle #1503 scores and set a flag to prevent re-addition"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if Vox's scores exist for Wordle #1503
        cursor.execute("""
            SELECT id, player_name, wordle_num, score, timestamp, emoji_pattern, league_id 
            FROM scores 
            WHERE player_name = 'Vox' AND wordle_num = '1503'
        """)
        
        records = cursor.fetchall()
        
        if records:
            logging.info(f"Found {len(records)} erroneous scores for Vox (Wordle #1503)")
            
            # Delete each record
            for record in records:
                record_id = record[0]
                cursor.execute("DELETE FROM scores WHERE id = ?", (record_id,))
                logging.info(f"Deleted score ID {record_id} for Vox, Wordle #1503")
            
            # Commit the changes
            conn.commit()
            logging.info("Deletion committed to database")
            
            # Create a marker file to prevent future extraction attempts
            with open('vox_1503_deleted.marker', 'w') as f:
                f.write("Vox's Wordle #1503 scores were deleted on purpose. Do not re-add.")
            logging.info("Created marker file to prevent future extraction attempts")
        else:
            logging.info("No Wordle #1503 scores found for Vox - already deleted")
        
        # Verify Vox's Wordle #1502 (yesterday's) scores still exist
        cursor.execute("""
            SELECT id, player_name, wordle_num, score, timestamp, emoji_pattern, league_id 
            FROM scores 
            WHERE player_name = 'Vox' AND wordle_num = '1502'
        """)
        
        records = cursor.fetchall()
        logging.info(f"Vox still has {len(records)} valid scores for Wordle #1502")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        logging.error(f"Error: {e}")
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    delete_vox_scores()
