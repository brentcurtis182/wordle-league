#!/usr/bin/env python3
"""
Comprehensive Fixes for Wordle League:
1. Fix emoji pattern display (remove appended date/time)
2. Fix weekly stats sorting (more games played first, then by score)
3. Fix weekly scores data accuracy
"""

import os
import re
import json
import shutil
import logging
import sqlite3
import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(script_dir, 'wordle_league.db')
EXPORT_DIR = os.path.join(script_dir, 'website_export')
HTML_TEMPLATE_PATH = os.path.join(EXPORT_DIR, 'templates', 'wordle.html')

def backup_file(file_path):
    """Create a backup of the file with timestamp"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{file_path}.bak_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backup created: {backup_path}")
    return backup_path

def fix_emoji_pattern_template():
    """Fix emoji pattern rendering in Jinja2 template"""
    if not os.path.exists(HTML_TEMPLATE_PATH):
        logging.error(f"Template file not found: {HTML_TEMPLATE_PATH}")
        return False
    
    # Backup template file
    backup_file(HTML_TEMPLATE_PATH)
    
    # Read template content
    with open(HTML_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the section that renders emoji patterns
    pattern_section = re.search(r'{% if score\.emoji_pattern %}.*?{% endif %}', content, re.DOTALL)
    if not pattern_section:
        logging.error("Could not find emoji_pattern section in template")
        return False
    
    # Original pattern rendering code
    original_code = pattern_section.group(0)
    
    # Create improved version that cleanses emoji patterns
    improved_code = """{% if score.emoji_pattern %}
                        <div class="emoji-pattern">
                            {% set cleaned_pattern = score.emoji_pattern.split(',')[0].strip() %}
                            {% for line in cleaned_pattern.split('\\n') %}
                            {% if line and '⬜' in line or '🟨' in line or '🟩' in line %}
                            <div class="emoji-row">{{ line }}</div>
                            {% endif %}
                            {% endfor %}
                        </div>
                        {% endif %}"""
    
    # Replace the pattern rendering code
    new_content = content.replace(original_code, improved_code)
    
    # Write the updated content back
    with open(HTML_TEMPLATE_PATH, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    logging.info(f"Updated emoji pattern rendering in template: {HTML_TEMPLATE_PATH}")
    return True

def fix_emoji_patterns_in_database():
    """Fix emoji patterns in the database by removing appended date/time"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all scores with emoji patterns
        cursor.execute("SELECT id, emoji_pattern FROM scores WHERE emoji_pattern IS NOT NULL")
        scores_with_patterns = cursor.fetchall()
        
        updated_count = 0
        for score_id, emoji_pattern in scores_with_patterns:
            if emoji_pattern and (',' in emoji_pattern or '.' in emoji_pattern):
                # Clean the pattern - keep only the emoji grid part
                cleaned_pattern = emoji_pattern.split(',')[0].strip()
                
                # Update the database
                cursor.execute("UPDATE scores SET emoji_pattern = ? WHERE id = ?", (cleaned_pattern, score_id))
                updated_count += 1
        
        conn.commit()
        logging.info(f"Fixed {updated_count} emoji patterns in database")
        return updated_count > 0
    except Exception as e:
        logging.error(f"Error fixing emoji patterns in database: {e}")
        return False
    finally:
        if conn:
            conn.close()

