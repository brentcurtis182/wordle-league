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
        ORDER BY s.score
        """, (wordle_number, league_id))
        
        result = cursor.fetchall()
        
        for row in result:
            name = row[1] if row[1] else row[0]  # Use nickname if available
            score = row[2]
            emoji_pattern = row[3]
            
            # Process score for display
            has_score = True
            
            # Handle failed attempts (stored as 7 in DB) for display
            if score == 7 or score == '7':
                score_display = 'X'  # Remove "/6" - template will add it
                css_class = 'X'
            elif score in ('X', '-', 'None', ''):
                score_display = 'X'  # Remove "/6" - template will add it
                css_class = 'X'
            else:
                # Regular scores 1-6 (without /6 suffix - template will add it)
                score_display = str(score)
                css_class = str(score)
            
            # Use emoji pattern directly from database or leave blank if not available
            processed_emoji_pattern = emoji_pattern
            
            # Set to None if the emoji pattern is missing or empty
            if not processed_emoji_pattern or processed_emoji_pattern == 'None' or processed_emoji_pattern == '':
                processed_emoji_pattern = None

            logging.info(f"Found score for {name}: {score_display}/6, emoji pattern: {'Yes' if processed_emoji_pattern else 'No'}")
            
            scores.append({
                'name': name,
                'has_score': has_score,
                'score': score_display,
                'css_class': css_class,
                'emoji_pattern': processed_emoji_pattern
            })
        
        return scores
        
    except Exception as e:
        logging.error(f"Error getting scores for Wordle {wordle_number}, league {league_id}: {e}")
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

def generate_day_pages_with_real_data(league_id, league_name):
    """Generate day pages for Wordle games 1507-1513 with real data from database for specific league"""
    league_slug = get_league_slug(league_name)
    logging.info(f"Generating day pages with real data for league {league_id} ({league_name})")
    
    # Create days directory if it doesn't exist
    if not os.path.exists(DAYS_DIR):
        os.makedirs(DAYS_DIR)
    
    # Get the day template
    env = Environment(loader=FileSystemLoader("website_export/templates"))
    template = env.get_template("league_day.html")
    
    # Generate pages for each Wordle day 1507-1513
    for wordle_num in range(1507, 1514):
        # Get actual date for this Wordle
        wordle_date = get_date_for_wordle(wordle_num)
        
        # Get real scores from database
        scores = get_scores_for_wordle_by_league(wordle_num, league_id)
        
        # If we have scores, generate the page
        formatted_num = f"{wordle_num:,}"
        
        logging.info(f"Found {len(scores)} scores for Wordle #{formatted_num} in {league_name}")
        
        # Prepare data for the day page
        day_data = {
            'title': f'Wordle #{formatted_num} - {wordle_date} - {league_name}',
            'wordle_number': formatted_num,
            'wordle_date': wordle_date,
            'week_slug': 'aug-4th-(14)',
            'scores': scores,
            'league_name': league_name,
            'league_slug': league_slug
        }
        
        # Create league-specific filename
        output_path = os.path.join(DAYS_DIR, f"wordle-{wordle_num}-{league_slug}.html")
        
        # Generate the page
        with open(output_path, 'w', encoding='utf-8') as f:
            html_content = template.render(**day_data)
            f.write(html_content)
        logging.info(f"Generated day page for Wordle #{formatted_num} with {len(scores)} real scores for league {league_name}")

def main():
    """Main function to generate day pages with real data"""
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Generate day pages with real data for all leagues
    for league in config.get('leagues', []):
        league_id = league.get('league_id')
        league_name = league.get('name', f"League {league_id}")
        
        logging.info(f"Processing league: {league_name} (ID: {league_id})")
        generate_day_pages_with_real_data(league_id, league_name)
    
    logging.info("Completed generating day pages with real data")

if __name__ == "__main__":
    main()
