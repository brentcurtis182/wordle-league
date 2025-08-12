#!/usr/bin/env python3
"""
Modified version of export script that uses our fixed template
"""
import os
import sys
import logging
import shutil
import sqlite3
import json
from datetime import datetime
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_scores_for_wordle_by_league(wordle_number, league_id):
    """Get scores for a specific Wordle number and league"""
    try:
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        # Get scores for the specified Wordle number and league
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_name = p.name AND s.league_id = p.league_id
        WHERE s.wordle_num = ? AND s.league_id = ?
        ORDER BY 
            CASE 
                WHEN s.score = 'X' THEN 7
                ELSE CAST(s.score AS INTEGER)
            END
        """, (wordle_number, league_id))
        
        result = cursor.fetchall()
        
        # Get all players from the league
        cursor.execute("""
        SELECT name, nickname 
        FROM players 
        WHERE league_id = ?
        """, (league_id,))
        
        all_players = cursor.fetchall()
        
        # Map of player name to score
        score_map = {row[0]: (row[2], row[3]) for row in result}
        
        scores = []
        
        for player in all_players:
            name = player[1] if player[1] else player[0]  # Use nickname if available
            
            has_score = player[0] in score_map
            
            if has_score:
                score = score_map[player[0]][0]
                emoji_pattern = score_map[player[0]][1]
                
                # Special handling for failed attempts
                if score == "X":
                    score_value = "X"
                else:
                    score_value = int(score)
            else:
                score_value = None
                emoji_pattern = None
            
            scores.append({
                'name': name,
                'has_score': has_score,
                'score': score_value,
                'emoji_pattern': emoji_pattern
            })
        
        conn.close()
        return scores
    except Exception as e:
        logging.error(f"Error getting scores: {e}")
        return []

def run_export_for_league(league_id, league_name, league_directory):
    """Run the export for a single league using our fixed template"""
    try:
        from jinja2 import Environment, FileSystemLoader
        
        # Create league directory if it doesn't exist
        if not os.path.exists(league_directory):
            os.makedirs(league_directory)
        
        # Get the latest Wordle number from the database
        conn = sqlite3.connect('wordle_league.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(wordle_num) FROM scores WHERE league_id = ?", (league_id,))
        latest_wordle = cursor.fetchone()[0]
        
        if not latest_wordle:
            logging.warning(f"No scores found for league {league_name} (ID: {league_id})")
            return
        
        # Get scores for the latest Wordle number
        scores = get_scores_for_wordle_by_league(latest_wordle, league_id)
        
        # Get weekly stats (simplified for this script)
        player_stats = []
        all_time_stats = []
        
        # Setup Jinja2 environment
        env = Environment(loader=FileSystemLoader('website_export/templates'))
        
        # Use our fixed template
        template = env.from_string(open('website_export/templates/index_fixed.html', 'r', encoding='utf-8').read())
        
        # Calculate relative path for CSS based on league directory
        css_path = '../styles.css' if league_id != 1 else 'styles.css'
        
        # Render the template
        html = template.render(
            league_name=league_name,
            league_id=league_id,
            wordle_number=latest_wordle,
            scores=scores,
            player_stats=player_stats,
            all_time_stats=all_time_stats,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            css_path=css_path
        )
        
        # Write the HTML to a file
        with open(os.path.join(league_directory, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        
        logging.info(f"Exported index.html for league {league_name} (ID: {league_id})")
        
    except Exception as e:
        logging.error(f"Error exporting league {league_name}: {e}")

def main():
    """Main function to run the export with our fixed template"""
    try:
        from jinja2 import Environment, FileSystemLoader
    except ImportError:
        logging.error("Jinja2 is required for this script. Install it with: pip install Jinja2")
        sys.exit(1)
    
    # Get league config from the database
    conn = sqlite3.connect('wordle_league.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT league_id, name FROM leagues")
    leagues = cursor.fetchall()
    
    conn.close()
    
    if not leagues:
        logging.error("No leagues found in the database")
        sys.exit(1)
    
    for league_id, league_name in leagues:
        # Set league directory based on the league name
        if league_id == 1:
            league_directory = 'website_export'
        else:
            # Create a simplified version of the league name for the directory
            simplified_name = re.sub(r'[^a-zA-Z0-9]', '', league_name.split()[1].lower())
            league_directory = os.path.join('website_export', simplified_name)
        
        run_export_for_league(league_id, league_name, league_directory)
    
    logging.info("Export with fixed template completed successfully")

if __name__ == "__main__":
    main()
