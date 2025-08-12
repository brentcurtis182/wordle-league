#!/usr/bin/env python
# Verify and fix both Joanna and Evan's scores

import sqlite3
import logging
from datetime import datetime

# Configure logging with encoding to handle emoji
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("score_fixes.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def check_database_tables():
    """Check all tables in database to determine structure"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        logging.info(f"Database contains {len(tables)} tables:")
        for table in tables:
            table_name = table[0]
            logging.info(f"Table: {table_name}")
            
            # Get columns for this table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            logging.info(f"  Columns: {', '.join(column_names)}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logging.info(f"  Row count: {count}")
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error examining database: {e}")
        return False

def get_player_scores(player_name, wordle_num=None):
    """Get scores for a specific player, optionally filtered by wordle number"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Check if player exists in player table
        cursor.execute("SELECT id FROM player WHERE name = ?", (player_name,))
        player = cursor.fetchone()
        
        scores = []
        # Check score table (singular)
        if player:
            player_id = player['id']
            query = "SELECT * FROM score WHERE player_id = ?"
            params = (player_id,)
            
            if wordle_num:
                query += " AND wordle_number = ?"
                params = (player_id, wordle_num)
                
            cursor.execute(query, params)
            scores = cursor.fetchall()
            logging.info(f"Found {len(scores)} records for {player_name} in 'score' table")
            
            if scores:
                for score in scores:
                    score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
                    logging.info(f"  Wordle #{score['wordle_number']}, Score: {score_display}")
        else:
            logging.warning(f"Player {player_name} not found in player table")
        
        conn.close()
        return scores
    except Exception as e:
        logging.error(f"Error getting player scores: {e}")
        return []

def fix_evan_score():
    """Fix Evan's Wordle #1500 score to X/6"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Find Evan in player table
        cursor.execute("SELECT id FROM player WHERE name = 'Evan'")
        result = cursor.fetchone()
        if not result:
            logging.error("Evan not found in player table")
            conn.close()
            return False
            
        evan_id = result[0]
        logging.info(f"Found Evan's ID: {evan_id}")
        
        # Check if Evan has a score for Wordle #1500
        cursor.execute("SELECT id, score FROM score WHERE player_id = ? AND wordle_number = 1500", (evan_id,))
        score = cursor.fetchone()
        
        if score:
            score_id, current_score = score
            logging.info(f"Found Evan's score for Wordle #1500: {current_score}/6")
            
            if current_score != 7:
                # Update score to 7 (X/6)
                cursor.execute("UPDATE score SET score = 7 WHERE id = ?", (score_id,))
                conn.commit()
                logging.info("✅ Updated Evan's score to X/6 (value 7)")
            else:
                logging.info("Evan's score is already set to X/6 (value 7)")
        else:
            logging.error("Could not find Evan's score for Wordle #1500")
            conn.close()
            return False
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error fixing Evan's score: {e}")
        return False

def verify_joanna_score():
    """Verify Joanna's Wordle #1500 score is correct"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Find Joanna in player table
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.error("Joanna not found in player table")
            conn.close()
            return False
            
        joanna_id = result[0]
        logging.info(f"Found Joanna's ID: {joanna_id}")
        
        # Check if Joanna has a score for Wordle #1500
        cursor.execute("SELECT id, score, emoji_pattern FROM score WHERE player_id = ? AND wordle_number = 1500", (joanna_id,))
        score = cursor.fetchone()
        
        if score:
            score_id, current_score, emoji_pattern = score
            logging.info(f"Found Joanna's score for Wordle #1500: {current_score}/6")
            logging.info(f"Emoji pattern: {emoji_pattern}")
            conn.close()
            return True
        else:
            logging.error("Could not find Joanna's score for Wordle #1500")
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Error verifying Joanna's score: {e}")
        return False

if __name__ == "__main__":
    logging.info("Checking database structure...")
    check_database_tables()
    
    logging.info("\nVerifying Joanna's score...")
    joanna_verified = verify_joanna_score()
    
    logging.info("\nGetting Evan's current scores...")
    evan_scores = get_player_scores("Evan", 1500)
    
    logging.info("\nFixing Evan's score to X/6...")
    evan_fixed = fix_evan_score()
    
    if evan_fixed:
        logging.info("\nEvan's score after fix:")
        get_player_scores("Evan", 1500)
        
        logging.info("\nRunning integrated_auto_update.py to update website...")
        import os
        os.system("python integrated_auto_update.py")
    else:
        logging.error("Could not fix Evan's score")
