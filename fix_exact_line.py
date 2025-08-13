#!/usr/bin/env python3
import os
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_exact_line():
    """Fix the specific problematic line in the HTML file"""
    file_path = 'website_export/pal/daily/wordle-1503.html'
    
    try:
        # Read the file
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Find and fix the line with the extra text
        found = False
        for i, line in enumerate(lines):
            if '🟩🟩🟩🟩🟩"' in line and 'emoji-row' in line:
                # Extract just the emoji squares
                lines[i] = '                             <div class="emoji-row">🟩🟩🟩🟩🟩</div>\n'
                found = True
                logging.info(f"Fixed line {i+1}: {lines[i].strip()}")
                break
        
        if found:
            # Write the fixed content back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            logging.info("Successfully fixed the problematic line")
            return True
        else:
            logging.warning("Couldn't find the problematic line")
            return False
            
    except Exception as e:
        logging.error(f"Error: {e}")
        return False

def check_weekly_order():
    """Check if the weekly stats have Vox at the top with 2 games played"""
    json_file = 'website_export/api/league_3.json'
    
    try:
        import json
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'weekly_stats' in data:
            # Check if Vox is at the top
            if len(data['weekly_stats']) > 0 and data['weekly_stats'][0]['name'] == 'Vox':
                logging.info("Weekly stats order is correct - Vox is at the top")
            else:
                logging.info("Fixing weekly stats order...")
                # Sort by used_scores (descending), then by weekly_score (ascending)
                data['weekly_stats'].sort(
                    key=lambda x: (
                        -1 * (x.get('used_scores', 0) if isinstance(x.get('used_scores'), int) else 0),
                        x.get('weekly_score', 999) if isinstance(x.get('weekly_score'), int) else 999
                    )
                )
                
                # Write the updated data back
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                logging.info("Fixed weekly stats order")
                
                # Print the new order
                for player in data['weekly_stats']:
                    logging.info(f"  {player['name']}: {player.get('used_scores', 0)} games, score: {player.get('weekly_score', '-')}")
                
                return True
            
        return False
        
    except Exception as e:
        logging.error(f"Error checking weekly order: {e}")
        return False

def add_pants():
    """Add Pants to the player list with no scores"""
    json_file = 'website_export/api/league_3.json'
    
    try:
        import json
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'weekly_stats' in data:
            # Check if Pants is already in the list
            pants_found = False
            for player in data['weekly_stats']:
                if player['name'] == 'Pants':
                    pants_found = True
                    break
            
            if not pants_found:
                # Add Pants
                data['weekly_stats'].append({
                    'name': 'Pants',
                    'weekly_score': '-',
                    'used_scores': 0,
                    'failed_attempts': 0,
                    'failed': 0,
                    'thrown_out': '-'
                })
                
                # Write the updated data back
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                logging.info("Added Pants to the player list")
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"Error adding Pants: {e}")
        return False

def manually_update_html():
    """Manually update the index.html and Wordle #1503 HTML files for the PAL league"""
    pal_dir = 'website_export/pal'
    wordle_file = os.path.join(pal_dir, 'daily', 'wordle-1503.html')
    index_file = os.path.join(pal_dir, 'index.html')
    
    try:
        # First ensure Vox is at the top of the weekly stats
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index_content = f.read()
            
            # Check if weekly table has Vox at the top
            weekly_table = re.search(r'<table id="weekly-table">(.*?)</table>', index_content, re.DOTALL)
            if weekly_table:
                table_content = weekly_table.group(1)
                # If Vox is not the first player in the table
                if '<td>Vox</td>' not in table_content[:500]:
                    logging.info("Regenerating PAL league pages")
                    # Run the export again focusing on PAL league
                    os.system("python export_leaderboard_multi_league.py --league-id=3")
                    logging.info("Regenerated PAL league pages")
            
        return True
        
    except Exception as e:
        logging.error(f"Error manually updating HTML: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting exact line fix")
    
    # Fix the exact problematic line
    line_fixed = fix_exact_line()
    
    # Check weekly order
    order_fixed = check_weekly_order()
    
    # Add Pants
    pants_added = add_pants()
    
    # Manual HTML update
    html_updated = manually_update_html()
    
    logging.info("All fixes complete!")
