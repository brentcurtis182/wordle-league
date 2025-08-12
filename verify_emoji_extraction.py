#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to verify emoji pattern extraction from Google Voice HTML
"""

import re
import sqlite3
from bs4 import BeautifulSoup
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("verify_emoji_extraction.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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
        '2063519843': 'Malia'
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
    
    logging.info(f"Found {len(hidden_elements)} hidden elements")
    
    extracted_data = []
    for hidden_elem in hidden_elements:
        hidden_text = hidden_elem.text
        
        if "Wordle" in hidden_text and "/6" in hidden_text:
            logging.info(f"Found Wordle data: {hidden_text[:100]}...")
            
            # Extract phone number
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
            
            data = {
                'phone': phone_number,
                'player': player_name,
                'wordle_num': wordle_num,
                'score': score,
                'emoji_pattern': emoji_pattern
            }
            
            extracted_data.append(data)
            logging.info(f"Extracted data for {player_name}: Wordle #{wordle_num}, Score: {score}/6")
            if emoji_pattern:
                logging.info(f"Emoji pattern with {len(emoji_rows)} rows:\n{emoji_pattern}")
            
    return extracted_data

def update_database_with_patterns(extracted_data):
    """Update database with extracted patterns"""
    conn = None
    try:
        conn = sqlite3.connect('wordle_league.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        for data in extracted_data:
            player = data['player']
            wordle_num = data['wordle_num']
            emoji_pattern = data['emoji_pattern']
            
            if not emoji_pattern:
                logging.warning(f"No emoji pattern to update for {player}, Wordle #{wordle_num}")
                continue
            
            # Update scores table
            cursor.execute(
                "SELECT id FROM scores WHERE player_name = ? AND wordle_num = ?",
                (player, wordle_num)
            )
            scores_result = cursor.fetchone()
            
            if scores_result:
                cursor.execute(
                    "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                    (emoji_pattern, scores_result['id'])
                )
                logging.info(f"Updated emoji pattern for {player} in 'scores' table")
            
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
                
                if has_emoji_pattern:
                    cursor.execute(
                        "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?",
                        (player_id, wordle_num)
                    )
                    score_result = cursor.fetchone()
                    
                    if score_result:
                        cursor.execute(
                            "UPDATE score SET emoji_pattern = ? WHERE id = ?",
                            (emoji_pattern, score_result['id'])
                        )
                        logging.info(f"Updated emoji pattern for {player} in 'score' table")
            
        conn.commit()
        logging.info("Database updates complete")
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def check_current_html_files():
    """Check current HTML files in directory for Wordle data"""
    html_files = []
    for file in os.listdir('.'):
        if file.endswith('.html'):
            html_files.append(file)
    
    if not html_files:
        logging.warning("No HTML files found in current directory")
        return
    
    logging.info(f"Found {len(html_files)} HTML files to check")
    
    all_data = []
    for html_file in html_files:
        logging.info(f"Processing {html_file}")
        data = extract_from_html_file(html_file)
        all_data.extend(data)
    
    if all_data:
        logging.info(f"Extracted {len(all_data)} Wordle scores from HTML files")
        
        # Print extracted data for verification
        for item in all_data:
            player = item['player']
            wordle_num = item['wordle_num']
            score = item['score']
            emoji_pattern = item['emoji_pattern']
            
            print(f"\n{'='*40}")
            print(f"Player: {player} - Wordle #{wordle_num} - Score: {score}/6")
            print(f"Emoji Pattern:\n{emoji_pattern}")
            print(f"{'='*40}")
        
        update_database_with_patterns(all_data)
        
        # Export website files
        logging.info("Exporting website files")
        os.system("python export_leaderboard.py")
        
        # Publish to GitHub
        logging.info("Publishing to GitHub")
        os.system("python server_publish_to_github.py")
    else:
        logging.warning("No Wordle data extracted from HTML files")

def test_from_sample():
    """Test extraction from a sample hidden element text"""
    sample = """Message from 7 6 0 8 4 6 2 3 0 2, Wordle 1,500 X/6

⬛⬛⬛⬛🟨
🟩⬛🟨⬛🟩
🟩🟩⬛⬛🟩
🟩🟩⬛⬛🟩
🟩🟩⬛⬛🟩
🟩🟩⬛⬛🟩, Monday, July 28 2025, 4:34 PM."""

    # Extract phone
    phone_match = re.search(r'from\s+(\d[\s\d]+\d)', sample)
    phone_number = phone_match.group(1).replace(" ", "") if phone_match else "Not found"
    player = extract_player_name_from_phone(phone_number)
    
    # Extract Wordle number
    wordle_match = re.search(r'Wordle\s+#?([\d,]+)', sample)
    wordle_num = int(wordle_match.group(1).replace(',', '')) if wordle_match else "Not found"
    
    # Extract score
    score_match = re.search(r'([\dX])/6', sample)
    score = score_match.group(1) if score_match else "Not found"
    score_val = 7 if score == 'X' else int(score) if score.isdigit() else "Not found"
    
    # Extract emoji pattern
    emoji_rows = re.findall(r'[⬛⬜🟨🟩]{5}', sample)
    emoji_pattern = "\n".join(emoji_rows) if emoji_rows else "Not found"
    
    # Safe print to handle Windows console encoding issues
    print(f"Sample Extraction Results:")
    print(f"Phone: {phone_number}")
    print(f"Player: {player}")
    print(f"Wordle #: {wordle_num}")
    print(f"Score: {score}/6 (Value: {score_val})")
    
    # Safe print for emoji pattern - replace emojis with safe text representations
    row_count = len(emoji_rows)
    print(f"Emoji pattern ({row_count} rows):")
    try:
        # Try to print actual emojis
        print(emoji_pattern)
    except UnicodeEncodeError:
        # If that fails, use text representation
        safe_pattern = emoji_pattern
        if emoji_pattern:
            safe_pattern = emoji_pattern.replace('⬛', '[B]').replace('⬜', '[W]') \
                                       .replace('🟨', '[Y]').replace('🟩', '[G]')
        print(safe_pattern)
    
    # Print detailed analysis of pattern
    print("\nEmoji pattern analysis:")
    for i, row in enumerate(emoji_rows):
        try:
            print(f"Row {i+1}: {row}")
        except UnicodeEncodeError:
            safe_row = row.replace('⬛', '[B]').replace('⬜', '[W]') \
                         .replace('🟨', '[Y]').replace('🟩', '[G]')
            print(f"Row {i+1}: {safe_row}")
            
    # Return the data for further use
    return {
        'phone': phone_number,
        'player': player,
        'wordle_num': wordle_num,
        'score': score_val,
        'emoji_pattern': emoji_pattern,
        'emoji_rows': emoji_rows
    }

if __name__ == "__main__":
    print("\n=== Verifying Emoji Pattern Extraction ===\n")
    
    # Test with sample
    test_from_sample()
    
    # Check for HTML files
    check_current_html_files()
