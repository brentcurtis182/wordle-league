#!/usr/bin/env python3
"""
Script to restore the Wordle League site structure from backup while preserving current data
"""

import os
import shutil
import sqlite3
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_site_preserve_structure.log"),
        logging.StreamHandler()
    ]
)

def get_current_wordle_data():
    """Get current Wordle data from the database"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get latest Wordle number
        cursor.execute("""
            SELECT wordle_number, date(date) as wordle_date 
            FROM scores 
            WHERE league_id = 1
            ORDER BY wordle_number DESC
            LIMIT 1
        """)
        result = cursor.fetchone()
        if not result:
            logging.error("No Wordle data found in database")
            return None
        
        latest_wordle = result[0]
        latest_date = result[1]
        
        # Get player scores for latest Wordle
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.wordle_number = ? AND s.league_id = 1
            ORDER BY s.score
        """, (latest_wordle,))
        latest_scores = cursor.fetchall()
        
        # Get all players for the league
        cursor.execute("""
            SELECT DISTINCT p.name
            FROM players p
            WHERE p.league_id = 1
        """)
        all_players = [row[0] for row in cursor.fetchall()]
        
        # Get weekly stats
        cursor.execute("""
            SELECT p.name, 
                   SUM(CASE WHEN s.score BETWEEN 1 AND 6 THEN s.score ELSE 0 END) AS weekly_score,
                   COUNT(CASE WHEN s.score BETWEEN 1 AND 6 THEN 1 END) AS used_scores,
                   COUNT(CASE WHEN s.score = 'X/6' THEN 1 END) AS failed_attempts
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id 
                AND s.league_id = 1
                AND s.wordle_number >= (? - 6) AND s.wordle_number <= ?
            WHERE p.league_id = 1
            GROUP BY p.name
            ORDER BY weekly_score
        """, (latest_wordle, latest_wordle))
        weekly_stats = cursor.fetchall()
        
        # Get all-time stats
        cursor.execute("""
            SELECT p.name, 
                   COUNT(CASE WHEN s.score BETWEEN 1 AND 6 THEN 1 END) AS games_played,
                   ROUND(AVG(CASE WHEN s.score BETWEEN 1 AND 6 THEN s.score 
                           WHEN s.score = 'X/6' THEN 7
                           ELSE NULL END), 2) AS average
            FROM players p
            LEFT JOIN scores s ON p.id = s.player_id AND s.league_id = 1
            WHERE p.league_id = 1
            GROUP BY p.name
            ORDER BY average
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
        logging.error(f"Error getting Wordle data: {e}")
        return None

def update_index_with_current_data(data):
    """Update index.html with current data while preserving structure"""
    try:
        export_dir = "website_export"
        backup_file = os.path.join(export_dir, "index.html.bak")
        current_file = os.path.join(export_dir, "index.html")
        
        # First make a copy of the current file (even if broken)
        shutil.copyfile(current_file, f"{current_file}.broken")
        
        # Check if backup file exists
        if not os.path.exists(backup_file):
            logging.error(f"Backup file not found: {backup_file}")
            return False
            
        # Read backup file content
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_content = f.read()
            
        # Parse backup content
        soup = BeautifulSoup(backup_content, 'html.parser')
        
        # Update the latest Wordle header
        latest_header = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if latest_header:
            latest_header.string = f"Wordle #{data['latest_wordle']} - {data['latest_date']}"
        
        # Clear existing score cards
        latest_tab = soup.find('div', {'id': 'latest'})
        if latest_tab:
            # Remove existing score cards
            for score_card in latest_tab.find_all('div', class_='score-card'):
                score_card.extract()
                
            # Add current score cards
            player_scores = {name: {'score': '-', 'pattern': None} for name in data['all_players']}
            for name, score, pattern in data['latest_scores']:
                player_scores[name] = {'score': score, 'pattern': pattern}
            
            # Add score cards back in sorted order
            sorted_players = sorted(player_scores.items(), 
                                  key=lambda x: (0 if x[1]['score'] != '-' else 1, 
                                               int(x[1]['score']) if x[1]['score'] != '-' and x[1]['score'] != 'X/6' else 7))
            
            for player_name, score_data in sorted_players:
                score_value = score_data['score']
                emoji_pattern = score_data['pattern']
                
                score_card = soup.new_tag('div', attrs={'class': 'score-card'})
                
                # Player info div
                player_info = soup.new_tag('div', attrs={'class': 'player-info'})
                player_name_div = soup.new_tag('div', attrs={'class': 'player-name'})
                player_name_div.string = player_name
                player_info.append(player_name_div)
                
                # Player score div
                player_score_div = soup.new_tag('div', attrs={'class': 'player-score'})
                if score_value != '-':
                    score_span = soup.new_tag('span', attrs={'class': f"score-{score_value if score_value != 'X/6' else 'x'}"})
                    score_span.string = f"{score_value}/6" if score_value != 'X/6' else "X/6"
                else:
                    score_span = soup.new_tag('span', attrs={'class': 'score-none'})
                    score_span.string = "No Score"
                player_score_div.append(score_span)
                player_info.append(player_score_div)
                score_card.append(player_info)
                
                # Emoji pattern
                if emoji_pattern:
                    emoji_container = soup.new_tag('div', attrs={'class': 'emoji-container'})
                    emoji_pattern_div = soup.new_tag('div', attrs={'class': 'emoji-pattern'})
                    
                    # Split by rows
                    rows = emoji_pattern.strip().split('\n')
                    for row in rows:
                        row_div = soup.new_tag('div', attrs={'class': 'emoji-row'})
                        row_div.string = row
                        emoji_pattern_div.append(row_div)
                        
                    emoji_container.append(emoji_pattern_div)
                    score_card.append(emoji_container)
                
                latest_tab.append(score_card)
        
        # Update weekly stats
        weekly_tab = soup.find('div', {'id': 'weekly'})
        if weekly_tab:
            table = weekly_tab.find('table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Add current rows
                    for name, weekly_score, used_scores, failed in data['weekly_stats']:
                        tr = soup.new_tag('tr')
                        
                        # Highlight if used_scores is at least 5
                        if used_scores and int(used_scores) >= 5:
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
                        
                        # Thrown out
                        td_thrown = soup.new_tag('td', attrs={'class': 'thrown-out'})
                        td_thrown.string = '-'
                        tr.append(td_thrown)
                        
                        tbody.append(tr)
        
        # Update all-time stats
        alltime_tab = soup.find('div', {'id': 'stats'})
        if alltime_tab and not alltime_tab.find('div', {'id': 'stats'}):  # Check it's not the nested one
            table = alltime_tab.find('table')
            if table:
                tbody = table.find('tbody')
                if tbody:
                    # Clear existing rows
                    tbody.clear()
                    
                    # Add current rows
                    for name, games, avg in data['alltime_stats']:
                        tr = soup.new_tag('tr')
                        
                        # Highlight if games played is at least 5
                        if games and int(games) >= 5:
                            tr['class'] = 'highlight'
                        
                        # Player name
                        td_name = soup.new_tag('td')
                        td_name.string = name
                        tr.append(td_name)
                        
                        # Games played
                        td_games = soup.new_tag('td')
                        td_games.string = str(games) if games else '-'
                        tr.append(td_games)
                        
                        # Average
                        td_avg = soup.new_tag('td')
                        td_avg.string = str(avg) if avg else '-'
                        tr.append(td_avg)
                        
                        tbody.append(tr)
        
        # Write updated content back to file
        with open(current_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info("Successfully updated index.html with current data while preserving structure")
        return True
        
    except Exception as e:
        logging.error(f"Error updating index.html: {e}")
        return False

def restore_landing_page():
    """Ensure landing.html is available as the entry point"""
    try:
        export_dir = "website_export"
        landing_file = os.path.join(export_dir, "landing.html")
        
        # Check if landing.html exists
        if not os.path.exists(landing_file):
            logging.warning("landing.html not found, cannot restore landing page")
            return False
        
        logging.info("Landing page is available at website_export/landing.html")
        return True
    except Exception as e:
        logging.error(f"Error checking landing page: {e}")
        return False

def main():
    logging.info("Starting targeted site fix...")
    
    # Get current data from database
    logging.info("Getting current data from database...")
    data = get_current_wordle_data()
    if not data:
        logging.error("Failed to get current data, cannot proceed")
        return False
    
    # Update index.html with current data while preserving structure
    logging.info("Updating index.html with current data...")
    if not update_index_with_current_data(data):
        logging.error("Failed to update index.html")
        return False
    
    # Check landing page
    logging.info("Checking landing page...")
    restore_landing_page()
    
    logging.info("Site fix completed")
    print("Site has been fixed with current data while preserving the nice formatting!")
    print("You can view the site in the website_export directory.")
    return True

if __name__ == "__main__":
    main()
