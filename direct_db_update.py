#!/usr/bin/env python3
"""
Direct Database to HTML Updater

This script:
1. Connects directly to the database to get the latest scores
2. Reads the current HTML files (with tabs intact)
3. Updates ONLY the content within the tabs, never touching the structure
4. Writes the updated HTML back to the same files

No templates, no export scripts, no intermediary steps - just direct updates.
"""

import os
import sys
import sqlite3
import re
import logging
import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    filename='direct_db_update.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
EXPORT_DIR = 'website_export'
BACKUP_DIR = r"C:\Wordle-League\website_export_backup_Aug10_2025_1148pm_with_season_20250810_234948"
DATABASE_PATH = 'wordle_league.db'
LEAGUES = [
    {'dir': '', 'id': 1, 'name': 'Wordle Warriorz'},  # Main league
    {'dir': 'gang', 'id': 2, 'name': 'Wordle Gang'},
    {'dir': 'pal', 'id': 3, 'name': 'Wordle PAL'},
    {'dir': 'party', 'id': 4, 'name': 'Wordle Party'},
    {'dir': 'vball', 'id': 5, 'name': 'Wordle Vball'}
]

def connect_to_database():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"Failed to connect to database: {str(e)}")
        return None

def get_latest_wordle_number():
    """Get the latest Wordle number from the database"""
    conn = connect_to_database()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(wordle_num) as latest FROM scores")
        result = cursor.fetchone()
        if result and result['latest']:
            return result['latest']
        else:
            # Calculate based on date if not in database
            start_date = datetime.datetime(2021, 6, 19)  # Wordle #0
            today = datetime.datetime.now()
            days_since_start = (today - start_date).days
            return days_since_start
    except Exception as e:
        logging.error(f"Error getting latest wordle number: {str(e)}")
        return None
    finally:
        conn.close()

def get_wordle_date(wordle_number):
    """Calculate the date for a given Wordle number"""
    try:
        start_date = datetime.datetime(2021, 6, 19)  # Wordle #0
        wordle_date = start_date + datetime.timedelta(days=wordle_number)
        return wordle_date.strftime('%B %d, %Y')
    except Exception as e:
        logging.error(f"Error calculating Wordle date: {str(e)}")
        return datetime.datetime.now().strftime('%B %d, %Y')

def get_player_scores(league_id, wordle_number):
    """Get player scores from the database for a specific league and wordle number"""
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        query = """
        SELECT p.player_name, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.league_id = ? AND s.wordle_num = ?
        ORDER BY 
            CASE 
                WHEN s.score = 'X/6' THEN 7 
                ELSE CAST(substr(s.score, 1, 1) AS INTEGER) 
            END
        """
        cursor.execute(query, (league_id, wordle_number))
        
        scores = []
        for row in cursor.fetchall():
            scores.append({
                'name': row['player_name'],
                'score': row['score'],
                'emoji_pattern': row['emoji_pattern'] or ''
            })
        
        return scores
    except Exception as e:
        logging.error(f"Error fetching player scores: {str(e)}")
        return []
    finally:
        conn.close()

def get_weekly_totals(league_id):
    """Get weekly totals for all players in a league"""
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Get current week's start date (Monday)
        today = datetime.datetime.now()
        days_since_monday = today.weekday()  # 0 is Monday
        monday = today - datetime.timedelta(days=days_since_monday)
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate start and end wordle numbers for this week
        start_date = datetime.datetime(2021, 6, 19)  # Wordle #0
        days_since_start_monday = (monday - start_date).days
        days_since_start_sunday = days_since_start_monday + 6
        
        monday_wordle = days_since_start_monday
        sunday_wordle = days_since_start_sunday
        
        query = """
        SELECT 
            p.player_name,
            COUNT(*) as games_played,
            SUM(CASE WHEN s.score = 'X/6' THEN 7 ELSE CAST(substr(s.score, 1, 1) AS INTEGER) END) as total_score,
            ROUND(AVG(CASE WHEN s.score = 'X/6' THEN 7 ELSE CAST(substr(s.score, 1, 1) AS INTEGER) END), 2) as average,
            SUM(CASE WHEN s.score = 'X/6' THEN 1 ELSE 0 END) as failed_attempts
        FROM 
            scores s
        JOIN 
            players p ON s.player_id = p.id
        WHERE 
            s.league_id = ? AND 
            s.wordle_num BETWEEN ? AND ?
        GROUP BY 
            p.player_name
        ORDER BY 
            average ASC,
            games_played DESC
        """
        
        cursor.execute(query, (league_id, monday_wordle, sunday_wordle))
        
        weekly_data = []
        for row in cursor.fetchall():
            weekly_data.append({
                'name': row['player_name'],
                'games_played': row['games_played'],
                'total_score': row['total_score'],
                'average': row['average'],
                'failed_attempts': row['failed_attempts']
            })
        
        return weekly_data
    except Exception as e:
        logging.error(f"Error fetching weekly totals: {str(e)}")
        return []
    finally:
        conn.close()

