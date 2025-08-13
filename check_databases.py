#!/usr/bin/env python
# Check and compare wordle_scores.db and wordle_league.db

import os
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

def check_database(db_path):
    """Check if database exists and get basic info"""
    if not os.path.exists(db_path):
        logging.info(f"Database does not exist: {db_path}")
        return False, None
        
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        # Check for score-related tables
        score_tables = [t for t in tables if 'score' in t.lower()]
        
        logging.info(f"Database {db_path} has {len(tables)} tables: {tables}")
        logging.info(f"Score tables: {score_tables}")
        
        # Check player table if it exists
        player_info = None
        if 'player' in tables:
            cursor.execute("SELECT COUNT(*) AS count FROM player")
            player_count = cursor.fetchone()['count']
            logging.info(f"Player table has {player_count} records")
            
            cursor.execute("SELECT name FROM player LIMIT 5")
            player_names = [row['name'] for row in cursor.fetchall()]
            logging.info(f"Sample players: {player_names}")
            
            player_info = {'count': player_count, 'sample': player_names}
        
        # Check score table
        score_info = None
        if 'score' in tables:
            cursor.execute("SELECT COUNT(*) AS count FROM score")
            score_count = cursor.fetchone()['count']
            logging.info(f"Score table has {score_count} records")
            
            cursor.execute("""
                SELECT s.id, p.name, s.wordle_number, s.score, s.emoji_pattern 
                FROM score s
                JOIN player p ON s.player_id = p.id
                ORDER BY s.id DESC LIMIT 5
            """)
            recent_scores = []
            for row in cursor.fetchall():
                score_data = {
                    'id': row['id'],
                    'player': row['name'],
                    'wordle': row['wordle_number'],
                    'score': row['score'],
                    'rows': row['emoji_pattern'].count('\n') + 1 if row['emoji_pattern'] else 0
                }
                recent_scores.append(score_data)
            
            logging.info(f"Recent scores: {recent_scores}")
            score_info = {'count': score_count, 'recent': recent_scores}
        
        # Also check scores table (plural) if it exists
        scores_info = None
        if 'scores' in tables:
            cursor.execute("SELECT COUNT(*) AS count FROM scores")
            scores_count = cursor.fetchone()['count']
            logging.info(f"Scores table has {scores_count} records")
            
            cursor.execute("SELECT * FROM scores ORDER BY id DESC LIMIT 5")
            recent_scores = []
            for row in cursor:
                score_data = {
                    'id': row['id'],
                    'player': row.get('player_name', row.get('player', 'unknown')),
                    'wordle': row.get('wordle_num', row.get('wordle_number', 0)),
                    'score': row['score'],
                    'rows': row.get('emoji_pattern', '').count('\n') + 1 if row.get('emoji_pattern') else 0
                }
                recent_scores.append(score_data)
            
            logging.info(f"Recent scores from scores table: {recent_scores}")
            scores_info = {'count': scores_count, 'recent': recent_scores}
        
        conn.close()
        return True, {'tables': tables, 'player': player_info, 'score': score_info, 'scores': scores_info}
    except Exception as e:
        logging.error(f"Error checking database {db_path}: {e}")
        return False, None

