#!/usr/bin/env python3
import os
import re
import logging
import shutil
import fileinput

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_emoji_ultra_precise():
    """Ultra-precise fix for the stubborn emoji pattern"""
    file_path = 'website_export/pal/daily/wordle-1503.html'
    
    # Create backup before proceeding
    backup_path = f"{file_path}.bak.{int(os.path.getmtime(file_path))}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backup created: {backup_path}")
    
    try:
        fixed = False
        for line in fileinput.input(file_path, inplace=True):
            if '🟩🟩🟩🟩🟩"' in line and 'emoji-row' in line and 'Thursday' in line:
                # This is our problematic line - replace with clean version
                line = '                             <div class="emoji-row">🟩🟩🟩🟩🟩</div>\n'
                fixed = True
                logging.info("Fixed problematic emoji line")
            print(line, end='')
        
        if fixed:
            logging.info(f"Successfully fixed emoji pattern in {file_path}")
            return True
        else:
            logging.warning(f"Could not find the problematic line in {file_path}")
            return False
            
    except Exception as e:
        logging.error(f"Error fixing emoji pattern: {e}")
        return False
        
def fix_weekly_stats():
    """Fix weekly stats order and add Pants"""
    json_file = 'website_export/api/league_3.json'
    
    if not os.path.exists(json_file):
        logging.error(f"JSON file not found: {json_file}")
        return False
    
    try:
        import json
        
        # Create backup
        backup_path = f"{json_file}.bak"
        shutil.copy2(json_file, backup_path)
        logging.info(f"Backup created: {backup_path}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'weekly_stats' not in data:
            logging.error("No weekly_stats found in JSON")
            return False
        
        # Check if Pants is in the weekly stats
        pants_found = False
        for player in data['weekly_stats']:
            if player['name'] == 'Pants':
                pants_found = True
                break
        
        if not pants_found:
            # Add Pants with no score
            data['weekly_stats'].append({
                'name': 'Pants',
                'weekly_score': '-',
                'used_scores': 0,
                'failed_attempts': 0,
                'failed': 0,
                'thrown_out': '-'
            })
            logging.info("Added Pants to weekly stats")
        
        # Fix the order - sort by used_scores (descending), then by weekly_score (ascending)
        data['weekly_stats'].sort(
            key=lambda x: (
                -1 * (x.get('used_scores', 0) if isinstance(x.get('used_scores'), int) else 0),
                x.get('weekly_score', 999) if isinstance(x.get('weekly_score', '-') != '-' and isinstance(x.get('weekly_score'), int)) else 999
            )
        )
        
        # Write the updated data back
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
        # Log the new order
        logging.info("Weekly stats order fixed:")
        for player in data['weekly_stats']:
            logging.info(f"  {player['name']}: {player.get('used_scores', 0)} games, score: {player.get('weekly_score', '-')}")
        
        return True
        
    except Exception as e:
        logging.error(f"Error fixing weekly stats: {e}")
        return False

def update_template_jinja():
    """Update the Jinja template to prevent future issues"""
    template_path = 'website_export/templates/wordle.html'
    
    if not os.path.exists(template_path):
        logging.error(f"Template not found: {template_path}")
        return False
    
    try:
        # Create backup
        backup_path = f"{template_path}.bak"
        shutil.copy2(template_path, backup_path)
        logging.info(f"Backup created: {backup_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the emoji pattern section and update it
        pattern = re.compile(
            r'({%\s+if\s+score\.emoji_pattern\s+%}.*?'
            r'<div class="emoji-pattern">.*?'
            r'{%\s+for\s+line\s+in\s+score\.emoji_pattern\.split\(.*?\)\s+%}.*?'
            r'<div class="emoji-row">)(.*?)(</div>.*?'
            r'{%\s+endfor\s+%})',
            re.DOTALL
        )
        
        if pattern.search(content):
            # Replace with a version that explicitly strips any text after the emojis
            modified = pattern.sub(
                r'\1{{ line.split(",")[0].split(".")[0].strip(\'"\')|trim }}\3',
                content
            )
            
            if modified != content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(modified)
                logging.info("Updated template with improved emoji cleaning")
                return True
            else:
                logging.info("Template already has the necessary cleaning code")
                return False
        else:
            logging.warning("Could not find emoji pattern section in template")
            return False
            
    except Exception as e:
        logging.error(f"Error updating template: {e}")
        return False

def regenerate_html():
    """Regenerate the HTML files using the export script"""
    try:
        # Run the export script focusing on the PAL league
        logging.info("Regenerating PAL league HTML files")
        os.system("python export_leaderboard_multi_league.py --league-id=3")
        logging.info("PAL league HTML files regenerated")
        return True
    except Exception as e:
        logging.error(f"Error regenerating HTML files: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting ultra-precise fix for emoji pattern and weekly stats")
    
    # Fix the emoji pattern
    emoji_fixed = fix_emoji_ultra_precise()
    
    # Fix weekly stats
    stats_fixed = fix_weekly_stats()
    
    # Update the template
    template_updated = update_template_jinja()
    
    # Regenerate HTML
    if emoji_fixed or stats_fixed or template_updated:
        html_regenerated = regenerate_html()
    else:
        html_regenerated = False
    
    logging.info(f"Fix results - Emoji: {emoji_fixed}, Stats: {stats_fixed}, Template: {template_updated}, HTML: {html_regenerated}")
    logging.info("All fixes complete - please verify the results!")
