#!/usr/bin/env python3
"""
Quick Export Today's Scores
A simplified script to export today's Wordle scores for all leagues
using the unified scores table structure
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime
import shutil
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
default_db_path = os.path.join(script_dir, 'wordle_league.db')
WORDLE_DATABASE = os.getenv('DATABASE_URI', default_db_path).replace('sqlite:///', '')
EXPORT_DIR = os.getenv('EXPORT_DIR', 'website_export')

def get_league_config():
    """Load league configuration from JSON file"""
    config_file = os.path.join(script_dir, 'league_config.json')
    
    if not os.path.exists(config_file):
        logging.error("league_config.json not found")
        return []
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            # Extract just the leagues array from the config
            return config.get('leagues', [])
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return []

def get_latest_wordle_number():
    """Get the latest Wordle number from the scores table"""
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(wordle_number) FROM scores")
        result = cursor.fetchone()
        
        if result and result[0]:
            return result[0]
        else:
            return None
    except Exception as e:
        logging.error(f"Error getting latest Wordle number: {e}")
        return None
    finally:
        if conn:
            conn.close()

def get_scores_for_wordle_by_league(wordle_number, league_id):
    """Get all scores for a specific wordle number and league"""
    try:
        conn = sqlite3.connect(WORDLE_DATABASE)
        cursor = conn.cursor()
        
        # Get all scores for this Wordle number for the specified league
        cursor.execute("""
        SELECT p.name, p.nickname, s.score, s.emoji_pattern
        FROM scores s
        JOIN players p ON s.player_id = p.id
        WHERE s.wordle_number = ? AND p.league_id = ?
        ORDER BY s.score
        """, (wordle_number, league_id))
        
        result = cursor.fetchall()
        
        scores = []
        for row in result:
            name = row[0]
            nickname = row[1] if row[1] else name
            score_value = row[2]
            emoji_pattern = row[3] if row[3] else ""
            
            # Format the score for display
            display_score = "X/6" if score_value == 7 else f"{score_value}/6"
            
            scores.append({
                'name': nickname,
                'score': display_score,
                'has_score': True,
                'emoji_pattern': emoji_pattern
            })
        
        return scores
    except Exception as e:
        logging.error(f"Error getting scores for Wordle {wordle_number}, league {league_id}: {e}")
        return []
    finally:
        if conn:
            conn.close()

def export_today_scores_html(league, latest_wordle, scores):
    """Export today's scores for a league to HTML"""
    try:
        league_id = league.get('id')
        league_name = league.get('name')
        html_path = league.get('html_export_path', '')
        
        # Create export directory for this league
        export_path = os.path.join(EXPORT_DIR, html_path)
        if not os.path.exists(export_path):
            os.makedirs(export_path)
        
        # Format today's date
        today = datetime.now()
        today_formatted = today.strftime("%B %d, %Y")
        
        # Create a simple HTML page
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Wordle {latest_wordle} - {league_name}</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2 {{
            color: #333;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        .emoji-pattern {{
            font-family: monospace;
            white-space: pre;
        }}
        .nav {{
            margin: 20px 0;
        }}
        .nav a {{
            margin-right: 15px;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <h1>Wordle {latest_wordle} - {league_name}</h1>
    <div class="nav">
        <a href="../index.html">Home</a>
        <a href="index.html">League Home</a>
    </div>
    <h2>Scores for {today_formatted}</h2>
    <table>
        <tr>
            <th>Player</th>
            <th>Score</th>
            <th>Pattern</th>
        </tr>
"""
        
        # Add scores to the table
        if scores:
            for score in scores:
                display_score = score['score']
                display_name = score['name']
                emoji_pattern = score['emoji_pattern'] if score['emoji_pattern'] else "No pattern available"
                
                html_content += f"""
        <tr>
            <td>{display_name}</td>
            <td>{display_score}</td>
            <td class="emoji-pattern">{emoji_pattern}</td>
        </tr>"""
        else:
            html_content += """
        <tr>
            <td colspan="3">No scores available for today</td>
        </tr>"""
            
        # Close the HTML
        html_content += """
    </table>
</body>
</html>"""
        
        # Write the HTML file
        output_file = os.path.join(export_path, f"wordle_{latest_wordle}.html")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Also update index.html to show the latest scores
        index_html = os.path.join(export_path, "index.html")
        
        # If index.html doesn't exist yet, create a basic one
        if not os.path.exists(index_html) or os.path.getsize(index_html) == 0:
            index_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{league_name} - Wordle League</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2 {{
            color: #333;
        }}
        .nav {{
            margin: 20px 0;
        }}
        .nav a {{
            margin-right: 15px;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <h1>{league_name}</h1>
    <div class="nav">
        <a href="../index.html">Home</a>
        <a href="wordle_{latest_wordle}.html">Today's Scores</a>
    </div>
    <h2>Latest: <a href="wordle_{latest_wordle}.html">Wordle #{latest_wordle}</a></h2>
    <p>Click the link above to see today's scores.</p>
</body>
</html>"""
            
            with open(index_html, 'w', encoding='utf-8') as f:
                f.write(index_content)
                
        return True
    
    except Exception as e:
        logging.error(f"Error exporting HTML for league {league.get('name')}: {e}")
        return False

def update_landing_page(leagues, latest_wordle):
    """Update the landing page with links to all leagues"""
    try:
        landing_file = os.path.join(EXPORT_DIR, "index.html")
        
        # Create landing page content
        landing_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Wordle Leagues</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2 {{
            color: #333;
        }}
        .league-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        .league-card {{
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            background-color: #f9f9f9;
        }}
        .league-name {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .league-button {{
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 8px 16px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin-top: 10px;
            cursor: pointer;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>Wordle Leagues</h1>
    <p>Latest: Wordle #{latest_wordle} - {datetime.now().strftime("%B %d, %Y")}</p>
    
    <div class="league-grid">
"""
        
        # Add a card for each league
        for league in leagues:
            if not league.get('enabled', True):
                continue
                
            league_name = league.get('name')
            html_path = league.get('html_export_path', '')
            
            landing_content += f"""
        <div class="league-card">
            <div class="league-name">{league_name}</div>
            <div class="league-description">{league.get('description', '')}</div>
            <form action="{html_path}/index.html" method="get">
                <button type="submit" class="league-button">View League</button>
            </form>
        </div>
"""
            
        # Close the HTML
        landing_content += """
    </div>
</body>
</html>
"""
        
        # Write the landing page
        with open(landing_file, 'w', encoding='utf-8') as f:
            f.write(landing_content)
            
        return True
            
    except Exception as e:
        logging.error(f"Error updating landing page: {e}")
        return False

def main():
    """Main function"""
    logging.info("Starting quick export of today's Wordle scores")
    
    # Make sure the export directory exists
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
        
    # Get the latest Wordle number
    latest_wordle = get_latest_wordle_number()
    if not latest_wordle:
        logging.error("Could not determine the latest Wordle number")
        return False
        
    logging.info(f"Exporting scores for Wordle #{latest_wordle}")
    
    # Load league configuration
    leagues = get_league_config()
    if not leagues:
        logging.error("No league configuration found")
        return False
        
    # Process each league
    for league in leagues:
        league_id = league.get('league_id')
        league_name = league.get('name')
        
        if not league.get('enabled', True):
            logging.info(f"Skipping disabled league: {league_name}")
            continue
            
        logging.info(f"Processing league: {league_name} (ID: {league_id})")
        
        # Get scores for this league and Wordle number
        scores = get_scores_for_wordle_by_league(latest_wordle, league_id)
        
        # Export the scores to HTML
        if export_today_scores_html(league, latest_wordle, scores):
            logging.info(f"Successfully exported scores for {league_name}")
        else:
            logging.error(f"Failed to export scores for {league_name}")
    
    # Update the landing page
    if update_landing_page(leagues, latest_wordle):
        logging.info("Updated landing page")
    else:
        logging.error("Failed to update landing page")
        
    logging.info("Quick export completed")
    return True
    
if __name__ == "__main__":
    main()
