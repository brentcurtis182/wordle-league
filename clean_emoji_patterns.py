#!/usr/bin/env python3
# Script to clean existing emoji patterns in the database

import sqlite3
import re
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("clean_emoji_patterns.log"),
        logging.StreamHandler()
    ]
)

def clean_emoji_pattern(pattern):
    """Clean an emoji pattern by keeping only the lines with emoji squares"""
    if not pattern:
        return None
        
    # Clean the pattern by keeping only lines with emoji squares
    emoji_lines = []
    
    # Split by lines and process each line
    lines = pattern.split('\n')
    
    for line in lines:
        # Keep only lines containing emoji squares
        if '🟩' in line or '⬛' in line or '⬜' in line or '🟨' in line:
            # Further clean each line by keeping only the emoji part
            # First, find the emoji pattern within the line
            emoji_only = ""
            emoji_started = False
            emoji_chars = []
            
            for i, char in enumerate(line):
                if char in ['🟩', '⬛', '⬜', '🟨']:
                    emoji_started = True
                    emoji_chars.append(char)
                elif emoji_started and char in [' ', ',', '.'] and i < len(line)-1 and line[i+1] in ['🟩', '⬛', '⬜', '🟨']:
                    # This is a separator between emoji squares, keep it
                    emoji_chars.append(char)
                elif emoji_started and len(emoji_chars) > 0 and line[i-1] in ['🟩', '⬛', '⬜', '🟨']:
                    # We've reached the end of the emoji pattern
                    break
            
            if emoji_chars:
                emoji_only = ''.join(emoji_chars)
                emoji_lines.append(emoji_only)
    
    if emoji_lines:
        return '\n'.join(emoji_lines)
    
    return pattern  # Return original if no emoji lines found

def fix_database_patterns():
    """Clean all emoji patterns in the database"""
    conn = None
    try:
        # Connect to database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all scores with emoji patterns
        cursor.execute("SELECT id, player_name, wordle_num, emoji_pattern FROM scores WHERE emoji_pattern IS NOT NULL")
        rows = cursor.fetchall()
        
        logging.info(f"Found {len(rows)} emoji patterns to clean")
        
        # Process each pattern
        cleaned_count = 0
        for row in rows:
            id, player, wordle_num, pattern = row
            
            # Clean the pattern
            cleaned_pattern = clean_emoji_pattern(pattern)
            
            if cleaned_pattern != pattern:
                # Update the database with cleaned pattern
                cursor.execute(
                    "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                    (cleaned_pattern, id)
                )
                cleaned_count += 1
                logging.info(f"Cleaned pattern for {player}, Wordle #{wordle_num}")
                logging.info(f"  Original: {pattern}")
                logging.info(f"  Cleaned: {cleaned_pattern}")
        
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
            
def main():
    logging.info("Starting emoji pattern cleanup...")
    count = fix_database_patterns()
    logging.info(f"Emoji pattern cleanup complete. Cleaned {count} patterns.")
    
    # Now export the website to reflect the changes
    try:
        # Try to import the export script
        import export_leaderboard_multi_league
        logging.info("Exporting updated website...")
        website_success = export_leaderboard_multi_league.main()
        
        if website_success:
            logging.info("Website export successful")
        else:
            logging.error("Website export failed")
    except Exception as e:
        logging.error(f"Error exporting website: {e}")

if __name__ == "__main__":
    main()
