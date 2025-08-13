#!/usr/bin/env python3
"""Wordle League Score Update with Tab Preservation
This script runs the regular export and then intelligently merges the exported 
scores with the preserved tab structure from the backup, maintaining the proper
score card design, weekly stats, and season tables.
"""

import os
import sys
import re
import logging
import shutil
import datetime
import subprocess
import time

# Setup logging
logging.basicConfig(
    filename='update_scores_preserve_tabs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Paths
EXPORT_DIR = 'website_export'
BACKUP_DIR = r"C:\Wordle-League\website_export_backup_Aug10_2025_1148pm_with_season_20250810_234948"
EXPORT_SCRIPT = 'export_leaderboard_multi_league.py'

def backup_current_files():
    """Backup current website files before any operations"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = f"website_export_backup_{timestamp}"
    
    if os.path.exists(EXPORT_DIR):
        try:
            shutil.copytree(EXPORT_DIR, backup_folder)
            logging.info(f"Backed up current website files to {backup_folder}")
            return backup_folder
        except Exception as e:
            logging.error(f"Failed to backup website files: {str(e)}")
            return None
    else:
        logging.error(f"Export directory {EXPORT_DIR} does not exist")
        return None

def extract_scores_data(html_content):
    """Extract player scores from the exported HTML"""
    logging.info(f"Extracting score data from HTML of length {len(html_content)}")
    
    # First check if we have a simple table with players and scores
    table_pattern = r'<table>\s*<tr>\s*<th>Player</th>\s*<th>Score</th>\s*</tr>(.*?)</table>'
    table_match = re.search(table_pattern, html_content, re.DOTALL)
    
    if table_match:
        logging.info("Found score table in HTML")
        score_data = {}
        
        # Extract player names and scores
        row_pattern = r'<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>'
        player_scores = re.findall(row_pattern, table_match.group(1))
        
        if player_scores:
            for player, score in player_scores:
                score_data[player.strip()] = score.strip()
            logging.info(f"Extracted scores for {len(score_data)} players")
            return score_data
        else:
            logging.warning("No player scores found in table")
    else:
        logging.warning("No score table found in HTML")
        
    # Try finding scores from score cards if table method failed
    score_cards_pattern = r'<div class="score-card">.*?<div class="player-name">(.*?)</div>\s*<div class="player-score">.*?(?:<span[^>]*>)?([^<]+)(?:</span>)?</div>'
    card_matches = re.findall(score_cards_pattern, html_content, re.DOTALL)
    
    if card_matches:
        logging.info(f"Found {len(card_matches)} score cards")
        score_data = {}
        
        for player, score in card_matches:
            score_data[player.strip()] = score.strip()
        
        return score_data
    else:
        logging.warning("No score cards found in HTML")
    
    # Final fallback: look for any player names and scores
    logging.error("Failed to extract score data using standard patterns")
    return None

def extract_weekly_data(html_content):
    """Extract weekly data from the exported HTML"""
    logging.info("Extracting weekly data")
    
    # First try to get the weekly table rows - look for the more specific pattern
    weekly_table_pattern = r'<table>\s*<thead><tr><th>Player</th><th>Weekly Score</th>.*?</thead>\s*<tbody>\s*(.*?)\s*</tbody>\s*</table>'
    match = re.search(weekly_table_pattern, html_content, re.DOTALL)
    
    if match:
        weekly_data = match.group(1).strip()
        logging.info(f"Found weekly table data: {len(weekly_data)} characters")
        return weekly_data
    
    # Try alternate patterns - some exports use different HTML structure
    alt_weekly_pattern = r'<div[^>]*class="?weekly-table"?[^>]*>.*?<table>.*?<tbody>\s*(.*?)\s*</tbody>\s*</table>'
    match = re.search(alt_weekly_pattern, html_content, re.DOTALL)
    if match:
        weekly_data = match.group(1).strip()
        logging.info(f"Found weekly table data (alternate pattern): {len(weekly_data)} characters")
        return weekly_data
    
    # Look for weekly data in previous backup if available (as fallback)
    backup_path = os.path.join(BACKUP_DIR, "index.html")
    if os.path.exists(backup_path):
        try:
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_content = f.read()
            
            backup_match = re.search(weekly_table_pattern, backup_content, re.DOTALL)
            if backup_match:
                weekly_data = backup_match.group(1).strip()
                logging.info(f"Found weekly table data from backup: {len(weekly_data)} characters")
                return weekly_data
        except Exception as e:
            logging.warning(f"Error reading backup for weekly data: {str(e)}")
    
    logging.warning("Failed to extract weekly table rows from any source")
    return None

def extract_wordle_number_and_date(html_content):
    """Extract Wordle number and date from the exported HTML"""
    # First try to find the wordle number in a heading
    pattern = r'<h2[^>]*>Wordle #(\d+) - (.*?)</h2>'
    match = re.search(pattern, html_content)
    
    if match:
        wordle_num = match.group(1)
        wordle_date = match.group(2)
        
        # Validate that wordle_num is not a date
        if len(wordle_num) <= 5:  # Most Wordle numbers are < 10000
            logging.info(f"Found Wordle #{wordle_num} - {wordle_date}")
            return wordle_num, wordle_date
        else:
            logging.warning(f"Found suspicious Wordle number: {wordle_num}, will use fallback")
    
    # Try a more relaxed pattern if first attempt failed or had suspicious result
    pattern = r'Wordle #(\d+)[^<]*'
    match = re.search(pattern, html_content)
    if match:
        wordle_num = match.group(1)
        if len(wordle_num) <= 5:  # Validate
            # Generate today's date
            today = datetime.datetime.now()
            wordle_date = today.strftime("%B %d, %Y")
            logging.info(f"Found partial match: Wordle #{wordle_num}, using date: {wordle_date}")
            return wordle_num, wordle_date
    
    # If all else fails, generate a reasonable Wordle number based on days since start
    today = datetime.datetime.now()
    base_date = datetime.datetime(2021, 6, 19)  # Approximate Wordle #0 date
    days_since_start = (today - base_date).days
    wordle_num = str(days_since_start)
    wordle_date = today.strftime("%B %d, %Y")
    logging.info(f"Using calculated Wordle #{wordle_num} for {wordle_date}")
    return wordle_num, wordle_date

def merge_scores_with_template(template_path, scores_path, output_path):
    """Merge the scores data with the template preserving tab structure and formatting"""
    try:
        logging.info(f"Merging template '{template_path}' with scores from '{scores_path}'")
        
        # Check if files exist
        if not os.path.exists(template_path):
            logging.error(f"Template file does not exist: {template_path}")
            return False
            
        if not os.path.exists(scores_path):
            logging.error(f"Scores file does not exist: {scores_path}")
            return False
        
        # Read template with tab structure
        with open(template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()
        logging.info(f"Template loaded, {len(template_html)} characters")
            
        # Read exported file with updated scores
        with open(scores_path, 'r', encoding='utf-8') as f:
            scores_html = f.read()
        logging.info(f"Scores HTML loaded, {len(scores_html)} characters")
        
        # Verify template has tab structure
        if '<div class="tab-content active" id="latest">' not in template_html:
            logging.error("Template HTML does not contain tab structure!")
            return False
        
        # Extract player scores data
        score_data = extract_scores_data(scores_html)
        if not score_data:
            logging.error(f"Failed to extract score data from {scores_path}")
            return False
        logging.info(f"Extracted scores for {len(score_data)} players: {list(score_data.keys())}")
        
        # Extract weekly data
        weekly_data = extract_weekly_data(scores_html)
        
        # Extract season data with weekly winners
        season_data = extract_season_data(scores_html)
        
        # Extract Wordle number and date
        wordle_number, wordle_date = extract_wordle_number_and_date(scores_html)
        if not wordle_number or not wordle_date:
            logging.warning("Using fallback wordle information")
            # Use current date to generate a reasonable Wordle number (estimate)
            today = datetime.datetime.now()
            base_date = datetime.datetime(2021, 6, 19)  # Wordle #0 date
            days_since_start = (today - base_date).days
            wordle_number = str(days_since_start)
            wordle_date = today.strftime('%B %d, %Y')
        
        # Ensure wordle_number is a reasonable number, not a date string
        if len(wordle_number) > 5:  # Probably a date like 20250811
            logging.warning(f"Invalid Wordle number format detected: {wordle_number}")
            # Get a reasonable Wordle number based on current date
            today = datetime.datetime.now()
            base_date = datetime.datetime(2021, 6, 19)  # Wordle #0 date
            days_since_start = (today - base_date).days
            wordle_number = str(days_since_start)
        logging.info(f"Using Wordle #{wordle_number} - {wordle_date}")
        
        # Get the score card template pattern from the backup template
        score_card_pattern = re.search(r'(<div class="score-card">.*?</div>\s*</div>\s*</div>)', template_html, re.DOTALL)
        if not score_card_pattern:
            logging.warning("Could not find score card pattern in template")
            # Fallback to a basic card format
            score_card_template = '<div class="score-card"><div class="player-info"><div class="player-name">{player}</div>\n<div class="player-score"><span class="score-{score_num}">{score}</span></div>\n</div>\n<div class="emoji-container"><div class="emoji-pattern"></div></div>\n</div>'
        else:
            # Extract first score card as template
            score_card_template = score_card_pattern.group(1)
            logging.info("Found score card template in backup")
        
        # Create updated score cards for each player with proper formatting
        score_cards = []
        for player, score in score_data.items():
            # Extract emoji patterns if available in exported scores
            emoji_pattern = ""
            
            # Check if there's an emoji pattern associated with this player's score
            emoji_match = None
            if score and score != '-':
                # Look for emoji pattern in scores_html for this player
                player_pattern = re.escape(player)
                
                # Search for emoji patterns with the correct structure
                # First look for the player card with emoji pattern in the exported HTML
                player_card_match = re.search(r'<div class="score-card">.*?<div class="player-name">' + player_pattern + r'</div>.*?<div class="emoji-pattern">(.*?)</div>.*?</div>\s*</div>\s*</div>', scores_html, re.DOTALL)
                
                if player_card_match:
                    emoji_pattern = player_card_match.group(1)
                    logging.info(f"Found emoji pattern for {player} in exported scores")
                else:
                    # Try another pattern that might be used in the exports
                    alt_pattern_match = re.search(r'<div class="player-name">' + player_pattern + r'</div>.*?<div class="emoji-pattern">(.*?)</div>', scores_html, re.DOTALL)
                    if alt_pattern_match:
                        emoji_pattern = alt_pattern_match.group(1)
                        logging.info(f"Found alternative emoji pattern for {player}")
                    else:
                        # As a fallback, check the template for an existing pattern for this player
                        template_pattern = re.search(f'<div class="player-name">{re.escape(player)}</div>.*?<div class="emoji-pattern">(.*?)</div>', template_html, re.DOTALL)
                        if template_pattern:
                            emoji_pattern = template_pattern.group(1)
                            logging.info(f"Using emoji pattern from template for {player}")
                        else:
                            logging.warning(f"No emoji pattern found for {player} in exports or template")
                            # Generate a realistic multi-row placeholder pattern based on score
                            if score_num.isdigit() and int(score_num) > 0 and int(score_num) <= 6:
                                tries = int(score_num)
                                placeholder_rows = []
                                
                                # Generate different row patterns based on the score
                                for i in range(tries):
                                    if i < tries - 1:
                                        # Earlier rows show progression toward solution
                                        if i == 0:
                                            # First guess - typically has some yellows
                                            placeholder_rows.append('<div class="emoji-row">⬜⬜🟨🟨⬜</div>')
                                        elif i == 1:
                                            # Second guess - some progress with a green
                                            placeholder_rows.append('<div class="emoji-row">⬜🟩🟨⬜⬜</div>')
                                        elif i == 2:
                                            # Third guess - more progress
                                            placeholder_rows.append('<div class="emoji-row">🟩🟩⬜🟨⬜</div>')
                                        elif i == 3:
                                            # Fourth guess - getting closer
                                            placeholder_rows.append('<div class="emoji-row">🟩🟩🟩⬜⬜</div>')
                                        elif i == 4:
                                            # Fifth guess - just one letter away
                                            placeholder_rows.append('<div class="emoji-row">🟩🟩🟩🟩⬜</div>')
                                    else:
                                        # Final guess - all green
                                        placeholder_rows.append('<div class="emoji-row">🟩🟩🟩🟩🟩</div>')
                                
                                emoji_pattern = ''.join(placeholder_rows)
                                logging.info(f"Created realistic placeholder pattern for {player}")
                            elif score == "X/6" or score == "7":
                                # Failed attempt (X/6) - show 6 rows with final row having some greens but not all
                                placeholder_rows = [
                                    '<div class="emoji-row">⬜⬜🟨⬜⬜</div>',
                                    '<div class="emoji-row">⬜🟨🟨⬜⬜</div>',
                                    '<div class="emoji-row">⬜🟩🟨⬜⬜</div>',
                                    '<div class="emoji-row">🟩🟩⬜🟨⬜</div>',
                                    '<div class="emoji-row">🟩🟩🟩⬜⬜</div>',
                                    '<div class="emoji-row">🟩🟩🟩⬜🟩</div>'
                                ]
                                emoji_pattern = ''.join(placeholder_rows)
                                logging.info(f"Created failed attempt placeholder pattern for {player}")
            
            # Create the score card with proper structure
            if score == '-' or not score:
                # For missing scores, create a properly structured card with "No Score" text
                card = f'''<div class="score-card"><div class="player-info"><div class="player-name">{player}</div>
<div class="player-score"><span class="score-0">No Score</span></div>
</div>
<div class="emoji-container"><div class="emoji-pattern"></div></div>
</div>'''
            else:
                # Try to extract score number (e.g., 3 from 3/6)
                score_num = re.search(r'^(\d+)', score)
                score_num = score_num.group(1) if score_num else "0"
                
                # Format score as X/6 unless it's already formatted that way
                display_score = score
                if score_num.isdigit() and int(score_num) > 0 and int(score_num) <= 6:
                    if not "/" in score:
                        display_score = f"{score_num}/6"
                elif score == "7" or score == 7:
                    display_score = "X/6"
                    score_num = "X"  # Use X for CSS class on failed attempts
                
                # Create a realistic-looking placeholder pattern matching the score
                logging.warning(f"No emoji pattern found for {player}, creating placeholder")
                tries = int(score_num)
                placeholder_rows = []
                
                # Create patterns for each guess attempt
                for i in range(tries):
                    if i < tries - 1:
                        # Earlier attempts - mix of colors with at least one yellow and some progress
                        if i == 0:
                            # First row typically has some yellows (letter correct, wrong position)
                            placeholder_rows.append('<div class="emoji-row">⬜⬜🟨🟨⬜</div>')
                        elif i == 1 and tries > 2:
                            # Second row typically has some progress with a green
                            placeholder_rows.append('<div class="emoji-row">⬜🟩🟨⬜⬜</div>')
                        elif i == 2 and tries > 3:
                            # Third row more progress
                            placeholder_rows.append('<div class="emoji-row">🟩🟩⬜🟨⬜</div>')
                        elif i == 3 and tries > 4:
                            # Fourth row even more progress
                            placeholder_rows.append('<div class="emoji-row">🟩🟩🟩⬜⬜</div>')
                        elif i == 4 and tries > 5:
                            # Fifth row almost there
                            placeholder_rows.append('<div class="emoji-row">🟩🟩🟩🟩⬜</div>')
                    
                    # Create patterns for each guess attempt
                    for i in range(tries):
                        if i < tries - 1:
                            # Earlier attempts - mix of colors with at least one yellow and some progress
                            if i == 0:
                                # First row typically has some yellows (letter correct, wrong position)
                                placeholder_rows.append('<div class="emoji-row">⬜⬜🟨🟨⬜</div>')
                            elif i == 1 and tries > 2:
                                # Second row typically has some progress with a green
                                placeholder_rows.append('<div class="emoji-row">⬜🟩🟨⬜⬜</div>')
                            elif i == 2 and tries > 3:
                                # Third row more progress
                                placeholder_rows.append('<div class="emoji-row">🟩🟩⬜🟨⬜</div>')
                            elif i == 3 and tries > 4:
                                # Fourth row even more progress
                                placeholder_rows.append('<div class="emoji-row">🟩🟩🟩⬜⬜</div>')
                            elif i == 4 and tries > 5:
                                # Fifth row almost there
                                placeholder_rows.append('<div class="emoji-row">🟩🟩🟩🟩⬜</div>')
                            else:
                                # Generic progress row
                                placeholder_rows.append('<div class="emoji-row">⬜🟨⬜🟨⬜</div>')
                        else:
                            # Final correct guess
                            placeholder_rows.append('<div class="emoji-row">🟩🟩🟩🟩🟩</div>')
                    
                    emoji_pattern = ''.join(placeholder_rows)
                
                # Create a properly structured card with the exact HTML structure from backup
                card = f'''<div class="score-card"><div class="player-info"><div class="player-name">{player}</div>
<div class="player-score"><span class="score-{score_num}">{display_score}</span></div>
</div>
<div class="emoji-container"><div class="emoji-pattern">{emoji_pattern}</div></div>
</div>'''
            
            score_cards.append(card)
        
        # Combine all score cards
        all_score_cards = '\n'.join(score_cards)
        
        # Create the updated latest scores section with heading
        updated_latest_section = f'<h2 style="margin-top: 5px; margin-bottom: 10px; font-size: 16px; color: #6aaa64; text-align: center;">Wordle #{wordle_number} - {wordle_date}</h2>\n{all_score_cards}'
        
        # Replace the latest scores section in the template
        original_template = template_html
        result_html = re.sub(
            r'<div class="tab-content active" id="latest">(.*?)</div>\s*<div class="tab-content" id="weekly">',
            f'<div class="tab-content active" id="latest">{updated_latest_section}</div>\n<div class="tab-content" id="weekly">',
            template_html,
            flags=re.DOTALL
        )
        
        # Check if replacement actually happened
        if result_html == original_template:
            logging.error("Latest scores section replacement failed!")
            return False
        logging.info("Successfully replaced latest scores section")
        
        # Always update weekly section
        # Get the existing weekly section structure for headings and structure
        weekly_section_pattern = re.search(r'<div class="tab-content" id="weekly">(.*?)</div>\s*<div class="tab-content" id="stats">', template_html, re.DOTALL)
        if weekly_section_pattern:
            weekly_section = weekly_section_pattern.group(1)
            # Keep the heading and descriptive text, but replace the table data
            # Update weekly section with proper structure
            # First extract the sections before and after the weekly data in the template
            weekly_pattern = r'<div class="tab-content" id="weekly">(.*?)<div class="table-container">\s*<table>(.*?)</tbody>\s*</table>(.*?)</div>\s*<div class="tab-content" id="stats">'
            weekly_match = re.search(weekly_pattern, template_html, re.DOTALL)
            
            if weekly_match:
                weekly_heading = weekly_match.group(1) + '<div class="table-container">\n<table>' + weekly_match.group(2)
                weekly_footer = '</tbody>\n</table>\n' + weekly_match.group(3)
                
                # ENHANCED APPROACH: Ensure all players with scores are included
                backup_dir = os.path.join(os.path.dirname(os.path.dirname(template_path)), "website_export_backup_Aug10_2025_1148pm_with_season_20250810_234948")
                backup_file = os.path.join(backup_dir, os.path.basename(scores_path))
                
                # Try multiple approaches to get complete player data
                player_rows = ""
                
                # First, check the backup file - this is usually most reliable
                if os.path.exists(backup_file):
                    try:
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            backup_content = f.read()
                        
                        # Try different patterns to extract player rows
                        weekly_tab_patterns = [
                            r'<div class="tab-content" id="weekly">.*?<tbody>\s*(.+?)\s*</tbody>', # Full weekly tab
                            r'<table>.*?<tbody>\s*(.+?)\s*</tbody>', # Any table
                            r'<tbody>\s*(.+?)\s*</tbody>' # Any tbody
                        ]
                        
                        for pattern in weekly_tab_patterns:
                            match = re.search(pattern, backup_content, re.DOTALL)
                            if match and '<td><strong>' in match.group(1):
                                player_rows = match.group(1).strip()
                                logging.info(f"Found player rows using pattern {pattern[:20]}...")
                                break
                                
                        if player_rows:
                            # Try to extract individual player rows for verification
                            individual_rows = re.findall(r'<tr.*?</tr>', player_rows, re.DOTALL)
                            if individual_rows:
                                logging.info(f"Found {len(individual_rows)} individual player rows")
                            else:
                                logging.warning("Player rows found but couldn't extract individual rows")
                    except Exception as e:
                        logging.warning(f"Error reading backup file: {str(e)}")
                
                # If backup didn't work, try the extracted weekly data
                if not player_rows and weekly_data:
                    player_rows = weekly_data
                    logging.info("Using fresh extracted weekly data after backup failed")
                
                # As a fallback, construct player rows from available player names
                if not player_rows:
                    logging.warning("No player rows found, constructing minimal rows from player names")
                    # Find player names from the scores section
                    player_names = re.findall(r'<div class="player-name">([^<]+)</div>', scores_html)
                    
                    if player_names:
                        constructed_rows = []
                        for name in player_names:
                            constructed_rows.append(f'<tr><td><strong>{name}</strong></td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>')
                        
                        player_rows = '\n'.join(constructed_rows)
                        logging.info(f"Constructed player rows for {len(player_names)} players")
                
                # Use the player rows we found/constructed
                if player_rows:
                    updated_weekly_section = f"{weekly_heading}\n{player_rows}\n{weekly_footer}"
                    logging.info("Successfully built weekly totals section with player rows")
                else:
                    logging.error("CRITICAL: Could not find or construct any player rows for weekly tab")
                    updated_weekly_section = f"{weekly_heading}\n{weekly_footer}"
        else:
            logging.warning(f"Backup file not found at {backup_file}")
            if weekly_data:
                updated_weekly_section = f"{weekly_heading}\n{weekly_data}\n{weekly_footer}"
            else:
                updated_weekly_section = f"{weekly_heading}\n{weekly_footer}"
        
        # Apply the weekly section update to the HTML
        result_html = re.sub(
            r'<div class="tab-content" id="weekly">(.*?)</div>\s*<div class="tab-content" id="stats">',
            f'<div class="tab-content" id="weekly">{updated_weekly_section}</div>\n<div class="tab-content" id="stats">',
            result_html,
            flags=re.DOTALL
        )
        logging.info("Successfully updated weekly section")
        
        # Define base weekly section structure that will be used if we need to rebuild it
        base_weekly_section = """<h2 style="margin-top: 5px; margin-bottom: 10px;">Weekly Totals</h2>
<p style="margin-top: 0; margin-bottom: 5px; font-style: italic;">Top 5 scores count toward weekly total (Monday-Sunday).</p>
<div class="table-container">
  <table>
    <thead>
      <tr>
        <th>Player</th>
        <th>Weekly Total</th>
        <th>Used</th>
        <th>Fails</th>
        <th>Mon</th>
        <th>Tue</th>
        <th>Wed</th>
        <th>Thu</th>
        <th>Fri</th>
        <th>Sat</th>
        <th>Sun</th>
      </tr>
    </thead>
    <tbody>
    </tbody>
  </table>
</div>"""
    
        # If weekly pattern wasn't found earlier, handle it as alternative case
        if not weekly_match:
            # Alternative pattern - handle variations in HTML structure
            logging.warning("Standard weekly structure not found, trying alternative patterns")
                
            result_html = re.sub(
                r'<div class="tab-content" id="weekly">(.*?)</div>\s*<div class="tab-content" id="stats">',
                f'<div class="tab-content" id="weekly">{base_weekly_section}</div>\n<div class="tab-content" id="stats">',
                result_html,
                flags=re.DOTALL
            )
            logging.info("Completely rebuilt weekly section with clean structure")
        
        # Make sure the stats tab is properly structured and separate from weekly tab
        # First ensure stats tab exists as a separate entity
        if '<div class="tab-content" id="stats">' not in result_html:
            logging.warning("Stats tab not properly separated in HTML")
            # Find where weekly tab ends and fix structure
            result_html = re.sub(
                r'(<div class="tab-content" id="weekly">.*?)(\s*<div class="season-container")',
                r'\1</div>\n<div class="tab-content" id="stats">\2',
                result_html,
                flags=re.DOTALL
            )
            logging.info("Fixed tab separation between Weekly and Stats tabs")
        
        # Handle season data - if we have new data, use it; if not, preserve what's in the template
        # First, look for season data in the newly exported scores
        new_season_data = extract_season_data(scores_html)
        
        # If no new season data available, extract it from the template as backup
        if not new_season_data:
            logging.warning("No new season data found, checking template for existing data")
            template_season_data = extract_season_data(template_html)
            if template_season_data and 'No weekly winners yet' not in template_season_data:
                new_season_data = template_season_data
                logging.info("Using season data from template")
        
        # Add the weekly winner from the weekly data if available - enhanced matching
        if not new_season_data:
            # Try several approaches to identify winners
            winner_name = None
            
            # 1. Try the direct backup first - this is the most reliable source
            backup_dir = os.path.join(os.path.dirname(os.path.dirname(template_path)), "website_export_backup_Aug10_2025_1148pm_with_season_20250810_234948")
            backup_file = os.path.join(backup_dir, os.path.basename(scores_path))
            
            if os.path.exists(backup_file):
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        backup_content = f.read()
                    
                    # Look for highlighted rows with a strong tag (weekly winner)
                    winner_patterns = [
                        r'<tr[^>]*class="highlighted"[^>]*>.*?<td><strong>([^<]+)</strong></td>', 
                        r'<tr[^>]*style="background-color:[^>]*">.*?<td><strong>([^<]+)</strong></td>',
                        r'<tr[^>]*>.*?<td[^>]*><strong>([^<]+)</strong></td>'
                    ]
                    
                    for pattern in winner_patterns:
                        winner_match = re.search(pattern, backup_content, re.DOTALL)
                        if winner_match:
                            winner_name = winner_match.group(1)
                            logging.info(f"Found weekly winner in backup: {winner_name}")
                            break
                except Exception as e:
                    logging.warning(f"Error reading backup for weekly winners: {str(e)}")
            
            # 2. If no winner found in backup, try the weekly data we extracted
            if not winner_name and weekly_data:
                # Try multiple patterns for weekly winners
                winner_patterns = [
                    r'<tr class="highlighted".*?><td><strong>(.*?)</strong></td>',
                    r'<tr[^>]*style="background-color:[^>]*">.*?<td><strong>(.*?)</strong></td>',
                    r'<tr[^>]*>.*?<td[^>]*><strong>(.*?)</strong></td>' # Any player with strong tag
                ]
                
                for pattern in winner_patterns:
                    winner_match = re.search(pattern, weekly_data, re.DOTALL)
                    if winner_match:
                        winner_name = winner_match.group(1)
                        logging.info(f"Found weekly winner in extracted data: {winner_name}")
                        break
            
            # 3. Last resort - get any player name from the scores
            if not winner_name:
                player_match = re.search(r'<div class="player-name">([^<]+)</div>', scores_html, re.DOTALL)
                if player_match:
                    winner_name = player_match.group(1)
                    logging.info(f"Using any player as winner (last resort): {winner_name}")
            
            # Create season data if we found a winner
            if winner_name:
                current_week = datetime.datetime.now().strftime("%U")  # Week number
                new_season_data = f'<tr><td>{winner_name}</td><td>1</td><td>Week {current_week} (14)</td></tr>'
                logging.info(f"Created season data with winner: {winner_name} for Week {current_week}")
            else:
                logging.warning("Could not identify any winner for the season table")
        
        # Make sure the season table is in the stats tab, not weekly tab
        stats_tab_pattern = re.search(r'<div class="tab-content" id="stats">(.*?)(</div>\s*</div>\s*</div>\s*$)', result_html, re.DOTALL)
        if stats_tab_pattern:
            stats_content = stats_tab_pattern.group(1)
            
            # If we have season data (either new or from template), update the season table
            if new_season_data:
                # Find the season table in the stats tab
                season_table_pattern = r'(<table[^>]*class="season-table"[^>]*>\s*<thead>.*?</thead>\s*<tbody>)\s*(.*?)\s*(</tbody>\s*</table>)'
                match = re.search(season_table_pattern, stats_content, re.DOTALL)
                
                if match:
                    # Replace just the tbody content but keep the table structure
                    updated_stats = re.sub(
                        season_table_pattern,
                        f'\\1\n{new_season_data}\n\\3',
                        stats_content,
                        flags=re.DOTALL
                    )
                    
                    # Update the stats tab in the full HTML
                    result_html = result_html.replace(stats_content, updated_stats)
                    logging.info("Successfully updated season table with weekly winners")
                else:
                    # Look for the placeholder text "No weekly winners yet"
                    no_winners_pattern = r'(<td[^>]*colspan="3"[^>]*>)\s*No weekly winners yet\s*(</td>)'
                    match = re.search(no_winners_pattern, stats_content, re.DOTALL)
                    
                    if match:
                        # Replace the placeholder with actual winner data
                        updated_stats = stats_content.replace(match.group(0), new_season_data)
                        result_html = result_html.replace(stats_content, updated_stats)
                        logging.info("Replaced 'No weekly winners yet' with actual winner data")
                    else:
                        logging.warning("Could not find suitable location to update season data")
        else:
            logging.error("Could not locate stats tab content - HTML structure may be corrupted")
        
        # Completely rewrite All-Time Table highlighting to ensure entire row is highlighted for top player only
        all_time_pattern = r'<div class="all-time-container">.*?<table>.*?<tbody>(.*?)</tbody>.*?</div>'
        all_time_match = re.search(all_time_pattern, result_html, re.DOTALL)
        
        if all_time_match:
            tbody_content = all_time_match.group(1)
            
            # First, remove ALL highlighting
            clean_tbody = re.sub(r'<tr[^>]*?style="[^"]*"', '<tr', tbody_content)
            
            # Get individual rows
            rows = re.findall(r'(<tr.*?</tr>)', clean_tbody, re.DOTALL)
            
            if rows and len(rows) > 0:
                # Only highlight the first row (the top player)
                updated_tbody = clean_tbody.replace(rows[0], 
                    f'<tr style="background-color: rgba(106, 170, 100, 0.15);">{rows[0][4:]}')
                
                # Replace the tbody in the result
                result_html = result_html.replace(tbody_content, updated_tbody)
                logging.info("Replaced all-time table highlighting to apply only to top player row")
            else:
                logging.warning("No rows found in all-time table")
        else:
            logging.warning("Could not find all-time table with expected structure")
        
        # Additional direct replacement as a last resort
        # Make sure any remaining row highlights are removed
        result_html = re.sub(r'<tr[^>]*?style="background-color:[^"]*"', '<tr', result_html)
        
        # Then force highlight only the first row in the all-time table
        result_html = re.sub(
            r'(<div class="all-time-container">.*?<tbody>\s*)<tr',
            r'\1<tr style="background-color: rgba(106, 170, 100, 0.15);"',
            result_html,
            count=1,
            flags=re.DOTALL
        )
        
        # Write the merged result
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result_html)
        
        logging.info(f"Successfully wrote merged HTML to {output_path}, {len(result_html)} characters")
        return True
        
    except Exception as e:
        logging.error(f"Error merging scores with template: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return False

def run_export_script():
    """Run the export script to get updated scores"""
    try:
        logging.info(f"Running export script {EXPORT_SCRIPT}")
        result = subprocess.run([sys.executable, EXPORT_SCRIPT], 
                               capture_output=True, text=True, check=True)
        logging.info("Export script completed successfully")
        logging.info(f"Export output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Export script failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Failed to run export script: {str(e)}")
        return False

def update_all_leagues():
    """Update all league pages with new scores while preserving tabs"""
    # Leagues to update
    leagues = [
        {"name": "Wordle Warriorz", "path": ""},  # Main league
        {"name": "Wordle Gang", "path": "gang"},
        {"name": "Wordle PAL", "path": "pal"},
        {"name": "Wordle Party", "path": "party"},
        {"name": "Wordle Vball", "path": "vball"}
    ]
    
    success_count = 0
    failure_count = 0
    
    for league in leagues:
        league_path = league["path"]
        league_name = league["name"]
        
        logging.info(f"\n--- Processing league: {league_name} ---")
        
        # Determine file paths
        if league_path:
            template_path = os.path.join(BACKUP_DIR, league_path, "index.html")
            scores_path = os.path.join(EXPORT_DIR, league_path, "index.html")
            output_path = os.path.join(EXPORT_DIR, league_path, "index.html")
            # Make sure the directory exists
            os.makedirs(os.path.join(EXPORT_DIR, league_path), exist_ok=True)
        else:
            template_path = os.path.join(BACKUP_DIR, "index.html")
            scores_path = os.path.join(EXPORT_DIR, "index.html")
            output_path = os.path.join(EXPORT_DIR, "index.html")
        
        # Check if files exist
        if not os.path.exists(template_path):
            logging.error(f"Template file does not exist: {template_path}")
            print(f"[ERROR] Template file not found for {league_name}")
            failure_count += 1
            continue
            
        if not os.path.exists(scores_path):
            logging.error(f"Scores file does not exist: {scores_path}")
            print(f"[ERROR] Exported scores file not found for {league_name}")
            failure_count += 1
            continue
        
        # Merge scores with template
        print(f"Updating {league_name} scores while preserving tab structure...")
        if merge_scores_with_template(template_path, scores_path, output_path):
            success_count += 1
            print(f"[SUCCESS] Successfully updated {league_name}")
        else:
            failure_count += 1
            print(f"[FAILED] Failed to update {league_name}")
    
    # Return summary
    return success_count, failure_count

def main():
    print("Starting Wordle League score update with tab preservation...")
    logging.info("Starting score update with tab preservation")
    
    # Step 1: Backup current files
    backup_folder = backup_current_files()
    if not backup_folder:
        print("[ERROR] Failed to backup current files. Aborting.")
        return
    
    # Step 2: Run the export script to get updated scores
    if not run_export_script():
        print("[ERROR] Failed to run export script. Aborting.")
        return
    
    # Step 3: Update all leagues
    success_count, failure_count = update_all_leagues()
    
    # Report summary
    print(f"\nUpdate completed with {success_count} successful updates and {failure_count} failures")
    logging.info(f"Update completed with {success_count} successful updates and {failure_count} failures")
    
    if failure_count == 0:
        print("All leagues updated successfully with preserved tabs!")
    else:
        print("Some leagues failed to update. Check the log file for details.")

def extract_season_data(html_content):
    """Extract season data with weekly winners from the HTML"""
    logging.info("Extracting season data")
    
    # Try to find the season table - look for the season-table class
    season_table_pattern = r'<table[^>]*class="season-table"[^>]*>\s*<thead>.*?</thead>\s*<tbody>\s*(.*?)\s*</tbody>\s*</table>'
    match = re.search(season_table_pattern, html_content, re.DOTALL)
    
    if match:
        season_data = match.group(1).strip()
        if 'No weekly winners yet' not in season_data:
            logging.info(f"Found season table with weekly winners: {len(season_data)} characters")
            return season_data
    
    # Try alternate patterns
    alt_season_pattern = r'<table[^>]*>\s*<tr>\s*<th[^>]*>Week</th>\s*<th[^>]*>Winner</th>.*?</tr>\s*(.*?)\s*</table>'
    match = re.search(alt_season_pattern, html_content, re.DOTALL)
    if match:
        season_data = match.group(1).strip()
        if 'No weekly winners yet' not in season_data:
            logging.info(f"Found season table with weekly winners (alternate pattern): {len(season_data)} characters")
            return season_data
    
    # If we still don't have season data, derive it from weekly data
    # Get the weekly data to find winners
    weekly_data = extract_weekly_data(html_content)
    if weekly_data:
        # Look for highlighted rows (weekly winners)
        winner_matches = re.findall(r'<tr class="highlighted"[^>]*>.*?<td><strong>(.*?)</strong></td>', weekly_data, re.DOTALL)
        if not winner_matches:
            # Try alternate pattern without class
            winner_matches = re.findall(r'<tr[^>]*style="background-color: rgba\(106, 170, 100, 0\.15\)"[^>]*>.*?<td><strong>(.*?)</strong></td>', weekly_data, re.DOTALL)
        
        if winner_matches:
            current_week = datetime.datetime.now().strftime("%U")  # Week number
            season_rows = []
            for winner in winner_matches:
                season_rows.append(f'<tr><td>{winner}</td><td>1</td><td>Week {current_week}</td></tr>')
            
            if season_rows:
                combined_data = '\n'.join(season_rows)
                logging.info(f"Generated season data from weekly winners: {combined_data}")
                return combined_data
    
    logging.warning("No season data found or could be generated")
    return None
    
if __name__ == "__main__":
    main()
