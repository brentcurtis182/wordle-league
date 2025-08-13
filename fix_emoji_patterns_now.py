#!/usr/bin/env python
import sqlite3
import os
import re
import shutil
from datetime import datetime
from bs4 import BeautifulSoup
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("emoji_fix.log"),
        logging.StreamHandler()
    ]
)

DB_PATH = "wordle_league.db"
WEBSITE_EXPORT_DIR = "website_export"
BACKUP_DIR = os.path.join("website_export_backup", "backups")

# League IDs and directories
LEAGUES = [
    {"id": 1, "name": "warriorz", "dir": ""},
    {"id": 2, "name": "gang", "dir": "gang"},
    {"id": 3, "name": "pal", "dir": "pal"},
    {"id": 4, "name": "party", "dir": "party"},
    {"id": 5, "name": "vball", "dir": "vball"},
]

def backup_file(file_path):
    """Create a backup of the file"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    filename = os.path.basename(file_path)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f"{filename}.backup_{timestamp}")
    
    shutil.copy2(file_path, backup_path)
    logging.info(f"Backed up {file_path} to {backup_path}")
    return backup_path

def get_real_emoji_patterns(conn, league_id):
    """Get real emoji patterns for the latest wordle number in a league"""
    cursor = conn.cursor()
    
    # Get the latest wordle number
    cursor.execute("""
        SELECT MAX(wordle_num) 
        FROM scores 
        WHERE league_id = ?
    """, (league_id,))
    latest_wordle = cursor.fetchone()[0]
    
    if not latest_wordle:
        logging.warning(f"No scores found for league {league_id}")
        return {}
    
    # Get all scores and patterns for that wordle number
    cursor.execute("""
        SELECT player_name, score, pattern
        FROM scores
        JOIN players ON scores.player_id = players.id
        WHERE league_id = ? AND wordle_num = ?
    """, (league_id, latest_wordle))
    
    results = cursor.fetchall()
    patterns = {}
    
    for player, score, pattern in results:
        if pattern and pattern != "No emoji pattern available":
            # Convert pattern to HTML rows
            pattern_rows = []
            rows = pattern.strip().split('\n')
            for row in rows:
                # Clean up any non-emoji characters that might be in the pattern
                cleaned_row = re.sub(r'[^⬛⬜🟨🟩]', '', row)
                if cleaned_row:
                    pattern_rows.append(f'<div class="emoji-row">{cleaned_row}</div>')
            
            if pattern_rows:
                patterns[player] = '\n'.join(pattern_rows)
            else:
                logging.warning(f"Empty pattern for {player}, score {score}, wordle #{latest_wordle}")
    
    return patterns

def fix_emoji_patterns_in_html(html_path, patterns):
    """Fix emoji patterns in HTML file"""
    if not os.path.exists(html_path):
        logging.error(f"HTML file not found: {html_path}")
        return False
    
    # Backup original file
    backup_file(html_path)
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    fixed_count = 0
    
    # Find all score cards
    score_cards = soup.select('.score-card')
    for card in score_cards:
        # Get player name
        player_name_div = card.select_one('.player-name')
        if not player_name_div:
            continue
            
        player_name = player_name_div.text.strip()
        
        # Get current emoji pattern container
        emoji_container = card.select_one('.emoji-container')
        if not emoji_container:
            continue
            
        # If we have a real pattern for this player, replace the fake one
        if player_name in patterns:
            emoji_pattern = emoji_container.select_one('.emoji-pattern')
            if emoji_pattern:
                # Replace the inner HTML with the real pattern
                emoji_pattern.clear()
                emoji_pattern.append(BeautifulSoup(patterns[player_name], 'html.parser'))
                fixed_count += 1
                logging.info(f"Fixed pattern for {player_name} in {html_path}")
    
    # Save the fixed HTML
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    return fixed_count

def main():
    """Main function to fix all emoji patterns"""
    logging.info("Starting emoji pattern fix")
    
    # Connect to database
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info(f"Connected to database {DB_PATH}")
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        return
    
    total_fixed = 0
    
    # Process each league
    for league in LEAGUES:
        league_id = league["id"]
        league_dir = league["dir"]
        league_name = league["name"]
        
        # Get HTML path
        if league_dir:
            html_path = os.path.join(WEBSITE_EXPORT_DIR, league_dir, "index.html")
        else:
            html_path = os.path.join(WEBSITE_EXPORT_DIR, "index.html")
        
        # Get real patterns from database
        patterns = get_real_emoji_patterns(conn, league_id)
        
        if patterns:
            # Fix patterns in HTML
            fixed = fix_emoji_patterns_in_html(html_path, patterns)
            total_fixed += fixed
            logging.info(f"Fixed {fixed} patterns in {league_name} league")
        else:
            logging.warning(f"No patterns found for {league_name} league")
    
    conn.close()
    
    logging.info(f"Total emoji patterns fixed: {total_fixed}")
    logging.info("Emoji pattern fix complete")
    
    # Run standardize_leagues.py to ensure tabs still work
    try:
        import standardize_leagues
        standardize_leagues.main()
        logging.info("Re-applied standardization to ensure tabs functionality")
    except Exception as e:
        logging.error(f"Failed to run standardization: {e}")

if __name__ == "__main__":
    main()
