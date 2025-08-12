#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Export directory
EXPORT_DIR = 'website_export'

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

def fix_index_page_links(league_id, league_name, export_path):
    """Fix the links in a league's index page to point to league-specific week pages"""
    league_slug = get_league_slug(league_name)
    
    # Path to the league's main index page
    if export_path:
        index_page_path = os.path.join(EXPORT_DIR, export_path, "index.html")
    else:
        index_page_path = os.path.join(EXPORT_DIR, "index.html")
    
    if not os.path.exists(index_page_path):
        logging.warning(f"Index page not found at {index_page_path}")
        return False
    
    try:
        # Read the current content
        with open(index_page_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace links to week pages with league-specific links
        # Pattern matches: <a href="weeks/aug-4th-(14).html" target="_blank">
        old_pattern = r'<a href="(weeks/[^"]+\.html)"'
        
        # Function to replace each match with league-specific link
        def replace_link(match):
            original_link = match.group(1)
            # Extract the base part of the link (e.g., 'weeks/aug-4th-(14)')
            base_link = original_link.rsplit('.', 1)[0]
            # Create new league-specific link
            new_link = f'{base_link}-{league_slug}.html'
            return f'<a href="{new_link}"'
        
        # Replace all matching links
        modified_content = re.sub(old_pattern, replace_link, content)
        
        # Write the modified content back
        with open(index_page_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        logging.info(f"Fixed links in {index_page_path} to point to league-specific pages")
        return True
    
    except Exception as e:
        logging.error(f"Error fixing links in {index_page_path}: {e}")
        return False

def main():
    """Main function to fix navigation links"""
    # Get league configuration
    config = get_league_config()
    if not config:
        logging.error("Failed to load league configuration")
        return
    
    # Fix links for all leagues
    for league in config.get('leagues', []):
        league_id = league.get('league_id')
        league_name = league.get('name', f"League {league_id}")
        export_path = league.get('export_path', '')
        
        logging.info(f"Fixing navigation links for league: {league_name} (ID: {league_id})")
        fix_index_page_links(league_id, league_name, export_path)
    
    logging.info("Completed fixing navigation links")

if __name__ == "__main__":
    main()
