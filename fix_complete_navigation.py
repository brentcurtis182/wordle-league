#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
import json
import re
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='fix_complete_navigation.log'
)
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())  # Add console output

# Constants
WORDLE_DATABASE = 'wordle_league.db'
EXPORT_DIR = 'website_export'
DAYS_DIR = os.path.join(EXPORT_DIR, 'days')
WEEKS_DIR = os.path.join(EXPORT_DIR, 'weeks')
CONFIG_FILE = 'league_config.json'
DB_FILE = WORDLE_DATABASE

# Current Wordle data
CURRENT_WORDLE_NUM = 1507  # August 4, 2025
WORDLE_START_DATE = datetime(2021, 6, 19)  # Wordle #1

def get_date_for_wordle_num(wordle_num):
    """Calculate the date for a given Wordle number"""
    return WORDLE_START_DATE + timedelta(days=wordle_num-1)

def get_league_config():
    """Load league configuration from the config file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading league configuration: {e}")
        return None

def get_league_slug(league_name):
    """Convert league name to a slug for use in filenames"""
    return re.sub(r'\W+', '-', league_name.lower())

def get_scores_for_wordle_by_league(wordle_number, league_id):
    """Get all scores for a specific wordle number and league"""
    conn = None
    scores = []
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all scores for this Wordle number for the specified league
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number = ? AND p.league_id = ?
        ORDER BY 
            CASE 
                WHEN s.score = 'X/6' THEN 7 
                ELSE CAST(SUBSTR(s.score, 1, 1) AS INTEGER) 
            END ASC,
            p.name ASC
        """, (wordle_number, league_id))
        
        scores = cursor.fetchall()
    except Exception as e:
        logging.error(f"Error getting scores for Wordle #{wordle_number}: {e}")
    finally:
        if conn:
            conn.close()
    
    return scores

def get_wordle_stats_for_week(wordle_numbers, league_id):
    """Get player stats for a range of wordle numbers for a specific league"""
    conn = None
    player_stats = {}
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all players for this league
        cursor.execute("""
        SELECT id, name, nickname
        FROM players
        WHERE league_id = ?
        ORDER BY name
        """, (league_id,))
        
        players = cursor.fetchall()
        
        # Initialize player stats
        for player_id, name, nickname in players:
            player_stats[player_id] = {
                'name': name,
                'nickname': nickname or name,
                'games_played': 0,
                'total_score': 0,
                'scores': [],
                'wins': 0,
                'best': 7,
                'average': 0
            }
        
        # Get all scores for these Wordle numbers for players in this league
        # Ensure wordle_numbers is a list
        if not isinstance(wordle_numbers, list):
            wordle_numbers = [wordle_numbers]
            
        placeholders = ','.join(['?'] * len(wordle_numbers))
        query_params = wordle_numbers + [league_id]
        
        cursor.execute(f"""
        SELECT s.player_id, s.score, s.wordle_number
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number IN ({placeholders})
        AND p.league_id = ?
        ORDER BY s.wordle_number, p.name
        """, query_params)
        
        scores = cursor.fetchall()
        
        # Process scores
        for player_id, score, wordle_number in scores:
            if player_id in player_stats:
                # Convert X/6 to numerical 7 for calculations
                numerical_score = 7 if score == 'X/6' else int(score[0])
                
                player_stats[player_id]['games_played'] += 1
                player_stats[player_id]['total_score'] += numerical_score
                player_stats[player_id]['scores'].append((wordle_number, score))
                
                # Check for win (score of 1)
                if numerical_score == 1:
                    player_stats[player_id]['wins'] += 1
                
                # Update best score
                player_stats[player_id]['best'] = min(player_stats[player_id]['best'], numerical_score)
        
        # Calculate averages
        for player_id in player_stats:
            games = player_stats[player_id]['games_played']
            if games > 0:
                player_stats[player_id]['average'] = round(player_stats[player_id]['total_score'] / games, 2)
    
    except Exception as e:
        logging.error(f"Error getting weekly stats: {e}")
    finally:
        if conn:
            conn.close()
    
    # Convert to list and sort by wins (descending) then average (ascending)
    stats_list = list(player_stats.values())
    stats_list.sort(key=lambda x: (-x['wins'], x['average']))
    
    return stats_list