def get_season_winners(league_id):
    """Get weekly winners for the current season"""
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Get current season (approximation - just last 10 weeks)
        today = datetime.datetime.now()
        ten_weeks_ago = today - datetime.timedelta(weeks=10)
        
        # Convert dates to wordle numbers
        start_date = datetime.datetime(2021, 6, 19)  # Wordle #0
        days_since_start_today = (today - start_date).days
        days_since_start_ten_weeks = (ten_weeks_ago - start_date).days
        
        query = """
        WITH WeeklyScores AS (
            SELECT 
                p.player_name,
                (s.wordle_num - ?) / 7 as week_number,
                ROUND(AVG(CASE WHEN s.score = 'X/6' THEN 7 ELSE CAST(substr(s.score, 1, 1) AS INTEGER) END), 2) as average,
                COUNT(*) as games_played
            FROM 
                scores s
            JOIN 
                players p ON s.player_id = p.id
            WHERE 
                s.league_id = ? AND 
                s.wordle_num BETWEEN ? AND ?
            GROUP BY 
                p.player_name, week_number
            HAVING 
                games_played >= 5  -- At least 5 games in a week
        ),
        WeeklyRanks AS (
            SELECT 
                player_name,
                week_number,
                average,
                games_played,
                RANK() OVER (PARTITION BY week_number ORDER BY average ASC, games_played DESC) as rank
            FROM 
                WeeklyScores
        )
        SELECT 
            player_name,
            week_number,
            average,
            games_played
        FROM 
            WeeklyRanks
        WHERE 
            rank = 1
        ORDER BY 
            week_number DESC
        """
        
        cursor.execute(query, (days_since_start_ten_weeks, league_id, days_since_start_ten_weeks, days_since_start_today))
        
        weekly_winners = []
        for row in cursor.fetchall():
            weekly_winners.append({
                'name': row['player_name'],
                'week': row['week_number'],
                'average': row['average'],
                'games': row['games_played']
            })
        
        return weekly_winners
    except Exception as e:
        logging.error(f"Error fetching season winners: {str(e)}")
        return []
    finally:
        conn.close()

def get_all_time_stats(league_id):
    """Get all-time stats for all players in a league"""
    conn = connect_to_database()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        query = """
        SELECT 
            p.player_name,
            COUNT(*) as games_played,
            SUM(CASE WHEN s.score = 'X/6' THEN 7 ELSE CAST(substr(s.score, 1, 1) AS INTEGER) END) as total_score,
            ROUND(AVG(CASE WHEN s.score = 'X/6' THEN 7 ELSE CAST(substr(s.score, 1, 1) AS INTEGER) END), 2) as average,
            SUM(CASE WHEN s.score = 'X/6' THEN 1 ELSE 0 END) as failed_attempts,
            SUM(CASE WHEN CAST(substr(s.score, 1, 1) AS INTEGER) = 1 THEN 1 ELSE 0 END) as ones,
            SUM(CASE WHEN CAST(substr(s.score, 1, 1) AS INTEGER) = 2 THEN 1 ELSE 0 END) as twos,
            SUM(CASE WHEN CAST(substr(s.score, 1, 1) AS INTEGER) = 3 THEN 1 ELSE 0 END) as threes,
            SUM(CASE WHEN CAST(substr(s.score, 1, 1) AS INTEGER) = 4 THEN 1 ELSE 0 END) as fours,
            SUM(CASE WHEN CAST(substr(s.score, 1, 1) AS INTEGER) = 5 THEN 1 ELSE 0 END) as fives,
            SUM(CASE WHEN CAST(substr(s.score, 1, 1) AS INTEGER) = 6 THEN 1 ELSE 0 END) as sixes
        FROM 
            scores s
        JOIN 
            players p ON s.player_id = p.id
        WHERE 
            s.league_id = ?
        GROUP BY 
            p.player_name
        HAVING 
            games_played >= 10  -- At least 10 games all-time
        ORDER BY 
            average ASC,
            games_played DESC
        """
        
        cursor.execute(query, (league_id,))
        
        all_time_data = []
        for row in cursor.fetchall():
            all_time_data.append({
                'name': row['player_name'],
                'games_played': row['games_played'],
                'total_score': row['total_score'],
                'average': row['average'],
                'failed_attempts': row['failed_attempts'],
                'ones': row['ones'],
                'twos': row['twos'],
                'threes': row['threes'],
                'fours': row['fours'],
                'fives': row['fives'],
                'sixes': row['sixes']
            })
        
        return all_time_data
    except Exception as e:
        logging.error(f"Error fetching all-time stats: {str(e)}")
        return []
    finally:
        conn.close()

