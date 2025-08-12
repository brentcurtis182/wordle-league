#!/usr/bin/env python3
"""
Script to update a specific league's website with current data while preserving formatting
"""

import os
import sqlite3
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re
import shutil
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("league_update.log"),
        logging.StreamHandler()
    ]
)

# League definitions
LEAGUES = {
    "warriorz": {"id": 1, "name": "Wordle Warriorz", "path": "website_export/index.html"},
    "gang": {"id": 2, "name": "Wordle Gang", "path": "website_export/wordle-gang/index.html"},
    "pal": {"id": 3, "name": "Wordle PAL", "path": "website_export/wordle-pal/index.html"},
    "party": {"id": 4, "name": "Wordle Party", "path": "website_export/wordle-party/index.html"},
    "vball": {"id": 5, "name": "Wordle Vball", "path": "website_export/wordle-vball/index.html"}
}

def get_league_data(league_id):
    """Get current data from the database for a specific league"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get latest Wordle number and date
        cursor.execute("""
            SELECT wordle_number, date(date) as wordle_date 
            FROM scores 
            ORDER BY wordle_number DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        if not result:
            logging.error("No Wordle data found in database")
            return None
        
        latest_wordle = result[0]
        latest_date = result[1]
        
        logging.info(f"Getting data for league ID {league_id}, Wordle #{latest_wordle} ({latest_date})")
        
        # Get player scores for the latest Wordle for this league
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ? AND p.league_id = ?
            ORDER BY 
                CASE 
                    WHEN s.score = 'X/6' THEN 7
                    WHEN s.score = '-' THEN 8
                    ELSE CAST(SUBSTRING(s.score, 1, 1) AS INTEGER)
                END
        """, (latest_wordle, league_id))
        latest_scores = cursor.fetchall()
        
        # Get all players for this league
        cursor.execute("""
            SELECT DISTINCT p.name
            FROM players p
            WHERE p.league_id = ?
        """, (league_id,))
        all_players = [row[0] for row in cursor.fetchall()]
        
        # If no players found, try getting players from scores table for this league
        if not all_players:
            cursor.execute("""
                SELECT DISTINCT p.name
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE p.league_id = ?
            """, (league_id,))
            all_players = [row[0] for row in cursor.fetchall()]
            
        # Get weekly stats (scores from the past 7 days)
        cursor.execute("""
            SELECT p.name, 
                   SUM(CASE WHEN s.score BETWEEN '1' AND '6' THEN CAST(SUBSTRING(s.score, 1, 1) AS INTEGER) ELSE 0 END) AS weekly_score,
                   COUNT(CASE WHEN s.score BETWEEN '1' AND '6' THEN 1 END) AS used_scores,
                   COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id 
                AND s.wordle_number >= (? - 6) AND s.wordle_number <= ?
            WHERE p.league_id = ?
            GROUP BY p.name
            ORDER BY 
                CASE WHEN weekly_score IS NULL THEN 999 ELSE weekly_score END,
                CASE WHEN used_scores IS NULL THEN 0 ELSE used_scores END DESC
        """, (latest_wordle, latest_wordle, league_id))
        weekly_stats = cursor.fetchall()
        
        # Get all-time stats
        cursor.execute("""
            SELECT p.name, 
                   COUNT(CASE WHEN s.score BETWEEN '1' AND '6' THEN 1 END) AS games_played,
                   ROUND(AVG(CASE WHEN s.score BETWEEN '1' AND '6' THEN CAST(SUBSTRING(s.score, 1, 1) AS INTEGER) 
                           WHEN s.score = 'X/6' THEN 7
                           ELSE NULL END), 2) AS average,
                   COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id
            WHERE p.league_id = ?
            GROUP BY p.name
            ORDER BY 
                CASE WHEN average IS NULL THEN 999 ELSE average END,
                CASE WHEN games_played IS NULL THEN 0 ELSE games_played END DESC
        """, (league_id,))
        alltime_stats = cursor.fetchall()
        
        conn.close()
        
        # Prepare data structure
        data = {
            'latest_wordle': latest_wordle,
            'latest_date': latest_date,
            'latest_scores': latest_scores,
            'all_players': all_players,
            'weekly_stats': weekly_stats,
            'alltime_stats': alltime_stats
        }
        
        return data
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        return None

def update_html_safely(html_path, data):
    """Update HTML with current data while preserving structure"""
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{html_path}.backup_{timestamp}"
        shutil.copy2(html_path, backup_file)
        logging.info(f"Backed up {html_path} to {backup_file}")
        
        # Read the current index.html
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Update Wordle number and date
        wordle_heading = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if wordle_heading:
            wordle_heading.string = f"Wordle #{data['latest_wordle']} - {data['latest_date']}"
            logging.info(f"Updated Wordle number to #{data['latest_wordle']} - {data['latest_date']}")
        
        # Update Latest Scores
        scores_div = soup.find('div', id='latest')
        if scores_div:
            # Find existing score cards
            score_cards = scores_div.find_all('div', class_='score-card')
            
            # Remove all existing score cards
            for card in score_cards:
                card.decompose()
            
            # Create a dictionary of players with scores
            scored_players = {name: (score, pattern) for name, score, pattern in data['latest_scores']}
            
            # Add score cards for all players
            for player_name in data['all_players']:
                score_card = soup.new_tag('div', attrs={'class': 'score-card'})
                
                # Player info section
                player_info = soup.new_tag('div', attrs={'class': 'player-info'})
                
                # Player name
                player_name_div = soup.new_tag('div', attrs={'class': 'player-name'})
                player_name_div.string = player_name
                player_info.append(player_name_div)
                
                # Player score
                player_score_div = soup.new_tag('div', attrs={'class': 'player-score'})
                
                if player_name in scored_players:
                    score, pattern = scored_players[player_name]
                    
                    # Determine score class
                    if score == 'X/6':
                        score_class = 'score-fail'
                    else:
                        score_num = int(score[0])
                        if score_num <= 3:
                            score_class = f'score-{score_num}'
                        else:
                            score_class = 'score-high'
                    
                    # Create score span
                    score_span = soup.new_tag('span', attrs={'class': score_class})
                    score_span.string = score
                    player_score_div.append(score_span)
                    
                    # If pattern exists, create emoji pattern
                    if pattern:
                        emoji_container = soup.new_tag('div', attrs={'class': 'emoji-container'})
                        emoji_pattern = soup.new_tag('div', attrs={'class': 'emoji-pattern'})
                        
                        # Process pattern - split by newline and create rows
                        pattern_rows = pattern.strip().split('\\n')
                        for row in pattern_rows:
                            if row.strip():  # Skip empty rows
                                emoji_row = soup.new_tag('div', attrs={'class': 'emoji-row'})
                                emoji_row.string = row.strip()
                                emoji_pattern.append(emoji_row)
                        
                        emoji_container.append(emoji_pattern)
                        score_card.append(emoji_container)
                else:
                    # No score for this player
                    no_score_span = soup.new_tag('span', attrs={'class': 'score-none'})
                    no_score_span.string = "No Score"
                    player_score_div.append(no_score_span)
                
                player_info.append(player_score_div)
                score_card.append(player_info)
                
                # Add the score card to the scores div
                scores_div.append(score_card)
            
            logging.info(f"Updated latest scores section with {len(data['all_players'])} players")
        
        # Update Weekly Stats
        weekly_div = soup.find('div', id='weekly')
        if weekly_div:
            weekly_table = weekly_div.find('table')
            if weekly_table:
                tbody = weekly_table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Create a dictionary of weekly stats with safer unpacking
                    weekly_dict = {}
                    for item in data['weekly_stats']:
                        if isinstance(item, tuple) and len(item) >= 4:
                            name, score, used, failed = item
                            weekly_dict[name] = (score, used, failed)
                        elif isinstance(item, tuple) and len(item) >= 1:
                            weekly_dict[item[0]] = (None, None, None)
                        else:
                            logging.warning(f"Unexpected weekly stat format: {item}")
                    
                    # Add rows for all players
                    for player_name in data['all_players']:
                        tr = soup.new_tag('tr')
                        
                        if player_name in weekly_dict:
                            # Safely unpack weekly_dict values
                            weekly_data = weekly_dict[player_name]
                            
                            # Check if weekly_data is a tuple and has enough values
                            if isinstance(weekly_data, tuple) and len(weekly_data) >= 3:
                                weekly_score, used_scores, failed = weekly_data
                            else:
                                weekly_score = used_scores = failed = None
                            
                            # Highlight players with 5+ scores
                            if used_scores and used_scores >= 5:
                                tr['class'] = 'highlight'
                            
                            # Player name
                            td_name = soup.new_tag('td')
                            td_name.string = player_name
                            tr.append(td_name)
                            
                            # Weekly score
                            td_weekly = soup.new_tag('td', attrs={'class': 'weekly-score'})
                            td_weekly.string = str(weekly_score) if weekly_score else '-'
                            tr.append(td_weekly)
                            
                            # Used scores
                            td_used = soup.new_tag('td', attrs={'class': 'used-scores'})
                            td_used.string = str(used_scores) if used_scores else '0'
                            tr.append(td_used)
                            
                            # Failed attempts
                            td_failed = soup.new_tag('td', attrs={'class': 'failed-attempts'})
                            td_failed.string = str(failed) if failed else ''
                            tr.append(td_failed)
                            
                            # Thrown out (unused scores, calculated as max 7 - used)
                            td_thrown = soup.new_tag('td', attrs={'class': 'thrown-out'})
                            td_thrown.string = '-'  # For now, we don't calculate thrown out scores
                            tr.append(td_thrown)
                        else:
                            # Player with no weekly stats
                            # Player name
                            td_name = soup.new_tag('td')
                            td_name.string = player_name
                            tr.append(td_name)
                            
                            # Empty stats
                            for _ in range(4):  # Weekly score, used scores, failed attempts, thrown out
                                td = soup.new_tag('td')
                                td.string = '-'
                                tr.append(td)
                        
                        tbody.append(tr)
                    
                    logging.info(f"Updated weekly stats section with {len(data['all_players'])} players")
        
        # Update All-time Stats
        alltime_div = soup.find('div', id='all-time')
        if alltime_div:
            alltime_table = alltime_div.find('table')
            if alltime_table:
                tbody = alltime_table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Create a dictionary of all-time stats with safer unpacking
                    alltime_dict = {}
                    for item in data['alltime_stats']:
                        if isinstance(item, tuple) and len(item) >= 4:
                            name, games, avg, failed = item
                            alltime_dict[name] = (games, avg, failed)
                        elif isinstance(item, tuple) and len(item) >= 1:
                            alltime_dict[item[0]] = (None, None, None)
                        else:
                            logging.warning(f"Unexpected all-time stat format: {item}")
                    
                    # Add rows for all players
                    for player_name in data['all_players']:
                        tr = soup.new_tag('tr')
                        
                        if player_name in alltime_dict:
                            # Safely unpack alltime_dict values
                            alltime_data = alltime_dict[player_name]
                            
                            # Check if alltime_data is a tuple and has enough values
                            if isinstance(alltime_data, tuple) and len(alltime_data) >= 3:
                                games, avg, failed = alltime_data
                            else:
                                games = avg = failed = None
                            
                            # Highlight if at least 5 games played
                            total_games = (games or 0) + (failed or 0)
                            if total_games >= 5:
                                tr['class'] = 'highlight'
                            
                            # Player name
                            td_name = soup.new_tag('td')
                            td_name.string = player_name
                            tr.append(td_name)
                            
                            # Games played
                            td_games = soup.new_tag('td')
                            td_games.string = str(games) if games else '-'
                            tr.append(td_games)
                            
                            # Average score
                            td_avg = soup.new_tag('td')
                            td_avg.string = str(avg) if avg is not None else '-'
                            tr.append(td_avg)
                            
                            # Failed attempts
                            td_failed = soup.new_tag('td')
                            td_failed.string = str(failed) if failed else '-'
                            tr.append(td_failed)
                        else:
                            # Player with no all-time stats
                            # Player name
                            td_name = soup.new_tag('td')
                            td_name.string = player_name
                            tr.append(td_name)
                            
                            # Empty stats
                            for _ in range(3):  # Games played, average score, failed attempts
                                td = soup.new_tag('td')
                                td.string = '-'
                                tr.append(td)
                        
                        tbody.append(tr)
                    
                    logging.info(f"Updated all-time stats section with {len(data['all_players'])} players")
        
        # Write updated content back to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Successfully updated {html_path} with current data while preserving structure")
        return True
        
    except Exception as e:
        logging.error(f"Error updating {html_path}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Update a specific league\'s page with current data')
    parser.add_argument('league', choices=LEAGUES.keys(), help='League to update (warriorz, gang, pal, party, vball)')
    
    args = parser.parse_args()
    
    league_info = LEAGUES[args.league]
    league_id = league_info['id']
    league_path = league_info['path']
    league_name = league_info['name']
    
    logging.info(f"Starting update for {league_name}...")
    
    # Get data for this league
    data = get_league_data(league_id)
    
    if not data:
        logging.error(f"Failed to get data for {league_name}")
        return False
    
    # Update HTML with data
    if update_html_safely(league_path, data):
        logging.info(f"Successfully updated {league_name} page at {league_path}")
        print(f"Successfully updated {league_name} page with current data")
        return True
    else:
        logging.error(f"Failed to update {league_name} page")
        print(f"Failed to update {league_name} page")
        return False

if __name__ == "__main__":
    main()