def get_all_time_stats_by_league(league_id):
    """Get all-time player stats for a specific league"""
    conn = None
    player_stats = {}
    
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all players for this league
        cursor.execute("""
        SELECT id, name, nickname
        FROM players
        WHERE league_id = ?
        ORDER BY name
        """, (league_id,))
        
        players = cursor.fetchall()
        
        # Initialize player stats
        for player_id, name, nickname in players:
            player_stats[player_id] = {
                'name': name,
                'nickname': nickname or name,
                'games_played': 0,
                'total_score': 0,
                'wins': 0,
                'best': 7,
                'average': 0
            }
        
        # Get all scores for players in this league
        cursor.execute("""
        SELECT s.player_id, s.score
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE p.league_id = ?
        """, (league_id,))
        
        scores = cursor.fetchall()
        
        # Process scores
        for player_id, score in scores:
            if player_id in player_stats:
                # Convert X/6 to numerical 7 for calculations
                numerical_score = 7 if score == 'X/6' else int(score[0])
                
                player_stats[player_id]['games_played'] += 1
                player_stats[player_id]['total_score'] += numerical_score
                
                # Check for win (score of 1)
                if numerical_score == 1:
                    player_stats[player_id]['wins'] += 1
                
                # Update best score
                player_stats[player_id]['best'] = min(player_stats[player_id]['best'], numerical_score)
        
        # Calculate averages
        for player_id in player_stats:
            games = player_stats[player_id]['games_played']
            if games > 0:
                player_stats[player_id]['average'] = round(player_stats[player_id]['total_score'] / games, 2)
    
    except Exception as e:
        logging.error(f"Error getting all-time stats: {e}")
    finally:
        if conn:
            conn.close()
    
    # Convert to list and sort by games played (descending) then average (ascending)
    stats_list = list(player_stats.values())
    stats_list.sort(key=lambda x: (-x['games_played'], x['average']))
    
    return stats_list

