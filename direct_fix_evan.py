#!/usr/bin/env python3
import os
import sqlite3
import logging
import json
import jinja2
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'wordle_league.db')
export_dir = os.path.join(script_dir, 'website_export')

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def get_weekly_wordle_range():
    """Get the Wordle number range for this week (Monday-Sunday)"""
    # Get the most recent Wordle number
    cursor.execute("SELECT MAX(wordle_number) FROM scores")
    result = cursor.fetchone()
    if not result or result[0] is None:
        logging.warning("No scores found to calculate weekly range, using default")
        return 1500, 1506
    
    today_wordle = int(result[0])
    
    # Calculate the day of the week (0 = Monday, 6 = Sunday)
    # Convert this to an offset for the Wordle number
    # Get the current date
    today = datetime.now()
    weekday = today.weekday()
    
    # Calculate the start of the week (Monday's Wordle)
    start_wordle = today_wordle - weekday
    
    # The end of the week is 6 Wordles after the start (Sunday)
    end_wordle = start_wordle + 6
    
    logging.info(f"Weekly Wordle range: {start_wordle} to {end_wordle}")
    return start_wordle, end_wordle

def direct_fix_evan_failed_attempt():
    """Apply a direct fix for Evan's failed attempt display"""
    # Get the weekly range
    start_wordle, end_wordle = get_weekly_wordle_range()
    
    # Verify Evan's failed attempt exists in the database
    cursor.execute("""
    SELECT s.id, s.score, s.date, s.wordle_number, p.name 
    FROM scores s 
    JOIN players p ON s.player_id = p.id 
    WHERE p.name = 'Evan' AND p.league_id = 1 
    AND s.wordle_number >= ? AND s.wordle_number <= ?
    AND (s.score = '7' OR s.score = 7 OR s.score = 'X')
    """, (start_wordle, end_wordle))
    
    failed_attempts = cursor.fetchall()
    if not failed_attempts:
        logging.error("No failed attempts found for Evan in the current week")
        return False
    
    logging.info(f"Found {len(failed_attempts)} failed attempts for Evan in the current week:")
    for attempt in failed_attempts:
        logging.info(f"ID: {attempt[0]}, Score: {attempt[1]}, Date: {attempt[2]}, Wordle: {attempt[3]}")
    
    # Now directly modify the HTML file to ensure Evan's failed attempt is displayed
    html_path = os.path.join(export_dir, 'index.html')
    
    if not os.path.exists(html_path):
        logging.error(f"HTML file not found at {html_path}")
        return False
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Find Evan's row in the weekly stats table and insert the failed attempt count
        search_pattern = '<td>Evan</td>\n                                <td class="weekly-score">0</td>\n                                <td class="used-scores">0</td>\n                                <td class="failed-attempts"></td>'
        replacement = f'<td>Evan</td>\n                                <td class="weekly-score">0</td>\n                                <td class="used-scores">0</td>\n                                <td class="failed-attempts">{len(failed_attempts)}</td>'
        
        if search_pattern in html_content:
            html_content = html_content.replace(search_pattern, replacement)
            logging.info("Successfully replaced Evan's failed attempts cell in HTML")
        else:
            logging.error("Could not find Evan's row pattern in the HTML")
            return False
        
        # Write the modified HTML back to the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logging.info(f"Successfully updated {html_path} with Evan's failed attempts")
        return True
    
    except Exception as e:
        logging.error(f"Error updating HTML file: {e}")
        return False

if __name__ == "__main__":
    if direct_fix_evan_failed_attempt():
        logging.info("Direct fix for Evan's failed attempts completed successfully")
    else:
        logging.error("Direct fix failed")
    conn.close()
