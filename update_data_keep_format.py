#!/usr/bin/env python3
"""
Script to directly update the website with current data while preserving formatting
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
        logging.FileHandler("direct_update.log"),
        logging.StreamHandler()
    ]
)

def get_current_data():
    """Get current data from the database"""
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
        
        # Get player scores for the latest Wordle (league 1)
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ?
            ORDER BY 
                CASE 
                    WHEN s.score = 'X/6' THEN 7
                    WHEN s.score = '-' THEN 8
                    ELSE CAST(SUBSTRING(s.score, 1, 1) AS INTEGER)
                END
        """, (latest_wordle,))
        latest_scores = cursor.fetchall()
        
        # Get all players for league 1
        cursor.execute("""
            SELECT DISTINCT p.name
            FROM players p
        """)
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
            GROUP BY p.name
            ORDER BY 
                CASE WHEN weekly_score IS NULL THEN 999 ELSE weekly_score END,
                CASE WHEN used_scores IS NULL THEN 0 ELSE used_scores END DESC
        """, (latest_wordle, latest_wordle))
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
            GROUP BY p.name
            ORDER BY 
                CASE WHEN average IS NULL THEN 999 ELSE average END,
                CASE WHEN games_played IS NULL THEN 0 ELSE games_played END DESC
        """)
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
        logging.error(f"Error getting data: {e}")
        return None

def update_index_html(data):
    """Update index.html with current data while preserving structure"""
    try:
        export_dir = "website_export"
        index_file = os.path.join(export_dir, "index.html")
        backup_file = os.path.join(export_dir, f"index.html.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Make a backup of the current file
        shutil.copy2(index_file, backup_file)
        logging.info(f"Backed up index.html to {backup_file}")
        
        # Read current content
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Parse content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Update latest Wordle header with current date
        latest_header = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if latest_header:
            latest_header.string = f"Wordle #{data['latest_wordle']} - {data['latest_date']}"
            logging.info(f"Updated header to: {latest_header.string}")
        
        # Get the latest scores tab content
        latest_tab = soup.find('div', {'id': 'latest'})
        if latest_tab:
            # Clear existing score cards
            for card in latest_tab.find_all('div', class_='score-card'):
                card.decompose()
            
            # Build a map of player scores
            player_scores = {name: {'score': '-', 'pattern': None} for name in data['all_players']}
            for name, score, pattern in data['latest_scores']:
                player_scores[name] = {'score': score, 'pattern': pattern}
            
            # Add score cards in order by score
            for player_name, score_data in sorted(player_scores.items(), 
                                              key=lambda x: (
                                                  0 if x[1]['score'] != '-' and x[1]['score'] != 'X/6' else 1, 
                                                  int(x[1]['score']) if x[1]['score'] != '-' and x[1]['score'] != 'X/6' else 7)
                                             ):
                score = score_data['score']
                pattern = score_data['pattern']
                
                # Create score card
                card = soup.new_tag('div', attrs={'class': 'score-card'})
                
                # Player info section
                player_info = soup.new_tag('div', attrs={'class': 'player-info'})
                
                # Player name
                name_div = soup.new_tag('div', attrs={'class': 'player-name'})
                name_div.string = player_name
                player_info.append(name_div)
                
                # Player score
                score_div = soup.new_tag('div', attrs={'class': 'player-score'})
                if score == '-':
                    score_span = soup.new_tag('span', attrs={'class': 'score-none'})
                    score_span.string = 'No Score'
                elif score == 'X/6':
                    score_span = soup.new_tag('span', attrs={'class': 'score-x'})
                    score_span.string = 'X/6'
                else:
                    score_span = soup.new_tag('span', attrs={'class': f'score-{score}'})
                    score_span.string = f'{score}/6'
                score_div.append(score_span)
                player_info.append(score_div)
                card.append(player_info)
                
                # Emoji pattern if available
                if pattern:
                    emoji_container = soup.new_tag('div', attrs={'class': 'emoji-container'})
                    emoji_pattern = soup.new_tag('div', attrs={'class': 'emoji-pattern'})
                    
                    # Split pattern by rows
                    rows = pattern.strip().split('\n')
                    for row in rows:
                        row_div = soup.new_tag('div', attrs={'class': 'emoji-row'})
                        row_div.string = row
                        emoji_pattern.append(row_div)
                    
                    emoji_container.append(emoji_pattern)
                    card.append(emoji_container)
                
                latest_tab.append(card)
            
            logging.info(f"Updated latest scores tab with {len(player_scores)} player cards")
        
        # Update weekly stats table
        weekly_tab = soup.find('div', {'id': 'weekly'})
        if weekly_tab:
            table = weekly_tab.find('table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Add new rows
                    for name, weekly_score, used_scores, failed in data['weekly_stats']:
                        tr = soup.new_tag('tr')
                        
                        # Highlight if at least 5 used scores
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
            # Find the first table, which is the all-time stats
            tables = stats_tab.find_all('table')
            if tables and len(tables) > 0:
                table = tables[0]
                tbody = table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Add new rows
                    for name, games, avg, failed in data['alltime_stats']:
                        tr = soup.new_tag('tr')
                        
                        # Highlight if at least 5 games played
                        if games and games >= 5:
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
                        
                        tbody.append(tr)
                    
                    logging.info(f"Updated all-time stats table with {len(data['alltime_stats'])} rows")
        
        # Write updated content back to file
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info("Successfully updated index.html with current data while preserving structure")
        return True
        
    except Exception as e:
        logging.error(f"Error updating index.html: {e}")
        return False

def main():
    logging.info("Starting direct update process...")
    
    # Get current data
    logging.info("Fetching current data from database...")
    data = get_current_data()
    if not data:
        logging.error("Failed to get current data, aborting")
        return False
    
    # Update index.html
    logging.info("Updating index.html with current data...")
    if not update_index_html(data):
        logging.error("Failed to update index.html")
        return False
    
    logging.info("Update complete")
    print(f"Successfully updated website with data through Wordle #{data['latest_wordle']} ({data['latest_date']})")
    return True

if __name__ == "__main__":
    main()