def fix_week_pages():
    """Fix all league-specific week pages by adding game listings and links"""
    league_config = get_league_config()
    if not league_config:
        logging.error("Failed to load league configuration.")
        return
    
    # Define the week range (August 4-10, 2025)
    # Wordle numbers 1507-1513
    start_wordle = 1507
    end_wordle = 1513
    wordle_numbers = list(range(start_wordle, end_wordle + 1))
    
    # Get dates for the week
    start_date = get_date_for_wordle_num(start_wordle)
    week_name = f"aug-4th-(14)"  # Week 14, starting August 4th
    
    # Loop through leagues in the config
    for league_data in league_config['leagues']:
        league_id = league_data['league_id']
        league_name = league_data['name']
        league_slug = get_league_slug(league_name)
        
        # Week page filename
        week_filename = f"{week_name}-{league_slug}.html"
        week_filepath = os.path.join(WEEKS_DIR, week_filename)
        
        # Check if week page exists
        if not os.path.exists(week_filepath):
            logging.warning(f"Week page {week_filename} does not exist, skipping.")
            continue
        
        try:
            # Load existing page
            with open(week_filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Find the games table body
            tbody = soup.select_one('.week-details table tbody')
            if not tbody:
                logging.warning(f"Could not find table body in {week_filename}")
                continue
            
            # Clear existing content
            tbody.clear()
            
            # Add game listings
            for wordle_num in wordle_numbers:
                date = get_date_for_wordle_num(wordle_num)
                day_page = f"wordle-{wordle_num}-{league_slug}.html"
                
                tr = soup.new_tag('tr')
                
                # Wordle number column with link to day page
                td_num = soup.new_tag('td')
                a_tag = soup.new_tag('a', href=f"../days/{day_page}")
                a_tag.string = f"Wordle #{wordle_num}"
                td_num.append(a_tag)
                tr.append(td_num)
                
                # Date column
                td_date = soup.new_tag('td')
                td_date.string = date.strftime("%B %d, %Y")
                tr.append(td_date)
                
                tbody.append(tr)
            
            # Update week title
            h1 = soup.select_one('h1')
            if h1:
                h1.string = f"Wordle Week: August 4-10, 2025"
            
            # Add player stats tables
            # Get stats for this week for this league
            week_stats = get_wordle_stats_for_week(wordle_numbers, league_id)
            
            # Find or create the weekly stats section
            weekly_stats_div = soup.select_one('.weekly-stats')
            if not weekly_stats_div:
                weekly_stats_div = soup.new_tag('div', attrs={'class': 'weekly-stats'})
                week_details_div = soup.select_one('.week-details')
                if week_details_div:
                    week_details_div.append(weekly_stats_div)
            else:
                weekly_stats_div.clear()
            
            # Add weekly stats title
            stats_title = soup.new_tag('h3')
            stats_title.string = "Weekly Stats"
            weekly_stats_div.append(stats_title)
            
            if week_stats:
                # Create table container
                table_div = soup.new_tag('div', attrs={'class': 'table-container'})
                
                # Create table
                table = soup.new_tag('table')
                
                # Table header
                thead = soup.new_tag('thead')
                header_tr = soup.new_tag('tr')
                
                headers = ['Player', 'Games', 'Avg', 'Best', 'Wins']
                for header in headers:
                    th = soup.new_tag('th')
                    th.string = header
                    header_tr.append(th)
                
                thead.append(header_tr)
                table.append(thead)
                
                # Table body
                tbody = soup.new_tag('tbody')
                
                for stats in week_stats:
                    tr = soup.new_tag('tr')
                    
                    # Player name
                    td_name = soup.new_tag('td')
                    td_name.string = stats['nickname']
                    tr.append(td_name)
                    
                    # Games played
                    td_games = soup.new_tag('td')
                    td_games.string = str(stats['games_played'])
                    tr.append(td_games)
                    
                    # Average score
                    td_avg = soup.new_tag('td')
                    td_avg.string = str(stats['average'])
                    tr.append(td_avg)
                    
                    # Best score
                    td_best = soup.new_tag('td')
                    td_best.string = 'X/6' if stats['best'] == 7 else f"{stats['best']}/6"
                    tr.append(td_best)
                    
                    # Wins
                    td_wins = soup.new_tag('td')
                    td_wins.string = str(stats['wins'])
                    tr.append(td_wins)
                    
                    tbody.append(tr)
                
                table.append(tbody)
                table_div.append(table)
                weekly_stats_div.append(table_div)
            else:
                no_stats_p = soup.new_tag('p', style="text-align: center;")
                no_stats_p.string = "No statistics available for this week."
                weekly_stats_div.append(no_stats_p)
            
            # Save updated file
            with open(week_filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            logging.info(f"Updated week page: {week_filename}")
            
        except Exception as e:
            logging.error(f"Error updating week page {week_filename}: {e}")

def fix_main_index_page():
    """Fix the main index page to show proper player data and league tabs"""
    league_config = get_league_config()
    if not league_config:
        logging.error("Failed to load league configuration.")
        return
        
    # Ensure the leagues key exists in config
    if 'leagues' not in league_config:
        logging.error("Invalid league configuration: 'leagues' key not found.")
        return
        
    # Main index page path
    main_index_path = os.path.join(EXPORT_DIR, 'index.html')
    
    try:
        # Load the existing index page
        with open(main_index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Get today's Wordle data for each league
        today_wordle = CURRENT_WORDLE_NUM
        today_date = get_date_for_wordle_num(today_wordle)
        today_date_str = today_date.strftime("%B %d, %Y")
        
        # Create tabs for each league
        tabs_div = soup.select_one('.tab-buttons.tabs')
        if not tabs_div:
            logging.error("Could not find tab buttons div in index.html")
            return
            
        # Clear the existing tab buttons
        tabs_div.clear()
        
        # Create the main tabs section (Latest, Weekly, Stats)
        main_tabs_div = soup.new_tag('div', style="width: 100%; display: flex; justify-content: center;")
        main_tabs_div.append(soup.new_tag('button', attrs={'class': 'tab-button active', 'data-tab': 'latest', 'data-league': 'all'}))
        main_tabs_div.select_one('button').string = 'Latest Scores'
        
        main_tabs_div.append(soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'weekly', 'data-league': 'all'}))
        main_tabs_div.select('button')[1].string = 'Weekly Totals'
        
        main_tabs_div.append(soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'stats', 'data-league': 'all'}))
        main_tabs_div.select('button')[2].string = 'Season / All-Time Stats'
        
        tabs_div.append(main_tabs_div)
        
        # Create league tabs section
        league_tabs_div = soup.new_tag('div', style="width: 100%; display: flex; justify-content: center; margin-top: 10px;")
        
        for league in league_config['leagues']:
            league_name = league['name']
            league_slug = get_league_slug(league_name)
            
            # Create league tab button
            league_button = soup.new_tag('button', attrs={
                'class': 'tab-button league-tab',
                'data-league': league_slug
            })
            league_button.string = league_name
            
            # Add league button to the tabs
            league_tabs_div.append(league_button)
        
        # Add the league tabs section to the main tabs div
        tabs_div.append(league_tabs_div)
        
        # Default league is the first one
        default_league = league_config['leagues'][0]
        default_league_name = default_league['name']
        default_league_id = default_league['league_id']
        default_league_slug = get_league_slug(default_league_name)
        
        # Update page title to match default league
        title_tag = soup.select_one('title')
        if title_tag:
            title_tag.string = f"{default_league_name} - Wordle League"
        
        header_title = soup.select_one('header .title')
        if header_title:
            header_title.string = default_league_name
        
        # Update tab content for Latest Scores (latest tab)
        latest_tab = soup.select_one('#latest')
        if latest_tab:
            latest_tab.clear()
            
            # Add title
            title_h2 = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px; font-size: 16px; color: #6aaa64; text-align: center;")
            title_h2.string = f"Wordle #{today_wordle} - {today_date_str}"
            latest_tab.append(title_h2)
            
            # Add scores
            scores = get_scores_for_wordle_by_league(today_wordle, default_league_id)
            
            if scores:
                # Create player cards container
                cards_div = soup.new_tag('div', attrs={'class': 'player-cards'})
                
                for name, nickname, score, emoji_pattern in scores:
                    player_name = nickname or name
                    
                    # Create player card
                    card_div = soup.new_tag('div', attrs={'class': 'player-card'})
                    
                    # Player name
                    name_p = soup.new_tag('p', attrs={'class': 'player-name'})
                    name_p.string = player_name
                    card_div.append(name_p)
                    
                    # Player score
                    score_p = soup.new_tag('p', attrs={'class': 'player-score'})
                    score_p.string = score
                    card_div.append(score_p)
                    
                    # Emoji pattern
                    if emoji_pattern:
                        pattern_div = soup.new_tag('div', attrs={'class': 'emoji-pattern'})
                        pattern_div.string = emoji_pattern
                        card_div.append(pattern_div)
                    
                    # Add card to container
                    cards_div.append(card_div)
                
                latest_tab.append(cards_div)
            else:
                # No scores found - add a message
                no_scores_p = soup.new_tag('p', style="text-align: center; padding: 20px;")
                no_scores_p.string = "No scores available for today."
                latest_tab.append(no_scores_p)
            
            # Add link to week page regardless of whether there are scores
            link_p = soup.new_tag('p', style="text-align: center; margin-top: 20px;")
            week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html", attrs={'class': 'button'})
            week_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            week_link.string = "View This Week"
            link_p.append(week_link)
            latest_tab.append(link_p)
        
        # Update Weekly Totals tab
        weekly_tab = soup.select_one('#weekly')
        if weekly_tab:
            weekly_tab.clear()
            
            # Add title
            title_h2 = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px;")
            title_h2.string = "Weekly Totals"
            weekly_tab.append(title_h2)
            
            # Get weekly stats
            wordle_numbers = list(range(1507, 1514))  # 1507-1513
            weekly_stats = get_wordle_stats_for_week(wordle_numbers, default_league_id)
            
            if weekly_stats:
                # Create table container
                table_div = soup.new_tag('div', attrs={'class': 'table-container'})
                table = soup.new_tag('table')
                
                # Table header
                thead = soup.new_tag('thead')
                header_tr = soup.new_tag('tr')
                
                headers = ['Player', 'Games', 'Avg', 'Best', 'Wins']
                for header in headers:
                    th = soup.new_tag('th')
                    th.string = header
                    header_tr.append(th)
                
                thead.append(header_tr)
                table.append(thead)
                
                # Table body
                tbody = soup.new_tag('tbody')
                
                for stats in weekly_stats:
                    tr = soup.new_tag('tr')
                    
                    # Player name
                    td_name = soup.new_tag('td')
                    td_name.string = stats['nickname']
                    tr.append(td_name)
                    
                    # Games played
                    td_games = soup.new_tag('td')
                    td_games.string = str(stats['games_played'])
                    tr.append(td_games)
                    
                    # Average score
                    td_avg = soup.new_tag('td')
                    td_avg.string = str(stats['average'])
                    tr.append(td_avg)
                    
                    # Best score
                    td_best = soup.new_tag('td')
                    td_best.string = 'X/6' if stats['best'] == 7 else f"{stats['best']}/6"
                    tr.append(td_best)
                    
                    # Wins
                    td_wins = soup.new_tag('td')
                    td_wins.string = str(stats['wins'])
                    tr.append(td_wins)
                    
                    tbody.append(tr)
                
                table.append(tbody)
                table_div.append(table)
                weekly_tab.append(table_div)
                
                # Add link to week page
                link_p = soup.new_tag('p', style="text-align: center; margin-top: 20px;")
                week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html", attrs={'class': 'button'})
                week_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
                week_link.string = "View Week Details"
                link_p.append(week_link)
                weekly_tab.append(link_p)
            else:
                # No stats found
                no_stats_p = soup.new_tag('p', style="text-align: center; padding: 20px;")
                no_stats_p.string = "No weekly statistics available."
                weekly_tab.append(no_stats_p)
                
                # Add link to week page anyway
                link_p = soup.new_tag('p', style="text-align: center;")
                week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html")
                week_link.string = f"View week of August 4th"
                link_p.append(week_link)
                weekly_tab.append(link_p)
        
        # Update Season / All-Time Stats tab
        stats_tab = soup.select_one('#stats')
        if stats_tab:
            stats_tab.clear()
            
            # Season title
            season_h2 = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px;")
            season_h2.string = "Season 1"
            stats_tab.append(season_h2)
            
            season_p = soup.new_tag('p', style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;")
            season_p.string = "Weekly wins are tracked here. First player to reach 4 wins is the Season Winner!"
            stats_tab.append(season_p)
            
            # Add link to week page
            link_div = soup.new_tag('div', style="text-align: center; padding: 20px;")
            week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html", attrs={'class': 'button'})
            week_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            week_link.string = "View Current Week"
            link_div.append(week_link)
            stats_tab.append(link_div)
            
            # All-Time Stats title
            alltime_h2 = soup.new_tag('h2', style="margin-top: 20px; margin-bottom: 10px;")
            alltime_h2.string = "All-Time Stats"
            stats_tab.append(alltime_h2)
            
            alltime_p = soup.new_tag('p', style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;")
            alltime_p.string = "Average includes all games. Failed attempts (X/6) count as 7 in the average calculation."
            stats_tab.append(alltime_p)
            
            # Get all-time stats
            alltime_stats = get_all_time_stats_by_league(default_league_id)
            
            if alltime_stats:
                # Create table container
                table_div = soup.new_tag('div', attrs={'class': 'table-container'})
                table = soup.new_tag('table')
                
                # Table header
                thead = soup.new_tag('thead')
                header_tr = soup.new_tag('tr')
                
                headers = ['Player', 'Games', 'Avg', 'Best', 'Wins']
                for header in headers:
                    th = soup.new_tag('th')
                    th.string = header
                    header_tr.append(th)
                
                thead.append(header_tr)
                table.append(thead)
                
                # Table body
                tbody = soup.new_tag('tbody')
                
                for stats in alltime_stats:
                    tr = soup.new_tag('tr')
                    
                    # Player name
                    td_name = soup.new_tag('td')
                    td_name.string = stats['nickname']
                    tr.append(td_name)
                    
                    # Games played
                    td_games = soup.new_tag('td')
                    td_games.string = str(stats['games_played'])
                    tr.append(td_games)
                    
                    # Average score
                    td_avg = soup.new_tag('td')
                    td_avg.string = str(stats['average'])
                    tr.append(td_avg)
                    
                    # Best score
                    td_best = soup.new_tag('td')
                    td_best.string = 'X/6' if stats['best'] == 7 else f"{stats['best']}/6"
                    tr.append(td_best)
                    
                    # Wins
                    td_wins = soup.new_tag('td')
                    td_wins.string = str(stats['wins'])
                    tr.append(td_wins)
                    
                    tbody.append(tr)
                
                table.append(tbody)
                table_div.append(table)
                stats_tab.append(table_div)
            else:
                # No stats found
                no_stats_p = soup.new_tag('p', style="text-align: center; padding: 20px;")
                no_stats_p.string = "No all-time statistics available."
                stats_tab.append(no_stats_p)
        
        # Add JavaScript for league switching
        script_tag = soup.find('script', src='script.js')
        if script_tag:
            # Add custom script after the main script
            league_script = soup.new_tag('script')
            league_script.string = """
            document.addEventListener('DOMContentLoaded', function() {
                // Handle league tab clicks
                const leagueTabs = document.querySelectorAll('.league-tab');
                const defaultLeague = leagueTabs.length > 0 ? leagueTabs[0].getAttribute('data-league') : null;
                
                // Set default active league
                document.querySelectorAll('.league-tab').forEach(tab => {
                    if (tab.getAttribute('data-league') === defaultLeague) {
                        tab.classList.add('active');
                    }
                });
                
                // League tab click handler
                leagueTabs.forEach(tab => {
                    tab.addEventListener('click', function() {
                        const league = this.getAttribute('data-league');
                        
                        // Update active tab
                        document.querySelectorAll('.league-tab').forEach(t => {
                            t.classList.remove('active');
                        });
                        this.classList.add('active');
                        
                        // Update week links
                        document.querySelectorAll('a[href*="weeks/aug-4th-(14)-"]').forEach(link => {
                            link.setAttribute('href', 'weeks/aug-4th-(14)-' + league + '.html');
                        });
                        
                        // Update header title
                        const leagueName = this.textContent;
                        document.querySelector('header .title').textContent = leagueName;
                        
                        // Store selected league in local storage
                        localStorage.setItem('selectedLeague', league);
                        localStorage.setItem('selectedLeagueName', leagueName);
                        
                        // Refresh data for this league
                        fetchLeagueData(league, leagueName);
                    });
                });
                
                // Function to fetch league data (simulation for this fix)
                function fetchLeagueData(league, leagueName) {
                    // For now, just redirect to the league's week page
                    window.location.href = 'weeks/aug-4th-(14)-' + league + '.html';
                }
                
                // Check if there's a stored league preference
                const storedLeague = localStorage.getItem('selectedLeague');
                const storedLeagueName = localStorage.getItem('selectedLeagueName');
                
                if (storedLeague && storedLeagueName) {
                    // Find the corresponding tab and simulate click
                    const tab = Array.from(leagueTabs).find(t => t.getAttribute('data-league') === storedLeague);
                    if (tab) {
                        // Update header and links without page reload
                        document.querySelector('header .title').textContent = storedLeagueName;
                        document.querySelectorAll('a[href*="weeks/aug-4th-(14)-"]').forEach(link => {
                            link.setAttribute('href', 'weeks/aug-4th-(14)-' + storedLeague + '.html');
                        });
                    }
                }
            });
            """
            soup.body.append(league_script)
        
        # Save the updated index page
        with open(main_index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info("Successfully updated main index page with league navigation")
        
    except Exception as e:
        logging.error(f"Error updating main index page: {e}")


if __name__ == "__main__":
    logging.info("Starting navigation fix process...")
    
    # Step 1: Fix league-specific week pages with game listings and links
    logging.info("Step 1: Fixing league-specific week pages...")
    fix_week_pages()
    
    # Step 2: Fix main index page with proper player data and league tabs
    logging.info("Step 2: Fixing main index page...")
    fix_main_index_page()
    
    logging.info("Navigation fix complete!")
    print("\nAll fixes have been applied. Please check the website to verify.")
    print("You can run an HTTP server to test locally with: python -m http.server 8080 -d website_export")
