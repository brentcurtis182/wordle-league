#!/usr/bin/env python3
import os
import json
import re
import logging
import shutil
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_emoji_pattern_in_json(league_id):
    """Fix emoji patterns in the JSON file directly"""
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
        
        modified = False
        
        # Process each score's emoji pattern
        if 'scores' in data:
            for score in data['scores']:
                if 'emoji_pattern' in score:
                    original = score['emoji_pattern']
                    
                    # Clean up emoji pattern - remove anything after the last emoji
                    if '"' in original or ',' in original or '.' in original:
                        # Split by newlines
                        lines = original.split('\n')
                        cleaned_lines = []
                        
                        for line in lines:
                            # Extract just the emoji squares
                            emoji_match = re.match(r'^((?:[⬛⬜⬛⬜🟨🟩🟦🟥🟪🟧🟫⬇️]+))', line)
                            if emoji_match:
                                cleaned_lines.append(emoji_match.group(1))
                            else:
                                # If no match, keep the line as is
                                cleaned_lines.append(line)
                        
                        # Join back with newlines
                        cleaned_pattern = '\n'.join(cleaned_lines)
                        
                        if cleaned_pattern != original:
                            score['emoji_pattern'] = cleaned_pattern
                            modified = True
                            logging.info(f"Fixed emoji pattern for {score['name']} in league {league_id}, Wordle #{score['wordle_num']}")
                            logging.info(f"  Original: {original}")
                            logging.info(f"  Cleaned : {cleaned_pattern}")
        
        if modified:
            # Write the updated data back
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logging.info(f"Updated emoji patterns in {json_file}")
            return True
        else:
            logging.info(f"No emoji patterns needed fixing in {json_file}")
            return False
            
    except Exception as e:
        logging.error(f"Error fixing emoji patterns in {json_file}: {e}")
        return False

