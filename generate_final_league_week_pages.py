#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging
import json
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Database path and export directories
WORDLE_DATABASE = 'wordle_league.db'
EXPORT_DIR = 'website_export'
DAYS_DIR = os.path.join(EXPORT_DIR, 'days')
WEEKS_DIR = os.path.join(EXPORT_DIR, 'weeks')

def get_league_config():
    """Load league configuration from JSON file"""
    if not os.path.exists('league_config.json'):
        logging.error("league_config.json not found")
        return None
        
    try:
        with open('league_config.json', 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return None

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
        """, (league_id,))
        
        players = cursor.fetchall()
        
        # Initialize player stats
        for player_id, name, nickname in players:
            player_name = nickname if nickname else name
            player_stats[player_id] = {
                'name': player_name,
                'scores': {},
                'total_score': 0,
                'used_scores': 0,
                'games_played': 0,
                'has_scores': False
            }
        
        # Get scores for each wordle number
        wordle_placeholders = ','.join('?' for _ in wordle_numbers)
        cursor.execute(f"""
        SELECT s.player_id, s.wordle_number, s.score, p.name, p.nickname
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number IN ({wordle_placeholders})
        AND p.league_id = ?
        ORDER BY s.wordle_number, s.score
        """, wordle_numbers + [league_id])
        
        for player_id, wordle_number, score, name, nickname in cursor.fetchall():
            player_name = nickname if nickname else name
            
            # Make sure player exists in our dict (could be added to the DB after we queried players)
            if player_id not in player_stats:
                player_stats[player_id] = {
                    'name': player_name,
                    'scores': {},
                    'total_score': 0,
                    'used_scores': 0,
                    'games_played': 0,
                    'has_scores': False
                }
            
            # Convert score to appropriate format for display and calculations
            if score in (7, '7', 'X', 'x'):
                display_score = 'X/6'
                numeric_score = 7  # For calculation purposes
                counts_for_stats = False  # X doesn't count as a "used score"
            else:
                try:
                    numeric_score = int(score)
                    display_score = f"{numeric_score}/6"
                    counts_for_stats = True
                except (ValueError, TypeError):
                    # Skip invalid scores
                    continue
            
            # Add score to player's stats
            player_stats[player_id]['scores'][wordle_number] = {
                'display': display_score,
                'numeric': numeric_score,
                'counts': counts_for_stats
            }
            
            # Update stats if this is a countable score
            if counts_for_stats:
                player_stats[player_id]['total_score'] += numeric_score
                player_stats[player_id]['used_scores'] += 1
            
            # Either way, this is a game played
            player_stats[player_id]['games_played'] += 1
            player_stats[player_id]['has_scores'] = True
        
        # Convert player_stats dict to a list and sort by total score (ascending)
        result = []
        for player_id, stats in player_stats.items():
            result.append(stats)
        
        # Sort players by used scores (desc) then by total score (asc)
        result.sort(key=lambda x: (-x['used_scores'], x['total_score']))
        
        return result
        
    except Exception as e:
        logging.error(f"Error getting weekly stats: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_date_for_wordle(wordle_number):
    """Calculate the date for a specific Wordle number"""
    # Wordle #0 was released on June 19, 2021
    base_date = datetime(2021, 6, 19)
    wordle_date = base_date + timedelta(days=wordle_number)
    return wordle_date.strftime("%B %d, %Y")

def get_league_slug(league_name):
    """Convert league name to slug for filenames"""
    return league_name.lower().replace(' ', '-')

def generate_week_page(league_id, league_name):
    """Generate a week page for a specific league"""
    league_slug = get_league_slug(league_name)
    logging.info(f"Generating week page for league {league_id} ({league_name})")
    
    # Create weeks directory if it doesn't exist
    if not os.path.exists(WEEKS_DIR):
        os.makedirs(WEEKS_DIR)
    
    # Wordle numbers for the week (August 4-10, 2025)
    wordle_numbers = list(range(1507, 1514))  # 1507 to 1513 inclusive
    
    # Get player stats for this week
    player_stats = get_wordle_stats_for_week(wordle_numbers, league_id)
    
    # Create wordle day data
    wordle_days = []
    for wordle_num in wordle_numbers:
        wordle_date = get_date_for_wordle(wordle_num)
        wordle_days.append({
            'number': wordle_num,
            'formatted_number': f"{wordle_num:,}",
            'date': wordle_date,
            'filename': f"wordle-{wordle_num}-{league_slug}.html"
        })
    
    # Get the week template
    env = Environment(loader=FileSystemLoader("website_export/templates"))
    template = env.get_template("league_week.html")
    
    # Prepare data for the week page
    week_data = {
        'title': f'Week of August 4th, 2025 - {league_name}',
        'week_name': 'August 4th (14)',
        'wordle_days': wordle_days,
        'player_stats': player_stats,
        'league_name': league_name,
        'league_slug': league_slug
    }
    
    # Generate the page
    output_path = os.path.join(WEEKS_DIR, f"aug-4th-(14)-{league_slug}.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        html_content = template.render(**week_data)
        f.write(html_content)
    
    logging.info(f"Generated week page for league {league_name} with {len(player_stats)} players")

def main():
    """Main function to generate week pages"""
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Generate week pages for all leagues
    for league in config.get('leagues', []):
        league_id = league.get('league_id')
        league_name = league.get('name', f"League {league_id}")
        
        logging.info(f"Processing league: {league_name} (ID: {league_id})")
        generate_week_page(league_id, league_name)
    
    logging.info("Completed generating week pages")

if __name__ == "__main__":
    main()
