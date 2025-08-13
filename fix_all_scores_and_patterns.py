#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to fix all Wordle #1500 scores and emoji patterns for all players.

This script:
1. Backs up the current database
2. Extracts fresh scores and emoji patterns from conversation data
3. Ensures the correct data is saved in both 'scores' and 'score' tables
4. Updates the website with the corrected data
"""

import sqlite3
import logging
import os
import sys
import subprocess
import re
import bs4
from bs4 import BeautifulSoup
import shutil
from datetime import datetime

# Configure logging with UTF-8 encoding to handle emoji characters
logging.basicConfig(
    filename='fix_all_scores_patterns.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Add console handler
console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# Regex patterns for extracting Wordle scores and emoji patterns
wordle_patterns = [
    re.compile(r'Wordle\s+#?(\d+(?:,\d+)?)\s+(\d+)/6'),
    re.compile(r'Wordle[:\s]+#?(\d+(?:,\d+)?)\s*[:\s]+(\d+)/6'),
    re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*(\d+)/6')
]

failed_patterns = [
    re.compile(r'Wordle\s+#?(\d+(?:,\d+)?)\s+X/6'),
    re.compile(r'Wordle[:\s]+#?(\d+(?:,\d+)?)\s*[:\s]+X/6'),
    re.compile(r'Wordle[^\d]*(\d+(?:,\d+)?)[^\d]*X/6')
]

# Emoji detection regex - more comprehensive to match all square colors
emoji_regex = re.compile(r'((?:⬛|⬜|🟨|🟩|⬜️|⬛️|🟨️|🟩️)+)')

# Enhanced alt text regex for emoji extraction
alt_text_regex = re.compile(r'alt="([⬛⬜🟨🟩]|black large square|white large square|yellow square|green square)"')
enhanced_alt_regex = re.compile(r'alt=["\'](black large square|white large square|yellow square|green square|⬛|⬜|🟨|🟩)["\']')

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

def load_html_conversations():
    """Load HTML conversation files from the current directory."""
    conversations = []
    for filename in os.listdir('.'):
        if filename.startswith('conversation_') and filename.endswith('.html'):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                conversations.append((filename, html_content))
                logging.info(f"Loaded conversation file: {filename}")
            except Exception as e:
                logging.error(f"Error loading {filename}: {e}")
    
    return conversations

def extract_scores_and_patterns(html_content):
    """Extract Wordle scores and emoji patterns from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all message containers
    messages = soup.find_all('div', class_='message')
    
    results = []
    for message in messages:
        try:
            # Find player name
            sender_element = message.find('div', class_='sender')
            if not sender_element:
                continue
            
            player_name = sender_element.get_text().strip()
            
            # Skip system messages
            if player_name.lower() in ['system', 'admin', 'bot']:
                continue
            
            # Extract message content
            content_element = message.find('div', class_='content')
            if not content_element:
                continue
            
            message_content = content_element.get_text().strip()
            message_html = str(content_element)
            
            # Look for Wordle scores in this message
            wordle_matches = []
            for pattern in wordle_patterns:
                matches = pattern.findall(message_content)
                if matches:
                    wordle_matches.extend(matches)
            
            # Look for failed attempts
            failed_matches = []
            for pattern in failed_patterns:
                matches = pattern.findall(message_content)
                if matches:
                    for match in matches:
                        failed_matches.append(match)
            
            # Extract emoji pattern
            emoji_pattern_to_save = None
            
            # Try to extract from text content
            emoji_matches = emoji_regex.findall(message_content)
            if emoji_matches:
                valid_emoji_matches = []
                for match in emoji_matches:
                    # Split into rows
                    rows = match.split()
                    # Only accept if it looks like a valid Wordle pattern (1-6 rows)
                    if 1 <= len(rows) <= 6:
                        valid_emoji_matches.append('\n'.join(rows))
                
                if valid_emoji_matches:
                    # Select the pattern with the most rows
                    emoji_pattern_to_save = max(valid_emoji_matches, key=lambda p: p.count('\n') + 1)
            
            # If no pattern found in text, try alt text extraction
            if not emoji_pattern_to_save:
                alt_matches = alt_text_regex.findall(message_html)
                enhanced_alt_matches = enhanced_alt_regex.findall(message_html)
                
                if alt_matches or enhanced_alt_matches:
                    # Convert alt text matches to emoji characters
                    all_matches = alt_matches + enhanced_alt_matches
                    emoji_rows = []
                    current_row = []
                    
                    for match in all_matches:
                        if match == "black large square" or match == "⬛":
                            current_row.append("⬛")
                        elif match == "white large square" or match == "⬜":
                            current_row.append("⬜")
                        elif match == "yellow square" or match == "🟨":
                            current_row.append("🟨")
                        elif match == "green square" or match == "🟩":
                            current_row.append("🟩")
                        
                        # Start a new row after 5 squares
                        if len(current_row) == 5:
                            emoji_rows.append(''.join(current_row))
                            current_row = []
                    
                    # Add any remaining squares as a row
                    if current_row:
                        emoji_rows.append(''.join(current_row))
                    
                    if emoji_rows and 1 <= len(emoji_rows) <= 6:
                        emoji_pattern_to_save = '\n'.join(emoji_rows)
            
            # Process regular scores
            for wordle_match in wordle_matches:
                # Remove commas from the Wordle number before converting to int
                wordle_num_str = wordle_match[0].replace(',', '')
                wordle_num = int(wordle_num_str)
                score = int(wordle_match[1])
                
                results.append({
                    'player_name': player_name,
                    'wordle_num': wordle_num,
                    'score': score,
                    'emoji_pattern': emoji_pattern_to_save
                })
            
            # Process failed attempts (X/6)
            for failed_match in failed_matches:
                # Remove commas from the Wordle number before converting to int
                wordle_num_str = failed_match.replace(',', '')
                wordle_num = int(wordle_num_str)
                score = 7  # Use 7 to represent X/6 (failed attempt)
                
                results.append({
                    'player_name': player_name,
                    'wordle_num': wordle_num,
                    'score': score,
                    'emoji_pattern': emoji_pattern_to_save
                })
                
        except Exception as e:
            logging.error(f"Error processing message: {e}")
    
    return results

