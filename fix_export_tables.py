#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fix export script to only use the correct tables (scores and players).
This ensures we don't have inconsistencies between different data sources.
"""

import sqlite3
import logging
import os
import re
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def backup_file(file_path):
    """Create a backup of the original file"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_path = f"{file_path}_{timestamp}_backup"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backup created at: {backup_path}")
    return backup_path

def fix_export_script(file_path='export_leaderboard_multi_league.py'):
    """
    Fix the export script to only use the correct database tables.
    
    Args:
        file_path: Path to the export script file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, file_path)
    
    if not os.path.exists(full_path):
        logging.error(f"File not found: {full_path}")
        return False
    
    # Create a backup of the original file
    backup_path = backup_file(full_path)
    
    # Read the entire file
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace references to old tables with new ones
    # Replace 'player' table with 'players'
    modified_content = re.sub(r'\bplayer\b(?!\s*s)', 'players', content)
    
    # Replace 'score' table with 'scores'
    modified_content = re.sub(r'\bscore\b(?!\s*s)', 'scores', modified_content)
    
    # Replace old field names with new ones if they differ
    # For example, 'wordle_num' -> 'wordle_number'
    modified_content = modified_content.replace('wordle_num', 'wordle_number')
    
    # Write the modified content back to the file
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    logging.info(f"Successfully updated export script to use only the correct tables")
    
    # Additional check - look for remaining references to old tables
    remaining_old_references = []
    if 'player ' in modified_content or 'player.' in modified_content:
        remaining_old_references.append('player')
    if 'score ' in modified_content or 'score.' in modified_content:
        remaining_old_references.append('score')
    
    if remaining_old_references:
        logging.warning(f"Possible remaining references to old tables: {remaining_old_references}")
        logging.warning("Manual review may be needed to fix these references")
        return False
    
    return True

def verify_database(db_path='wordle_league.db'):
    """
    Verify that the database structure is consistent.
    
    Args:
        db_path: Path to the database file
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_db_path = os.path.join(script_dir, db_path)
    
    if not os.path.exists(full_db_path):
        logging.error(f"Database not found: {full_db_path}")
        return False
    
    conn = sqlite3.connect(full_db_path)
    cursor = conn.cursor()
    
    # Check for necessary tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    required_tables = ['scores', 'players']
    for table in required_tables:
        if table not in tables:
            logging.error(f"Required table '{table}' not found in database")
            conn.close()
            return False
    
    # Check for old tables that should be avoided
    old_tables = ['score', 'player', 'scores_backup']
    found_old_tables = [table for table in old_tables if table in tables]
    
    if found_old_tables:
        logging.warning(f"Found old tables that should be avoided: {found_old_tables}")
        
        # Offer to rename these tables to _old suffix to prevent accidental use
        choice = input(f"Do you want to rename old tables with _old suffix to prevent accidental use? (y/n): ")
        if choice.lower() == 'y':
            for old_table in found_old_tables:
                try:
                    cursor.execute(f"ALTER TABLE {old_table} RENAME TO {old_table}_old")
                    conn.commit()
                    logging.info(f"Renamed '{old_table}' to '{old_table}_old'")
                except sqlite3.Error as e:
                    logging.error(f"Error renaming table '{old_table}': {e}")
    
    conn.close()
    return True

if __name__ == "__main__":
    logging.info("Starting export script table fix")
    
    # Fix the export script
    success = fix_export_script()
    if success:
        logging.info("Export script updated successfully")
    else:
        logging.warning("Export script update may be incomplete, manual review recommended")
    
    # Verify database structure
    verify_database()
    
    logging.info("Fix completed. Run the export script to generate corrected website files.")
