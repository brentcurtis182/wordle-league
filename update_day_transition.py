import sqlite3
import logging
import os
import re
from pathlib import Path
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_server_extractor_for_day_transition():
    """Update server_extractor.py to handle day transitions correctly"""
    server_extractor_path = Path("server_extractor.py")
    if not server_extractor_path.exists():
        logging.error(f"Could not find {server_extractor_path}")
        return False
    
    # Read the current content
    with open(server_extractor_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Make a backup
    backup_path = server_extractor_path.with_suffix('.py.bak.day_transition')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logging.info(f"Created backup at {backup_path}")
    
    # Check if we need to make changes
    if "# Get tomorrow's Wordle number for transition handling" in content:
        logging.info("Day transition logic already exists in server_extractor.py")
        return True
    
    # Find the part where we check for the current Wordle
    code_to_find = """        # Only process current Wordle number
        today = datetime.now()
        expected_wordle = calculate_wordle_number(today)
        if score_data['wordle_number'] != expected_wordle:
            logging.info(f"Ignoring old Wordle #{score_data['wordle_number']} for {score_data['player_name']} (current Wordle is #{expected_wordle})")
            conn.close()
            return False"""
    
    # Replace with improved code that handles day transitions
    new_code = """        # Check if this is today's or tomorrow's Wordle number
        today = datetime.now()
        expected_wordle = calculate_wordle_number(today)
        
        # Get tomorrow's Wordle number for transition handling
        tomorrow = today + timedelta(days=1)
        tomorrow_wordle = calculate_wordle_number(tomorrow)
        
        # Accept current Wordle or tomorrow's Wordle (during day transition)
        if score_data['wordle_number'] == expected_wordle:
            logging.info(f"Processing current Wordle #{expected_wordle} for {score_data['player_name']}")
        elif score_data['wordle_number'] == tomorrow_wordle:
            # Handle day transition - accept tomorrow's scores after midnight
            if today.hour >= 22:  # After 10 PM, start accepting next day's scores
                logging.info(f"Processing tomorrow's Wordle #{tomorrow_wordle} for {score_data['player_name']} (day transition)")
            else:
                logging.info(f"Ignoring future Wordle #{score_data['wordle_number']} for {score_data['player_name']} (too early)")
                conn.close()
                return False
        else:
            logging.info(f"Ignoring old/invalid Wordle #{score_data['wordle_number']} for {score_data['player_name']} (current Wordle is #{expected_wordle})")
            conn.close()
            return False"""
    
    # Update the content
    updated_content = content.replace(code_to_find, new_code)
    
    # Also update export_leaderboard.py to handle both today's and yesterday's scores in weekly view
    export_leaderboard_path = Path("export_leaderboard.py")
    if export_leaderboard_path.exists():
        with open(export_leaderboard_path, 'r', encoding='utf-8') as f:
            export_content = f.read()
        
        export_backup_path = export_leaderboard_path.with_suffix('.py.bak.day_transition')
        with open(export_backup_path, 'w', encoding='utf-8') as f:
            f.write(export_content)
        logging.info(f"Created backup at {export_backup_path}")
        
        # Find the code where we get weekly scores
        weekly_code_to_find = """    # Get today's Wordle number
    today_wordle = calculate_wordle_number(today)
    print(f"Today's Wordle number is {today_wordle}")
    
    # Query ONLY scores from today's Wordle number
    cursor.execute("SELECT player_id, score, date FROM score WHERE wordle_number = ?", (today_wordle,))"""
        
        # Replace with improved code that handles 7-day window
        new_weekly_code = """    # Get today's Wordle number
    today_wordle = calculate_wordle_number(today)
    print(f"Today's Wordle number is {today_wordle}")
    
    # Also get yesterday's Wordle number
    yesterday = today - timedelta(days=1)
    yesterday_wordle = calculate_wordle_number(yesterday)
    print(f"Yesterday's Wordle number is {yesterday_wordle}")
    
    # Query scores from this week (allow today and yesterday to accumulate in weekly view)
    cursor.execute("SELECT player_id, score, date, wordle_number FROM score WHERE date >= ? ORDER BY wordle_number DESC", 
                 (start_of_week.strftime('%Y-%m-%d'),))"""
        
        # Update the export content
        updated_export_content = export_content.replace(weekly_code_to_find, new_weekly_code)
        
        # Write updated export content
        with open(export_leaderboard_path, 'w', encoding='utf-8') as f:
            f.write(updated_export_content)
        
        logging.info("Updated export_leaderboard.py to handle day transitions")
    
    # Write the updated content
    with open(server_extractor_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    logging.info("Successfully updated server_extractor.py to handle day transitions")
    return True

def main():
    logging.info("Adding day transition handling to improve Wordle League")
    
    # Update server_extractor.py to handle day transitions
    if fix_server_extractor_for_day_transition():
        logging.info("✓ Updated server_extractor.py to handle day transitions")
    else:
        logging.error("Failed to update server_extractor.py")
    
    logging.info("Day transition updates complete.")

if __name__ == "__main__":
    main()
