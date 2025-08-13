#!/usr/bin/env python
# Fix to make weekly scores only include current game #1500

import os
import sqlite3
import subprocess
import logging
import shutil
from datetime import datetime, timedelta
import time
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("current_game_fix.log")]
)

def examine_database():
    """Examine database to see what scores actually exist"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Get current wordle number (should be 1500)
        cursor.execute("""
            SELECT MAX(wordle_number) FROM score
        """)
        current_wordle = cursor.fetchone()[0]
        logging.info(f"Current Wordle number: {current_wordle}")
        
        # Get scores for current wordle with player names
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.date, s.attempts
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.wordle_number = ?
            ORDER BY p.name
        """, (current_wordle,))
        
        scores = cursor.fetchall()
        logging.info(f"Found {len(scores)} scores for Wordle #{current_wordle}:")
        for score in scores:
            logging.info(f"ID: {score[0]}, Player: {score[1]}, Wordle #{score[2]}, Date: {score[3]}, Attempts: {score[4]}")
        
        conn.close()
        return current_wordle
    except Exception as e:
        logging.error(f"Error examining database: {e}")
        return None

def fix_export_leaderboard(current_wordle):
    """Fix export_leaderboard.py to only include current wordle in weekly scores"""
    try:
        file_path = os.path.join(os.getcwd(), "export_leaderboard.py")
        
        # Read the current file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a backup
        with open(f"{file_path}.bak2", 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Created backup of export_leaderboard.py at {file_path}.bak2")
        
        # Find the get_player_stats function
        player_stats_match = re.search(r'def get_player_stats\(\):.*?return weekly_stats, all_time_stats', content, re.DOTALL)
        
        if player_stats_match:
            player_stats_function = player_stats_match.group(0)
            
            # Create a new version that only includes the current wordle in weekly scores
            new_function = f"""def get_player_stats():
    \"\"\"Get player stats for the current and all time scores\"\"\"
    conn = sqlite3.connect("wordle_league.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM player")
    players = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    # Current wordle number for weekly scores
    current_wordle = {current_wordle}
    print(f"Using current wordle #{current_wordle} for weekly scores")
    
    player_stats = []
    
    for player in players:
        player_id = player['id']
        
        # Get weekly scores (only current wordle)
        cursor.execute(\"\"\"SELECT * FROM score 
                      WHERE player_id = ? AND wordle_number = ?
                      ORDER BY wordle_number DESC\"\"\", (player_id, current_wordle))
        
        weekly_scores = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        print(f"Player {{player['name']}}: {{len(weekly_scores)}} weekly scores for Wordle #{current_wordle}")
        
        # Get all time scores
        cursor.execute("SELECT * FROM score WHERE player_id = ? ORDER BY wordle_number DESC", (player_id,))
        all_time_scores = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        # Count failures (6 attempts used)
        weekly_failures = sum(1 for score in weekly_scores if score['attempts'] == 6)
        all_time_failures = sum(1 for score in all_time_scores if score['attempts'] == 6)
        
        # Calculate weekly stats
        weekly_score = 0
        used_scores = 0
        for score in weekly_scores:
            attempts = score['attempts']
            if attempts < 6:  # Only count successful solves
                weekly_score += (6 - attempts)
                used_scores += 1
        
        # Calculate all-time stats
        all_time_score = 0
        all_time_used = 0
        for score in all_time_scores:
            attempts = score['attempts']
            if attempts < 6:  # Only count successful solves
                all_time_score += (6 - attempts)
                all_time_used += 1
        
        player_stats.append({{
            'name': player['name'],
            'weekly_score': weekly_score,
            'weekly_used': used_scores,
            'weekly_failed': weekly_failures,
            'all_time_score': all_time_score,
            'all_time_used': all_time_used,
            'all_time_failed': all_time_failures
        }})
    
    # Sort weekly stats by score
    weekly_stats = sorted(player_stats, key=lambda x: (-x['weekly_score'], x['name']))
    
    # Sort all-time stats by score
    all_time_stats = sorted(player_stats, key=lambda x: (-x['all_time_score'], x['name']))
    
    conn.close()
    
    return weekly_stats, all_time_stats"""
            
            # Replace the old function with the new one
            content = content.replace(player_stats_match.group(0), new_function)
            
            # Write the modified content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logging.info(f"Successfully fixed export_leaderboard.py to only include Wordle #{current_wordle} in weekly scores")
            return True
        else:
            logging.error("Could not find get_player_stats function in export_leaderboard.py")
            return False
    except Exception as e:
        logging.error(f"Error fixing export_leaderboard.py: {e}")
        return False

def fix_index_template():
    """Update the index template to clarify that weekly scores are current game only"""
    try:
        template_dir = os.path.join(os.getcwd(), "templates")
        index_template = os.path.join(template_dir, "index.html")
        
        if os.path.exists(index_template):
            with open(index_template, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Update the weekly scores description
            if "Weekly Totals" in content and "Top 5 scores count toward weekly total (Monday-Sunday)." in content:
                content = content.replace(
                    "Weekly Totals\n                Top 5 scores count toward weekly total (Monday-Sunday).", 
                    "Current Game Scores\n                Scores from current game only (updated daily)."
                )
                
                with open(index_template, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                logging.info("Updated index template with clearer weekly scores description")
                return True
            else:
                logging.warning("Weekly scores description not found in index template")
                return False
        else:
            logging.warning(f"Index template not found at {index_template}")
            return False
    except Exception as e:
        logging.error(f"Error updating index template: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        # Run with output capture for debugging
        process = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if process.returncode == 0:
            logging.info("Website export successful")
            logging.info(f"Output: {process.stdout}")
            return True
        else:
            logging.error(f"Website export failed: {process.stderr}")
            logging.error(f"Output: {process.stdout}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add timestamp file for cache busting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        timestamp_file = os.path.join(export_dir, f"timestamp_{timestamp}.txt")
        with open(timestamp_file, 'w') as f:
            f.write(f"Website updated at {timestamp}")
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        commit_msg = f"Current game scores only: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir)
        
        # Force push to gh-pages
        logging.info("Force pushing to GitHub...")
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"], 
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if "error" in push_result.stderr.lower():
            logging.error(f"Push error: {push_result.stderr}")
            return False
        else:
            logging.info("Successfully pushed to GitHub Pages")
            return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting current game scores fix...")
    
    # Step 1: Examine database to get current wordle number
    logging.info("\nStep 1: Examining database...")
    current_wordle = examine_database()
    
    if not current_wordle:
        logging.error("Could not determine current wordle number, aborting")
        return
    
    # Step 2: Fix export_leaderboard.py
    logging.info("\nStep 2: Fixing export_leaderboard.py...")
    if not fix_export_leaderboard(current_wordle):
        logging.error("Failed to update export_leaderboard.py, aborting")
        return
    
    # Step 3: Update index template
    logging.info("\nStep 3: Updating index template...")
    fix_index_template()
    
    # Step 4: Run export_leaderboard.py
    logging.info("\nStep 4: Running export_leaderboard.py...")
    if not run_export_leaderboard():
        logging.error("Failed to run export_leaderboard.py, aborting")
        return
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub...")
    push_to_github()
    
    logging.info("\nCurrent game scores fix complete!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("If you still see old data, please use Ctrl+F5 or open in incognito mode.")
    logging.info(f"The weekly scores should now only show scores from Wordle #{current_wordle}")
    logging.info("All-time scores will still include all historical games")

if __name__ == "__main__":
    main()
