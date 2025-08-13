import sqlite3
import logging
import os
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_server_extractor_save_function():
    """Add pattern preservation logic to server_extractor.py"""
    
    server_extractor_path = Path("server_extractor.py")
    if not server_extractor_path.exists():
        logging.error(f"Could not find {server_extractor_path}")
        return False
    
    # Read the current content
    with open(server_extractor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Make a backup
    backup_path = server_extractor_path.with_suffix('.py.bak')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Created backup at {backup_path}")
    
    # Find the save_score function
    if "def save_score(score_data):" not in content:
        logging.error("Could not find save_score function in server_extractor.py")
        return False
    
    # Check if the pattern preservation logic is already there
    if "# Don't overwrite existing valid emoji patterns" in content:
        logging.info("Pattern preservation logic already exists, no changes needed")
        return True
    
    # Modify the save_score function to preserve existing emoji patterns
    # This is the key part that adds the pattern preservation logic
    current_logic = """    # Save to scores table
    try:
        cursor.execute(
            "INSERT INTO scores (wordle_num, score, player_name, emoji_pattern) VALUES (?, ?, ?, ?)",
            (wordle_num, score, player_name, emoji_pattern)
        )"""
    
    new_logic = """    # Check if this score already exists with a valid emoji pattern
    try:
        cursor.execute(
            "SELECT id, emoji_pattern FROM scores WHERE wordle_num = ? AND player_name = ?",
            (wordle_num, player_name)
        )
        existing = cursor.fetchone()
        
        if existing:
            existing_pattern = existing['emoji_pattern'] if existing['emoji_pattern'] else ""
            
            # Don't overwrite existing valid emoji patterns
            if existing_pattern and "\n" in existing_pattern and len(existing_pattern.split("\n")) > 0:
                logging.info(f"Preserving existing valid emoji pattern for {player_name}'s Wordle #{wordle_num}")
                conn.close()
                return True
        
        # Save new score or update existing without valid pattern
        cursor.execute(
            "INSERT OR REPLACE INTO scores (wordle_num, score, player_name, emoji_pattern) VALUES (?, ?, ?, ?)",
            (wordle_num, score, player_name, emoji_pattern)
        )"""
    
    updated_content = content.replace(current_logic, new_logic)
    
    # Also fix the score table logic
    current_logic_score = """    # Save to score table if player_id is available
    if player_id:
        cursor.execute(
            "INSERT INTO score (player_id, score, wordle_number, date, created_at, emoji_pattern) VALUES (?, ?, ?, ?, datetime('now'), ?)",
            (player_id, score, wordle_num, date, emoji_pattern)
        )"""
    
    new_logic_score = """    # Save to score table if player_id is available, but preserve existing patterns
    if player_id:
        cursor.execute(
            "SELECT id, emoji_pattern FROM score WHERE player_id = ? AND wordle_number = ?",
            (player_id, wordle_num)
        )
        existing_score = cursor.fetchone()
        
        if existing_score:
            existing_pattern = existing_score['emoji_pattern'] if existing_score['emoji_pattern'] else ""
            
            # Don't overwrite existing valid emoji patterns
            if existing_pattern and "\n" in existing_pattern and len(existing_pattern.split("\n")) > 0:
                logging.info(f"Preserving existing valid emoji pattern in score table for player #{player_id}, Wordle #{wordle_num}")
            else:
                # Update with new pattern
                cursor.execute(
                    "UPDATE score SET score = ?, emoji_pattern = ? WHERE player_id = ? AND wordle_number = ?",
                    (score, emoji_pattern, player_id, wordle_num)
                )
        else:
            # Insert new score
            cursor.execute(
                "INSERT INTO score (player_id, score, wordle_number, date, created_at, emoji_pattern) VALUES (?, ?, ?, ?, datetime('now'), ?)",
                (player_id, score, wordle_num, date, emoji_pattern)
            )"""
    
    updated_content = updated_content.replace(current_logic_score, new_logic_score)
    
    # Write the updated content
    with open(server_extractor_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logging.info("Successfully added pattern preservation logic to server_extractor.py")
    return True

def main():
    logging.info("Starting to fix server_extractor.py to preserve emoji patterns")
    success = fix_server_extractor_save_function()
    if success:
        logging.info("Fix completed successfully")
    else:
        logging.error("Fix failed")

if __name__ == "__main__":
    main()
