#!/usr/bin/env python3
"""
Fix Weekly Stats Sorting in Multi-League Export

This script modifies the export_leaderboard_multi_league.py file to correctly sort
weekly stats by number of games played (descending) and then by score (ascending).
"""

import os
import re
import shutil
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

def backup_file(file_path):
    """Create a backup of the file with timestamp"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{file_path}.bak_{timestamp}"
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backup created: {backup_path}")
    return backup_path

def fix_weekly_stats_sorting():
    """Fix the weekly stats sorting logic in export_leaderboard_multi_league.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(script_dir, 'export_leaderboard_multi_league.py')
    
    if not os.path.exists(target_file):
        logging.error(f"Target file not found: {target_file}")
        return False
    
    # Create backup
    backup_file(target_file)
    
    # Read file content
    with open(target_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the sorting logic pattern
    old_sorting_pattern = r"# Sort by weekly score \(lower is better\)\s+stats\.sort\(key=lambda x: \(x\['weekly_score'\] is None, x\['weekly_score'\] if x\['weekly_score'\] is not None else float\('inf'\)\)\)"
    
    # New sorting logic that prioritizes games played (descending) then score (ascending)
    new_sorting_code = """# Sort by games played (descending) then weekly score (ascending)
        stats.sort(key=lambda x: (
            # First handle None values (put them at the end)
            x['used_scores'] is None or x['weekly_score'] is None,
            # Then sort by games played in descending order (negative for descending)
            -(x['used_scores'] if x['used_scores'] is not None else 0),
            # Then sort by weekly score in ascending order
            x['weekly_score'] if x['weekly_score'] is not None else float('inf'),
            # Finally sort alphabetically by name for equal scores/games
            x['name']
        ))
        
        logging.info(f"DEBUG: Weekly stats for {league_name}: {len(stats)} items")
        if stats:
            logging.info(f"DEBUG: First weekly stat item: {stats[0]}")"""
    
    # Replace the sorting logic
    new_content = re.sub(old_sorting_pattern, new_sorting_code, content)
    
    # Check if the pattern was found and replaced
    if new_content == content:
        logging.warning("Sorting pattern not found. Trying alternative approach...")
        
        # Try to find the line with just the sort function and replace it
        sort_line_pattern = r"stats\.sort\(key=lambda x: \(x\['weekly_score'\] is None, x\['weekly_score'\] if x\['weekly_score'\] is not None else float\('inf'\)\)\)"
        
        new_sort_line = """stats.sort(key=lambda x: (
            # First handle None values (put them at the end)
            x['used_scores'] is None or x['weekly_score'] is None,
            # Then sort by games played in descending order (negative for descending)
            -(x['used_scores'] if x['used_scores'] is not None else 0),
            # Then sort by weekly score in ascending order
            x['weekly_score'] if x['weekly_score'] is not None else float('inf'),
            # Finally sort alphabetically by name for equal scores/games
            x['name']
        ))
        
        logging.info(f"DEBUG: Weekly stats for {league_name}: {len(stats)} items")
        if stats:
            logging.info(f"DEBUG: First weekly stat item: {stats[0]}")"""
        
        new_content = re.sub(sort_line_pattern, new_sort_line, content)
        
        # If still no match, look for just the stats.sort part
        if new_content == content:
            logging.warning("Sort function pattern not found. Trying with basic pattern...")
            basic_pattern = r"stats\.sort\(.*?\)"
            
            new_content = re.sub(basic_pattern, """stats.sort(key=lambda x: (
                # First handle None values (put them at the end)
                x['used_scores'] is None or x['weekly_score'] is None,
                # Then sort by games played in descending order (negative for descending)
                -(x['used_scores'] if x['used_scores'] is not None else 0),
                # Then sort by weekly score in ascending order
                x['weekly_score'] if x['weekly_score'] is not None else float('inf'),
                # Finally sort alphabetically by name for equal scores/games
                x['name']
            ))""", content)
            
            # Add debug logging if it worked
            if new_content != content:
                new_content = new_content.replace("""x['name']
            ))""", """x['name']
            ))
            
            logging.info(f"DEBUG: Weekly stats for {league_name}: {len(stats)} items")
            if stats:
                logging.info(f"DEBUG: First weekly stat item: {stats[0]}")""")
    
    # Check if any replacement was made
    if new_content == content:
        logging.error("Failed to find and replace the weekly stats sorting logic")
        return False
    
    # Write the updated content back to file
    with open(target_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    logging.info(f"Successfully updated weekly stats sorting logic in {target_file}")
    
    # Also check for "league_name" variable
    if "league_name" not in content:
        # We need to add the league name variable for our debug logging to work
        with open(target_file, 'r', encoding='utf-8') as f:
            content = f.readlines()
        
        # Find the line with the get_weekly_stats_by_league function definition
        for i, line in enumerate(content):
            if "def get_weekly_stats_by_league(league_id):" in line:
                # Insert league_name extraction after the function definition
                for j in range(i+1, len(content)):
                    if "conn =" in content[j]:
                        # Add code to get league name
                        content.insert(j, "    # Get league name for logging\n")
                        content.insert(j+1, "    league_name = f'Unknown League {league_id}'\n")
                        content.insert(j+2, "    try:\n")
                        content.insert(j+3, "        # Try to get league name from league_config.json\n")
                        content.insert(j+4, "        with open(os.path.join(script_dir, 'league_config.json'), 'r') as f:\n")
                        content.insert(j+5, "            league_config = json.load(f)\n")
                        content.insert(j+6, "            for league in league_config:\n")
                        content.insert(j+7, "                if league.get('id') == league_id:\n")
                        content.insert(j+8, "                    league_name = league.get('name', f'League {league_id}')\n")
                        content.insert(j+9, "                    break\n")
                        content.insert(j+10, "    except Exception as e:\n")
                        content.insert(j+11, "        logging.warning(f\"Could not get league name: {e}\")\n")
                        content.insert(j+12, "\n")
                        break
                break
        
        # Write the updated content back to file
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(content)
        
        logging.info("Added league_name variable for debug logging")
    
    return True

def run_export_after_fix():
    """Run the export script to apply the fix"""
    import subprocess
    logging.info("Running export script to apply weekly stats sorting fix...")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
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
    """Main function"""
    logging.info("Starting weekly stats sorting fix")
    
    if fix_weekly_stats_sorting():
        logging.info("Weekly stats sorting logic updated successfully")
        
        # Run the export script to apply the fix
        if run_export_after_fix():
            logging.info("Fix applied and website exported successfully")
        else:
            logging.error("Failed to run export after fix")
    else:
        logging.error("Failed to update weekly stats sorting logic")

if __name__ == "__main__":
    main()
