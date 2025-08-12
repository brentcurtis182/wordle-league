#!/usr/bin/env python3
import sqlite3
import logging
import os
import re
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_database_issues():
    """Delete Vox's erroneous Wordle #1503 score and fix any other database issues"""
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

def fix_emoji_patterns():
    """Fix emoji patterns in HTML files by removing appended date/time text"""
    try:
        pal_daily_dir = 'website_export/pal/daily'
        if not os.path.exists(pal_daily_dir):
            logging.error(f"Directory not found: {pal_daily_dir}")
            return
        
        logging.info(f"Scanning directory: {pal_daily_dir}")
        
        # Process all Wordle HTML files in the PAL directory
        for file_name in os.listdir(pal_daily_dir):
            if file_name.startswith('wordle-') and file_name.endswith('.html'):
                file_path = os.path.join(pal_daily_dir, file_name)
                logging.info(f"Processing file: {file_path}")
                
                # Create a backup
                backup_file = f"{file_path}.bak"
                if not os.path.exists(backup_file):
                    shutil.copy2(file_path, backup_file)
                    logging.info(f"Created backup: {backup_file}")
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Fix emoji patterns - looking for any text after the emoji squares
                pattern = r'(<div class="emoji-row">[\u2B1B\u2B1C\u{1F7E5}-\u{1F7EB}]{5})[^<]+(</div>)'
                new_content = re.sub(pattern, r'\1\2', content)
                
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    logging.info(f"Fixed emoji patterns in: {file_path}")
                else:
                    logging.info(f"No emoji pattern issues found in: {file_path}")
    
    except Exception as e:
        logging.error(f"Error fixing emoji patterns: {e}")

def manually_fix_vox_html():
    """Manually remove Vox's score card from Wordle 1503 HTML file"""
    try:
        file_path = 'website_export/pal/daily/wordle-1503.html'
        if not os.path.exists(file_path):
            logging.error(f"File not found: {file_path}")
            return
        
        logging.info(f"Processing file: {file_path}")
        
        # Create a backup
        backup_file = f"{file_path}.manual_fix.bak"
        if not os.path.exists(backup_file):
            shutil.copy2(file_path, backup_file)
            logging.info(f"Created backup: {backup_file}")
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find and remove Vox's score card
        start_pattern = '<div class="score-card">[\\s\\S]*?<div class="player-name">Vox</div>'
        end_pattern = '</div>[\\s\\S]*?</div>[\\s\\S]*?</div>'
        pattern = f"({start_pattern}{end_pattern})"
        
        new_content = re.sub(pattern, '', content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logging.info(f"Manually removed Vox's score card from: {file_path}")
        else:
            logging.info(f"Could not find Vox's score card in: {file_path}")
    
    except Exception as e:
        logging.error(f"Error manually fixing Vox HTML: {e}")

if __name__ == "__main__":
    logging.info("Starting comprehensive fix script")
    fix_database_issues()
    fix_emoji_patterns()
    manually_fix_vox_html()
    logging.info("Comprehensive fix script completed")
