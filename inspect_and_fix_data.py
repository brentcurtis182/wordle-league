#!/usr/bin/env python3
"""
Inspect and fix Wordle League data issues
-----------------------------------------
This script diagnoses data issues in the Wordle League database
and restores correct data while preserving structural improvements.

It checks:
1. Database integrity and structure
2. Emoji pattern availability
3. Score data completeness across all leagues
"""

import os
import sqlite3
import logging
import json
from datetime import datetime, timedelta
import shutil
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_fix.log"),
        logging.StreamHandler()
    ]
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(SCRIPT_DIR, "database_backup")
LEAGUES = {
    'warriorz': {'id': 1, 'path': 'website_export/index.html', 'name': 'Wordle Warriorz'},
    'gang': {'id': 2, 'path': 'website_export/gang/index.html', 'name': 'Wordle Gang'},
    'pal': {'id': 3, 'path': 'website_export/pal/index.html', 'name': 'Wordle PAL'},
    'party': {'id': 4, 'path': 'website_export/party/index.html', 'name': 'Wordle Party'},
    'vball': {'id': 5, 'path': 'website_export/vball/index.html', 'name': 'Wordle Vball'}
}

# Create backup directory if it doesn't exist
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_database(db_path):
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"wordle_league_{timestamp}.db")
    shutil.copy2(db_path, backup_path)
    logging.info(f"Created database backup at {backup_path}")
    return backup_path

def inspect_database(db_path):
    """Inspect database structure and data"""
    logging.info(f"Inspecting database: {db_path}")
    
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    logging.info(f"Found tables: {tables}")
    
    # Check players table
    if 'players' in tables:
        cursor.execute("PRAGMA table_info(players)")
        player_columns = [row[1] for row in cursor.fetchall()]
        logging.info(f"Players table columns: {player_columns}")
        
        # Count players by league
        cursor.execute("SELECT league_id, COUNT(*) FROM players GROUP BY league_id")
        player_counts = cursor.fetchall()
        for league_id, count in player_counts:
            logging.info(f"League ID {league_id}: {count} players")
    else:
        logging.error("No players table found!")
    
    # Check scores table
    if 'scores' in tables:
        cursor.execute("PRAGMA table_info(scores)")
        score_columns = [row[1] for row in cursor.fetchall()]
        logging.info(f"Scores table columns: {score_columns}")
        
        # Check if emoji_pattern column exists
        if 'emoji_pattern' in score_columns:
            cursor.execute("SELECT COUNT(*) FROM scores WHERE emoji_pattern IS NOT NULL")
            pattern_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM scores")
            total_scores = cursor.fetchone()[0]
            logging.info(f"Emoji patterns: {pattern_count}/{total_scores} scores have patterns")
            
            if pattern_count == 0:
                logging.warning("No emoji patterns found in database!")
        else:
            logging.warning("No emoji_pattern column in scores table!")
        
        # Count scores by date (last 7 days)
        today = datetime.now().date()
        for i in range(7):
            check_date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM scores WHERE date = ?", (check_date,))
            score_count = cursor.fetchone()[0]
            logging.info(f"Scores on {check_date}: {score_count}")
    else:
        logging.error("No scores table found!")
    
    conn.close()
    return True

