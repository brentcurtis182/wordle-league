#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import json
import re
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Export directories
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

def fix_main_landing_page(league_id, league_name, export_path):
    """Fix the main landing page for a league to point to league-specific pages"""
    league_slug = get_league_slug(league_name)
    
    # Create the landing page from a template
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("landing_page.html")
    
    # Path to the league's main landing page
    landing_page_path = os.path.join(EXPORT_DIR, export_path, "index.html")
    directory = os.path.dirname(landing_page_path)
    
    # Create directory if it doesn't exist
    if not os.path.exists(directory):
        os.makedirs(directory)
        logging.info(f"Created directory: {directory}")
    
    # Prepare template data
    template_data = {
        'title': f"Wordle League - {league_name}",
        'league_name': league_name,
        'league_slug': league_slug,
        'week_page_path': f"../weeks/aug-4th-(14)-{league_slug}.html"
    }
    
    # Generate the landing page
    with open(landing_page_path, 'w', encoding='utf-8') as f:
        html_content = template.render(**template_data)
        f.write(html_content)
    
    logging.info(f"Fixed landing page for {league_name} at {landing_page_path}")
    
def create_landing_page_template():
    """Create a template for the landing page that includes links to league-specific pages"""
    template_path = os.path.join(TEMPLATES_DIR, "landing_page.html")
    
    template_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="stylesheet" href="../styles.css">
    <style>
        /* Emoji pattern styles */
        .score-display {
            display: flex;
            align-items: center;
        }
        
        .emoji-pattern {
            margin-left: 15px;
            font-size: 0.8rem;
            line-height: 1.1;
            display: inline-block;
            letter-spacing: 0;
            font-family: monospace;
            text-align: right;
        }
        
        .emoji-row {
            white-space: nowrap;
            height: 1.1em;
            margin: 0;
            padding: 0;
            display: block;
        }
        
        .emoji-container {
            height: auto;
            display: flex;
            flex-direction: column;
            justify-content: center;
            margin-left: auto;
        }
        
        /* Failed attempts column styling */
        .failed-attempts {
            background-color: rgba(128, 58, 58, 0.2);
            font-weight: bold;
            color: #ff6b6b;
        }
        
        /* When failed attempts is 0, make it less prominent */
        td.failed-attempts:empty {
            background-color: transparent;
            color: #d7dadc;
            font-weight: normal;
        }
    </style>
</head>
<body>
    <header style="padding: 10px 0; margin-bottom: 10px;">
        <div class="container" style="padding: 10px; text-align: center;">
            <h1 class="title" style="font-size: 24px; margin-bottom: 0; text-align: center;">{{ league_name }}</h1>
        </div>
    </header>
    
    <div class="container">
        <div class="content-section">
            <div class="section-header">
                <h2>Weekly Leaderboard</h2>
            </div>
            <div class="section-content">
                <p>View the latest weekly scores and statistics for the {{ league_name }}.</p>
                <p><a href="{{ week_page_path }}" class="button">View Current Week</a></p>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="container">
            <p>© 2025 Wordle League</p>
        </div>
    </footer>

    <script src="../script.js"></script>
</body>
</html>"""
    
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    logging.info(f"Created landing page template at {template_path}")

def fix_root_index_page(leagues):
    """Fix the root index page to list all leagues with proper links"""
    root_index_path = os.path.join(EXPORT_DIR, "index.html")
    
    # Create HTML content for the root index page
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wordle League</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header style="padding: 10px 0; margin-bottom: 10px;">
        <div class="container" style="padding: 10px; text-align: center;">
            <h1 class="title" style="font-size: 24px; margin-bottom: 0; text-align: center;">Wordle League</h1>
        </div>
    </header>
    
    <div class="container">
        <div class="content-section">
            <div class="section-header">
                <h2>Select Your League</h2>
            </div>
            <div class="section-content">
                <ul style="list-style-type: none; padding: 0;">"""
                
    # Add each league to the list
    for league in leagues:
        league_name = league.get('name')
        export_path = league.get('export_path', '')
        html_content += f"""
                    <li style="margin: 10px 0;">
                        <a href="{export_path}/index.html" class="button" style="display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;">{league_name}</a>
                    </li>"""
    
    html_content += """
                </ul>
            </div>
        </div>
    </div>
    
    <footer>
        <div class="container">
            <p>© 2025 Wordle League</p>
        </div>
    </footer>
</body>
</html>"""
    
    with open(root_index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logging.info(f"Fixed root index page at {root_index_path}")

def main():
    """Main function to fix landing pages"""
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Create the landing page template
    create_landing_page_template()
    
    # Fix landing pages for all leagues
    for league in config.get('leagues', []):
        league_id = league.get('league_id')
        league_name = league.get('name', f"League {league_id}")
        export_path = league.get('export_path', '')
        
        logging.info(f"Fixing landing page for league: {league_name} (ID: {league_id})")
        fix_main_landing_page(league_id, league_name, export_path)
    
    # Fix the root index page
    fix_root_index_page(config.get('leagues', []))
    
    logging.info("Completed fixing landing pages")

if __name__ == "__main__":
    main()