def update_latest_scores_tab(soup, latest_scores, wordle_number, wordle_date):
    """Update the Latest Scores tab with fresh data"""
    try:
        # Find the Latest Scores tab content
        latest_tab = soup.select_one('.tab-content#latest')
        if not latest_tab:
            logging.error("Could not find Latest Scores tab")
            return False
        
        # Update heading with wordle number and date
        heading = latest_tab.find('h2')
        if heading:
            heading.string = f"Wordle #{wordle_number} - {wordle_date}"
        
        # Remove existing score cards
        for card in latest_tab.select('.score-card'):
            card.decompose()
        
        # Add new score cards
        for player in latest_scores:
            # Get score number for styling
            score_num = "0"
            if player['score'] and player['score'][0].isdigit():
                score_num = player['score'][0]
            elif player['score'] and player['score'][0] == 'X':
                score_num = "X"
            
            # Format emoji pattern with line breaks
            emoji_pattern = ""
            if player['emoji_pattern']:
                rows = player['emoji_pattern'].strip().split('\n')
                emoji_pattern = "".join([f'<div class="emoji-row">{row}</div>' for row in rows])
            
            # Create new score card
            card_html = f'''
            <div class="score-card">
              <div class="player-info">
                <div class="player-name">{player['name']}</div>
                <div class="player-score"><span class="score-{score_num}">{player['score']}</span></div>
              </div>
              <div class="emoji-container">
                <div class="emoji-pattern">{emoji_pattern}</div>
              </div>
            </div>
            '''
            
            # Add to the DOM
            card_soup = BeautifulSoup(card_html, 'html.parser')
            latest_tab.append(card_soup)
        
        return True
    except Exception as e:
        logging.error(f"Error updating Latest Scores tab: {str(e)}")
        return False

def update_weekly_totals_tab(soup, weekly_data):
    """Update the Weekly Totals tab with fresh data"""
    try:
        # Find the Weekly Totals tab content
        weekly_tab = soup.select_one('.tab-content#weekly')
        if not weekly_tab:
            logging.error("Could not find Weekly Totals tab")
            return False
        
        # Find the table in the weekly tab
        weekly_table = weekly_tab.find('table')
        if not weekly_table:
            logging.error("Could not find Weekly Totals table")
            return False
        
        # Clear existing rows (keep header)
        header_row = weekly_table.find('tr')
        weekly_table.clear()
        weekly_table.append(header_row)
        
        # Add new data rows
        for player in weekly_data:
            # Create row
            row = soup.new_tag('tr')
            
            # Player name cell
            name_cell = soup.new_tag('td')
            name_cell.string = player['name']
            row.append(name_cell)
            
            # Games played cell
            games_cell = soup.new_tag('td')
            games_cell.string = str(player['games_played'])
            row.append(games_cell)
            
            # Total score cell
            total_cell = soup.new_tag('td')
            total_cell.string = str(player['total_score'])
            row.append(total_cell)
            
            # Average cell
            avg_cell = soup.new_tag('td')
            avg_cell.string = str(player['average'])
            row.append(avg_cell)
            
            # Failed attempts cell
            fail_cell = soup.new_tag('td', **{'class': 'failed-attempts'})
            if player['failed_attempts'] > 0:
                fail_cell.string = str(player['failed_attempts'])
            row.append(fail_cell)
            
            # Add the row to the table
            weekly_table.append(row)
        
        return True
    except Exception as e:
        logging.error(f"Error updating Weekly Totals tab: {str(e)}")
        return False

def update_season_tab(soup, season_winners):
    """Update the Season tab with fresh data"""
    try:
        # Find the Stats tab content which contains both Season and All-Time
        stats_tab = soup.select_one('.tab-content#stats')
        if not stats_tab:
            logging.error("Could not find Stats tab")
            return False
        
        # Find the Season table - it's the first table in the Stats tab
        season_table = stats_tab.find('table')
        if not season_table:
            logging.error("Could not find Season table")
            return False
        
        # Clear existing rows (keep header)
        header_row = season_table.find('tr')
        season_table.clear()
        season_table.append(header_row)
        
        # Add new data rows
        for winner in season_winners:
            # Create row
            row = soup.new_tag('tr', **{'class': 'highlight-row'})
            
            # Week cell
            week_cell = soup.new_tag('td')
            week_cell.string = f"Week {winner['week']}"
            row.append(week_cell)
            
            # Player name cell
            name_cell = soup.new_tag('td')
            name_cell.string = winner['name']
            row.append(name_cell)
            
            # Average cell
            avg_cell = soup.new_tag('td')
            avg_cell.string = str(winner['average'])
            row.append(avg_cell)
            
            # Games played cell
            games_cell = soup.new_tag('td')
            games_cell.string = str(winner['games'])
            row.append(games_cell)
            
            # Add the row to the table
            season_table.append(row)
        
        return True
    except Exception as e:
        logging.error(f"Error updating Season tab: {str(e)}")
        return False