def fix_emoji_patterns(db_path, html_dir):
    """Extract emoji patterns from HTML and update database"""
    logging.info("Attempting to fix missing emoji patterns...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if emoji_pattern column exists in scores table
    cursor.execute("PRAGMA table_info(scores)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'emoji_pattern' not in columns:
        logging.info("Adding emoji_pattern column to scores table...")
        cursor.execute("ALTER TABLE scores ADD COLUMN emoji_pattern TEXT")
    
    # Get all leagues' HTML files
    patterns_added = 0
    for league_key, league_info in LEAGUES.items():
        html_path = os.path.join(SCRIPT_DIR, league_info['path'])
        if not os.path.exists(html_path):
            logging.warning(f"HTML file not found: {html_path}")
            continue
        
        logging.info(f"Extracting patterns from {league_key} league HTML...")
        
        # Parse HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Find all emoji patterns
        emoji_containers = soup.select('.emoji-container')
        for container in emoji_containers:
            # Find associated player name
            player_div = container.find_previous_sibling('.player-info')
            if not player_div:
                continue
                
            player_name_div = player_div.select_one('.player-name')
            if not player_name_div:
                continue
                
            player_name = player_name_div.get_text().strip()
            
            # Find score
            score_div = player_div.select_one('.player-score span')
            if not score_div:
                continue
                
            score_text = score_div.get_text().strip()
            
            # Extract pattern
            pattern_div = container.select_one('.emoji-pattern')
            if not pattern_div:
                continue
                
            emoji_pattern = pattern_div.get_text().strip()
            
            # Skip empty or "No emoji pattern" patterns
            if not emoji_pattern or "No emoji pattern" in emoji_pattern:
                continue
            
            # Update database
            try:
                cursor.execute(
                    """
                    UPDATE scores SET emoji_pattern = ?
                    WHERE player_id = (SELECT id FROM players WHERE name = ?)
                    AND score = ?
                    AND emoji_pattern IS NULL
                    """,
                    (emoji_pattern, player_name, score_text)
                )
                if cursor.rowcount > 0:
                    patterns_added += cursor.rowcount
            except Exception as e:
                logging.error(f"Error updating pattern for {player_name}: {e}")
    
    conn.commit()
    conn.close()
    
    logging.info(f"Added {patterns_added} emoji patterns to database")
    return patterns_added > 0

def restore_data_from_backup(db_path):
    """Check for recent backups and restore missing data"""
    logging.info("Looking for previous database backups with more complete data...")
    
    # Find all database backups
    backups = []
    for root, _, files in os.walk(SCRIPT_DIR):
        for file in files:
            if file.endswith('.db') and file != os.path.basename(db_path):
                backup_path = os.path.join(root, file)
                backups.append(backup_path)
    
    if not backups:
        logging.warning("No database backups found")
        return False
    
    logging.info(f"Found {len(backups)} potential database backups")
    
    # Connect to current database
    conn_current = sqlite3.connect(db_path)
    cursor_current = conn.cursor()
    
    # Get current score count
    cursor_current.execute("SELECT COUNT(*) FROM scores")
    current_score_count = cursor_current.fetchone()[0]
    logging.info(f"Current database has {current_score_count} scores")
    
    # Find backup with most scores
    best_backup = None
    best_score_count = current_score_count
    
    for backup in backups:
        try:
            conn_backup = sqlite3.connect(backup)
            cursor_backup = conn_backup.cursor()
            
            cursor_backup.execute("SELECT COUNT(*) FROM scores")
            backup_score_count = cursor_backup.fetchone()[0]
            
            logging.info(f"Backup {backup} has {backup_score_count} scores")
            
            if backup_score_count > best_score_count:
                best_backup = backup
                best_score_count = backup_score_count
            
            conn_backup.close()
        except Exception as e:
            logging.warning(f"Couldn't check backup {backup}: {e}")
    
    if not best_backup:
        logging.warning("No better backup found")
        conn_current.close()
        return False
    
    logging.info(f"Found better backup with {best_score_count} scores: {best_backup}")
    
    # Create another backup of current db before restoration
    backup_database(db_path)
    
    # Copy the backup over the current database
    conn_current.close()
    shutil.copy2(best_backup, db_path)
    logging.info(f"Restored database from {best_backup}")
    
    return True

def fix_html_data():
    """Run the update script to fix HTML data"""
    import subprocess
    logging.info("Running update script to refresh HTML with correct data...")
    
    try:
        result = subprocess.run(
            ['python', 'update_all_correct_structure.py'], 
            check=True,
            capture_output=True, 
            text=True
        )
        logging.info("Successfully updated all leagues")
        logging.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to update leagues: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False

def apply_standardization():
    """Apply standardization script to maintain structural improvements"""
    import subprocess
    logging.info("Applying standardization to maintain structural improvements...")
    
    try:
        result = subprocess.run(
            ['python', 'standardize_leagues.py'], 
            check=True,
            capture_output=True, 
            text=True
        )
        logging.info("Successfully standardized all leagues")
        logging.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to standardize leagues: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False

def main():
    """Main function to inspect and fix data issues"""
    db_path = os.path.join(SCRIPT_DIR, "wordle_league.db")
    html_dir = os.path.join(SCRIPT_DIR, "website_export")
    
    logging.info("Starting data inspection and fix...")
    
    # Step 1: Create a backup
    backup_database(db_path)
    
    # Step 2: Inspect database
    if not inspect_database(db_path):
        logging.error("Database inspection failed")
        return 1
    
    # Step 3: Fix emoji patterns from HTML if needed
    fix_emoji_patterns(db_path, html_dir)
    
    # Step 4: Restore data from backup if available
    restored = restore_data_from_backup(db_path)
    
    # Step 5: Update HTML with correct data
    if restored:
        if not fix_html_data():
            logging.error("Failed to update HTML with correct data")
            return 1
    
    # Step 6: Apply standardization to maintain structural improvements
    if not apply_standardization():
        logging.error("Failed to apply standardization")
        return 1
    
    logging.info("Data inspection and fix complete")
    return 0

if __name__ == "__main__":
    exit_code = main()
    print("\nData inspection and fix complete.")
    print("Check the data_fix.log file for details.")
    exit(exit_code)
