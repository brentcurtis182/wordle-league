#!/usr/bin/env python
# Direct fix for weekly scores calculation

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
    handlers=[logging.StreamHandler(), logging.FileHandler("weekly_fix.log")]
)

def examine_database():
    """Examine database to see what scores actually exist for this week"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Get Monday 3:00 AM of current week
        today = datetime.now()
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        
        logging.info(f"Start of week: {start_of_week_str}")
        
        # Get ALL scores for this week with player names
        cursor.execute("""
            SELECT s.id, p.name, s.wordle_number, s.date, s.pattern
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.date >= ?
            ORDER BY s.date DESC
        """, (start_of_week_str,))
        
        scores = cursor.fetchall()
        logging.info(f"Found {len(scores)} scores since {start_of_week_str}:")
        for score in scores:
            logging.info(f"ID: {score[0]}, Player: {score[1]}, Wordle #{score[2]}, Date: {score[3]}, Pattern: {score[4]}")
        
        # Also get all players
        cursor.execute("SELECT id, name FROM player")
        players = cursor.fetchall()
        player_dict = {player[0]: player[1] for player in players}
        
        # Get scores from past 7 days for comparison
        seven_days_ago = today - timedelta(days=7)
        seven_days_ago_str = seven_days_ago.strftime('%Y-%m-%d')
        
        cursor.execute("""
            SELECT p.name, s.wordle_number, s.date
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.date >= ?
            ORDER BY s.date DESC
        """, (seven_days_ago_str,))
        
        recent_scores = cursor.fetchall()
        logging.info(f"\nScores from past 7 days ({seven_days_ago_str} to present):")
        for score in recent_scores:
            logging.info(f"Player: {score[0]}, Wordle #{score[1]}, Date: {score[2]}")
        
        conn.close()
        return scores, player_dict
    except Exception as e:
        logging.error(f"Error examining database: {e}")
        return [], {}

def fix_export_leaderboard():
    """Fix export_leaderboard.py to properly calculate weekly scores"""
    try:
        file_path = os.path.join(os.getcwd(), "export_leaderboard.py")
        
        # Read the current file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a backup
        with open(f"{file_path}.bak", 'w', encoding='utf-8') as f:
            f.write(content)
        logging.info(f"Created backup of export_leaderboard.py at {file_path}.bak")
        
        # Check if we already modified this file
        if "weekly_reset_marker.txt" in content:
            logging.info("export_leaderboard.py already has marker file code, updating to ensure it works")
            
            # Find the specific part where weekly scores are calculated
            # Looking for the get_player_stats function
            player_stats_match = re.search(r'def get_player_stats\(\):.*?return weekly_stats, all_time_stats', content, re.DOTALL)
            
            if player_stats_match:
                player_stats_function = player_stats_match.group(0)
                
                # Create a completely new version of the function
                new_function = """def get_player_stats():
    \"\"\"Get player stats for the current and all time scores\"\"\"
    conn = sqlite3.connect("wordle_league.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM player")
    players = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    # Determine start of week (Monday at 3:00 AM)
    today = datetime.now()
    marker_file = "weekly_reset_marker.txt"
    
    # Use marker file if it exists
    if os.path.exists(marker_file):
        with open(marker_file, 'r') as f:
            start_of_week_str = f.read().strip()
            try:
                start_of_week = datetime.strptime(start_of_week_str, '%Y-%m-%d %H:%M:%S')
                print(f"Using weekly reset marker: {start_of_week_str}")
            except ValueError:
                # If marker file has invalid date, fallback to Monday calculation
                today_weekday = today.weekday()  # 0 is Monday
                days_since_monday = today_weekday
                start_of_week = today - timedelta(days=days_since_monday)
                start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
                start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
                print(f"Invalid marker date, fallback to calculated: {start_of_week_str}")
    else:
        # Calculate Monday 3:00 AM if marker doesn't exist
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        print(f"No marker file, calculated start of week: {start_of_week_str}")
    
    player_stats = []
    
    for player in players:
        player_id = player['id']
        
        # Get weekly scores (using datetime comparison)
        cursor.execute(\"\"\"SELECT * FROM score 
                      WHERE player_id = ? AND datetime(date) >= datetime(?)
                      ORDER BY wordle_number DESC\"\"\", (player_id, start_of_week_str))
        
        weekly_scores = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
        
        print(f"Player {player['name']}: {len(weekly_scores)} weekly scores since {start_of_week_str}")
        
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
        
        player_stats.append({
            'name': player['name'],
            'weekly_score': weekly_score,
            'weekly_used': used_scores,
            'weekly_failed': weekly_failures,
            'all_time_score': all_time_score,
            'all_time_used': all_time_used,
            'all_time_failed': all_time_failures
        })
    
    # Sort weekly stats by score
    weekly_stats = sorted(player_stats, key=lambda x: (-x['weekly_score'], x['name']))
    
    # Sort all-time stats by score
    all_time_stats = sorted(player_stats, key=lambda x: (-x['all_time_score'], x['name']))
    
    conn.close()
    
    return weekly_stats, all_time_stats"""
                
                # Replace the old function with the new one
                content = content.replace(player_stats_match.group(0), new_function)
        else:
            logging.info("Adding weekly reset marker code to export_leaderboard.py")
            
            # Add the weekly reset marker code at the beginning of the get_player_stats function
            if "def get_player_stats():" in content:
                old_function_start = "def get_player_stats():"
                new_function_start = """def get_player_stats():
    \"\"\"Get player stats for the current and all time scores\"\"\"
    conn = sqlite3.connect("wordle_league.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM player")
    players = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]

    # Determine start of week (Monday at 3:00 AM)
    today = datetime.now()
    marker_file = "weekly_reset_marker.txt"
    
    # Use marker file if it exists
    if os.path.exists(marker_file):
        with open(marker_file, 'r') as f:
            start_of_week_str = f.read().strip()
            try:
                start_of_week = datetime.strptime(start_of_week_str, '%Y-%m-%d %H:%M:%S')
                print(f"Using weekly reset marker: {start_of_week_str}")
            except ValueError:
                # If marker file has invalid date, fallback to Monday calculation
                today_weekday = today.weekday()  # 0 is Monday
                days_since_monday = today_weekday
                start_of_week = today - timedelta(days=days_since_monday)
                start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
                start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
                print(f"Invalid marker date, fallback to calculated: {start_of_week_str}")
    else:
        # Calculate Monday 3:00 AM if marker doesn't exist
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        print(f"No marker file, calculated start of week: {start_of_week_str}")"""
                
                content = content.replace(old_function_start, new_function_start)
                
                # Fix the SQL query for weekly scores
                if "cursor.execute(\"\"\"SELECT * FROM score \\\n                      WHERE player_id = ? AND date >= ?" in content:
                    old_query = "cursor.execute(\"\"\"SELECT * FROM score \\\n                      WHERE player_id = ? AND date >= ?\"\"\", (player_id, start_of_week_str))"
                    new_query = "cursor.execute(\"\"\"SELECT * FROM score \\\n                      WHERE player_id = ? AND datetime(date) >= datetime(?)\"\"\", (player_id, start_of_week_str))"
                    content = content.replace(old_query, new_query)
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info("Successfully fixed export_leaderboard.py")
        return True
    except Exception as e:
        logging.error(f"Error fixing export_leaderboard.py: {e}")
        return False

def create_weekly_reset_marker():
    """Create or update the weekly reset marker file"""
    try:
        # Get Monday 3:00 AM of current week
        today = datetime.now()
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        
        # Write to the marker file
        with open("weekly_reset_marker.txt", 'w') as f:
            f.write(start_of_week_str)
            
        logging.info(f"Created weekly reset marker: {start_of_week_str}")
        return True
    except Exception as e:
        logging.error(f"Error creating weekly reset marker: {e}")
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
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        commit_msg = f"Fix weekly scores: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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
    logging.info("Starting weekly score fix...")
    
    # Step 1: Examine database
    logging.info("\nStep 1: Examining database...")
    scores, players = examine_database()
    
    # Step 2: Fix export_leaderboard.py
    logging.info("\nStep 2: Fixing export_leaderboard.py...")
    fix_export_leaderboard()
    
    # Step 3: Create weekly reset marker
    logging.info("\nStep 3: Creating weekly reset marker...")
    create_weekly_reset_marker()
    
    # Step 4: Run export_leaderboard.py
    logging.info("\nStep 4: Running export_leaderboard.py...")
    run_export_leaderboard()
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub...")
    push_to_github()
    
    logging.info("\nWeekly score fix complete!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("If you still see old data, please use Ctrl+F5 or open in incognito mode.")
    logging.info("The weekly scores should now correctly show only scores from this week (Monday 3:00 AM onwards)")
    logging.info("If there are no scores since Monday 3:00 AM, the weekly leaderboard should be empty or only show Malia and Nanna")

if __name__ == "__main__":
    main()
