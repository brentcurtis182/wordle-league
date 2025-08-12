#!/usr/bin/env python3
"""
Export Scores with Tab Preservation

This script:
1. Makes a backup of the current tabbed HTML
2. Runs the regular export script to get fresh score data
3. Extracts just the scores from the fresh export
4. Places those scores into the tabbed HTML structure
5. Restores the proper tab structure across all leagues
"""

import os
import sys
import re
import logging
import shutil
import subprocess
import datetime
import json
import time
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    filename='export_scores_preserve_tabs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Constants
EXPORT_DIR = 'website_export'
BACKUP_DIR = r"C:\Wordle-League\website_export_backup_Aug10_2025_1148pm_with_season_20250810_234948"
EXPORT_SCRIPT = 'export_leaderboard_multi_league.py'
LEAGUES = ['', 'gang', 'pal', 'party', 'vball']  # '' is the main league

def backup_current_files():
    """Create a backup of the current website files"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = f"website_export_backup_{timestamp}"
    
    try:
        if os.path.exists(EXPORT_DIR):
            shutil.copytree(EXPORT_DIR, backup_folder)
            logging.info(f"Backed up current website files to {backup_folder}")
            return backup_folder
        else:
            logging.error(f"Export directory {EXPORT_DIR} does not exist")
            return None
    except Exception as e:
        logging.error(f"Failed to create backup: {str(e)}")
        return None

def run_export_script():
    """Run the regular export script to get fresh scores data"""
    try:
        logging.info(f"Running export script: {EXPORT_SCRIPT}")
        result = subprocess.run(
            ['python', EXPORT_SCRIPT],
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            logging.info("Export script completed successfully")
            return True
        else:
            logging.error(f"Export script failed with code {result.returncode}")
            logging.error(f"Error output: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Failed to run export script: {str(e)}")
        return False

def extract_scores_from_export(html_content):
    """Extract latest scores from the exported HTML"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the table with player scores
        scores_table = soup.find('table')
        if not scores_table:
            logging.error("Could not find scores table in exported HTML")
            return None
        
        # Extract player names and scores
        scores_data = []
        rows = scores_table.find_all('tr')[1:]  # Skip header row
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                player_name = cells[0].text.strip()
                score = cells[1].text.strip()
                scores_data.append({
                    'name': player_name,
                    'score': score if score != '-' else None
                })
        
        # Extract Wordle number and date
        title_match = re.search(r'Wordle #(\d+)', html_content)
        if title_match:
            wordle_number = title_match.group(1)
        else:
            wordle_number = str(calculate_current_wordle())
        
        date_match = re.search(r'(\w+ \d+, \d{4})', html_content)
        if date_match:
            wordle_date = date_match.group(1)
        else:
            wordle_date = datetime.datetime.now().strftime('%B %d, %Y')
            
        return {
            'wordle_number': wordle_number,
            'wordle_date': wordle_date,
            'scores': scores_data
        }
    except Exception as e:
        logging.error(f"Error extracting scores from export: {str(e)}")
        return None

def update_scores_in_tabbed_html(tabbed_html, scores_data):
    """Update only the scores in the tabbed HTML structure"""
    try:
        soup = BeautifulSoup(tabbed_html, 'html.parser')
        
        # Find the "Latest Scores" tab content
        latest_tab = soup.select_one('.tab-content#latest')
        if not latest_tab:
            logging.error("Could not find Latest Scores tab in template HTML")
            return None
            
        # Update the Wordle number and date in the heading
        heading = latest_tab.find('h2')
        if heading:
            heading.string = f"Wordle #{scores_data['wordle_number']} - {scores_data['wordle_date']}"
        
        # Remove existing score cards
        for card in latest_tab.select('.score-card'):
            card.decompose()
            
        # Create new score cards for each player
        for player_data in scores_data['scores']:
            player_name = player_data['name']
            score = player_data['score'] if player_data['score'] else "-"
            
            # Create the HTML structure for a score card
            card_html = f"""
            <div class="score-card">
              <div class="player-info">
                <div class="player-name">{player_name}</div>
                <div class="player-score"><span class="score-{score[0] if score.isdigit() else '0'}">{score}</span></div>
              </div>
              <div class="emoji-container">
                <div class="emoji-pattern"></div>
              </div>
            </div>
            """
            card_soup = BeautifulSoup(card_html, 'html.parser')
            latest_tab.append(card_soup)
        
        return str(soup)
    except Exception as e:
        logging.error(f"Error updating scores in tabbed HTML: {str(e)}")
        return None

