#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract actual emoji patterns from HTML files and update database
Uses the cdk-visually-hidden elements to get complete, accurate data
"""

import re
import sqlite3
from bs4 import BeautifulSoup
import os
import logging
import shutil
from datetime import datetime

# Configure logging to handle emoji characters properly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("extract_and_update_patterns.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def backup_db():
    """Create a backup of the database before making changes."""
    try:
        backup_dir = 'db_backups'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'wordle_league_{timestamp}.db')
        
        # Copy the database to the backup location
        shutil.copy2('wordle_league.db', backup_path)
        logging.info(f"Database backed up to {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to create database backup: {e}")
        return False

def extract_player_name_from_phone(phone_number):
    """Map phone number to player name"""
    # Clean phone number of any formatting
    cleaned = ''.join(filter(str.isdigit, phone_number))
    
    # Player phone mapping
    phone_mapping = {
        '6129636824': 'Nanna',
        '7608462302': 'Evan',
        '9522215700': 'Joanna',
        '4256476950': 'Brent',
        '2063519843': 'Malia',
        '8587359353': 'Nanna'  # Added the number from your example
    }
    
    return phone_mapping.get(cleaned)

def extract_from_html_file(html_file_path):
    """Extract Wordle data from an HTML file"""
    if not os.path.exists(html_file_path):
        logging.error(f"HTML file not found: {html_file_path}")
        return []
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    hidden_elements = soup.select('.cdk-visually-hidden')
    
    logging.info(f"Found {len(hidden_elements)} hidden elements in {html_file_path}")
    
    extracted_data = []
    for hidden_elem in hidden_elements:
        hidden_text = hidden_elem.text
        
        if "Wordle" in hidden_text and "/6" in hidden_text:
            # Extract phone number using various formats
            phone_match = re.search(r'from\s+(\d[\s\d]+\d)', hidden_text)
            if not phone_match:
                phone_match = re.search(r'from\s+\(?(\d{3})\)?[\s-]*(\d{3})[\s-]*(\d{4})', hidden_text)
                if phone_match:
                    phone_number = f"{phone_match.group(1)}{phone_match.group(2)}{phone_match.group(3)}"
            else:
                # Remove spaces from the phone number
                phone_number = phone_match.group(1).replace(" ", "")
            
            if not phone_match:
                logging.warning(f"Could not extract phone number from: {hidden_text[:100]}")
                continue
            
            # Get player name
            player_name = extract_player_name_from_phone(phone_number)
            if not player_name:
                logging.warning(f"Could not identify player for phone {phone_number}")
                continue
            
            # Extract Wordle number
            wordle_match = re.search(r'Wordle\s+#?([\d,]+)', hidden_text)
            if not wordle_match:
                logging.warning(f"Could not extract Wordle number from: {hidden_text[:100]}")
                continue
            
            wordle_num = int(wordle_match.group(1).replace(',', ''))
            
            # Extract score
            score_match = re.search(r'([\dX])/6', hidden_text)
            if not score_match:
                logging.warning(f"Could not extract score from: {hidden_text[:100]}")
                continue
            
            score_value = score_match.group(1)
            score = 7 if score_value.upper() == 'X' else int(score_value)
            
            # Extract emoji pattern
            emoji_rows = re.findall(r'[⬛⬜🟨🟩]{5}', hidden_text)
            emoji_pattern = "\n".join(emoji_rows) if emoji_rows else None
            
            if emoji_pattern:
                data = {
                    'phone': phone_number,
                    'player': player_name,
                    'wordle_num': wordle_num,
                    'score': score,
                    'emoji_pattern': emoji_pattern
                }
                
                extracted_data.append(data)
                
                # Print safe version of the data
                try:
                    logging.info(f"Extracted data for {player_name}: Wordle #{wordle_num}, Score: {score}/6")
                    logging.info(f"Found emoji pattern with {len(emoji_rows)} rows")
                except UnicodeEncodeError:
                    logging.info(f"Extracted data for {player_name}: Wordle #{wordle_num}, Score: {score}/6 (Unicode emoji pattern found)")
    
    return extracted_data

def update_database_with_patterns(extracted_data):
    """Update database with extracted patterns"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        updated_count = 0
        for data in extracted_data:
            player = data['player']
            wordle_num = data['wordle_num']
            emoji_pattern = data['emoji_pattern']
            
            if not emoji_pattern:
                logging.warning(f"No emoji pattern to update for {player}, Wordle #{wordle_num}")
                continue
            
            # Update scores table
            cursor.execute(
                "SELECT id, emoji_pattern FROM scores WHERE player_name = ? AND wordle_num = ?",
                (player, wordle_num)
            )
            scores_result = cursor.fetchone()
            
            if scores_result:
                existing_pattern = scores_result['emoji_pattern']
                
                if not existing_pattern or existing_pattern.strip() == '':
                    cursor.execute(
                        "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                        (emoji_pattern, scores_result['id'])
                    )
                    logging.info(f"Updated emoji pattern for {player} in 'scores' table")
                    updated_count += 1
                elif existing_pattern != emoji_pattern:
                    cursor.execute(
                        "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                        (emoji_pattern, scores_result['id'])
                    )
                    logging.info(f"Replaced existing emoji pattern for {player} in 'scores' table")
                    updated_count += 1
                else:
                    logging.info(f"Emoji pattern already correct for {player} in 'scores' table")
            
            # Update score table - first get player_id
            cursor.execute("SELECT id FROM player WHERE name = ?", (player,))
            player_row = cursor.fetchone()
            
            if player_row:
                player_id = player_row['id']
                
                # Check if emoji_pattern column exists
                try:
                    cursor.execute("SELECT emoji_pattern FROM score LIMIT 1")
                    has_emoji_pattern = True
                except sqlite3.OperationalError:
                    has_emoji_pattern = False
                    logging.warning("'emoji_pattern' column doesn't exist in 'score' table")
                
                if has_emoji_pattern:
                    cursor.execute(
                        "SELECT id, emoji_pattern FROM score WHERE player_id = ? AND wordle_number = ?",
                        (player_id, wordle_num)
                    )
                    score_result = cursor.fetchone()
                    
                    if score_result:
                        existing_pattern = score_result['emoji_pattern']
                        
                        if not existing_pattern or existing_pattern.strip() == '':
                            cursor.execute(
                                "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                                (emoji_pattern, score_result['id'])
                            )
                            logging.info(f"Updated emoji pattern for {player} in 'score' table")
                            updated_count += 1
                        elif existing_pattern != emoji_pattern:
                            cursor.execute(
                                "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                                (emoji_pattern, score_result['id'])
                            )
                            logging.info(f"Replaced existing emoji pattern for {player} in 'score' table")
                            updated_count += 1
                        else:
                            logging.info(f"Emoji pattern already correct for {player} in 'score' table")
        
        conn.commit()
        logging.info(f"Database updated with {updated_count} emoji patterns")
        return updated_count
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()