def fix_weekly_stats_sorting():
    """Fix the weekly stats sorting logic in export_leaderboard_multi_league.py"""
    export_script_path = os.path.join(script_dir, 'export_leaderboard_multi_league.py')
    
    if not os.path.exists(export_script_path):
        logging.error(f"Export script not found: {export_script_path}")
        return False
    
    # Backup the export script
    backup_file(export_script_path)
    
    # Read file content
    with open(export_script_path, 'r', encoding='utf-8') as f:
        content = f.readlines()
    
    # Find the line with weekly stats sorting
    sorting_line_index = -1
    league_name_added = False
    
    for i, line in enumerate(content):
        if "stats.sort(key=lambda x:" in line and "weekly_score" in line:
            sorting_line_index = i
            break
    
    if sorting_line_index == -1:
        logging.error("Could not find weekly stats sorting line")
        return False
    
    # Add league_name for logging if needed
    for i, line in enumerate(content):
        if "def get_weekly_stats_by_league(league_id):" in line:
            function_start_index = i
            # Check if league_name is already being set
            league_name_found = False
            for j in range(i, min(i + 30, len(content))):
                if "league_name" in content[j]:
                    league_name_found = True
                    break
            
            if not league_name_found:
                # Find where to insert league_name code
                for j in range(i + 1, min(i + 30, len(content))):
                    if "conn =" in content[j]:
                        # Add code to get league name
                        content.insert(j, "    # Get league name for logging\n")
                        content.insert(j + 1, "    league_name = f'Unknown League {league_id}'\n")
                        content.insert(j + 2, "    try:\n")
                        content.insert(j + 3, "        # Try to get league name from league_config.json\n")
                        content.insert(j + 4, "        with open(os.path.join(script_dir, 'league_config.json'), 'r') as f:\n")
                        content.insert(j + 5, "            league_config = json.load(f)\n")
                        content.insert(j + 6, "            for league in league_config:\n")
                        content.insert(j + 7, "                if league.get('id') == league_id:\n")
                        content.insert(j + 8, "                    league_name = league.get('name', f'League {league_id}')\n")
                        content.insert(j + 9, "                    break\n")
                        content.insert(j + 10, "    except Exception as e:\n")
                        content.insert(j + 11, "        logging.warning(f\"Could not get league name: {e}\")\n")
                        content.insert(j + 12, "\n")
                        league_name_added = True
                        # Update sorting_line_index to account for inserted lines
                        if sorting_line_index > j:
                            sorting_line_index += 13
                        break
                break
    
    # Replace the sorting line and add debugging
    new_sorting_code = [
        "        # Sort by games played (descending) then weekly score (ascending)\n",
        "        stats.sort(key=lambda x: (\n",
        "            # First handle None values (put them at the end)\n",
        "            x['used_scores'] is None or x['weekly_score'] is None,\n",
        "            # Then sort by games played in descending order (negative for descending)\n",
        "            -(x['used_scores'] if x['used_scores'] is not None else 0),\n",
        "            # Then sort by weekly score in ascending order\n",
        "            x['weekly_score'] if x['weekly_score'] is not None else float('inf'),\n",
        "            # Finally sort alphabetically by name for equal scores/games\n",
        "            x['name']\n",
        "        ))\n",
        "        \n",
        f"        logging.info(f\"DEBUG: Weekly stats for {league_name}: {{len(stats)}} items\")\n",
        "        if stats:\n",
        "            logging.info(f\"DEBUG: First weekly stat item: {stats[0]}\")\n"
    ]
    
    # Replace the old sorting line with the new code
    content[sorting_line_index:sorting_line_index + 1] = new_sorting_code
    
    # Write the updated content back
    with open(export_script_path, 'w', encoding='utf-8') as f:
        f.writelines(content)
    
    logging.info(f"Updated weekly stats sorting in {export_script_path}")
    return True