def update_all_time_tab(soup, all_time_data):
    """Update the All-Time Stats tab with fresh data"""
    try:
        # Find the Stats tab content which contains both Season and All-Time
        stats_tab = soup.select_one('.tab-content#stats')
        if not stats_tab:
            logging.error("Could not find Stats tab")
            return False
        
        # Find the All-Time table - it's the second table in the Stats tab
        tables = stats_tab.find_all('table')
        if len(tables) < 2:
            logging.error("Could not find All-Time table")
            return False
        
        all_time_table = tables[1]
        
        # Clear existing rows (keep header)
        header_row = all_time_table.find('tr')
        all_time_table.clear()
        all_time_table.append(header_row)
        
        # Add new data rows
        for i, player in enumerate(all_time_data):
            # Create row - highlight only the first row
            row = soup.new_tag('tr')
            if i == 0:
                row['class'] = 'highlight-row'
            
            # Player name cell
            name_cell = soup.new_tag('td')
            name_cell.string = player['name']
            row.append(name_cell)
            
            # Games played cell
            games_cell = soup.new_tag('td')
            games_cell.string = str(player['games_played'])
            row.append(games_cell)
            
            # Average cell
            avg_cell = soup.new_tag('td')
            avg_cell.string = str(player['average'])
            row.append(avg_cell)
            
            # Distribution cells
            for score_type in ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes']:
                dist_cell = soup.new_tag('td')
                dist_cell.string = str(player[score_type])
                row.append(dist_cell)
            
            # Failed attempts cell
            fail_cell = soup.new_tag('td', **{'class': 'failed-attempts'})
            if player['failed_attempts'] > 0:
                fail_cell.string = str(player['failed_attempts'])
            row.append(fail_cell)
            
            # Add the row to the table
            all_time_table.append(row)
        
        return True
    except Exception as e:
        logging.error(f"Error updating All-Time tab: {str(e)}")
        return False

def update_league_html(league):
    """Update the HTML for a specific league"""
    league_dir = league['dir']
    league_id = league['id']
    league_name = league['name']
    
    # Define file path
    if league_dir:
        html_path = os.path.join(EXPORT_DIR, league_dir, "index.html")
    else:
        html_path = os.path.join(EXPORT_DIR, "index.html")
    
    logging.info(f"Updating HTML for {league_name} (ID: {league_id})")
    
    # Check if file exists
    if not os.path.exists(html_path):
        logging.error(f"HTML file does not exist: {html_path}")
        return False
    
    try:
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get latest data
        latest_wordle = get_latest_wordle_number()
        if not latest_wordle:
            logging.error("Could not determine latest Wordle number")
            return False
            
        wordle_date = get_wordle_date(latest_wordle)
        latest_scores = get_player_scores(league_id, latest_wordle)
        weekly_data = get_weekly_totals(league_id)
        season_winners = get_season_winners(league_id)
        all_time_data = get_all_time_stats(league_id)
        
        # Update each tab
        updated_latest = update_latest_scores_tab(soup, latest_scores, latest_wordle, wordle_date)
        updated_weekly = update_weekly_totals_tab(soup, weekly_data)
        updated_season = update_season_tab(soup, season_winners)
        updated_all_time = update_all_time_tab(soup, all_time_data)
        
        # Update the title
        title_tag = soup.find('title')
        if title_tag:
            title_tag.string = f"{league_name} - Wordle League"
        
        # Write the updated HTML back to the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info(f"Successfully updated {league_name}")
        return True
    except Exception as e:
        logging.error(f"Error updating {league_name}: {str(e)}")
        return False

def main():
    print("Starting direct database to HTML update...")
    logging.info("Starting direct database to HTML update")
    
    success_count = 0
    failure_count = 0
    
    # Update each league
    for league in LEAGUES:
        if update_league_html(league):
            success_count += 1
            print(f"[SUCCESS] Updated {league['name']}")
        else:
            failure_count += 1
            print(f"[FAILED] Failed to update {league['name']}")
    
    # Report summary
    print(f"\nUpdate completed with {success_count} successful updates and {failure_count} failures")
    logging.info(f"Update completed with {success_count} successful updates and {failure_count} failures")
    
    if failure_count > 0:
        print("Some leagues failed to update. Check the log file for details.")
        print("Running restore script to revert to last working version...")
        
        # Run restore script
        import subprocess
        try:
            result = subprocess.run(
                ['python', 'restore_last_night_backup.py', BACKUP_DIR],
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print("Successfully restored from backup.")
            else:
                print(f"Failed to restore from backup: {result.stderr}")
        except Exception as e:
            print(f"Error running restore script: {str(e)}")

if __name__ == "__main__":
    main()
