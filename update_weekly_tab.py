#!/usr/bin/env python3
"""
Update Weekly Tab Script for Wordle League
This script updates only the weekly tab without disturbing the emoji patterns in the latest tab
"""

import os
import re
import sqlite3
import logging
import datetime
from pathlib import Path
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_weekly_tab.log"),
        logging.StreamHandler()
    ]
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(SCRIPT_DIR, 'wordle_league.db')
WEBSITE_EXPORT_DIR = os.path.join(SCRIPT_DIR, 'website_export')

# Map of league IDs to directory names
LEAGUE_MAP = {
    1: "",  # Main league (Wordle Warriorz) is in root directory
    2: "gang",
    3: "pal", 
    4: "party",
    5: "vball"
}

# Map of league IDs to league names (for logging/display)
LEAGUE_NAMES = {
    1: "Wordle Warriorz",
    2: "Wordle Gang",
    3: "Wordle PAL",
    4: "Wordle Party",
    5: "Wordle Vball"
}

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    if os.path.exists(file_path):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        try:
            shutil.copy2(file_path, backup_path)
            logging.info(f"Created backup of {file_path} at {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Failed to create backup: {str(e)}")
            return False
    else:
        logging.warning(f"File {file_path} does not exist, no backup created")
        return False

def get_weekly_wordle_range():
    """Get the Wordle number range for the current week (Monday-Sunday)"""
    # Connect to database to get latest wordle number
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get the latest wordle number from the database
    cursor.execute("SELECT MAX(wordle_number) FROM scores")
    result = cursor.fetchone()
    conn.close()
    
    if not result or not result[0]:
        logging.error("Could not determine latest wordle number from database")
        return None, None
        
    today_wordle = int(result[0])
    
    # Get today's date and weekday (0 = Monday, 6 = Sunday)
    today = datetime.datetime.now()
    weekday = today.weekday()  # 0 = Monday, 6 = Sunday
    
    # Calculate the Wordle number for the start of the week (Monday)
    # If today is Monday (weekday=0), start is today's wordle
    # Otherwise, it's today's wordle minus weekday
    if weekday == 0:  # Monday
        start_wordle = today_wordle
    else:
        start_wordle = today_wordle - weekday
    
    # The end of the week is 6 Wordles after the start (Sunday)
    end_wordle = start_wordle + 6
    
    logging.info(f"Weekly Wordle range: {start_wordle} to {end_wordle}")
    return start_wordle, end_wordle

def calculate_weekly_stats(league_id):
    """Calculate weekly statistics for a specific league"""
    start_wordle, end_wordle = get_weekly_wordle_range()
    if not start_wordle or not end_wordle:
        return None
        
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dictionary access to rows
    cursor = conn.cursor()
    
    # Get all registered players for this league
    cursor.execute("""
        SELECT 
            p.id, 
            p.name, 
            COALESCE(p.nickname, p.name) as display_name
        FROM 
            players p
        WHERE 
            p.league_id = ?
        ORDER BY
            p.name
    """, (league_id,))
    
    players = cursor.fetchall()
    player_stats = []
    
    # Calculate weekday (0=Monday, 6=Sunday)
    weekday_mapping = {
        0: 'Mon',
        1: 'Tue',
        2: 'Wed',
        3: 'Thu',
        4: 'Fri',
        5: 'Sat',
        6: 'Sun'
    }
    
    # Process each player
    for player in players:
        player_id = player['id']
        player_name = player['display_name']
        
        # Get all scores for this player for this week
        cursor.execute("""
            SELECT 
                s.score,
                s.timestamp,
                s.wordle_number
            FROM 
                scores s 
            WHERE 
                s.player_id = ? AND 
                s.wordle_number BETWEEN ? AND ?
            ORDER BY
                s.wordle_number
        """, (player_id, start_wordle, end_wordle))
        
        scores = cursor.fetchall()
        
        # Initialize daily scores dictionary (day of week -> score)
        daily_scores = {day: '-' for day in weekday_mapping.values()}
        
        # Process scores
        all_scores = []
        failed_attempts = 0
        
        for score_row in scores:
            score = score_row['score']
            timestamp = score_row['timestamp']
            wordle_num = score_row['wordle_number']
            
            # Calculate which day of the week this score belongs to
            day_offset = wordle_num - start_wordle  # 0 for Monday, 6 for Sunday
            
            # Ensure day_offset is valid (0-6)
            if 0 <= day_offset <= 6:
                day_name = weekday_mapping[day_offset]
                
                # Store score for this day
                if score == 7:  # Failed attempt
                    daily_scores[day_name] = 'X'
                    failed_attempts += 1
                else:
                    daily_scores[day_name] = score
                    all_scores.append(score)
        
        # Calculate weekly score (sum of top 5 scores)
        all_scores.sort()  # Sort scores (lowest is best)
        used_scores = all_scores[:5]  # Take up to 5 best scores
        weekly_score = sum(used_scores) if used_scores else '-'
        used_count = len(used_scores)
        thrown_out = len(all_scores) - len(used_scores) if len(all_scores) > 5 else 0
        
        # Add player stats
        player_stats.append({
            'player_name': player_name,
            'weekly_score': weekly_score,
            'used_scores': used_count,
            'failed_attempts': failed_attempts,
            'thrown_out': thrown_out,
            'daily_scores': daily_scores,
            'total_games': len(all_scores) + failed_attempts,
            'all_scores': all_scores
        })
    
    # Sort by weekly score (best at top), then highlight players with 5+ scores
    player_stats.sort(key=lambda x: (
        # Sort criteria:
        # 1. Players with scores (not '-') first
        # 2. Players with 5+ used scores first (highlighted)
        # 3. Sort by weekly score (lowest is best)
        # 4. Sort by total games played (highest first)
        0 if x['weekly_score'] != '-' else 1,
        0 if x['used_scores'] >= 5 else 1,
        float('-inf') if x['weekly_score'] == '-' else x['weekly_score'],
        -x['total_games']
    ))
    
    conn.close()
    logging.info(f"Calculated weekly stats for {len(player_stats)} players in league {LEAGUE_NAMES.get(league_id, league_id)}")
    return player_stats