def validate_weekly_scores():
    """Validate and fix weekly scores data accuracy"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get the current week's start date (Monday)
        today = datetime.datetime.now()
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_date = start_of_week.strftime('%Y-%m-%d')
        
        logging.info(f"Validating weekly scores from {start_date}")
        
        # Check data for each league
        cursor.execute("SELECT DISTINCT league_id FROM scores")
        league_ids = [row[0] for row in cursor.fetchall()]
        
        for league_id in league_ids:
            # Check for duplicate scores on the same day
            cursor.execute("""
            SELECT player_name, date(timestamp), COUNT(*)
            FROM scores
            WHERE league_id = ? AND timestamp >= ?
            GROUP BY player_name, date(timestamp)
            HAVING COUNT(*) > 1
            """, (league_id, start_date))
            
            duplicates = cursor.fetchall()
            if duplicates:
                logging.warning(f"Found duplicate scores in league {league_id}:")
                for player, date, count in duplicates:
                    logging.warning(f"  {player} has {count} scores on {date}")
                
                # Fix duplicates by keeping only the best score per day
                for player, date, _ in duplicates:
                    # Find all score IDs for this player on this day
                    cursor.execute("""
                    SELECT id, score FROM scores
                    WHERE player_name = ? AND league_id = ? AND date(timestamp) = ?
                    ORDER BY 
                        CASE 
                            WHEN score = 'X' THEN 7
                            ELSE CAST(score AS INTEGER)
                        END
                    """, (player, league_id, date))
                    
                    score_records = cursor.fetchall()
                    # Keep the first one (best score) and delete the rest
                    if len(score_records) > 1:
                        keep_id = score_records[0][0]
                        delete_ids = [record[0] for record in score_records[1:]]
                        
                        for delete_id in delete_ids:
                            cursor.execute("DELETE FROM scores WHERE id = ?", (delete_id,))
                            logging.info(f"Deleted duplicate score ID {delete_id} for {player} on {date}")
        
        conn.commit()
        logging.info("Weekly scores validation complete")
        return True
    except Exception as e:
        logging.error(f"Error validating weekly scores: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def check_pants_in_pal():
    """Check if Pants is added to PAL league and add if missing"""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if Pants exists in PAL league (league_id=3)
        cursor.execute("SELECT COUNT(*) FROM scores WHERE player_name = 'Pants' AND league_id = 3")
        pants_exists = cursor.fetchone()[0] > 0
        
        if not pants_exists:
            logging.info("Adding Pants to PAL league with placeholder score")
            
            # Get most recent Wordle number
            cursor.execute("SELECT MAX(wordle_num) FROM scores")
            latest_wordle = cursor.fetchone()[0]
            
            # Get timestamp for today
            today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Add a placeholder score for Pants
            cursor.execute("""
            INSERT INTO scores (player_name, score, wordle_num, emoji_pattern, timestamp, league_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """, ('Pants', '-', latest_wordle, None, today, 3))
            
            conn.commit()
            logging.info("Added Pants to PAL league")
            return True
        else:
            logging.info("Pants already exists in PAL league")
            return False
    except Exception as e:
        logging.error(f"Error checking/adding Pants: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def run_export_script():
    """Run the export script to apply all fixes"""
    import subprocess
    logging.info("Running export script to apply all fixes...")
    
    export_script = os.path.join(script_dir, 'export_leaderboard_multi_league.py')
    
    try:
        result = subprocess.run(['python', export_script], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        logging.info("Export completed successfully")
        logging.info(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Export failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False

def main():
    """Main function to run all fixes"""
    logging.info("Starting comprehensive fixes for Wordle League")
    
    # 1. Fix emoji pattern template
    if fix_emoji_pattern_template():
        logging.info("✅ Emoji pattern template fix applied")
    else:
        logging.error("❌ Failed to fix emoji pattern template")
    
    # 2. Fix emoji patterns in database
    if fix_emoji_patterns_in_database():
        logging.info("✅ Emoji patterns in database fixed")
    else:
        logging.info("⚠️ No emoji patterns needed fixing in database")
    
    # 3. Fix weekly stats sorting
    if fix_weekly_stats_sorting():
        logging.info("✅ Weekly stats sorting fix applied")
    else:
        logging.error("❌ Failed to fix weekly stats sorting")
    
    # 4. Validate weekly scores data
    if validate_weekly_scores():
        logging.info("✅ Weekly scores validated")
    else:
        logging.error("❌ Failed to validate weekly scores")
    
    # 5. Check if Pants is added to PAL league
    pants_added = check_pants_in_pal()
    if pants_added:
        logging.info("✅ Added Pants to PAL league")
    else:
        logging.info("⚠️ Pants already in PAL league")
    
    # 6. Run export script to apply all fixes
    if run_export_script():
        logging.info("✅ Export completed successfully")
    else:
        logging.error("❌ Export failed")
    
    logging.info("Comprehensive fixes completed")

if __name__ == "__main__":
    main()