def print_safe_pattern(player, pattern):
    """Print pattern in a way that works in Windows console"""
    if not pattern:
        print(f"{player}: No pattern")
        return
    
    rows = pattern.split('\n')
    print(f"{player} pattern ({len(rows)} rows):")
    
    try:
        print(pattern)
    except UnicodeEncodeError:
        # If emojis don't print, use text representation
        safe_pattern = pattern
        if pattern:
            safe_pattern = pattern.replace('⬛', '[B]').replace('⬜', '[W]') \
                                 .replace('🟨', '[Y]').replace('🟩', '[G]')
        print(safe_pattern)

def extract_and_update():
    """Extract emoji patterns from HTML files and update the database"""
    # First, back up the current database
    backup_db()
    
    # Find HTML files
    html_files = []
    for file in os.listdir('.'):
        if file.endswith('.html'):
            html_files.append(file)
    
    if not html_files:
        logging.warning("No HTML files found in current directory")
        return
    
    logging.info(f"Found {len(html_files)} HTML files to process")
    
    # Extract data from HTML files
    all_data = []
    for html_file in html_files:
        extracted_data = extract_from_html_file(html_file)
        all_data.extend(extracted_data)
    
    if not all_data:
        logging.warning("No Wordle data extracted from HTML files")
        return
    
    logging.info(f"Extracted {len(all_data)} Wordle data items total")
    
    # Print extracted patterns
    print("\n=== Extracted Emoji Patterns ===\n")
    for data in all_data:
        player = data['player']
        wordle_num = data['wordle_num']
        score = data['score']
        pattern = data['emoji_pattern']
        
        print(f"\n{'=' * 40}")
        print(f"Player: {player} - Wordle #{wordle_num} - Score: {score}/6")
        print_safe_pattern(player, pattern)
        print(f"{'=' * 40}")
    
    # Update database
    updated_count = update_database_with_patterns(all_data)
    
    if updated_count > 0:
        # Export website files
        logging.info("Exporting website files")
        os.system("python export_leaderboard.py")
        
        # Publish to GitHub
        logging.info("Publishing to GitHub")
        os.system("python server_publish_to_github.py")
        
        logging.info("Website has been updated with correct emoji patterns")
    else:
        logging.info("No new emoji patterns to update")

if __name__ == "__main__":
    logging.info("Starting emoji pattern extraction and update...")
    extract_and_update()
    logging.info("Script execution completed")
