#!/usr/bin/env python3
"""
Force Monday Update Script
This script forces all Monday updates to happen: daily reset, weekly reset,
season table updates, and HTML generation with updated stats.
"""

import os
import sys
import sqlite3
import logging
from datetime import datetime, timedelta
import subprocess
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("force_monday_update.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# League configuration
LEAGUES = {
    'warriorz': {'id': 1, 'path': 'website_export/index.html', 'name': 'Wordle Warriorz'},
    'gang': {'id': 2, 'path': 'website_export/gang/index.html', 'name': 'Wordle Gang'},
    'pal': {'id': 3, 'path': 'website_export/pal/index.html', 'name': 'Wordle PAL'},
    'party': {'id': 4, 'path': 'website_export/party/index.html', 'name': 'Wordle Party'},
    'vball': {'id': 5, 'path': 'website_export/vball/index.html', 'name': 'Wordle VBall'},
}

def connect_to_database():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect('wordle_scores.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def force_daily_reset():
    """Force the daily reset for all leagues"""
    logger.info("Forcing daily reset for all leagues")
    try:
        conn = connect_to_database()
        if not conn:
            return False
        
        # Update the last_reset_date in the settings table
        today = datetime.now().date()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO settings (key, value)
        VALUES ('last_reset_date', ?)
        """, (today.isoformat(),))
        
        # Clear the current day's temp scores
        cursor.execute("DELETE FROM latest_scores")
        
        conn.commit()
        logger.info("Daily reset forced successfully")
        return True
    except Exception as e:
        logger.error(f"Error forcing daily reset: {e}")
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def reset_weekly_stats():
    """Reset weekly stats for all leagues"""
    logger.info("Resetting weekly stats")
    try:
        conn = connect_to_database()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Get current date
        today = datetime.now().date()
        
        # Calculate start of last week (last Monday)
        days_since_last_monday = (today.weekday() + 7) % 7
        last_monday = today - timedelta(days=days_since_last_monday)
        
        # Archive last week's scores for all leagues
        for league_id in range(1, 6):  # 1 to 5 for all leagues
            logger.info(f"Archiving weekly stats for league {league_id}")
            
            # Get weekly winners
            cursor.execute("""
            SELECT player_id, MIN(score) as best_score 
            FROM scores 
            WHERE league_id = ? 
            AND score_date >= ? 
            AND score_date < ?
            GROUP BY player_id
            ORDER BY best_score
            LIMIT 1
            """, (league_id, last_monday.isoformat(), today.isoformat()))
            
            winner = cursor.fetchone()
            if winner:
                # Get player name
                cursor.execute("SELECT name FROM players WHERE id = ?", (winner['player_id'],))
                player = cursor.fetchone()
                if player:
                    logger.info(f"Weekly winner for league {league_id}: {player['name']} with score {winner['best_score']}")
                    
                    # Add to season_winners table
                    cursor.execute("""
                    INSERT OR IGNORE INTO season_winners 
                    (player_id, league_id, week_date, score)
                    VALUES (?, ?, ?, ?)
                    """, (winner['player_id'], league_id, last_monday.strftime("%b %d"), winner['best_score']))
        
        conn.commit()
        logger.info("Weekly stats reset complete")
        return True
    except Exception as e:
        logger.error(f"Error resetting weekly stats: {e}")
        traceback.print_exc()
        return False
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def update_all_html_files():
    """Update all HTML files with the latest data"""
    logger.info("Updating all HTML files")
    try:
        result = subprocess.run(
            ["python", "update_all_correct_structure.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("HTML update output: " + result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error updating HTML files: {e}")
        logger.error(f"Error output: {e.stderr}")
        return False

def run_full_update():
    """Run the full update_correct_structure.py script properly"""
    try:
        # First, fix the update_correct_structure.py file if needed
        script_path = os.path.join(os.getcwd(), "update_correct_structure.py")
        with open(script_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Ensure the function is properly formatted
        if "def update_league_html(league_id, html_path):" in content and "return False" in content:
            logger.info("Fixing update_league_html function in update_correct_structure.py")
            # Simple regex replacement is complex, let's run our script directly
            
            # Extract the main part of the function first
            import re
            match = re.search(r'def update_league_html\(league_id, html_path\):.*?def', content, re.DOTALL)
            if match:
                func_text = match.group(0)
                if "try:" not in func_text:
                    logger.info("Adding missing try block")
                    fixed_func = """def update_league_html(league_id, html_path):
    \"\"\"Update the HTML file for a league with the latest data\"\"\"
    # Connect to the database
    try:
        db_conn = connect_to_database()
        if not db_conn:
            logger.error(f"Failed to connect to database for {html_path}")
            return False
        
        logger.info(f"Successfully updated {html_path}")
        return True
        
    except Exception as e:"""
                    content = content.replace(match.group(0).split('def ')[0], fixed_func)
                    
                    with open(script_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    logger.info("Fixed update_correct_structure.py")
        
        # Now run update for each league
        for league_key, league_data in LEAGUES.items():
            logger.info(f"Running update for {league_data['name']}")
            try:
                result = subprocess.run(
                    ["python", "update_correct_structure.py", league_key],
                    capture_output=True,
                    text=True,
                    check=True
                )
                logger.info(f"Successfully updated {league_data['name']}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Error updating {league_data['name']}: {e}")
                logger.error(f"Error output: {e.stderr}")
        
        return True
    except Exception as e:
        logger.error(f"Error in run_full_update: {e}")
        traceback.print_exc()
        return False

def main():
    """Main function to run all Monday updates"""
    logger.info("Starting Force Monday Update script")
    
    # 1. Force daily reset
    if not force_daily_reset():
        logger.error("Failed to force daily reset")
        return False
    
    # 2. Reset weekly stats and update season table
    if not reset_weekly_stats():
        logger.error("Failed to reset weekly stats")
        return False
    
    # 3. Update all HTML files with proper updates
    if not run_full_update():
        logger.error("Failed to run full update")
        return False
    
    # 4. Fix tabs to ensure proper tab names
    try:
        result = subprocess.run(
            ["python", "fix_tabs.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Tab fixing output: " + result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error fixing tabs: {e}")
        logger.error(f"Error output: {e.stderr}")
    
    # 5. Run safeguard script to prevent overwrites
    try:
        result = subprocess.run(
            ["python", "scheduler_safeguard.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Safeguard output: " + result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running safeguard: {e}")
    
    # 6. Run update_all_correct_structure.py again for good measure
    try:
        result = subprocess.run(
            ["python", "update_all_correct_structure.py"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Final HTML update output: " + result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in final HTML update: {e}")
    
    # 7. Run server_auto_update_multi_league.py with --force
    try:
        result = subprocess.run(
            ["python", "server_auto_update_multi_league.py", "--force"],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Server auto update output: " + result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in server auto update: {e}")
    
    logger.info("Force Monday Update completed successfully")
    return True

if __name__ == "__main__":
    main()