def save_scores_to_db(extracted_scores):
    """Save the extracted scores and patterns to both database tables."""
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Update scores in 'scores' table
        for score_data in extracted_scores:
            player_name = score_data['player_name']
            wordle_num = score_data['wordle_num']
            score = score_data['score']
            emoji_pattern = score_data.get('emoji_pattern')
            
            # Skip if not Wordle #1500
            if wordle_num != 1500:
                continue
            
            logging.info(f"Processing {player_name}'s Wordle #{wordle_num} score: {score}/6")
            
            # Check if this score exists in the scores table
            cursor.execute(
                "SELECT id, score, emoji_pattern FROM scores WHERE wordle_num = ? AND player_name = ?",
                (wordle_num, player_name)
            )
            result = cursor.fetchone()
            
            if result:
                # Update the score and pattern if needed
                current_score = result['score']
                current_pattern = result['emoji_pattern']
                
                if current_score != score:
                    cursor.execute(
                        "UPDATE scores SET score = ? WHERE id = ?",
                        (score, result['id'])
                    )
                    logging.info(f"Updated {player_name}'s score from {current_score}/6 to {score}/6")
                
                if emoji_pattern and (not current_pattern or current_pattern.strip() == ''):
                    cursor.execute(
                        "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                        (emoji_pattern, result['id'])
                    )
                    logging.info(f"Added emoji pattern for {player_name}'s Wordle #{wordle_num} score")
            else:
                # Insert new score
                if emoji_pattern:
                    cursor.execute(
                        "INSERT INTO scores (wordle_num, score, player_name, emoji_pattern) VALUES (?, ?, ?, ?)",
                        (wordle_num, score, player_name, emoji_pattern)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO scores (wordle_num, score, player_name) VALUES (?, ?, ?)",
                        (wordle_num, score, player_name)
                    )
                logging.info(f"Added new score for {player_name}: {score}/6 for Wordle #{wordle_num}")
        
        # Check if 'score' table exists and update it too
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='score'")
        if cursor.fetchone():
            # Also update the 'score' table to ensure consistency
            for score_data in extracted_scores:
                player_name = score_data['player_name']
                wordle_num = score_data['wordle_num']
                score = score_data['score']
                emoji_pattern = score_data.get('emoji_pattern')
                
                # Skip if not Wordle #1500
                if wordle_num != 1500:
                    continue
                
                # Try different column name combinations
                try:
                    # First try the most common schema
                    cursor.execute(
                        "SELECT id FROM score WHERE wordle_number = ? AND player = ?",
                        (wordle_num, player_name)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        cursor.execute(
                            "UPDATE score SET score = ? WHERE id = ?",
                            (score, result['id'])
                        )
                        logging.info(f"Updated {player_name}'s score in 'score' table")
                    else:
                        # Try alternate column names
                        cursor.execute(
                            "SELECT id FROM score WHERE wordle_num = ? AND player_name = ?",
                            (wordle_num, player_name)
                        )
                        result = cursor.fetchone()
                        
                        if result:
                            cursor.execute(
                                "UPDATE score SET score = ? WHERE id = ?",
                                (score, result['id'])
                            )
                            logging.info(f"Updated {player_name}'s score in 'score' table (alternate schema)")
                        else:
                            # Insert into 'score' table if not exists
                            # First determine the column names
                            cursor.execute("PRAGMA table_info(score)")
                            columns = {row['name']: row['cid'] for row in cursor.fetchall()}
                            
                            wordle_col = 'wordle_number' if 'wordle_number' in columns else 'wordle_num'
                            player_col = 'player' if 'player' in columns else 'player_name'
                            
                            query = f"INSERT INTO score ({wordle_col}, score, {player_col}) VALUES (?, ?, ?)"
                            cursor.execute(query, (wordle_num, score, player_name))
                            logging.info(f"Inserted {player_name}'s score into 'score' table")
                except sqlite3.OperationalError as e:
                    logging.error(f"Error updating 'score' table: {e}")
        
        # Commit changes
        conn.commit()
        logging.info("All scores have been updated in the database")
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def update_website():
    """Update the website to reflect the corrected scores."""
    try:
        logging.info("Updating website with corrected scores...")
        
        # Try different possible update scripts
        update_scripts = [
            'update_website.py',
            'publish_to_github.py',
            'server_auto_update.py'
        ]
        
        for script in update_scripts:
            if os.path.exists(script):
                subprocess.run(['python', script], check=True)
                logging.info(f"Website updated successfully using {script}")
                return True
        
        logging.warning("No website update script found. Please manually update the website.")
        return False
    except subprocess.SubprocessError as e:
        logging.error(f"Failed to update website: {e}")
        return False

def main():
    """Main execution function."""
    logging.info("Starting comprehensive fix for Wordle #1500 scores and patterns...")
    
    # Step 1: Back up the database
    if not backup_db():
        logging.error("Database backup failed. Aborting.")
        return
    
    # Step 2: Load HTML conversations
    conversations = load_html_conversations()
    if not conversations:
        logging.error("No conversation files found. Make sure conversation_*.html files are present.")
        return
    
    # Step 3: Extract scores and patterns from each conversation
    all_extracted_data = []
    for filename, html_content in conversations:
        logging.info(f"Extracting scores from {filename}...")
        extracted_data = extract_scores_and_patterns(html_content)
        all_extracted_data.extend(extracted_data)
        logging.info(f"Extracted {len(extracted_data)} score entries from {filename}")
    
    # Step 4: Save extracted scores and patterns to database
    if all_extracted_data:
        if save_scores_to_db(all_extracted_data):
            logging.info(f"Successfully updated database with {len(all_extracted_data)} score entries")
        else:
            logging.error("Failed to update database with extracted scores")
    else:
        logging.warning("No scores were extracted from conversations")
    
    # Step 5: Update the website
    update_website()
    
    logging.info("Wordle #1500 score and pattern fix complete!")

if __name__ == "__main__":
    main()
