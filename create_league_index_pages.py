#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import json
import shutil
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, Template

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Export directory
EXPORT_DIR = 'website_export'
TEMPLATES_DIR = os.path.join(EXPORT_DIR, 'templates')

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

def get_league_slug(league_name):
    """Convert league name to slug for filenames"""
    return league_name.lower().replace(' ', '-')

def create_index_template():
    """Create or ensure the existence of an index page template"""
    template_path = os.path.join(TEMPLATES_DIR, "league_index.html")
    
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)
    
    template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ league_name }} - Wordle League</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="stylesheet" href="{{ css_path }}">
    <link rel="icon" type="image/x-icon" href="{{ favicon_path }}">
</head>
<body>
    <header style="padding: 10px 0; margin-bottom: 10px;">
        <div class="container" style="padding: 10px; text-align: center;">
            <h1 class="title" style="font-size: 24px; margin-bottom: 0; text-align: center;">{{ league_name }}</h1>
        </div>
    </header>
    
    <div class="container">
        <div class="tab-container">
            <div class="tab-buttons tabs">
                <div style="width: 100%; display: flex; justify-content: center;">
                    <button class="tab-button active" data-tab="latest">Latest Scores</button>
                    <button class="tab-button" data-tab="weekly">Weekly Totals</button>
                </div>
                <div style="width: 100%; display: flex; justify-content: center;">
                    <button class="tab-button" data-tab="stats">Season / All-Time Stats</button>
                </div>
            </div>
            
            <div id="latest" class="tab-content active">
                <h2 style="margin-top: 5px; margin-bottom: 10px; font-size: 16px; color: #6aaa64; text-align: center;">{{ latest_wordle_title }}</h2>
                <!-- Latest scores content from export script would go here -->
                <p style="text-align: center; padding: 20px;">Visit the <a href="{{ current_week_url }}">current week page</a> to see all scores.</p>
            </div>
            
            <div id="weekly" class="tab-content">
                <h2 style="margin-top: 5px; margin-bottom: 10px;">Weekly Totals</h2>
                <p style="text-align: center; padding: 20px;">Visit the <a href="{{ current_week_url }}">current week page</a> to see all weekly statistics.</p>
            </div>
            
            <div id="stats" class="tab-content">
                <h2 style="margin-top: 5px; margin-bottom: 10px;">Season 1</h2>
                <p style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;">Weekly wins are tracked here. First player to reach 4 wins is the Season Winner!</p>
                
                <div style="text-align: center; padding: 20px;">
                    <a href="{{ current_week_url }}" class="button" style="display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;">View Current Week</a>
                </div>
                
                <h2 style="margin-top: 20px; margin-bottom: 10px;">All-Time Stats</h2>
                <p style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;">Average includes all games. Failed attempts (X/6) count as 7 in the average calculation.</p>
                <p style="text-align: center; padding: 20px;">Visit the <a href="{{ current_week_url }}">current week page</a> to see all-time statistics.</p>
            </div>
        </div>
    </div>
    
    <script src="{{ js_path }}"></script>
</body>
</html>"""
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    logging.info(f"Created league index template at {template_path}")
    return template_path

def create_league_index_page(league_id, league_name, export_path):
    """Create a proper index page for each league that links to league-specific pages"""
    league_slug = get_league_slug(league_name)
    
    # Determine relative paths for CSS and JS based on export path
    if export_path:
        css_path = "../styles.css"
        js_path = "../script.js"
        favicon_path = "../favicon.ico"
        # Create the league directory if it doesn't exist
        league_dir = os.path.join(EXPORT_DIR, export_path)
        if not os.path.exists(league_dir):
            os.makedirs(league_dir)
    else:
        css_path = "styles.css"
        js_path = "script.js"
        favicon_path = "favicon.ico"
    
    # Get the index template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("league_index.html")
    
    # Current week URL (relative path)
    if export_path:
        current_week_url = f"../weeks/aug-4th-(14)-{league_slug}.html"
    else:
        current_week_url = f"weeks/aug-4th-(14)-{league_slug}.html"
    
    # Get today's date for display
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Prepare data for the index page
    index_data = {
        'league_name': league_name,
        'league_slug': league_slug,
        'css_path': css_path,
        'js_path': js_path,
        'favicon_path': favicon_path,
        'current_week_url': current_week_url,
        'latest_wordle_title': f"Wordle #1513 - {current_date}"
    }
    
    # Generate the index page
    if export_path:
        output_path = os.path.join(EXPORT_DIR, export_path, "index.html")
    else:
        output_path = os.path.join(EXPORT_DIR, "index.html")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        html_content = template.render(**index_data)
        f.write(html_content)
    
    logging.info(f"Created league index page for {league_name} at {output_path}")

def create_main_index_page(leagues):
    """Create a main index page that lists all leagues with proper links"""
    main_index_path = os.path.join(EXPORT_DIR, "leagues.html")
    
    # Create HTML content for the main index page
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wordle Leagues</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="stylesheet" href="styles.css">
    <link rel="icon" type="image/x-icon" href="favicon.ico">
</head>
<body>
    <header style="padding: 10px 0; margin-bottom: 10px;">
        <div class="container" style="padding: 10px; text-align: center;">
            <h1 class="title" style="font-size: 24px; margin-bottom: 0; text-align: center;">Wordle Leagues</h1>
        </div>
    </header>
    
    <div class="container">
        <div class="content-section">
            <div class="section-header">
                <h2>Select Your League</h2>
            </div>
            <div class="section-content">
                <ul style="list-style-type: none; padding: 0; text-align: center;">"""
                
    # Add each league to the list
    for league in leagues:
        league_name = league.get('name')
        export_path = league.get('html_export_path', '')
        
        # Create the URL based on export path
        if export_path:
            league_url = f"{export_path}/index.html"
        else:
            league_url = "index.html"
        
        html_content += f"""
                    <li style="margin: 15px 0;">
                        <a href="{league_url}" class="button" style="display: inline-block; padding: 12px 25px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px; font-size: 16px;">{league_name}</a>
                    </li>"""
    
    html_content += """
                </ul>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="container">
            <p style="text-align: center; margin-top: 30px; font-size: 0.9em;">© 2025 Wordle League</p>
        </div>
    </footer>
</body>
</html>"""
    
    with open(main_index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logging.info(f"Created main league selection page at {main_index_path}")

def main():
    """Main function to create league index pages"""
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Create the index template
    create_index_template()
    
    # Create index pages for all leagues
    for league in config.get('leagues', []):
        league_id = league.get('league_id')
        league_name = league.get('name', f"League {league_id}")
        export_path = league.get('html_export_path', '')
        
        logging.info(f"Creating index page for league: {league_name} (ID: {league_id})")
        create_league_index_page(league_id, league_name, export_path)
    
    # Create the main leagues selection page
    create_main_index_page(config.get('leagues', []))
    
    logging.info("Completed creating league index pages")

if __name__ == "__main__":
    main()
