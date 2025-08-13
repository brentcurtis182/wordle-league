#!/usr/bin/env python3
"""
Simplified script to update a specific league's website with current data
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
        logging.FileHandler("league_update_simple.log"),
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

def update_league_html(league_id, league_path):
    """Update HTML with league-specific data"""
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
            return False
        
        latest_wordle = result[0]
        latest_date = result[1]
        
        logging.info(f"Updating league {league_id} with data for Wordle #{latest_wordle} ({latest_date})")
        
        # Create backup of the HTML file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{league_path}.backup_{timestamp}"
        shutil.copy2(league_path, backup_file)
        logging.info(f"Backed up {league_path} to {backup_file}")
        
        # Read the current HTML
        with open(league_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Update Wordle number and date
        wordle_heading = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if wordle_heading:
            wordle_heading.string = f"Wordle #{latest_wordle} - {latest_date}"
            logging.info(f"Updated Wordle number to #{latest_wordle} - {latest_date}")
        
        # Get all players for this league
        cursor.execute("""
            SELECT DISTINCT name
            FROM players
            WHERE league_id = ?
        """, (league_id,))
        all_players = [row[0] for row in cursor.fetchall()]
        
        if not all_players:
            logging.warning(f"No players found for league {league_id}!")
            # Fall back to scores table to get players
            cursor.execute("""
                SELECT DISTINCT p.name
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE p.league_id = ?
            """, (league_id,))
            all_players = [row[0] for row in cursor.fetchall()]
            
        logging.info(f"Found {len(all_players)} players for league {league_id}: {all_players}")
        
        # Get latest scores for each player
        latest_scores = {}
        for player in all_players:
            cursor.execute("""
                SELECT s.score, s.emoji_pattern 
                FROM scores s
                JOIN players p ON s.player_id = p.id
                WHERE s.wordle_number = ? AND p.league_id = ? AND p.name = ?
            """, (latest_wordle, league_id, player))
            result = cursor.fetchone()
            if result:
                latest_scores[player] = result
        
        # Update Latest Scores section
        scores_div = soup.find('div', id='latest')
        if scores_div:
            # Find existing score cards
            score_cards = scores_div.find_all('div', class_='score-card')
            
            # Remove all existing score cards
            for card in score_cards:
                card.decompose()
            
            # Add new score cards
            for player in all_players:
                score_card = soup.new_tag('div', attrs={'class': 'score-card'})
                
                # Player info section
                player_info = soup.new_tag('div', attrs={'class': 'player-info'})
                
                # Player name
                player_name_div = soup.new_tag('div', attrs={'class': 'player-name'})
                player_name_div.string = player
                player_info.append(player_name_div)
                
                # Player score
                player_score_div = soup.new_tag('div', attrs={'class': 'player-score'})
                
                if player in latest_scores:
                    score, pattern = latest_scores[player]
                    
                    # Determine score class
                    if score == 'X/6':
                        score_class = 'score-fail'
                    else:
                        try:
                            score_num = int(score[0])
                            if score_num <= 3:
                                score_class = f'score-{score_num}'
                            else:
                                score_class = 'score-high'
                        except:
                            score_class = 'score-high'
                    
                    # Create score span
                    score_span = soup.new_tag('span', attrs={'class': score_class})
                    # Make sure score is a string
                    score_span.string = str(score)
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
            
            logging.info(f"Updated latest scores section with {len(all_players)} players")
        
        # Update Weekly Stats table
        weekly_div = soup.find('div', id='weekly')
        if weekly_div:
            weekly_table = weekly_div.find('table')
            if weekly_table:
                tbody = weekly_table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # For each player, get weekly stats and add a row
                    for player in all_players:
                        cursor.execute("""
                            SELECT 
                                SUM(CASE WHEN s.score BETWEEN '1' AND '6' THEN CAST(SUBSTRING(s.score, 1, 1) AS INTEGER) ELSE 0 END) AS weekly_score,
                                COUNT(CASE WHEN s.score BETWEEN '1' AND '6' THEN 1 END) AS used_scores,
                                COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
                            FROM players p
                            LEFT JOIN scores s ON p.id = s.player_id 
                                AND s.wordle_number >= (? - 6) AND s.wordle_number <= ?
                            WHERE p.league_id = ? AND p.name = ?
                            GROUP BY p.name
                        """, (latest_wordle, latest_wordle, league_id, player))
                        
                        result = cursor.fetchone()
                        weekly_score = used_scores = failed_attempts = None
                        
                        if result:
                            weekly_score, used_scores, failed_attempts = result
                        
                        tr = soup.new_tag('tr')
                        
                        # Highlight players with 5+ scores
                        if used_scores and used_scores >= 5:
                            tr['class'] = 'highlight'
                        
                        # Player name
                        td_name = soup.new_tag('td')
                        td_name.string = player
                        tr.append(td_name)
                        
                        # Weekly score
                        td_weekly = soup.new_tag('td', attrs={'class': 'weekly-score'})
                        td_weekly.string = str(weekly_score) if weekly_score is not None and weekly_score > 0 else '-'
                        tr.append(td_weekly)
                        
                        # Used scores
                        td_used = soup.new_tag('td', attrs={'class': 'used-scores'})
                        td_used.string = str(used_scores) if used_scores is not None and used_scores > 0 else '0'
                        tr.append(td_used)
                        
                        # Failed attempts
                        td_failed = soup.new_tag('td', attrs={'class': 'failed-attempts'})
                        td_failed.string = str(failed_attempts) if failed_attempts is not None and failed_attempts > 0 else ''
                        tr.append(td_failed)
                        
                        # Thrown out (unused scores, calculated as max 7 - used)
                        td_thrown = soup.new_tag('td', attrs={'class': 'thrown-out'})
                        td_thrown.string = '-'  # For now, we don't calculate thrown out scores
                        tr.append(td_thrown)
                        
                        tbody.append(tr)
                    
                    logging.info(f"Updated weekly stats section with {len(all_players)} players")
        
        # Update All-time Stats table
        alltime_div = soup.find('div', id='all-time')
        if alltime_div:
            alltime_table = alltime_div.find('table')
            if alltime_table:
                tbody = alltime_table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # For each player, get all-time stats and add a row
                    for player in all_players:
                        cursor.execute("""
                            SELECT 
                                COUNT(CASE WHEN s.score BETWEEN '1' AND '6' THEN 1 END) AS games_played,
                                ROUND(AVG(CASE WHEN s.score BETWEEN '1' AND '6' THEN CAST(SUBSTRING(s.score, 1, 1) AS INTEGER) 
                                       WHEN s.score = 'X/6' THEN 7
                                       ELSE NULL END), 2) AS average,
                                COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
                            FROM players p
                            LEFT JOIN scores s ON p.id = s.player_id
                            WHERE p.league_id = ? AND p.name = ?
                            GROUP BY p.name
                        """, (league_id, player))
                        
                        result = cursor.fetchone()
                        games_played = average = failed_attempts = None
                        
                        if result:
                            games_played, average, failed_attempts = result
                        
                        tr = soup.new_tag('tr')
                        
                        # Highlight if at least 5 games played
                        total_games = (games_played or 0) + (failed_attempts or 0)
                        if total_games >= 5:
                            tr['class'] = 'highlight'
                        
                        # Player name
                        td_name = soup.new_tag('td')
                        td_name.string = player
                        tr.append(td_name)
                        
                        # Games played
                        td_games = soup.new_tag('td')
                        td_games.string = str(games_played) if games_played is not None and games_played > 0 else '-'
                        tr.append(td_games)
                        
                        # Average score
                        td_avg = soup.new_tag('td')
                        td_avg.string = str(average) if average is not None else '-'
                        tr.append(td_avg)
                        
                        # Failed attempts
                        td_failed = soup.new_tag('td')
                        td_failed.string = str(failed_attempts) if failed_attempts is not None and failed_attempts > 0 else '-'
                        tr.append(td_failed)
                        
                        tbody.append(tr)
                    
                    logging.info(f"Updated all-time stats section with {len(all_players)} players")
        
        # Write updated content back to file
        with open(league_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Successfully updated {league_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error updating {league_path}: {e}")
        import traceback
        logging.error(traceback.format_exc())
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    parser = argparse.ArgumentParser(description='Update a specific league\'s page with current data')
    parser.add_argument('league', choices=LEAGUES.keys(), help='League to update (warriorz, gang, pal, party, vball)')
    
    args = parser.parse_args()
    
    league_info = LEAGUES[args.league]
    league_id = league_info['id']
    league_path = league_info['path']
    league_name = league_info['name']
    
    print(f"Starting update for {league_name}...")
    
    # Update HTML with data
    if update_league_html(league_id, league_path):
        print(f"Successfully updated {league_name} page with current data")
        return True
    else:
        print(f"Failed to update {league_name} page")
        return False

if __name__ == "__main__":
    main()
