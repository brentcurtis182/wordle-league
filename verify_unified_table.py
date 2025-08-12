#!/usr/bin/env python3
"""
Verification script for the unified player_scores table.
This script creates the table if it doesn't exist, migrates data from both old tables,
and then displays sample data to verify it worked correctly.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('verify_unified_table.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')

def create_unified_table():
    """Create the new unified player_scores table if it doesn't exist"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_scores'")
        if cursor.fetchone():
            logging.info("player_scores table already exists")
            return True
            
        # Create the new unified table
        cursor.execute("""
        CREATE TABLE player_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            player_name TEXT NOT NULL,
            wordle_number TEXT NOT NULL,
            score TEXT NOT NULL,
            emoji_pattern TEXT,
            timestamp TEXT,
            league_id INTEGER,
            UNIQUE(player_name, wordle_number, league_id)
        )
        """)
        
        # Create indices for faster queries
        cursor.execute("CREATE INDEX idx_player_scores_player_name ON player_scores(player_name)")
        cursor.execute("CREATE INDEX idx_player_scores_player_id ON player_scores(player_id)")
        cursor.execute("CREATE INDEX idx_player_scores_wordle_number ON player_scores(wordle_number)")
        cursor.execute("CREATE INDEX idx_player_scores_league_id ON player_scores(league_id)")
        
        conn.commit()
        logging.info("Created new unified player_scores table")
        return True
        
    except Exception as e:
        logging.error(f"Error creating unified table: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def migrate_from_scores_table():
    """Migrate data from the 'scores' table to the new 'player_scores' table"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get player IDs for mapping
        cursor.execute("SELECT id, name, league_id FROM players")
        player_mapping = {}
        for row in cursor.fetchall():
            player_id, name, league_id = row
            player_mapping[(name, league_id)] = player_id
        
        # Count rows in scores table
        cursor.execute("SELECT COUNT(*) FROM scores")
        total_rows = cursor.fetchone()[0]
        logging.info(f"Found {total_rows} rows in scores table to migrate")
        
        # Fetch all records from scores table
        cursor.execute("""
        SELECT player_name, wordle_num, score, emoji_pattern, timestamp, league_id
        FROM scores
        """)
        
        batch_size = 500
        rows_processed = 0
        
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
                
            for row in batch:
                player_name, wordle_num, score, emoji_pattern, timestamp, league_id = row
                
                # Get player_id if available
                player_id = player_mapping.get((player_name, league_id))
                
                # Skip invalid wordle numbers
                if not wordle_num:
                    continue
                    
                try:
                    # Insert into new table, ignore duplicates
                    cursor.execute("""
                    INSERT OR IGNORE INTO player_scores 
                    (player_id, player_name, wordle_number, score, emoji_pattern, timestamp, league_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (player_id, player_name, wordle_num, score, emoji_pattern, timestamp, league_id))
                except Exception as e:
                    logging.error(f"Error migrating score for {player_name}, wordle {wordle_num}: {e}")
                    
                rows_processed += 1
                
            conn.commit()
            logging.info(f"Processed {rows_processed}/{total_rows} rows from scores table")
            
        logging.info(f"Migration from scores table complete. Processed {rows_processed} rows.")
        return True
        
    except Exception as e:
        logging.error(f"Error migrating from scores table: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def migrate_from_score_table():
    """Migrate data from the 'score' table to the new 'player_scores' table"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get player names for mapping
        cursor.execute("SELECT id, name, league_id FROM players")
        player_mapping = {}
        for row in cursor.fetchall():
            player_id, name, league_id = row
            player_mapping[player_id] = name
        
        # Count rows in score table
        cursor.execute("SELECT COUNT(*) FROM score")
        total_rows = cursor.fetchone()[0]
        logging.info(f"Found {total_rows} rows in score table to migrate")
        
        # Fetch all records from score table
        cursor.execute("""
        SELECT player_id, wordle_number, score, emoji_pattern, date, league_id
        FROM score
        """)
        
        batch_size = 500
        rows_processed = 0
        
        while True:
            batch = cursor.fetchmany(batch_size)
            if not batch:
                break
                
            for row in batch:
                player_id, wordle_num, score, emoji_pattern, date_str, league_id = row
                
                # Get player_name
                player_name = player_mapping.get(player_id)
                if not player_name:
                    # Look up player name from players table
                    cursor.execute("SELECT name FROM players WHERE id = ?", (player_id,))
                    result = cursor.fetchone()
                    if result:
                        player_name = result[0]
                        player_mapping[player_id] = player_name
                    else:
                        logging.warning(f"No player name found for player_id {player_id}")
                        continue
                
                # Skip invalid wordle numbers
                if not wordle_num:
                    continue
                    
                try:
                    # Insert into new table, ignore duplicates
                    cursor.execute("""
                    INSERT OR IGNORE INTO player_scores 
                    (player_id, player_name, wordle_number, score, emoji_pattern, timestamp, league_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (player_id, player_name, wordle_num, score, emoji_pattern, date_str, league_id))
                except Exception as e:
                    logging.error(f"Error migrating score for player_id {player_id}, wordle {wordle_num}: {e}")
                    
                rows_processed += 1
                
            conn.commit()
            logging.info(f"Processed {rows_processed}/{total_rows} rows from score table")
            
        logging.info(f"Migration from score table complete. Processed {rows_processed} rows.")
        return True
        
    except Exception as e:
        logging.error(f"Error migrating from score table: {e}")
        if conn:
            conn.rollback()
        return False
        
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Verify that the migration was successful by comparing counts and showing sample data"""
    conn = None
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Count rows in each table
        cursor.execute("SELECT COUNT(*) FROM scores")
        scores_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM score")
        score_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM player_scores")
        unified_count = cursor.fetchone()[0]
        
        # The unified count might be lower due to deduplication
        print(f"\nOriginal tables: scores={scores_count}, score={score_count}, Total={scores_count+score_count}")
        print(f"Unified table: player_scores={unified_count}")
        
        # Get sample data from the unified table for each league
        for league_id in [1, 2, 3]:  # League IDs: 1=Warriorz, 2=Gang, 3=PAL
            print(f"\nSample data for League {league_id}:")
            
            # Get players in this league
            cursor.execute("""
            SELECT DISTINCT player_name FROM player_scores 
            WHERE league_id = ?
            ORDER BY player_name
            """, (league_id,))
            
            players = cursor.fetchall()
            print(f"Players in league {league_id}: {[p[0] for p in players]}")
            
            # Get the latest 5 wordle numbers in this league
            cursor.execute("""
            SELECT DISTINCT wordle_number 
            FROM player_scores 
            WHERE league_id = ?
            ORDER BY CAST(REPLACE(wordle_number, ',', '') AS INTEGER) DESC
            LIMIT 5
            """, (league_id,))
            
            wordles = cursor.fetchall()
            print(f"Latest wordle numbers: {[w[0] for w in wordles]}")
            
            # Get detailed data for the latest wordle
            if wordles:
                latest_wordle = wordles[0][0]
                print(f"\nDetailed data for Wordle {latest_wordle} in League {league_id}:")
                
                cursor.execute("""
                SELECT player_name, score, emoji_pattern, timestamp
                FROM player_scores
                WHERE league_id = ? AND wordle_number = ?
                ORDER BY player_name
                """, (league_id, latest_wordle))
                
                latest_scores = cursor.fetchall()
                for score_row in latest_scores:
                    player, score, pattern, timestamp = score_row
                    print(f"  {player}: Score={score}, Pattern={pattern}, Time={timestamp}")
        
        # Check for any potential duplicates
        cursor.execute("""
        SELECT player_name, wordle_number, league_id, COUNT(*)
        FROM player_scores
        GROUP BY player_name, wordle_number, league_id
        HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print("\nWARNING: Potential duplicates found in player_scores:")
            for dup in duplicates:
                print(f"  {dup[0]}, Wordle {dup[1]}, League {dup[2]}: {dup[3]} entries")
        else:
            print("\nNo duplicates found in player_scores table.")
            
        return True
        
    except Exception as e:
        logging.error(f"Error verifying migration: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

def main():
    """Run the migration and verification process"""
    print("=== Unified Table Verification ===")
    print("This script will create and verify the new unified player_scores table")
    
    # Create the unified table
    print("\n1. Creating unified player_scores table...")
    if create_unified_table():
        print("SUCCESS: Created unified player_scores table")
    else:
        print("FAILED: Could not create unified player_scores table")
        return
    
    # Migrate from scores table
    print("\n2. Migrating data from 'scores' table...")
    if migrate_from_scores_table():
        print("SUCCESS: Migrated data from scores table")
    else:
        print("FAILED: Could not migrate from scores table")
        
    # Migrate from score table
    print("\n3. Migrating data from 'score' table...")
    if migrate_from_score_table():
        print("SUCCESS: Migrated data from score table")
    else:
        print("FAILED: Could not migrate from score table")
        
    # Verify the migration
    print("\n4. Verifying migration...")
    if verify_migration():
        print("\nVERIFICATION COMPLETE: Migration successful")
    else:
        print("\nVERIFICATION FAILED: Please check the logs")
    
if __name__ == "__main__":
    main()