def fix_emoji_patterns_in_db():
    """Fix emoji patterns directly in the database"""
    db_path = "wordle_league.db"
    
    if not os.path.exists(db_path):
        logging.error(f"Database not found: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query all scores with emoji patterns
        cursor.execute("SELECT id, name, emoji_pattern, league_id FROM scores WHERE emoji_pattern IS NOT NULL")
        records = cursor.fetchall()
        
        fixed_count = 0
        
        for record in records:
            record_id, name, emoji_pattern, league_id = record
            
            if emoji_pattern and ('"' in emoji_pattern or ',' in emoji_pattern or '.' in emoji_pattern):
                # Split by newlines
                lines = emoji_pattern.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    # Extract just the emoji squares
                    emoji_match = re.match(r'^((?:[⬛⬜⬛⬜🟨🟩🟦🟥🟪🟧🟫⬇️]+))', line)
                    if emoji_match:
                        cleaned_lines.append(emoji_match.group(1))
                    else:
                        # If no match, keep the line as is
                        cleaned_lines.append(line)
                
                # Join back with newlines
                cleaned_pattern = '\n'.join(cleaned_lines)
                
                if cleaned_pattern != emoji_pattern:
                    cursor.execute(
                        "UPDATE scores SET emoji_pattern = ? WHERE id = ?",
                        (cleaned_pattern, record_id)
                    )
                    fixed_count += 1
                    logging.info(f"Fixed emoji pattern for {name} in league {league_id}")
                    logging.info(f"  Original: {emoji_pattern}")
                    logging.info(f"  Cleaned : {cleaned_pattern}")
        
        # Commit changes
        conn.commit()
        conn.close()
        
        logging.info(f"Fixed {fixed_count} emoji patterns in the database")
        return fixed_count > 0
        
    except Exception as e:
        logging.error(f"Error fixing emoji patterns in database: {e}")
        return False

def add_pants_to_pal_league():
    """Add Pants to the PAL league JSON if not present"""
    json_file = "website_export/api/league_3.json"
    
    if not os.path.exists(json_file):
        logging.error(f"JSON file not found: {json_file}")
        return False
    
    try:
        # Check the database for Pants
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Look for Pants in league 3
        cursor.execute("SELECT id FROM players WHERE name = 'Pants' AND league_id = 3")
        pants_record = cursor.fetchone()
        
        if not pants_record:
            # Add Pants to the players table
            cursor.execute(
                "INSERT INTO players (name, league_id) VALUES (?, ?)",
                ("Pants", 3)
            )
            conn.commit()
            logging.info("Added Pants to the players table for PAL league")
        
        conn.close()
        return True
        
    except Exception as e:
        logging.error(f"Error adding Pants to PAL league: {e}")
        return False

def update_export_logic():
    """Update the export_leaderboard_multi_league.py script to ensure proper sorting"""
    script_path = "export_leaderboard_multi_league.py"
    
    if not os.path.exists(script_path):
        logging.error(f"Export script not found: {script_path}")
        return False
    
    try:
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{script_path}.{timestamp}.bak"
        shutil.copy2(script_path, backup_path)
        logging.info(f"Created backup at {backup_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        modified = False
        for i, line in enumerate(content):
            # Find the sorting logic for weekly stats
            if "sort weekly stats by score" in line.lower() or "sort by weekly_score" in line.lower():
                # Check if we need to update the sorting logic
                if "used_scores" not in line and i < len(content) - 1:
                    # Look for the actual sorting line
                    for j in range(i, min(i+10, len(content))):
                        if "sort" in content[j].lower() and "key" in content[j].lower():
                            # Found the sorting line - check if it includes used_scores
                            if "used_scores" not in content[j]:
                                # Update the sorting logic to prioritize used_scores
                                original = content[j]
                                if "lambda x" in content[j]:
                                    content[j] = content[j].replace(
                                        "lambda x", 
                                        "lambda x: (-1 * x.get('used_scores', 0), "
                                    )
                                    content[j] = content[j].rstrip(")\n") + ")\n"
                                else:
                                    # Try another approach for different syntax
                                    content[j] = content[j].rstrip('\n') + " # Sort by used_scores first, then weekly_score\n"
                                    content.insert(j+1, "        weekly_stats.sort(key=lambda x: (-1 * x.get('used_scores', 0), x.get('weekly_score', 999)))\n")
                                
                                modified = True
                                logging.info(f"Updated sorting logic at line {j+1}")
                                logging.info(f"  Original: {original.strip()}")
                                logging.info(f"  Updated : {content[j].strip()}")
                                break
        
        if modified:
            # Write the updated content back
            with open(script_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
            
            logging.info(f"Updated export script with improved sorting logic")
            return True
        else:
            logging.info(f"Export script already has the correct sorting logic")
            return False
            
    except Exception as e:
        logging.error(f"Error updating export script: {e}")
        return False

def run_export_script():
    """Run the export script to generate HTML files with fixed data"""
    try:
        logging.info("Running export script to regenerate HTML files...")
        os.system("python export_leaderboard_multi_league.py")
        logging.info("HTML files regenerated successfully")
        return True
    except Exception as e:
        logging.error(f"Error running export script: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting comprehensive fix for JSON data and export logic")
    
    # Fix emoji patterns in the database
    db_fixed = fix_emoji_patterns_in_db()
    
    # Fix emoji patterns in all league JSON files
    warriorz_json_fixed = fix_emoji_pattern_in_json(1)
    gang_json_fixed = fix_emoji_pattern_in_json(2)
    pal_json_fixed = fix_emoji_pattern_in_json(3)
    
    # Add Pants to PAL league
    pants_added = add_pants_to_pal_league()
    
    # Update export script logic
    export_logic_fixed = update_export_logic()
    
    # Run the export script if anything was fixed
    if db_fixed or warriorz_json_fixed or gang_json_fixed or pal_json_fixed or pants_added or export_logic_fixed:
        export_run = run_export_script()
    else:
        export_run = False
    
    logging.info("Fix results:")
    logging.info(f"  Database emoji patterns: {db_fixed}")
    logging.info(f"  Wordle Warriorz JSON: {warriorz_json_fixed}")
    logging.info(f"  Wordle Gang JSON: {gang_json_fixed}")
    logging.info(f"  PAL League JSON: {pal_json_fixed}")
    logging.info(f"  Added Pants to PAL: {pants_added}")
    logging.info(f"  Export logic updated: {export_logic_fixed}")
    logging.info(f"  Export script run: {export_run}")
    logging.info("All fixes complete - please check the results!")
