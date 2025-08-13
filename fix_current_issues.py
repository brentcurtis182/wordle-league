#!/usr/bin/env python3
import os
import re
import sqlite3
import logging
import shutil
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_emoji_patterns():
    """Fix emoji patterns in HTML files by removing appended text"""
    try:
        # Directories to process
        directories = [
            'website_export/daily',         # Main league
            'website_export/pal/daily',     # PAL league
            'website_export/gang/daily'     # Gang league
        ]
        
        # Compile regex pattern once
        # This pattern matches emoji square pattern followed by anything else on the line
        emoji_pattern = re.compile(r'(<div class="emoji-row">)([⬜⬛🟨🟩🟥🟦🟪🟧🟫⬜]{5})(.*?)(</div>)')
        
        files_processed = 0
        files_modified = 0
        
        for directory in directories:
            if not os.path.exists(directory):
                logging.info(f"Directory not found: {directory}")
                continue
                
            logging.info(f"Processing directory: {directory}")
            
            # Process all HTML files
            for filename in os.listdir(directory):
                if filename.endswith('.html'):
                    filepath = os.path.join(directory, filename)
                    files_processed += 1
                    
                    # Create backup if not already exists
                    backup_file = f"{filepath}.bak"
                    if not os.path.exists(backup_file):
                        shutil.copy2(filepath, backup_file)
                        logging.info(f"Created backup: {backup_file}")
                    
                    # Read file content
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix emoji patterns
                    modified_content = emoji_pattern.sub(r'\1\2\4', content)
                    
                    # Only write if changes were made
                    if modified_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                        files_modified += 1
                        logging.info(f"Fixed emoji patterns in {filepath}")
        
        logging.info(f"Processed {files_processed} files, modified {files_modified} files")
        return files_modified
        
    except Exception as e:
        logging.error(f"Error fixing emoji patterns: {e}")
        return 0

def fix_weekly_scores_logic():
    """Fix the weekly scores logic to properly rank players with more games played higher"""
    try:
        # Connect to the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # First, check the existing rankings for PAL league
        logging.info("Checking existing PAL league weekly rankings")
        cursor.execute("""
            SELECT player_name, COUNT(*) as game_count
            FROM scores 
            WHERE league_id = 3 
            AND date(timestamp) >= date('now', '-7 days')
            GROUP BY player_name
            ORDER BY game_count DESC
        """)
        
        current_rankings = cursor.fetchall()
        logging.info("Current PAL weekly rankings by game count:")
        for player, count in current_rankings:
            logging.info(f"  {player}: {count} games")
        
        # Update the JSON data for league 3 (PAL)
        json_file = 'website_export/league_3.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'weekly_stats' in data:
                # Sort weekly stats by games_played (used_scores) in descending order
                data['weekly_stats'].sort(key=lambda x: (x.get('used_scores', 0), x.get('weekly_score', 999)), reverse=True)
                
                logging.info("Updated weekly stats ranking for PAL league:")
                for player in data['weekly_stats']:
                    logging.info(f"  {player['name']}: {player.get('used_scores', 0)} games, score: {player.get('weekly_score', '-')}")
                
                # Write the updated data back
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                logging.info(f"Updated {json_file} with corrected weekly rankings")
        
        # Also update HTML files to reflect the correct order
        # This requires regenerating the HTML files
        logging.info("Running export to update HTML files with corrected rankings")
        os.system("python export_leaderboard_multi_league.py")
        
        logging.info("Weekly scores logic fixed")
        return True
        
    except Exception as e:
        logging.error(f"Error fixing weekly scores logic: {e}")
        return False

def add_missing_players_to_html():
    """Ensure players with no scores like Pants are properly listed with '-'"""
    try:
        # Connect to database to get all players
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get all players in PAL league
        cursor.execute("""
            SELECT DISTINCT player_name 
            FROM scores 
            WHERE league_id = 3
        """)
        
        pal_players = [row[0] for row in cursor.fetchall()]
        logging.info(f"PAL league players: {', '.join(pal_players)}")
        
        # Add Pants to the player list if not already there
        if 'Pants' not in pal_players:
            logging.info("Adding Pants to known PAL players")
            pal_players.append('Pants')
        
        # Check weekly stats in JSON file
        json_file = 'website_export/league_3.json'
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'weekly_stats' in data:
                # Check if each player is in the weekly stats
                weekly_players = [item['name'] for item in data['weekly_stats']]
                
                # Add missing players
                for player in pal_players:
                    if player not in weekly_players:
                        logging.info(f"Adding {player} to weekly stats with no scores")
                        data['weekly_stats'].append({
                            'name': player,
                            'weekly_score': '-',
                            'used_scores': 0,
                            'failed_attempts': 0,
                            'failed': 0,
                            'thrown_out': '-'
                        })
                
                # Write the updated data back
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                logging.info(f"Updated {json_file} with missing players")
        
        # Run export again to update HTML files
        logging.info("Running export to update HTML files with all players")
        os.system("python export_leaderboard_multi_league.py")
        
        logging.info("Missing players added")
        return True
        
    except Exception as e:
        logging.error(f"Error adding missing players: {e}")
        return False

def fix_template():
    """Update the wordle.html template to ensure clean emoji patterns"""
    template_path = 'website_export/templates/wordle.html'
    
    try:
        if not os.path.exists(template_path):
            logging.error(f"Template file not found: {template_path}")
            return False
            
        # Create backup if not already exists
        backup_file = f"{template_path}.bak"
        if not os.path.exists(backup_file):
            shutil.copy2(template_path, backup_file)
            logging.info(f"Created backup of template: {backup_file}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find the emoji pattern section
        emoji_section = re.search(r'({% if score\.emoji_pattern %}.*?<div class="emoji-pattern">.*?{% for line in score\.emoji_pattern\.split\(\'\\\n\'\) %}.*?<div class="emoji-row">)(.*?)(</div>.*?{% endfor %}.*?{% endif %})', content, re.DOTALL)
        
        if emoji_section:
            # Ensure we're only showing the emoji squares
            cleaned_content = content.replace(
                emoji_section.group(0),
                f'{emoji_section.group(1)}{{ line.split(",")[0].split(".")[0].strip(\'"\'") }}{emoji_section.group(3)}'
            )
            
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
                
            logging.info("Template updated to ensure clean emoji patterns")
            return True
        else:
            logging.warning("Could not find emoji pattern section in template")
            return False
            
    except Exception as e:
        logging.error(f"Error fixing template: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting comprehensive fix")
    
    # Step 1: Fix emoji patterns in HTML files
    fix_emoji_patterns()
    
    # Step 2: Update the template
    fix_template()
    
    # Step 3: Fix weekly scores logic
    fix_weekly_scores_logic()
    
    # Step 4: Add missing players to HTML
    add_missing_players_to_html()
    
    # Step 5: Run full export to apply all changes
    logging.info("Running full export to apply all fixes")
    os.system("python integrated_auto_update_multi_league.py --export-only")
    
    logging.info("All issues fixed!")
