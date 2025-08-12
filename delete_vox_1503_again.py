#!/usr/bin/env python3
import sqlite3
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def delete_vox_1503():
    """Delete erroneous Wordle #1503 scores for Vox"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First, check if Vox has a score for Wordle #1503
        cursor.execute(
            "SELECT id, player_name, wordle_num, score, date(timestamp), league_id FROM scores WHERE player_name = 'Vox' AND wordle_num = 1503"
        )
        records = cursor.fetchall()
        
        if records:
            logging.info("===== VOX'S WORDLE #1503 SCORES BEFORE DELETION =====")
            for record in records:
                logging.info(f"ID: {record[0]}, League: {'PAL' if record[5] == 3 else 'Warriorz'}, Wordle: {record[2]}, Score: {record[3]}/6, Date: {record[4]}")
            
            # Now delete them
            cursor.execute(
                "DELETE FROM scores WHERE player_name = 'Vox' AND wordle_num = 1503"
            )
            conn.commit()
            
            # Verify deletion
            cursor.execute(
                "SELECT id, player_name, wordle_num, score, date(timestamp), league_id FROM scores WHERE player_name = 'Vox' AND wordle_num = 1503"
            )
            remaining = cursor.fetchall()
            
            if not remaining:
                logging.info("All Vox's Wordle #1503 scores successfully deleted.")
            else:
                logging.warning(f"Warning: {len(remaining)} scores still remain for Vox's Wordle #1503!")
        else:
            logging.info("No Wordle #1503 scores found for Vox.")
        
        # Verify Vox's Wordle #1502 scores still exist
        cursor.execute(
            "SELECT id, player_name, wordle_num, score, date(timestamp), league_id FROM scores WHERE player_name = 'Vox' AND wordle_num = 1502"
        )
        records = cursor.fetchall()
        
        if records:
            logging.info("===== VOX'S WORDLE #1502 SCORES (SHOULD REMAIN) =====")
            for record in records:
                logging.info(f"ID: {record[0]}, League: {'PAL' if record[5] == 3 else 'Warriorz'}, Wordle: {record[2]}, Score: {record[3]}/6, Date: {record[4]}")
        else:
            logging.warning("No Wordle #1502 scores found for Vox! These should exist.")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"Error: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    delete_vox_1503()
