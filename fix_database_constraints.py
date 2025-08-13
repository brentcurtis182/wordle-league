#!/usr/bin/env python3
"""
Fix Database Constraints

This script ensures that foreign key constraints are properly enabled in the SQLite database.
It recreates the scores table with explicit foreign key constraints.
"""

import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_constraints():
    """Fix foreign key constraints in the database"""
    # Create a backup first
    try:
        backup_name = f"wordle_league_backup_constraints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        conn_src = sqlite3.connect('wordle_league.db')
        conn_dst = sqlite3.connect(backup_name)
        conn_src.backup(conn_dst)
        conn_src.close()
        conn_dst.close()
        logging.info(f"Created database backup: {backup_name}")
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return False
    
    # Now fix the constraints
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Get existing scores to preserve them
        cursor.execute("""
        SELECT player_id, wordle_number, score, date, emoji_pattern, timestamp 
        FROM scores
        """)
        existing_scores = cursor.fetchall()
        logging.info(f"Retrieved {len(existing_scores)} existing scores to preserve")
        
        # Drop and recreate the scores table with explicit foreign key constraint
        cursor.execute("DROP TABLE IF EXISTS scores")
        
        cursor.execute("""
        CREATE TABLE scores (
            id INTEGER PRIMARY KEY,
            player_id INTEGER NOT NULL,
            wordle_number INTEGER NOT NULL,
            score INTEGER NOT NULL,
            date TEXT NOT NULL,
            emoji_pattern TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (player_id) REFERENCES players(id),
            UNIQUE (player_id, wordle_number)
        )
        """)
        
        # Create an index for faster lookups
        cursor.execute("""
        CREATE INDEX idx_scores_player_wordle ON scores (player_id, wordle_number)
        """)
        
        # Reinsert the scores
        for score in existing_scores:
            cursor.execute("""
            INSERT INTO scores (player_id, wordle_number, score, date, emoji_pattern, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """, score)
            
        conn.commit()
        logging.info(f"Successfully reinserted {len(existing_scores)} scores with proper constraints")
        
        # Verify foreign keys are enabled
        cursor.execute("PRAGMA foreign_keys")
        fk_enabled = cursor.fetchone()[0]
        logging.info(f"Foreign keys enabled: {bool(fk_enabled)}")
        
        # Verify the table structure
        cursor.execute("PRAGMA table_info(scores)")
        columns = cursor.fetchall()
        logging.info("Scores table structure:")
        for col in columns:
            logging.info(f"  {col}")
            
        # Verify foreign keys
        cursor.execute("PRAGMA foreign_key_list(scores)")
        foreign_keys = cursor.fetchall()
        logging.info("Foreign key constraints:")
        for fk in foreign_keys:
            logging.info(f"  {fk}")
            
        return True
        
    except Exception as e:
        logging.error(f"Error fixing constraints: {e}")
        if conn:
            conn.rollback()
        return False
    
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logging.info("Starting database constraint fix")
    if fix_constraints():
        print("\nSUCCESS: Database constraints fixed successfully!")
        print("Foreign keys are now properly enforced.")
    else:
        print("\nFAILED: Could not fix database constraints.")
