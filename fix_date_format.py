#!/usr/bin/env python3
"""
Fix the date format in Latest Scores section for all league pages
Changes date format from "Wordle #XXXX - YYYY-MM-DD" to "Wordle #XXXX - Month DDth, YYYY"
"""

import os
import re
import datetime
import logging
import shutil
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_date_format.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Constants
WEBSITE_EXPORT_DIR = "website_export"
LEAGUE_DIRS = {
    "Wordle Warriorz": "",
    "Wordle Gang": "gang",
    "Wordle PAL": "pal",
    "Wordle Party": "party",
    "Wordle Vball": "vball"
}

def create_backup(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def get_ordinal_suffix(day):
    """Get the ordinal suffix for a day number (1st, 2nd, 3rd, etc.)"""
    if 11 <= day <= 13:
        return "th"
    last_digit = day % 10
    if last_digit == 1:
        return "st"
    elif last_digit == 2:
        return "nd"
    elif last_digit == 3:
        return "rd"
    else:
        return "th"

def format_date_nicely(date_str):
    """Convert YYYY-MM-DD to Month DDth, YYYY"""
    try:
        # Parse the ISO format date
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        
        # Get the day with ordinal suffix
        day = date_obj.day
        suffix = get_ordinal_suffix(day)
        
        # Format as "Month DDth, YYYY"
        return date_obj.strftime(f"%B {day}{suffix}, %Y")
    except ValueError:
        logging.warning(f"Could not parse date: {date_str}")
        return date_str  # Return original if parsing fails

def fix_date_format_in_file(file_path):
    """Fix the date format in a league HTML file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Create a backup of the file before modifying
        create_backup(file_path)
        
        # Find and replace the date format
        # Pattern matches: Wordle #XXXX - YYYY-MM-DD
        pattern = r'(Wordle #\d+) - (\d{4}-\d{2}-\d{2})'
        
        def replace_date(match):
            wordle_num = match.group(1)
            date_str = match.group(2)
            nice_date = format_date_nicely(date_str)
            return f"{wordle_num} - {nice_date}"
        
        new_content = re.sub(pattern, replace_date, content)
        
        # Write the updated content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        logging.info(f"Updated date format in {file_path}")
        return True
    except Exception as e:
        logging.error(f"Error updating date format in {file_path}: {e}")
        return False

def main():
    """Update date format in all league HTML files"""
    logging.info("Starting date format update for all leagues")
    
    success_count = 0
    error_count = 0
    
    for league_name, league_dir in LEAGUE_DIRS.items():
        # Construct the path to the league's index.html file
        if league_dir:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
        else:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, "index.html")
            
        if os.path.exists(index_path):
            logging.info(f"Updating date format for {league_name} league")
            if fix_date_format_in_file(index_path):
                success_count += 1
            else:
                error_count += 1
        else:
            logging.warning(f"Could not find index.html for {league_name} league at {index_path}")
            error_count += 1
    
    logging.info(f"Date format update completed: {success_count} successful, {error_count} errors")
    print(f"Date format update completed: {success_count} successful, {error_count} errors")

if __name__ == "__main__":
    main()
