#!/usr/bin/env python3
import os
import json
import logging
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_weekly_stats_for_league(league_id):
    """Fix weekly stats for a specific league
    
    - Sort by used_scores (games played) descending, then by weekly_score ascending
    - Add missing players with '-' scores (like Pants for PAL league)
    """
    json_file = f"website_export/api/league_{league_id}.json"
    
    if not os.path.exists(json_file):
        logging.error(f"JSON file not found: {json_file}")
        return False
    
    # Create backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{json_file}.{timestamp}.bak"
    shutil.copy2(json_file, backup_path)
    logging.info(f"Created backup at {backup_path}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if we have weekly_stats
        if 'weekly_stats' not in data:
            logging.error(f"No weekly_stats found in {json_file}")
            return False
        
        # Add Pants to PAL league if missing
        if league_id == 3:
            pants_found = False
            for player in data['weekly_stats']:
                if player['name'] == 'Pants':
                    pants_found = True
                    break
            
            if not pants_found:
                logging.info("Adding Pants to PAL league weekly stats")
                data['weekly_stats'].append({
                    'name': 'Pants',
                    'weekly_score': '-',
                    'used_scores': 0,
                    'failed_attempts': 0,
                    'failed': 0,
                    'thrown_out': '-'
                })
        
        # Sort weekly stats properly
        logging.info(f"Sorting weekly stats for league {league_id}")
        original_order = [p['name'] for p in data['weekly_stats']]
        
        # Sort by used_scores (descending), then by weekly_score (ascending)
        # Handle cases where weekly_score might be '-' or non-numeric
        data['weekly_stats'].sort(key=lambda x: (
            -1 * (int(x.get('used_scores', 0)) if isinstance(x.get('used_scores'), (int, str)) and str(x.get('used_scores', 0)).isdigit() else 0),
            int(x.get('weekly_score', 999)) if isinstance(x.get('weekly_score'), (int, str)) and str(x.get('weekly_score', '')).isdigit() else 999
        ))
        
        new_order = [p['name'] for p in data['weekly_stats']]
        logging.info(f"Order changed from {original_order} to {new_order}")
        
        # Log detailed info about the weekly stats
        logging.info(f"Detailed weekly stats for league {league_id}:")
        for player in data['weekly_stats']:
            logging.info(f"  {player['name']}: {player.get('used_scores', 0)} games, score: {player.get('weekly_score', '-')}")
        
        # Write the updated data back
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        return True
        
    except Exception as e:
        logging.error(f"Error fixing weekly stats for league {league_id}: {e}")
        return False

def update_html_files():
    """Run the export script to update HTML files with the fixed JSON data"""
    try:
        logging.info("Updating HTML files with fixed weekly stats...")
        os.system("python export_leaderboard_multi_league.py")
        logging.info("HTML files updated successfully")
        return True
    except Exception as e:
        logging.error(f"Error updating HTML files: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting weekly stats fix")
    
    # Fix Wordle Warriorz (league 1)
    warriorz_fixed = fix_weekly_stats_for_league(1)
    logging.info(f"Wordle Warriorz stats fixed: {warriorz_fixed}")
    
    # Fix Wordle Gang (league 2)
    gang_fixed = fix_weekly_stats_for_league(2)
    logging.info(f"Wordle Gang stats fixed: {gang_fixed}")
    
    # Fix PAL league (league 3)
    pal_fixed = fix_weekly_stats_for_league(3)
    logging.info(f"PAL league stats fixed: {pal_fixed}")
    
    # Update HTML files if any league was fixed
    if warriorz_fixed or gang_fixed or pal_fixed:
        html_updated = update_html_files()
        logging.info(f"HTML files updated: {html_updated}")
    
    logging.info("Weekly stats fix complete!")
