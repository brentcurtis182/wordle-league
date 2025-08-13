#!/usr/bin/env python3
"""
Update Season Table with Weekly Winners

This script:
1. Determines weekly winners based on the lowest weekly score for each week
2. Updates the Season table in all league HTML files with:
   - Player name
   - Weekly wins count
   - Week date in the format "Aug 4th - (14)" where 14 is the score

Fixed version: Uses exact Wordle numbers (1506-1513) for Aug 4-10, 2025
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
        logging.FileHandler("update_season_winners.log"),
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

def debug_print_scores(label, data):
    """Debug function to print player scores"""
    logging.info(f"--- DEBUG: {label} ---")
    for item in data:
        logging.info(f"  {item}")
    logging.info("-------------------------------------")

def get_weekly_winners(league_id):
    """
    Get weekly winners for a league based on the lowest total of 5 BEST weekly scores
    Returns a list of dictionaries with weekly winner data
    Uses FIXED Wordle numbers for Aug 4-10, 2025: #1506-1513
    Players need at least 5 valid scores to be eligible
    Only the 5 best (lowest) scores are used to calculate the total score
    """
    conn = None
    weekly_winners = []
    player_wins = {}  # Track win count per player
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # FIXED: Use exact Wordle numbers for the week Aug 4-10
        # Monday (Aug 4) = Wordle #1506, Sunday (Aug 10) = Wordle #1513
        start_wordle = 1506
        end_wordle = 1513
        
        logging.info(f"Getting weekly scores for league {league_id}, wordles {start_wordle}-{end_wordle}")
        
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
        """, (start_wordle, end_wordle, league_id))
        
        raw_scores = cursor.fetchall()
        
        # Log raw score data for debugging
        logging.info(f"Found {len(raw_scores)} raw scores for league {league_id}, wordles {start_wordle}-{end_wordle}")
        for name, score, wordle in raw_scores:
            logging.info(f"  {name}: {score} (Wordle {wordle})")
        
        # Collect all valid scores per player
        player_scores = {}
        valid_score_counts = {}
        
        for name, score, wordle in raw_scores:
            try:
                score_int = int(score)
                if name not in player_scores:
                    player_scores[name] = []
                    valid_score_counts[name] = 0
                
                player_scores[name].append((score_int, wordle))
                valid_score_counts[name] += 1
            except (ValueError, TypeError):
                logging.warning(f"Invalid score format: {score} for player {name}")
                continue
        
        # Calculate weekly totals using BEST 5 scores for each player
        player_totals = {}
        best_scores = {}
        
        for name, scores in player_scores.items():
            # Only use 5 best (lowest) scores if they have at least 5
            if len(scores) >= 5:
                # Sort by score value (lowest first) and take top 5
                best_five = sorted(scores, key=lambda x: x[0])[:5]
                best_scores[name] = best_five
                
                # Sum the best 5 scores
                total = sum(score for score, _ in best_five)
                player_totals[name] = total
                
                # Log the best 5 scores for debugging
                logging.info(f"Best 5 scores for {name}:")
                for score, wordle in sorted(best_five, key=lambda x: x[1]):  # Sort by wordle number for display
                    logging.info(f"  Wordle {wordle}: {score}")
        
        # Log weekly totals for debugging
        logging.info(f"Weekly totals using best 5 scores for league {league_id}:")
        for name, total in player_totals.items():
            logging.info(f"  {name}: {total} (from best 5 of {valid_score_counts[name]} scores)")
        
        # Filter for players with at least 5 scores (they're already in player_totals)
        eligible_players = [(name, total) for name, total in player_totals.items()]
        
        # Sort eligible players by score (lowest is winner)
        eligible_players.sort(key=lambda x: x[1])  # Sort by total score
        
        # Log eligible players for debugging
        logging.info(f"Eligible players (with 5+ scores) for league {league_id}:")
        for name, total in eligible_players:
            logging.info(f"  {name}: {total}")
        
        # Determine winners (players with lowest total score)
        if eligible_players:
            lowest_score = eligible_players[0][1]
            
            # Get all winners (could be multiple if tied)
            winners = [name for name, score in eligible_players if score == lowest_score]
            
            logging.info(f"Winners for league {league_id}: {winners} with score {lowest_score}")
            
            # Monday date for Aug 4th, 2025
            monday_date = datetime(2025, 8, 4)
            
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
                    'weekly_wins': 1  # Will be updated below
                })
        
        # Update weekly win counts
        for winner in weekly_winners:
            winner['weekly_wins'] = player_wins[winner['name']]
            
        # Sort winners by weekly wins (highest first), then by player name
        weekly_winners.sort(key=lambda x: (-x['weekly_wins'], x['name']))
        
        return weekly_winners
        
    except Exception as e:
        logging.error(f"Error getting weekly winners for league {league_id}: {e}")
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
    logging.info("Starting to update season tables with weekly winners")
    
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
