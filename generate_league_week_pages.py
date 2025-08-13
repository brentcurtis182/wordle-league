#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
from datetime import datetime, timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Export directories
EXPORT_DIR = 'website_export'
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

def get_date_for_wordle(wordle_number):
    """Calculate the date for a specific Wordle number"""
    # Wordle #0 was released on June 19, 2021
    base_date = datetime(2021, 6, 19)
    wordle_date = base_date + timedelta(days=wordle_number)
    return wordle_date.strftime("%B %d, %Y")

def get_league_slug(league_name):
    """Convert league name to slug for filenames"""
    return league_name.lower().replace(' ', '-')

def generate_league_week_pages():
    """Generate week pages with actual data for each league"""
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Create weeks directory if it doesn't exist
    if not os.path.exists(WEEKS_DIR):
        os.makedirs(WEEKS_DIR)
    
    # Get the week template
    env = Environment(loader=FileSystemLoader("website_export/templates"))
    template = env.get_template("league_week.html")
    
    # For each league, generate a week page
    for league in config.get('leagues', []):
        league_id = league.get('league_id')
        league_name = league.get('name', f"League {league_id}")
        league_slug = get_league_slug(league_name)
        
        logging.info(f"Generating week page for league: {league_name} (ID: {league_id})")
        
        # Create data for Aug 4th week (Wordles 1507-1513)
        wordle_games = []
        for wordle_num in range(1507, 1514):
            date = get_date_for_wordle(wordle_num)
            wordle_games.append({
                'number': f"{wordle_num:,}",
                'clean_number': f"{wordle_num}",
                'date': date,
                'league_slug': league_slug
            })
        
        # Prepare week data
        week_data = {
            'title': f'Wordle League - Week of August 4, 2025 - {league_name}',
            'week_title': f'August 4, 2025 - {league_name}',
            'wordle_games': wordle_games,
            'league_name': league_name,
            'league_slug': league_slug
        }
        
        # Generate week page for this league
        output_path = os.path.join(WEEKS_DIR, f"aug-4th-(14)-{league_slug}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            html_content = template.render(**week_data)
            f.write(html_content)
        logging.info(f"Generated week page for August 4th for {league_name}")

if __name__ == "__main__":
    generate_league_week_pages()
