#!/usr/bin/env python3
"""
Fix for Wordle Score Extraction

This script patches the regex pattern used in the extraction script to better detect
modern Wordle score formats, fixes common issues with extraction, and diagnoses any
remaining problems with the unified scores table.
"""

import logging
import sqlite3
import os
import re
import sys
from datetime import datetime
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_extraction.log"),
        logging.StreamHandler()
    ]
)

def backup_file(filepath):
    """Create a backup of a file before modifying it"""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        logging.info(f"Created backup of {filepath} at {backup_path}")
        return True
    return False

def update_extraction_regex():
    """Update the regex pattern in extract_scores_from_conversation.py"""
    filepath = 'extract_scores_from_conversation.py'
    
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False
    
    # Create backup
    backup_file(filepath)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Existing pattern: wordle_regex = re.compile(r'Wordle ([\d,]+)(?: #([\d,]+)?)? ([1-6X])/6')
    # This may be missing matches for newer Wordle formats
    
    # Define new patterns that cover more variations
    old_pattern = r"wordle_regex = re.compile\(r'Wordle \([\d,]+\)\(?: #\([\d,]+\)\)? \([1-6X]\)/6'\)"
    new_pattern = r"wordle_regex = re.compile(r'Wordle\\s+(?:#)?(\\d[\\d,]*)\\s+(\\d|X)/6', re.IGNORECASE)"
    
    # Simplified replacement for more reliability
    content = content.replace(
        "wordle_regex = re.compile(r'Wordle ([\d,]+)(?: #([\d,]+)?)? ([1-6X])/6')", 
        "wordle_regex = re.compile(r'Wordle\\s+(?:#)?(\\d[\\d,]*)\\s+(\\d|X)/6', re.IGNORECASE)"
    )
    
    # Update variable references in the code
    content = content.replace("match.group(3)", "match.group(2)")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logging.info(f"Updated regex pattern in {filepath}")
    return True

def add_debugging_code():
    """Add extra debugging to extract_scores_from_conversation.py"""
    filepath = 'extract_scores_from_conversation.py'
    
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    # Find the line where we process regex matches
    insert_index = None
    for i, line in enumerate(content):
        if "match = wordle_regex.search(message_content)" in line:
            insert_index = i + 1
            break
    
    if insert_index:
        debug_code = [
            "                # Debug logging to show exact text being searched\n",
            "                logging.info(f\"Searching for Wordle score in text: '{message_content[:100]}...'\")\n",
            "                if not match:\n",
            "                    # Try alternate regex patterns for debugging\n",
            "                    alt_patterns = [\n",
            "                        r'Wordle\\s+#?(\\d[\\d,]*)\\s+(\\d|X)/6',\n", 
            "                        r'Wordle\\s+(\\d[\\d,]*)\\s+(\\d|X)/6',\n",
            "                        r'Wordle[:\\s]+(\\d[\\d,]*)[:\\s]+(\\d|X)/6'\n",
            "                    ]\n",
            "                    for i, pattern in enumerate(alt_patterns):\n",
            "                        alt_match = re.search(pattern, message_content, re.IGNORECASE)\n",
            "                        if alt_match:\n",
            "                            logging.info(f\"Alternative pattern {i+1} matched: {alt_match.groups()}\")\n",
            "                            match = alt_match  # Use this match instead\n",
            "                            break\n"
        ]
        content[insert_index:insert_index] = debug_code
    
    # Enhanced debug after extracting emoji pattern
    emoji_index = None
    for i, line in enumerate(content):
        if "if emoji_lines:" in line:
            emoji_index = i + 3
            break
    
    if emoji_index:
        emoji_debug = [
            "                        logging.info(f\"Extracted emoji pattern:\\n{emoji_pattern}\")\n"
        ]
        content[emoji_index:emoji_index] = emoji_debug
    
    # Debug successful score saves
    save_index = None 
    for i, line in enumerate(content):
        if "result = save_score_to_db(" in line:
            save_index = i + 1
            break
    
    if save_index:
        save_debug = [
            "                     \n",
            "                    logging.info(f\"Result of save_score_to_db: {result}\")\n",
        ]
        content[save_index:save_index] = save_debug
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(content)
    
    logging.info(f"Added debugging code to {filepath}")
    return True

def test_extraction():
    """Run the extraction script and report results"""
    try:
        # Import the run function
        from integrated_auto_update_multi_league import main as run_extraction
        
        # Run extraction
        logging.info("Running extraction with fixed regex...")
        run_extraction()
        
        # Check database for scores
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Calculate today's Wordle number
        ref_date = datetime(2025, 7, 31).date()
        ref_wordle = 1503
        today = datetime.now().date()
        days_diff = (today - ref_date).days
        todays_wordle = ref_wordle + days_diff
        
        # Get scores for today
        cursor.execute("""
        SELECT p.name, p.league_id, s.score, s.wordle_number, s.date, s.emoji_pattern
        FROM scores s 
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number = ?
        ORDER BY p.league_id, p.name
        """, (todays_wordle,))
        
        scores = cursor.fetchall()
        
        if scores:
            logging.info(f"SUCCESS! Found {len(scores)} scores for Wordle #{todays_wordle}:")
            for score in scores:
                name, league_id, score_val, wordle_num, date, emoji = score
                display_score = 'X' if score_val == 7 else score_val
                league_name = "Wordle Warriorz" if league_id == 1 else "PAL" if league_id == 3 else "Gang"
                
                logging.info(f"{name} ({league_name}): Wordle #{wordle_num} - {display_score}/6 on {date}")
                if emoji:
                    emoji_lines = emoji.split('\n')
                    for line in emoji_lines:
                        logging.info(f"  {line}")
        else:
            logging.warning(f"No scores found for Wordle #{todays_wordle} after extraction")
            
        conn.close()
        return bool(scores)
        
    except Exception as e:
        logging.error(f"Error testing extraction: {e}", exc_info=True)
        return False

def main():
    """Main function to run all fixes"""
    logging.info("Starting extraction fix script...")
    
    # Update regex pattern
    if update_extraction_regex():
        logging.info("Successfully updated regex pattern")
    else:
        logging.error("Failed to update regex pattern")
        return False
    
    # Add debugging code
    if add_debugging_code():
        logging.info("Successfully added debugging code")
    else:
        logging.error("Failed to add debugging code")
        return False
    
    # Test extraction
    if test_extraction():
        logging.info("Extraction test successful! Scores were found and saved.")
        return True
    else:
        logging.warning("Extraction test completed but no new scores were found.")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logging.info("Fix completed successfully")
    else:
        logging.warning("Fix completed with warnings")