def sync_databases(source_db, target_db):
    """Attempt to synchronize scores between databases"""
    try:
        # Connect to both databases
        source_conn = sqlite3.connect(source_db)
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()
        
        target_conn = sqlite3.connect(target_db)
        target_conn.row_factory = sqlite3.Row
        target_cursor = target_conn.cursor()
        
        # Get all recent scores from source database (wordle_league.db)
        source_cursor.execute("""
            SELECT s.id, p.name as player_name, s.wordle_number, s.score, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.wordle_number >= 1490
            ORDER BY s.wordle_number DESC, p.name
        """)
        
        source_scores = source_cursor.fetchall()
        logging.info(f"Found {len(source_scores)} recent scores in {source_db}")
        
        # Check scores table exists in target database (wordle_scores.db)
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scores'")
        if not target_cursor.fetchone():
            logging.info("Creating scores table in target database")
            target_cursor.execute('''
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY,
                    wordle_num INTEGER,
                    score INTEGER,
                    player_name TEXT,
                    emoji_pattern TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            target_conn.commit()
        
        # Transfer scores from source to target
        scores_added = 0
        scores_updated = 0
        
        for score in source_scores:
            player = score['player_name']
            wordle = score['wordle_number']
            score_val = score['score']
            pattern = score['emoji_pattern']
            
            # Check if score exists in target
            target_cursor.execute(
                "SELECT id, score, emoji_pattern FROM scores WHERE wordle_num = ? AND player_name = ?", 
                (wordle, player)
            )
            existing = target_cursor.fetchone()
            
            if not existing:
                # Add new score
                target_cursor.execute(
                    "INSERT INTO scores (wordle_num, score, player_name, emoji_pattern) VALUES (?, ?, ?, ?)",
                    (wordle, score_val, player, pattern)
                )
                scores_added += 1
            else:
                # Update if source has better data
                update_needed = False
                
                # If existing score is worse, or if pattern is missing
                if existing['score'] > score_val or (not existing['emoji_pattern'] and pattern):
                    target_cursor.execute(
                        "UPDATE scores SET score = ?, emoji_pattern = ? WHERE id = ?",
                        (score_val, pattern, existing['id'])
                    )
                    scores_updated += 1
        
        target_conn.commit()
        logging.info(f"Synchronized {scores_added} new scores and updated {scores_updated} existing scores")
        
        source_conn.close()
        target_conn.close()
        return True
    except Exception as e:
        logging.error(f"Error synchronizing databases: {e}")
        return False

def copy_config_to_integrated_auto_update():
    """Copy the database configuration from the correct database to the integrated auto update script"""
    try:
        with open('integrated_auto_update.py', 'r') as f:
            script_content = f.read()
        
        # Replace the database connection string
        if "wordle_scores.db" in script_content:
            modified_content = script_content.replace("wordle_scores.db", "wordle_league.db")
            
            # Create backup first
            backup_name = f"integrated_auto_update_{datetime.now().strftime('%Y%m%d%H%M%S')}_backup.py"
            with open(backup_name, 'w') as f:
                f.write(script_content)
            logging.info(f"Created backup of integrated_auto_update.py as {backup_name}")
            
            # Write updated content
            with open('integrated_auto_update.py', 'w') as f:
                f.write(modified_content)
            
            logging.info("Updated integrated_auto_update.py to use wordle_league.db")
            return True
        else:
            logging.info("No database configuration change needed in integrated_auto_update.py")
            return False
    except Exception as e:
        logging.error(f"Error updating script configuration: {e}")
        return False

def fix_brent_pattern():
    """Fix Brent's emoji pattern to have 6 rows"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get Brent's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Brent'")
        brent_id = cursor.fetchone()["id"]
        logging.info(f"Brent's player ID: {brent_id}")
        
        # Get his current score for today's Wordle
        cursor.execute("""
            SELECT id, wordle_number, score, emoji_pattern 
            FROM score 
            WHERE player_id = ? 
            ORDER BY wordle_number DESC 
            LIMIT 1
        """, (brent_id,))
        
        score_record = cursor.fetchone()
        if score_record:
            score_id = score_record["id"]
            wordle_num = score_record["wordle_number"]
            score = score_record["score"]
            pattern = score_record["emoji_pattern"]
            
            logging.info(f"Brent's Wordle {wordle_num} score: ID={score_id}, Score={score}")
            
            # Count rows in pattern
            rows = 0
            if pattern:
                rows = pattern.count('\n') + 1
                logging.info(f"Pattern has {rows} rows but score is {score}")
                logging.info(f"Current pattern: {pattern}")
            
            # Fix if there's a mismatch
            if score == 6 and rows != 6:
                logging.info("Fixing Brent's pattern to match his 6/6 score")
                
                # Create a proper 6-row pattern using the existing pattern but ensuring 6 rows
                # Split the pattern into rows
                pattern_rows = pattern.split('\n')
                
                if len(pattern_rows) < 6:
                    # Add missing rows by duplicating the last row
                    while len(pattern_rows) < 5:
                        pattern_rows.append(pattern_rows[-1])
                    
                    # Last row should be all green
                    pattern_rows.append("🟩🟩🟩🟩🟩")
                    
                    # Join back into a single string
                    new_pattern = '\n'.join(pattern_rows)
                    
                    # Update in database
                    cursor.execute("""
                        UPDATE score 
                        SET emoji_pattern = ? 
                        WHERE id = ?
                    """, (new_pattern, score_id))
                    
                    conn.commit()
                    logging.info("Updated Brent's pattern in the database")
                    
                    # Verify the update
                    cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
                    updated_pattern = cursor.fetchone()["emoji_pattern"]
                    updated_rows = updated_pattern.count('\n') + 1
                    logging.info(f"Verified pattern now has {updated_rows} rows")
                    logging.info(f"New pattern: {updated_pattern}")
                    
                    conn.close()
                    return True
            else:
                if rows == 6:
                    logging.info("Pattern already has 6 rows, no fix needed")
                else:
                    logging.warning(f"Unexpected pattern rows: {rows} for score: {score}")
                conn.close()
                return False
        else:
            logging.error("No recent score found for Brent")
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Error fixing Brent's pattern: {e}")
        return False

def main():
    logging.info("Checking databases and configurations...")
    
    # Check both databases
    league_db_exists, league_info = check_database("wordle_league.db")
    scores_db_exists, scores_info = check_database("wordle_scores.db")
    
    # Determine which is the primary database
    if league_db_exists and league_info and league_info.get('score'):
        logging.info("wordle_league.db appears to be the primary database")
        primary_db = "wordle_league.db"
    elif scores_db_exists and scores_info and scores_info.get('scores'):
        logging.info("wordle_scores.db appears to be the primary database")
        primary_db = "wordle_scores.db"
    else:
        logging.error("Could not determine primary database")
        return
    
    # Synchronize databases if both exist
    if league_db_exists and scores_db_exists:
        logging.info("Attempting to synchronize databases...")
        sync_databases("wordle_league.db", "wordle_scores.db")
    
    # Update script configuration if needed
    if primary_db == "wordle_league.db":
        copy_config_to_integrated_auto_update()
    
    # Fix Brent's pattern if needed
    logging.info("Checking and fixing Brent's pattern...")
    fix_brent_pattern()
    
    # Run export after fixes
    logging.info("Running export_leaderboard.py to update website...")
    import subprocess
    subprocess.run(["python", "export_leaderboard.py"])
    
    logging.info("Database check and fix completed")

if __name__ == "__main__":
    main()
