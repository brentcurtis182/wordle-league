#!/usr/bin/env python3
# Enhanced script to aggressively clean emoji patterns in the database

import sqlite3
import re
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("enhanced_pattern_cleanup.log"),
        logging.StreamHandler()
    ]
)

def extract_emoji_squares(pattern):
    """Extract only the emoji squares from a pattern, rebuilding clean rows"""
    if not pattern:
        return None
    
    # All possible emoji squares we're looking for
    emoji_squares = ['🟩', '⬛', '⬜', '🟨']
    
    # Extract all emoji squares from the pattern
    all_emojis = []
    for char in pattern:
        if char in emoji_squares:
            all_emojis.append(char)
    
    # If no emojis found, return None
    if not all_emojis:
        return None
    
    # Determine the number of rows based on count (assuming 5 squares per row)
    total_squares = len(all_emojis)
    
    # Default to 1 row if we can't determine
    num_rows = total_squares // 5 if total_squares % 5 == 0 else 1
    
    # Rebuild clean rows
    clean_rows = []
    for i in range(num_rows):
        # Get 5 emoji squares for this row
        start_idx = i * 5
        end_idx = start_idx + 5
        
        # Make sure we don't go out of bounds
        if start_idx < len(all_emojis):
            row_emojis = all_emojis[start_idx:min(end_idx, len(all_emojis))]
            clean_rows.append(''.join(row_emojis))
    
    # Return clean pattern
    return '\n'.join(clean_rows)

def fix_database_patterns():
    """Aggressively clean all emoji patterns in the database"""
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all scores with emoji patterns
        cursor.execute("SELECT id, player_name, wordle_num, emoji_pattern, score FROM scores WHERE emoji_pattern IS NOT NULL")
        rows = cursor.fetchall()
        
        logging.info(f"Found {len(rows)} emoji patterns to clean")
        
        # Process each pattern
        cleaned_count = 0
        for row in rows:
            id, player, wordle_num, pattern, score = row
            
            # Try to infer number of rows from score
            expected_rows = score if score and score != 7 else 6
            
            # Clean the pattern
            cleaned_pattern = extract_emoji_squares(pattern)
            
            if cleaned_pattern:
                # Update the database with cleaned pattern
                cursor.execute(
                    "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                    (cleaned_pattern, id)
                )
                cleaned_count += 1
                logging.info(f"Cleaned pattern for {player}, Wordle #{wordle_num}")
                logging.info(f"  Original: {pattern}")
                logging.info(f"  Cleaned: {cleaned_pattern}")
            else:
                logging.warning(f"Could not clean pattern for {player}, Wordle #{wordle_num}")
        
        # Commit changes
        conn.commit()
        
        logging.info(f"Cleaned {cleaned_count} patterns out of {len(rows)} total")
        return cleaned_count
        
    except Exception as e:
        logging.error(f"Error cleaning emoji patterns: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()
            
def fix_html_files():
    """Fix emoji patterns directly in HTML files"""
    try:
        website_dir = os.path.join(os.getcwd(), 'website_export')
        
        # Find HTML files
        html_files = []
        for root, dirs, files in os.walk(website_dir):
            for file in files:
                if file.endswith('.html'):
                    html_files.append(os.path.join(root, file))
        
        logging.info(f"Found {len(html_files)} HTML files to check")
        
        # Process each HTML file
        fixed_count = 0
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for emoji patterns with contamination
                pattern = re.compile(r'<div class="emoji-row">(.*?(?:🟩|⬛|⬜|🟨).*?)</div>')
                matches = pattern.findall(content)
                
                if matches:
                    for match in matches:
                        if any(date_marker in match.lower() for date_marker in [', monday', ', tuesday', ', wednesday', ', thursday', ', friday', ', saturday', ', sunday', ' am', ' pm']):
                            # Extract clean emojis
                            clean_emojis = ''.join([char for char in match if char in ['🟩', '⬛', '⬜', '🟨', ' ']])
                            
                            # Replace in content
                            content = content.replace(match, clean_emojis)
                            fixed_count += 1
                            logging.info(f"Fixed contaminated emoji pattern in {html_file}")
                            logging.info(f"  Original: {match}")
                            logging.info(f"  Cleaned: {clean_emojis}")
                    
                    # Write fixed content back
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            except Exception as e:
                logging.error(f"Error processing HTML file {html_file}: {e}")
        
        logging.info(f"Fixed {fixed_count} contaminated emoji patterns in HTML files")
        return fixed_count
        
    except Exception as e:
        logging.error(f"Error fixing HTML files: {e}")
        return 0
            
def main():
    logging.info("Starting enhanced emoji pattern cleanup...")
    
    # Fix database patterns
    db_count = fix_database_patterns()
    logging.info(f"Database cleanup complete. Cleaned {db_count} patterns.")
    
    # Fix HTML files directly
    html_count = fix_html_files()
    logging.info(f"HTML file cleanup complete. Fixed {html_count} patterns.")
    
    # Now export the website to reflect the changes
    try:
        # Try to import the export script
        import sys
        import subprocess
        logging.info("Exporting updated website...")
        result = subprocess.run([sys.executable, "export_leaderboard_multi_league.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
        else:
            logging.error(f"Website export failed: {result.stderr}")
            
    except Exception as e:
        logging.error(f"Error exporting website: {e}")

if __name__ == "__main__":
    main()
