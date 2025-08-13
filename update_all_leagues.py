#!/usr/bin/env python3
"""
Script to update all league pages with current data while preserving formatting
"""

import os
import sqlite3
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("multi_league_update.log"),
        logging.StreamHandler()
    ]
)

# League definitions
LEAGUES = {
    "1": {
        "name": "Wordle Warriorz",
        "path": "website_export/index.html"  # Main league at root level
    },
    "2": {
        "name": "Wordle Gang",
        "path": "website_export/wordle-gang/index.html"
    },
    "3": {
        "name": "Wordle PAL",
        "path": "website_export/wordle-pal/index.html"
    },
    "4": {
        "name": "Wordle Party",
        "path": "website_export/wordle-party/index.html"
    },
    "5": {
        "name": "Wordle Vball",
        "path": "website_export/wordle-vball/index.html"
    }
}

def get_league_data(league_id):
    """Get current data for a specific league from the database"""
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
        
        return {
            'latest_wordle': latest_wordle,
            'latest_date': latest_date,
            'latest_scores': latest_scores,
            'all_players': all_players,
            'weekly_stats': weekly_stats,
            'alltime_stats': alltime_stats
        }
        
    except Exception as e:
        logging.error(f"Error getting data for league {league_id}: {e}")
        return None

def update_html_file(index_file, data):
    """Update a league's index.html with current data while preserving structure"""
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{index_file}.backup_{timestamp}"
        shutil.copy2(index_file, backup_file)
        logging.info(f"Backed up {index_file} to {backup_file}")
        
        # Read the current index.html
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse HTML
        soup = BeautifulSoup(content, 'html.parser')
        
        # Update Wordle number and date
        wordle_heading = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if wordle_heading:
            wordle_heading.string = f"Wordle #{data['latest_wordle']} - {data['latest_date']}"
        
        # Update player scores in Latest Scores tab
        latest_tab = soup.find('div', {'id': 'latest'})
        if latest_tab:
            # Clear existing score cards
            for card in latest_tab.find_all('div', {'class': 'score-card'}):
                card.decompose()
            
            # Create player_to_score mapping for all players
            player_to_score = {name: None for name in data['all_players']}
            for name, score, emoji in data['latest_scores']:
                player_to_score[name] = (score, emoji)
            
            # Add new score cards for all players
            for player in data['all_players']:
                score_data = player_to_score.get(player)
                
                # Create score card container
                card = soup.new_tag('div', attrs={'class': 'score-card'})
                
                # Player info container
                player_info = soup.new_tag('div', attrs={'class': 'player-info'})
                
                # Player name
                name_div = soup.new_tag('div', attrs={'class': 'player-name'})
                name_div.string = player
                player_info.append(name_div)
                
                # Player score
                score_div = soup.new_tag('div', attrs={'class': 'player-score'})
                
                if score_data:
                    score, emoji = score_data
                    # Score value with appropriate class
                    if score == 'X/6':
                        score_span = soup.new_tag('span', attrs={'class': 'score-x'})
                    else:
                        first_digit = score[0]
                        score_span = soup.new_tag('span', attrs={'class': f'score-{first_digit}'})
                    score_span.string = score
                    score_div.append(score_span)
                    
                    # Add emoji pattern if available
                    if emoji and emoji != "No emoji pattern available":
                        emoji_container = soup.new_tag('div', attrs={'class': 'emoji-container'})
                        emoji_pattern = soup.new_tag('div', attrs={'class': 'emoji-pattern'})
                        
                        # Parse emoji pattern into rows
                        emoji_rows = emoji.strip().split('\n')
                        for row in emoji_rows:
                            emoji_row = soup.new_tag('div', attrs={'class': 'emoji-row'})
                            emoji_row.string = row
                            emoji_pattern.append(emoji_row)
                        
                        emoji_container.append(emoji_pattern)
                        card.append(emoji_container)
                else:
                    # No score available
                    no_score = soup.new_tag('span', attrs={'class': 'no-score'})
                    no_score.string = "No Score"
                    score_div.append(no_score)
                
                player_info.append(score_div)
                card.append(player_info)
                latest_tab.append(card)
            
            logging.info(f"Updated Latest Scores tab with {len(data['all_players'])} player cards")
        
        # Update Weekly Stats table
        weekly_tab = soup.find('div', {'id': 'weekly'})
        if weekly_tab:
            tables = weekly_tab.find_all('table')
            if tables and len(tables) > 0:
                table = tables[0]
                tbody = table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Add new rows
                    for row in data['weekly_stats']:
                        tr = soup.new_tag('tr')
                        
                        # Unpack row data safely - handling both tuple format and single items
                        if isinstance(row, tuple) and len(row) >= 4:
                            name, weekly_score, used_scores, failed = row
                        else:
                            name = row
                            weekly_score = used_scores = failed = None
                        
                        # Highlight if 5+ scores used
                        if used_scores and used_scores >= 5:
                            tr['class'] = 'highlight'
                        
                        # Player name
                        td_name = soup.new_tag('td')
                        td_name.string = name
                        tr.append(td_name)
                        
                        # Weekly score
                        td_score = soup.new_tag('td', attrs={'class': 'weekly-score'})
                        td_score.string = str(weekly_score) if weekly_score else '-'
                        tr.append(td_score)
                        
                        # Used scores
                        td_used = soup.new_tag('td', attrs={'class': 'used-scores'})
                        td_used.string = str(used_scores) if used_scores else '0'
                        tr.append(td_used)
                        
                        # Failed attempts
                        td_failed = soup.new_tag('td', attrs={'class': 'failed-attempts'})
                        td_failed.string = str(failed) if failed else ''
                        tr.append(td_failed)
                        
                        tbody.append(tr)
                    
                    logging.info(f"Updated weekly stats table with {len(data['weekly_stats'])} rows")
        
        # Update all-time stats table
        stats_tab = soup.find('div', {'id': 'stats'})
        if stats_tab:
            # Find all tables in the stats tab
            tables = stats_tab.find_all('table')
            if tables and len(tables) > 0:
                # The all-time stats table is typically the last table
                all_time_table = None
                for table in tables:
                    # Check if this is the all-time stats table by looking for header text
                    header = table.find_previous('h3')
                    if header and 'All-Time Stats' in header.text:
                        all_time_table = table
                        break
                
                # If no specifically labeled all-time table found, use the last table
                if not all_time_table and tables:
                    all_time_table = tables[-1]
                
                if all_time_table:
                    tbody = all_time_table.find('tbody')
                    if tbody:
                        # Clear existing rows
                        tbody.clear()
                        
                        # Add new rows
                        for row in data['alltime_stats']:
                            tr = soup.new_tag('tr')
                            
                            # Unpack row data safely
                            if isinstance(row, tuple) and len(row) >= 4:
                                name, games, avg, failed = row
                            else:
                                name = row
                                games = avg = failed = None
                            
                            # Highlight if at least 5 games played
                            total_games = (games or 0) + (failed or 0)
                            if total_games >= 5:
                                tr['class'] = 'highlight'
                            
                            # Player name
                            td_name = soup.new_tag('td')
                            td_name.string = name
                            tr.append(td_name)
                            
                            # Games played
                            td_games = soup.new_tag('td')
                            td_games.string = str(games) if games else '-'
                            tr.append(td_games)
                            
                            # Average score
                            td_avg = soup.new_tag('td')
                            td_avg.string = str(avg) if avg is not None else '-'
                            tr.append(td_avg)
                            
                            # Add Failed Attempts if that column exists
                            headers = all_time_table.find('thead').find_all('th')
                            if len(headers) > 3:  # If there's a 4th column for failed attempts
                                td_failed = soup.new_tag('td')
                                td_failed.string = str(failed) if failed else ''
                                tr.append(td_failed)
                            
                            tbody.append(tr)
                        
                        logging.info(f"Updated all-time stats table with {len(data['alltime_stats'])} rows")
        
        # Write updated content back to file
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Successfully updated {index_file} with current data while preserving structure")
        return True
        
    except Exception as e:
        logging.error(f"Error updating {index_file}: {e}")
        return False

def main():
    logging.info("Starting multi-league update process...")
    
    success_count = 0
    
    for league_id, league_info in LEAGUES.items():
        league_name = league_info["name"]
        league_path = league_info["path"]
        
        if not os.path.exists(league_path):
            logging.warning(f"League file not found: {league_path}, skipping")
            continue
            
        logging.info(f"Processing {league_name}...")
        
        # Get data for this league
        data = get_league_data(league_id)
        if not data:
            logging.error(f"Failed to get data for {league_name}, skipping")
            continue
            
        # Update the league's HTML
        if update_html_file(league_path, data):
            logging.info(f"Successfully updated {league_name}")
            success_count += 1
        else:
            logging.error(f"Failed to update {league_name}")
    
    logging.info(f"Update complete. Successfully updated {success_count} of {len(LEAGUES)} leagues.")
    print(f"Successfully updated {success_count} of {len(LEAGUES)} league pages with current data.")
    return success_count == len(LEAGUES)

if __name__ == "__main__":
    main()
