#!/usr/bin/env python3
import sqlite3
import re
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_emoji_patterns():
    """Clean up emoji patterns in the database, removing any text after the emoji squares"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all scores with emoji patterns
        cursor.execute("SELECT id, player_name, wordle_num, score, emoji_pattern, league_id FROM scores WHERE emoji_pattern IS NOT NULL")
        records = cursor.fetchall()
        
        logging.info(f"Found {len(records)} records with emoji patterns")
        
        # Pattern to match emoji squares (black, white, yellow, green)
        emoji_pattern = re.compile(r'[⬛⬜🟨🟩]+')
        
        updated_count = 0
        for record in records:
            record_id = record[0]
            player = record[1]
            wordle_num = record[2]
            score_val = record[3]
            emoji_text = record[4]
            league_id = record[5]
            
            if emoji_text:
                # Split the emoji text by lines
                lines = emoji_text.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # Extract just the emoji squares from each line
                    match = emoji_pattern.search(line)
                    if match:
                        emoji_squares = match.group(0)
                        cleaned_lines.append(emoji_squares)
                
                # Join the cleaned lines back together
                cleaned_emoji = '\n'.join(cleaned_lines)
                
                # Only update if the pattern has changed
                if cleaned_emoji != emoji_text:
                    cursor.execute(
                        "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                        (cleaned_emoji, record_id)
                    )
                    updated_count += 1
                    
                    logging.info(f"Fixed pattern for {player}, Wordle #{wordle_num}, League {league_id}")
                    logging.info(f"  Before: {emoji_text}")
                    logging.info(f"  After:  {cleaned_emoji}")
        
        # Commit all changes
        conn.commit()
        logging.info(f"Updated {updated_count} emoji patterns")
        
        # Close the connection
        conn.close()
        
    except Exception as e:
        logging.error(f"Error fixing emoji patterns: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_emoji_patterns()