def update_weekly_tab(league_id, weekly_stats):
    """Update only the weekly tab in the HTML file"""
    league_dir = LEAGUE_MAP.get(league_id, "")
    html_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
    
    if not os.path.exists(html_path):
        logging.error(f"HTML file not found: {html_path}")
        return False
    
    # Create backup before modifying
    backup_file(html_path)
    
    try:
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Find the weekly tab content section
        weekly_tab_match = re.search(r'<div class="tab-content" id="weekly">(.*?)<div class="tab-content"', html_content, re.DOTALL)
        if not weekly_tab_match:
            logging.error(f"Could not find weekly tab content in {html_path}")
            return False
        
        # Generate new weekly tab content
        start_wordle, end_wordle = get_weekly_wordle_range()
        if not start_wordle or not end_wordle:
            logging.error("Could not determine weekly Wordle range")
            return False
            
        # Create new weekly tab HTML
        new_weekly_tab = f'<div class="tab-content" id="weekly">\n'
        new_weekly_tab += f'<h2 style="margin-top: 5px; margin-bottom: 10px;">Weekly Totals</h2>\n'
        new_weekly_tab += f'<p style="margin-top: 0; margin-bottom: 5px;; font-style: italic;">Top 5 scores count toward weekly total (Monday-Sunday).</p>\n'
        new_weekly_tab += f'<p style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em;">At least 5 scores needed to compete for the week!</p>\n'
        new_weekly_tab += f'<div class="table-container">\n<table>\n'
        new_weekly_tab += f'<thead><tr><th>Player</th><th>Weekly Score</th><th>Used Scores</th><th>Failed</th><th>Thrown Out</th><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th>Sat</th><th>Sun</th></tr></thead>\n<tbody>\n'
        
        # Add player rows
        player_rows = []
        for player in weekly_stats:
            player_name = player['player_name']
            weekly_score = player['weekly_score']
            used_scores = player['used_scores']
            failed_attempts = player['failed_attempts']
            thrown_out = player['thrown_out']
            daily_scores = player['daily_scores']
            
            # Build the row with proper highlighting for players with 5+ scores
            highlight_class = 'class="highlighted" style="background-color: rgba(106, 170, 100, 0.15); font-weight: bold;"' if used_scores >= 5 else ''
            
            row = f'<tr {highlight_class}><td><strong>{player_name}</strong></td>'
            row += f'<td>{weekly_score}</td>'
            row += f'<td>{used_scores}</td>'
            row += f'<td class="failed-attempts">{failed_attempts if failed_attempts else ""}</td>'
            row += f'<td>{thrown_out}</td>'
            
            # Add daily scores
            for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']:
                row += f'<td>{daily_scores[day]}</td>'
            
            row += '</tr>'
            player_rows.append(row)
        
        # Add all player rows
        new_weekly_tab += ''.join(player_rows)
        
        # Close the table
        new_weekly_tab += '</tbody>\n</table>'
        new_weekly_tab += '<p style="margin-top: 10px; font-size: 0.9em; font-style: italic; text-align: center;">Failed attempts do not count towards your \'Used Scores\'</p>\n'
        new_weekly_tab += '</div>\n</div>\n'
        
        # Replace the weekly tab content in the HTML
        new_html = re.sub(r'<div class="tab-content" id="weekly">.*?<div class="tab-content"', 
                          new_weekly_tab + '<div class="tab-content"', 
                          html_content, 
                          flags=re.DOTALL)
        
        # Write the updated HTML back to the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(new_html)
        
        logging.info(f"Successfully updated weekly tab in {html_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating weekly tab for {LEAGUE_NAMES.get(league_id, league_id)}: {str(e)}")
        return False

def main():
    """Main function to update weekly tabs for all leagues"""
    logging.info("Starting update of weekly tabs for all leagues")
    
    success_count = 0
    
    for league_id in LEAGUE_MAP:
        league_name = LEAGUE_NAMES.get(league_id, f"League {league_id}")
        logging.info(f"Updating weekly tab for {league_name}")
        
        # Calculate weekly stats
        weekly_stats = calculate_weekly_stats(league_id)
        if not weekly_stats:
            logging.error(f"Failed to calculate weekly stats for {league_name}")
            continue
            
        # Update the weekly tab
        if update_weekly_tab(league_id, weekly_stats):
            success_count += 1
    
    logging.info(f"Update completed: {success_count} weekly tabs updated successfully")
    print(f"Update completed: {success_count} weekly tabs updated successfully")

if __name__ == "__main__":
    main()
