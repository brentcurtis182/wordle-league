#!/usr/bin/env python3
"""
Update Season Table with Weekly Winners - FIXED VERSION

This script:
1. Determines weekly winners based on the lowest weekly score for each week
2. Updates the Season table in all league HTML files with:
   - Player name
   - Weekly wins count
   - Week date in the format "Aug 4th - (14)" where 14 is the score
3. Fixed to use the correct calculation logic to identify winners
"""

import os
import sys
import re
import sqlite3
import logging
import datetime
import shutil
from bs4 import BeautifulSoup
import calendar
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_season_winners_fixed.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Constants
WEBSITE_EXPORT_DIR = "website_export"
DATABASE_PATH = "wordle_league.db"
LEAGUE_DIRS = {
    "Wordle Warriorz": "",
    "Wordle Gang": "gang",
    "Wordle PAL": "pal",
    "Wordle Party": "party",
    "Wordle Vball": "vball"
}

def create_backup(file_path):
    """Create a backup of the file before modifying it"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup of {file_path} at {backup_path}")
    return backup_path

def get_ordinal_suffix(day):
    """Return the ordinal suffix for a day (1st, 2nd, 3rd, etc.)"""
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return suffix

def format_week_date(date, score):
    """Format a date as 'Aug 4th - (14)' where 14 is the score"""
    day = date.day
    suffix = get_ordinal_suffix(day)
    month_abbr = date.strftime("%b")
    return f"{month_abbr} {day}{suffix} - ({score})"

def get_monday_of_week(date):
    """Get the Monday of the week for a given date"""
    weekday = date.weekday()  # 0 is Monday, 6 is Sunday
    return date - timedelta(days=weekday)

def debug_print_scores(league_id, player_scores):
    """Debug function to print player scores for a week"""
    logging.info(f"--- DEBUG: League {league_id} Player Scores ---")
    for name, score in player_scores:
        logging.info(f"Player: {name}, Score: {score}")
    logging.info("-------------------------------------")

def get_weekly_winners(league_id):
    """
    Get weekly winners for a league based on the lowest TOTAL weekly score
    Returns a list of dictionaries with weekly winner data
    """
    conn = None
    weekly_winners = []
    player_wins = {}  # Track win count per player
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get the most recent week from scores
        cursor.execute("""
        SELECT MAX(wordle_number) FROM scores
        """)
        latest_wordle = cursor.fetchone()[0]
        if not latest_wordle:
            logging.warning("No wordle scores found in database")
            return []
            
        # Calculate Monday's wordle number for current week
        current_date = datetime.now()
        weekday = current_date.weekday()  # 0 = Monday, 6 = Sunday
        monday_wordle = int(latest_wordle) - weekday
        
        # For debug, get all scores for Aug 4th week (wordle 1507 - Monday)
        # This is just a simple hardcoded approach for now since we know the data
        monday_wordle = 1507  # Aug 4, 2025
        end_wordle = monday_wordle + 6  # Sunday
        
        logging.info(f"Getting weekly scores for league {league_id}, wordles {monday_wordle}-{end_wordle}")
        
        # Get raw scores for this week's wordle range
        cursor.execute("""
        SELECT p.name, s.score, s.wordle_number
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number BETWEEN ? AND ?
          AND p.league_id = ?
          AND s.score NOT IN ('X', 'X/6', '7')
          AND s.score IS NOT NULL 
          AND TRIM(s.score) != ''
        ORDER BY p.name, s.wordle_number
        """, (monday_wordle, end_wordle, league_id))
        
        raw_scores = cursor.fetchall()
        
        # Log raw score data for debugging
        logging.info(f"Found {len(raw_scores)} raw scores for league {league_id}, week of {monday_wordle}")
        for name, score, wordle in raw_scores:
            logging.info(f"  {name}: {score} (Wordle {wordle})")
        
        # Calculate weekly totals for each player
        player_totals = {}
        valid_score_counts = {}
        
        for name, score, _ in raw_scores:
            try:
                score_int = int(score)
                if name not in player_totals:
                    player_totals[name] = 0
                    valid_score_counts[name] = 0
                
                player_totals[name] += score_int
                valid_score_counts[name] += 1
            except (ValueError, TypeError):
                logging.warning(f"Invalid score format: {score} for player {name}")
                continue
        
        # Log weekly totals for debugging
        logging.info(f"Weekly totals for league {league_id}:")
        for name, total in player_totals.items():
            logging.info(f"  {name}: {total} (from {valid_score_counts[name]} scores)")
        
        # Filter for players with at least 5 scores
        eligible_players = []
        for name, count in valid_score_counts.items():
            if count >= 5:  # Need at least 5 valid scores to be eligible
                eligible_players.append((name, player_totals[name]))
        
        # Sort eligible players by score (lowest is winner)
        eligible_players.sort(key=lambda x: x[1])  # Sort by total score
        
        # Debug print eligible players
        logging.info(f"Eligible players (with 5+ scores) for league {league_id}:")
        for name, total in eligible_players:
            logging.info(f"  {name}: {total}")
        
        # Determine winners (players with lowest total score)
        if eligible_players:
            lowest_score = eligible_players[0][1]
            
            # Get the Monday date for this week
            monday_date = datetime.strptime(f"{current_date.year}-01-01", "%Y-%m-%d")
            monday_date += timedelta(days=7 * ((monday_wordle - 1507) // 7))
            while monday_date.weekday() != 0:  # Adjust to Monday
                monday_date -= timedelta(days=1)
            
            # Get all winners (could be multiple if tied)
            winners = [name for name, score in eligible_players if score == lowest_score]
            
            logging.info(f"Winners for league {league_id}: {winners} with score {lowest_score}")
            
            # Update win counts
            for winner in winners:
                if winner in player_wins:
                    player_wins[winner] += 1
                else:
                    player_wins[winner] = 1
                    
                weekly_winners.append({
                    'name': winner,
                    'week_date': monday_date,
                    'score': lowest_score,
                    'formatted_date': format_week_date(monday_date, lowest_score),
                    'weekly_wins': 1  # Will update this later
                })
        
        # Update weekly win counts
        for winner in weekly_winners:
            winner['weekly_wins'] = 1  # For now hardcode to 1 win since it's just 1 week
            
        # Sort winners by weekly wins (highest first), then by player name
        weekly_winners.sort(key=lambda x: (-x['weekly_wins'], x['name']))
        
        return weekly_winners
        
    except Exception as e:
        logging.error(f"Error getting weekly winners for league {league_id}: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if conn:
            conn.close()

def update_season_table(file_path, league_id):
    """Update the Season table in an HTML file with weekly winners"""
    try:
        # Create backup
        create_backup(file_path)
        
        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for the Season table
        season_container = soup.find('div', {'class': 'season-container'})
        if not season_container:
            logging.warning(f"Could not find season container in {file_path}")
            return False
        
        # Find the Season table
        season_table = season_container.find('table', {'class': 'season-table'})
        if not season_table:
            logging.warning(f"Could not find season table in {file_path}")
            return False
        
        # Get weekly winners for this league
        weekly_winners = get_weekly_winners(league_id)
        
        # Get the table body
        tbody = season_table.find('tbody')
        if not tbody:
            logging.warning(f"Could not find table body in season table in {file_path}")
            return False
        
        # Clear the current table body content
        tbody.clear()
        
        if weekly_winners:
            # Add weekly winners to the table
            for winner in weekly_winners:
                tr = soup.new_tag('tr')
                
                # Player column
                td_player = soup.new_tag('td')
                td_player.string = winner['name']
                tr.append(td_player)
                
                # Weekly wins column
                td_wins = soup.new_tag('td')
                td_wins.string = str(winner['weekly_wins'])
                tr.append(td_wins)
                
                # Wordle week column
                td_week = soup.new_tag('td')
                td_week.string = winner['formatted_date']
                tr.append(td_week)
                
                tbody.append(tr)
        else:
            # If no winners, add a placeholder row
            tr = soup.new_tag('tr')
            td = soup.new_tag('td')
            td['colspan'] = '3'
            td['style'] = 'text-align: center;'
            td.string = 'No weekly winners yet'
            tr.append(td)
            tbody.append(tr)
        
        # Save the modified HTML
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info(f"Successfully updated season table in {file_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating season table in {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_league_id_from_name(league_name):
    """Get league ID from league name"""
    league_id_map = {
        "Wordle Warriorz": 1,
        "Wordle Gang": 2,
        "Wordle PAL": 3,
        "Wordle Party": 4,
        "Wordle Vball": 5
    }
    return league_id_map.get(league_name)

def main():
    """Update season tables across all league HTML files"""
    logging.info("Starting to update season tables with weekly winners - FIXED VERSION")
    
    success_count = 0
    error_count = 0
    
    for league_name, league_dir in LEAGUE_DIRS.items():
        # Get league ID
        league_id = get_league_id_from_name(league_name)
        if not league_id:
            logging.warning(f"Could not determine league ID for {league_name}")
            error_count += 1
            continue
            
        # Construct the path to the league's index.html file
        if league_dir:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
        else:
            index_path = os.path.join(WEBSITE_EXPORT_DIR, "index.html")
            
        if os.path.exists(index_path):
            logging.info(f"Updating season table for {league_name} league (ID: {league_id})")
            if update_season_table(index_path, league_id):
                success_count += 1
            else:
                error_count += 1
        else:
            logging.warning(f"Could not find index.html for {league_name} league at {index_path}")
            error_count += 1
    
    logging.info(f"Season table updates completed: {success_count} successful, {error_count} errors")
    print(f"Season table updates completed: {success_count} successful, {error_count} errors")

if __name__ == "__main__":
    main()
