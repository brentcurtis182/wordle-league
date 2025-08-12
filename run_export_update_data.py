#!/usr/bin/env python3
"""
Script to run the export script while preserving format AND updating data
"""

import os
import shutil
import subprocess
import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_data_export.log"),
        logging.StreamHandler()
    ]
)

def backup_current_files():
    """Back up the current website files before exporting"""
    export_dir = "website_export"
    backup_dir = os.path.join(export_dir, "format_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    try:
        # Create backup directory
        os.makedirs(backup_dir, exist_ok=True)
        
        # Copy index.html to backup
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            shutil.copy2(index_file, os.path.join(backup_dir, "index.html"))
            logging.info(f"Backed up index.html to {backup_dir}")
            
        # Copy CSS files to backup
        css_file = os.path.join(export_dir, "styles.css")
        if os.path.exists(css_file):
            shutil.copy2(css_file, os.path.join(backup_dir, "styles.css"))
            logging.info(f"Backed up styles.css to {backup_dir}")
            
        # Copy JavaScript files to backup
        js_file = os.path.join(export_dir, "script.js")
        if os.path.exists(js_file):
            shutil.copy2(js_file, os.path.join(backup_dir, "script.js"))
            logging.info(f"Backed up script.js to {backup_dir}")
            
        # Make a special backup of index.html for easy recovery
        if os.path.exists(index_file):
            shutil.copy2(index_file, os.path.join(export_dir, "index.html.format_backup"))
            logging.info("Created special backup of index.html for easy recovery")
            
        return True
    except Exception as e:
        logging.error(f"Error backing up files: {e}")
        return False

def run_export_script():
    """Run the export script to update data"""
    try:
        # Run export script
        result = subprocess.run(
            ["python", "export_leaderboard_multi_league.py"],
            capture_output=True,
            text=True,
            check=True
        )
        
        logging.info("Export script completed successfully")
        
        if result.stderr:
            logging.warning(f"Export warnings/errors: {result.stderr}")
            
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Export script failed: {e}")
        logging.error(f"Export error output: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error running export script: {e}")
        return False

def get_latest_wordle_info():
    """Get the latest Wordle number and date from the exported file"""
    export_dir = "website_export"
    index_file = os.path.join(export_dir, "index.html")
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Find the Wordle header
        header = soup.find('h2', string=re.compile(r'Wordle #\d+'))
        if header:
            # Extract Wordle number and date
            match = re.search(r'Wordle #(\d+) - (.+)', header.text)
            if match:
                wordle_number = match.group(1)
                wordle_date = match.group(2)
                logging.info(f"Found latest Wordle info: #{wordle_number} - {wordle_date}")
                return wordle_number, wordle_date
        
        logging.error("Could not find Wordle number and date in exported file")
        return None, None
    except Exception as e:
        logging.error(f"Error getting latest Wordle info: {e}")
        return None, None

def merge_data_preserve_format():
    """Merge the new data into the formatted file"""
    export_dir = "website_export"
    index_file = os.path.join(export_dir, "index.html")
    format_backup = os.path.join(export_dir, "index.html.format_backup")
    new_data_file = os.path.join(export_dir, "index.html.new_data")
    
    try:
        # Create a temporary copy of the newly exported file
        shutil.copy2(index_file, new_data_file)
        
        # Restore the formatted version from backup
        shutil.copy2(format_backup, index_file)
        
        # Get Wordle number and date from the new data
        wordle_number, wordle_date = get_latest_wordle_info()
        if not wordle_number or not wordle_date:
            logging.error("Failed to get Wordle info from new data, cannot update")
            return False
            
        # Read the formatted file
        with open(index_file, 'r', encoding='utf-8') as f:
            formatted_content = f.read()
            
        # Update the Wordle number and date
        formatted_content = re.sub(
            r'(Wordle #)\d+( - ).+?(?=</h2>)',
            f'\\1{wordle_number}\\2{wordle_date}',
            formatted_content
        )
        
        # Write the updated content back to the file
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
            
        logging.info(f"Updated Wordle number to #{wordle_number} and date to {wordle_date}")
        
        # Parse the content to update player data
        with open(index_file, 'r', encoding='utf-8') as f:
            formatted_soup = BeautifulSoup(formatted_content, 'html.parser')
            
        with open(new_data_file, 'r', encoding='utf-8') as f:
            new_soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Extract player data from the new data file
        new_player_data = {}
        new_latest_tab = new_soup.find('div', {'id': 'latest'})
        if new_latest_tab:
            for card in new_latest_tab.find_all('div', class_='score-card'):
                player_name_div = card.find('div', class_='player-name')
                if player_name_div:
                    player_name = player_name_div.text.strip()
                    # Get score
                    score_span = card.find('span', class_=re.compile(r'score-'))
                    score = score_span.text if score_span else None
                    # Get emoji pattern
                    emoji_pattern_div = card.find('div', class_='emoji-pattern')
                    emoji_pattern = emoji_pattern_div if emoji_pattern_div else None
                    
                    new_player_data[player_name] = {
                        'score': score,
                        'emoji_pattern': emoji_pattern
                    }
        
        # Update the player cards in the formatted file
        formatted_latest_tab = formatted_soup.find('div', {'id': 'latest'})
        if formatted_latest_tab:
            # Clear existing score cards
            for card in formatted_latest_tab.find_all('div', class_='score-card'):
                card.decompose()
                
            # Add new score cards based on new data
            for player_name, data in new_player_data.items():
                # Create new score card with proper formatting
                card = formatted_soup.new_tag('div', attrs={'class': 'score-card'})
                
                # Player info section
                player_info = formatted_soup.new_tag('div', attrs={'class': 'player-info'})
                
                # Player name
                name_div = formatted_soup.new_tag('div', attrs={'class': 'player-name'})
                name_div.string = player_name
                player_info.append(name_div)
                
                # Player score
                score_div = formatted_soup.new_tag('div', attrs={'class': 'player-score'})
                if data['score']:
                    score_match = re.match(r'(\d+|X)/6', data['score'])
                    if score_match:
                        score_value = score_match.group(1)
                        score_class = f"score-{score_value}"
                        score_span = formatted_soup.new_tag('span', attrs={'class': score_class})
                        score_span.string = data['score']
                        score_div.append(score_span)
                player_info.append(score_div)
                card.append(player_info)
                
                # Emoji pattern if available
                if data['emoji_pattern']:
                    emoji_container = formatted_soup.new_tag('div', attrs={'class': 'emoji-container'})
                    emoji_container.append(data['emoji_pattern'])
                    card.append(emoji_container)
                
                formatted_latest_tab.append(card)
                
        # Get weekly stats from new data
        new_weekly_tab = new_soup.find('div', {'id': 'weekly'})
        formatted_weekly_tab = formatted_soup.find('div', {'id': 'weekly'})
        
        if new_weekly_tab and formatted_weekly_tab:
            new_weekly_table = new_weekly_tab.find('table')
            formatted_weekly_table = formatted_weekly_tab.find('table')
            
            if new_weekly_table and formatted_weekly_table:
                new_weekly_tbody = new_weekly_table.find('tbody')
                formatted_weekly_tbody = formatted_weekly_table.find('tbody')
                
                if new_weekly_tbody and formatted_weekly_tbody:
                    # Clear existing rows
                    formatted_weekly_tbody.clear()
                    
                    # Copy new rows to formatted table
                    for row in new_weekly_tbody.find_all('tr'):
                        formatted_weekly_tbody.append(row)
        
        # Get all-time stats from new data
        new_stats_tab = new_soup.find('div', {'id': 'stats'})
        formatted_stats_tab = formatted_soup.find('div', {'id': 'stats'})
        
        if new_stats_tab and formatted_stats_tab:
            new_stats_tables = new_stats_tab.find_all('table')
            formatted_stats_tables = formatted_stats_tab.find_all('table')
            
            if new_stats_tables and formatted_stats_tables and len(new_stats_tables) > 0 and len(formatted_stats_tables) > 0:
                new_stats_table = new_stats_tables[0]
                formatted_stats_table = formatted_stats_tables[0]
                
                new_stats_tbody = new_stats_table.find('tbody')
                formatted_stats_tbody = formatted_stats_table.find('tbody')
                
                if new_stats_tbody and formatted_stats_tbody:
                    # Clear existing rows
                    formatted_stats_tbody.clear()
                    
                    # Copy new rows to formatted table
                    for row in new_stats_tbody.find_all('tr'):
                        formatted_stats_tbody.append(row)
        
        # Write the updated formatted content back to the file
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(str(formatted_soup))
            
        logging.info("Successfully merged new data into formatted file")
        return True
    except Exception as e:
        logging.error(f"Error merging data while preserving format: {e}")
        return False

def main():
    logging.info("Starting export with data update and format preservation...")
    
    # Back up current files
    logging.info("Backing up current files...")
    if not backup_current_files():
        logging.error("Failed to back up files, aborting")
        return False
    
    # Run the export script
    logging.info("Running export script...")
    if not run_export_script():
        logging.error("Export script failed")
        return False
    
    # Merge data and preserve format
    logging.info("Merging data while preserving format...")
    if not merge_data_preserve_format():
        logging.error("Failed to merge data and preserve format")
        return False
    
    logging.info("Export with data update and format preservation completed successfully")
    print("Export completed with data update and format preservation!")
    print("The website files have been updated with current data through today while maintaining the nice formatting.")
    return True

if __name__ == "__main__":
    main()