def calculate_current_wordle():
    """Calculate the current Wordle number based on the start date"""
    start_date = datetime.datetime(2021, 6, 19)  # Wordle #0
    today = datetime.datetime.now()
    days_since_start = (today - start_date).days
    return days_since_start

def update_league_file(league_path):
    """Update scores for a specific league file while preserving tab structure"""
    league_name = os.path.basename(os.path.dirname(league_path)) if os.path.dirname(league_path) else "Wordle Warriorz"
    
    logging.info(f"Updating {league_name} scores while preserving tab structure")
    
    # Define file paths
    export_path = os.path.join(EXPORT_DIR, os.path.basename(os.path.dirname(league_path)) if os.path.dirname(league_path) else "", "index.html")
    template_path = os.path.join(BACKUP_DIR, os.path.basename(os.path.dirname(league_path)) if os.path.dirname(league_path) else "", "index.html")
    
    # Check if files exist
    if not os.path.exists(export_path):
        logging.error(f"Exported file does not exist: {export_path}")
        return False
        
    if not os.path.exists(template_path):
        logging.error(f"Template file does not exist: {template_path}")
        return False
    
    # Read the exported file with fresh scores
    try:
        with open(export_path, 'r', encoding='utf-8') as f:
            export_html = f.read()
    except Exception as e:
        logging.error(f"Failed to read export file: {str(e)}")
        return False
    
    # Read the template with tab structure
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()
    except Exception as e:
        logging.error(f"Failed to read template file: {str(e)}")
        return False
    
    # Extract scores data from the exported HTML
    scores_data = extract_scores_from_export(export_html)
    if not scores_data:
        logging.error("Failed to extract scores data from export")
        return False
    
    # Update scores in the tabbed HTML
    updated_html = update_scores_in_tabbed_html(template_html, scores_data)
    if not updated_html:
        logging.error("Failed to update scores in tabbed HTML")
        return False
    
    # Write the updated HTML back to the export directory
    try:
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        logging.info(f"Successfully updated {league_name} with preserved tabs")
        return True
    except Exception as e:
        logging.error(f"Failed to write updated HTML: {str(e)}")
        return False

def update_all_leagues():
    """Update scores for all leagues while preserving tab structure"""
    success_count = 0
    failure_count = 0
    
    for league in LEAGUES:
        league_dir = os.path.join(EXPORT_DIR, league)
        index_path = os.path.join(league_dir, "index.html")
        
        if league == '':
            index_path = os.path.join(EXPORT_DIR, "index.html")
            league_name = "Wordle Warriorz"
        else:
            league_name = f"Wordle {league.capitalize()}"
        
        if update_league_file(index_path):
            success_count += 1
            print(f"[SUCCESS] Updated {league_name} with preserved tab structure")
        else:
            failure_count += 1
            print(f"[FAILED] Failed to update {league_name}")
    
    return success_count, failure_count

def main():
    print("Starting Wordle League score update with tab preservation...")
    logging.info("Starting score update with tab preservation")
    
    # Step 1: Backup current files
    backup_folder = backup_current_files()
    if not backup_folder:
        print("[ERROR] Failed to backup current files. Aborting.")
        return
    
    # Step 2: Run the export script to get fresh scores
    if not run_export_script():
        print("[ERROR] Failed to run export script. Aborting.")
        return
    
    # Step 3: Update all leagues with preserved tabs
    success_count, failure_count = update_all_leagues()
    
    # Report summary
    print(f"\nUpdate completed with {success_count} successful updates and {failure_count} failures")
    logging.info(f"Update completed with {success_count} successful updates and {failure_count} failures")
    
    if failure_count > 0:
        print("Some leagues failed to update. Check the log file for details.")
        print("Running restore script to revert to last working version...")
        
        # Run restore script if any failures occurred
        try:
            result = subprocess.run(
                ['python', 'restore_last_night_backup.py', BACKUP_DIR],
                capture_output=True, 
                text=True
            )
            if result.returncode == 0:
                print("Successfully restored from backup.")
            else:
                print(f"Failed to restore from backup: {result.stderr}")
        except Exception as e:
            print(f"Error running restore script: {str(e)}")
    else:
        print("All leagues updated successfully with preserved tabs!")

if __name__ == "__main__":
    main()
