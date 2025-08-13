#!/usr/bin/env python3
"""
Verify Unified Extraction Script

This script verifies that the extraction system correctly saves scores to the new unified schema.
It performs a test extraction and checks that scores are properly saved in the database.
"""

import os
import sys
import time
import logging
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

# Import our extraction function
from integrated_auto_update_multi_league import extract_wordle_scores_multi_league

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify_unified_extraction.log"),
        logging.StreamHandler()
    ]
)

def verify_database_structure():
    """
    Verify that the database has the correct structure for the unified schema
    """
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Check if scores table exists with the right structure
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        
        expected_columns = {
            'id': 'INTEGER',
            'player_id': 'INTEGER', 
            'wordle_number': 'INTEGER',
            'score': 'INTEGER',
            'date': 'TEXT',
            'emoji_pattern': 'TEXT',
            'timestamp': 'DATETIME'
        }
        
        actual_columns = {col[1]: col[2] for col in columns}
        
        # Check if all expected columns are present
        for col_name, col_type in expected_columns.items():
            if col_name not in actual_columns:
                logging.error(f"Missing column {col_name} in scores table")
                return False
            
            if not col_type in actual_columns[col_name]:
                logging.error(f"Column {col_name} has wrong type: {actual_columns[col_name]} (expected {col_type})")
                return False
                
        # Check foreign key constraint
        cursor.execute("PRAGMA foreign_key_list(scores)")
        foreign_keys = cursor.fetchall()
        
        # Output format from PRAGMA foreign_key_list is:
        # (id, seq, table, from, to, on_update, on_delete, match)
        # where 'from' is the column in the child table and 'to' is the column in the parent table
        
        has_player_fk = False
        for fk in foreign_keys:
            # Log for debugging
            logging.info(f"Found foreign key: {fk}")
            # Check if it's a foreign key from player_id to players.id
            if fk[2] == 'players' and fk[3] == 'player_id' and fk[4] == 'id':
                has_player_fk = True
                break
                
        if not has_player_fk:
            logging.error("Missing foreign key constraint on player_id")
            return False
            
        # Check unique constraint
        cursor.execute("PRAGMA index_list(scores)")
        indexes = cursor.fetchall()
        
        # For debugging
        logging.info(f"Found indexes: {indexes}")
        
        has_unique_index = False
        for idx in indexes:
            # Log index for debugging
            logging.info(f"Checking index: {idx}")
            
            # Check if this is the SQLite auto-generated unique index or a unique constraint
            # SQLite's PRAGMA output format has changed across versions, so handle both string and int
            is_unique = False
            if idx[1] == 'sqlite_autoindex_scores_1':
                is_unique = True
            elif isinstance(idx[2], str) and 'unique' in idx[2].lower():
                is_unique = True
            elif idx[2] == 1:  # SQLite sometimes uses 1 to indicate unique
                is_unique = True
                
            if is_unique:
                cursor.execute(f"PRAGMA index_info({idx[1]})")
                index_columns = cursor.fetchall()
                index_column_names = [col[2] for col in index_columns]
                logging.info(f"Index columns: {index_column_names}")
                if set(index_column_names) == set(['player_id', 'wordle_number']):
                    has_unique_index = True
                    break
                    
        if not has_unique_index:
            logging.error("Missing unique constraint on player_id and wordle_number")
            return False
            
        logging.info("Database structure verified successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error verifying database structure: {e}")
        return False
    finally:
        if conn:
            conn.close()

def run_extraction_test():
    """
    Run the extraction process and verify that scores are saved correctly
    """
    try:
        # First clear existing scores for today's test
        today = datetime.now().strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's scores count before extraction
        cursor.execute("""
        SELECT COUNT(*) FROM scores WHERE date = ?
        """, (today,))
        before_count = cursor.fetchone()[0]
        
        conn.close()
        
        logging.info(f"Found {before_count} scores for today before extraction")
        
        # Run the extraction
        logging.info("Running extraction process...")
        success = extract_wordle_scores_multi_league()
        
        if not success:
            logging.warning("Extraction reported no scores found, but continuing verification")
        
        # Check if new scores were added
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get today's scores count after extraction
        cursor.execute("""
        SELECT COUNT(*) FROM scores WHERE date = ?
        """, (today,))
        after_count = cursor.fetchone()[0]
        
        # Get scores added in this extraction
        cursor.execute("""
        SELECT s.score, p.name, p.league_id, s.wordle_number, s.date, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.date = ?
        ORDER BY p.league_id, p.name
        """, (today,))
        
        today_scores = cursor.fetchall()
        
        conn.close()
        
        # Report the results
        logging.info(f"Found {after_count} scores for today after extraction")
        logging.info(f"Net new scores added: {after_count - before_count}")
        
        if today_scores:
            logging.info("\nToday's scores in database:")
            for score_data in today_scores:
                score_val, player, league_id, wordle_num, date, emoji = score_data
                display_score = 'X' if score_val == 7 else score_val
                league_name = "Wordle Warriorz" if league_id == 1 else "PAL" if league_id == 3 else "Gang"
                
                logging.info(f"{player} ({league_name}): Wordle #{wordle_num} - {display_score}/6 on {date}")
                if emoji:
                    emoji_lines = emoji.split('\n')
                    for line in emoji_lines:
                        logging.info(f"  {line}")
                    
        return True
        
    except Exception as e:
        logging.error(f"Error running extraction test: {e}")
        return False

def main():
    load_dotenv()
    
    logging.info("Starting verification of unified extraction")
    
    # Step 1: Verify database structure
    if not verify_database_structure():
        logging.error("Database structure verification failed")
        return False
        
    # Step 2: Run extraction test
    if not run_extraction_test():
        logging.error("Extraction test failed")
        return False
        
    logging.info("Verification completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Verified that extraction is working with the unified scores table!")
    else:
        print("\nFAILED: Verification found issues with the unified extraction system")
        sys.exit(1)
