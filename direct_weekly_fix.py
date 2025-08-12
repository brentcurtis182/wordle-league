#!/usr/bin/env python3
"""
Direct Weekly Stats Fix for Wordle League
This script directly patches the export_leaderboard_multi_league.py to fix weekly stats sorting
and regenerates HTML files for all leagues.
"""

import os
import shutil
import logging
import sqlite3
from datetime import datetime
import fileinput
import re
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def backup_file(file_path):
    """Create a backup of the specified file"""
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return None
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Created backup at {backup_path}")
    return backup_path

def fix_multi_league_export():
    """Fix the multi-league export script"""
    file_path = "export_leaderboard_multi_league.py"
    if not os.path.exists(file_path):
        logging.error(f"Export script not found: {file_path}")
        return False
        
    # Create backup
    backup_path = backup_file(file_path)
    if not backup_path:
        return False
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for the weekly stats processing section
    weekly_stats_pattern = r"def get_player_stats\([^)]*\):"
    
    if re.search(weekly_stats_pattern, content):
        logging.info("Found get_player_stats function in multi-league export script")
        
        # Replace the entire function with our fixed version
        fixed_content = content
        
        # Replace or add the correct sorting logic after the get_player_stats function
        sort_pattern = r"# Sort weekly stats by score.*?(?=\n\s*return|\n\s*\n)"
        sort_replacement = """
    # Sort weekly stats by games played first, then by score
    # Separate players with at least 5 games played
    players_with_5_plus = [p for p in player_stats if p.get('used_scores', 0) >= 5 and p.get('weekly_score') is not None]
    players_with_less_than_5 = [p for p in player_stats if p.get('used_scores', 0) < 5 and p.get('weekly_score') is not None]
    players_without_scores = [p for p in player_stats if p.get('weekly_score') is None]
    
    # Sort players with 5+ games by weekly score (ascending)
    players_with_5_plus.sort(key=lambda x: (x.get('weekly_score', 999), x.get('name', '')))
    
    # Sort players with less than 5 games by number of games played (descending), then weekly score, then name
    players_with_less_than_5.sort(key=lambda x: (-x.get('used_scores', 0), x.get('weekly_score', 999), x.get('name', '')))
    
    # Sort players without scores alphabetically
    players_without_scores.sort(key=lambda x: x.get('name', ''))
    
    # Combine the lists: first 5+ games players, then <5 games players, then players without scores
    player_stats = players_with_5_plus + players_with_less_than_5 + players_without_scores"""
        
        # Check if there's existing sorting logic to replace
        if re.search(sort_pattern, content, re.DOTALL):
            fixed_content = re.sub(sort_pattern, sort_replacement, content, flags=re.DOTALL)
            logging.info("Replaced existing weekly stats sorting logic")
        else:
            # If no sorting logic found, insert our sorting logic before the return statement
            return_pattern = r"(\s*return player_stats, all_time_stats)"
            if re.search(return_pattern, content):
                fixed_content = re.sub(return_pattern, f"\n{sort_replacement}\n\\1", content)
                logging.info("Added weekly stats sorting logic before return statement")
            else:
                logging.error("Could not find suitable place to insert sorting logic")
                return False
        
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        logging.info("Successfully patched the multi-league export script")
        return True
    else:
        logging.error("Could not find the weekly stats processing section")
        return False

def add_pants_to_pal_league():
    """Add Pants to the PAL league if not already present"""
    try:
        # Connect to the database
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Check if Pants is already in the players table for PAL league (league_id = 3)
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
            result = True
        else:
            logging.info("Pants already exists in the PAL league")
            result = True
        
        conn.close()
        return result
        
    except Exception as e:
        logging.error(f"Error adding Pants to PAL league: {e}")
        return False

def fix_vox_emoji_pattern():
    """Fix Vox's emoji pattern in the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Check if there are any emoji patterns with date/time text appended
        cursor.execute("""
            SELECT s.id, s.emoji_pattern, s.wordle_number, p.name 
            FROM scores s
            JOIN players p ON s.player_id = p.id
            WHERE s.emoji_pattern LIKE '%,%' 
               OR s.emoji_pattern LIKE '%"%' 
               OR s.emoji_pattern LIKE '%.%'
        """)
        
        records = cursor.fetchall()
        fixed_count = 0
        
        for record in records:
            record_id, emoji_pattern, wordle_number, name = record
            
            if emoji_pattern:
                # Clean up emoji pattern - remove anything after the last emoji
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
                    logging.info(f"Fixed emoji pattern for {name}, Wordle #{wordle_number}")
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

def run_export_script():
    """Run the export script to regenerate HTML files"""
    logging.info("Running export script to regenerate HTML files...")
    os.system("python export_leaderboard_multi_league.py")
    logging.info("HTML files regenerated")
    return True

def check_results():
    """Check if the fixes were successful"""
    logging.info("Checking weekly stats sorting in HTML files...")
    
    # Check PAL league
    pal_path = "website_export/pal/index.html"
    if os.path.exists(pal_path):
        with open(pal_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for Vox in weekly stats
        if 'Vox' in content and 'weekly-score' in content:
            logging.info("PAL league HTML file contains weekly stats with Vox")
            
            # Check if Pants is included
            if 'Pants' in content:
                logging.info("Pants is included in the PAL league HTML")
            else:
                logging.warning("Pants is still missing from the PAL league HTML")
    
    # Check Wordle Warriorz league
    warriorz_path = "website_export/wordle-warriorz/index.html"
    if os.path.exists(warriorz_path):
        with open(warriorz_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Count players with used_scores = 3
        matches = re.findall(r'<td class="used-scores">3</td>', content)
        if matches:
            logging.info(f"Found {len(matches)} players with 3 games played in Wordle Warriorz")
            
    logging.info("Check complete - manual verification recommended")

if __name__ == "__main__":
    logging.info("Starting direct weekly stats fix")
    
    # Step 1: Fix the export script
    export_fixed = fix_multi_league_export()
    
    # Step 2: Add Pants to PAL league
    pants_added = add_pants_to_pal_league()
    
    # Step 3: Fix Vox's emoji pattern
    emoji_fixed = fix_vox_emoji_pattern()
    
    # Step 4: Run export script if any fixes were made
    if export_fixed or pants_added or emoji_fixed:
        export_run = run_export_script()
    else:
        export_run = False
        
    # Step 5: Check results
    check_results()
    
    logging.info("Fix results:")
    logging.info(f"  Export script fixed: {export_fixed}")
    logging.info(f"  Pants added to PAL league: {pants_added}")
    logging.info(f"  Emoji patterns fixed: {emoji_fixed}")
    logging.info(f"  Export script run: {export_run}")
    
    logging.info("All fixes complete - please check the website files to verify results")
