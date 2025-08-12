#!/usr/bin/env python3
import os
import re
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def direct_fix_vox_emoji():
    # Target file with the issue
    file_path = 'website_export/pal/daily/wordle-1503.html'
    
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return False
    
    # Create backup
    backup_path = f"{file_path}.direct_fix.bak"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup: {backup_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find Vox's emoji pattern specifically
        vox_pattern = re.compile(
            r'<div class="player-name">Vox</div>.*?'
            r'<div class="emoji-pattern">.*?'
            r'(<div class="emoji-row">)(🟩🟩🟩🟩🟩).*?(</div>)',
            re.DOTALL
        )
        
        # Clean up the emoji pattern
        modified_content = vox_pattern.sub(r'\1\2\3', content)
        
        if modified_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            logging.info(f"Successfully fixed Vox's emoji pattern in {file_path}")
            return True
        else:
            logging.warning(f"No changes made to {file_path} - pattern not found")
            return False
            
    except Exception as e:
        logging.error(f"Error fixing file: {e}")
        return False

def fix_weekly_stats_order():
    """Fix weekly stats ordering to put players with more games at the top"""
    json_file = 'website_export/league_3.json'
    
    try:
        import json
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'weekly_stats' in data:
            # Sort by used_scores (descending), then by weekly_score (ascending)
            data['weekly_stats'].sort(
                key=lambda x: (
                    -1 * (x.get('used_scores', 0) if isinstance(x.get('used_scores'), int) else 0),
                    x.get('weekly_score', 999) if isinstance(x.get('weekly_score'), int) else 999
                )
            )
            
            logging.info("Updated weekly stats ranking for PAL league:")
            for player in data['weekly_stats']:
                logging.info(f"  {player['name']}: {player.get('used_scores', 0)} games, score: {player.get('weekly_score', '-')}")
            
            # Write the updated data back
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            logging.info(f"Updated {json_file} with corrected weekly rankings")
            
            return True
    
    except Exception as e:
        logging.error(f"Error updating weekly stats: {e}")
        return False

def ensure_pants_in_list():
    """Make sure Pants is in the player list even with no scores"""
    json_file = 'website_export/league_3.json'
    
    try:
        import json
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'weekly_stats' in data:
            # Check if Pants is in the weekly stats
            pants_found = False
            for player in data['weekly_stats']:
                if player['name'] == 'Pants':
                    pants_found = True
                    break
            
            if not pants_found:
                # Add Pants to the weekly stats with no scores
                data['weekly_stats'].append({
                    'name': 'Pants',
                    'weekly_score': '-',
                    'used_scores': 0,
                    'failed_attempts': 0,
                    'failed': 0,
                    'thrown_out': '-'
                })
                
                logging.info("Added Pants to weekly stats")
                
                # Write the updated data back
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f)
                    
                return True
            else:
                logging.info("Pants already in weekly stats")
                return False
    
    except Exception as e:
        logging.error(f"Error ensuring Pants in list: {e}")
        return False

def fix_template():
    """Update the template for future exports"""
    template_path = 'website_export/templates/wordle.html'
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the emoji pattern section
        pattern = re.compile(
            r'({% for line in score\.emoji_pattern\.split\(\'\\\n\'\) %}.*?'
            r'<div class="emoji-row">)(.*?)(</div>)',
            re.DOTALL
        )
        
        if '|' not in content and 'strip' not in content:
            # Add the cleaning to the template
            modified = pattern.sub(
                r'\1{{ line.split(",")[0].split(".")[0].strip(\'"\')|trim }}\3', 
                content
            )
            
            if modified != content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(modified)
                logging.info("Updated template with improved cleaning")
                return True
        
        return False
    
    except Exception as e:
        logging.error(f"Error updating template: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting direct fix for Vox's emoji pattern")
    
    # Fix the emoji pattern
    emoji_fixed = direct_fix_vox_emoji()
    
    # Fix weekly stats order
    stats_fixed = fix_weekly_stats_order()
    
    # Ensure Pants is in the list
    pants_added = ensure_pants_in_list()
    
    # Fix template for future exports
    template_fixed = fix_template()
    
    # Run export again to apply all fixes
    if emoji_fixed or stats_fixed or pants_added or template_fixed:
        logging.info("Running full export to apply all fixes")
        os.system("python export_leaderboard_multi_league.py")
    
    logging.info("All fixes applied - check the results")
