#!/usr/bin/env python
# Fix both caching and weekly reset issues

import os
import sqlite3
import subprocess
import logging
import shutil
import random
import string
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Constants
EXPORT_DIR = os.path.join(os.getcwd(), "website_export")
WEEKLY_RESET_FILE = "weekly_reset_marker.txt"

def generate_random_id(length=8):
    """Generate a random string for cache busting"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def verify_weekly_reset_marker():
    """Verify and update the weekly reset marker file"""
    try:
        # Get Monday 3:00 AM of current week
        today = datetime.now()
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Check if marker file exists
        if os.path.exists(WEEKLY_RESET_FILE):
            with open(WEEKLY_RESET_FILE, 'r') as f:
                marker_date = f.read().strip()
                logging.info(f"Current weekly reset marker: {marker_date}")
        else:
            marker_date = ""
            logging.info("Weekly reset marker does not exist")
        
        # Format the current marker date
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update marker if it doesn't match
        if marker_date != start_of_week_str:
            logging.info(f"Updating weekly reset marker to: {start_of_week_str}")
            with open(WEEKLY_RESET_FILE, 'w') as f:
                f.write(start_of_week_str)
            return True
        else:
            logging.info("Weekly reset marker is up-to-date")
            return False
    except Exception as e:
        logging.error(f"Error verifying weekly reset marker: {e}")
        return False

def fix_export_leaderboard_script():
    """Fix export_leaderboard.py to properly calculate weekly scores"""
    try:
        filepath = os.path.join(os.getcwd(), "export_leaderboard.py")
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find the get_player_stats function
        if "def get_player_stats():" in content:
            # Check if weekly_reset_marker.txt reading logic exists
            if "weekly_reset_marker.txt" not in content:
                # Add marker file reading and use it for weekly calculations
                weekly_reset_logic = """def get_player_stats():
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
                logging.info(f"Using weekly reset marker: {start_of_week_str}")
            except ValueError:
                # If marker file has invalid date, fallback to Monday calculation
                today_weekday = today.weekday()  # 0 is Monday
                days_since_monday = today_weekday
                start_of_week = today - timedelta(days=days_since_monday)
                start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
                logging.warning(f"Invalid marker date, fallback to calculated: {start_of_week}")
    else:
        # Calculate Monday 3:00 AM if marker doesn't exist
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        logging.info(f"No marker file, calculated start of week: {start_of_week}")
    
    # Format for SQL query
    start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
    logging.info(f"Using weekly scores since: {start_of_week_str}")"""

                content = content.replace("def get_player_stats():", weekly_reset_logic, 1)

                # Update the SQL query to use the marker date
                old_sql = "start_of_week_str = start_of_week.strftime('%Y-%m-%d')"
                new_sql = "start_of_week_str = start_of_week.strftime('%Y-%m-%d')"  # Keep this line as is
                
                # Find the SQL query that retrieves scores
                if "cursor.execute(\"\"\"SELECT s.*, p.name" in content:
                    old_query = """cursor.execute(\"\"\"SELECT s.*, p.name 
                FROM score s
                JOIN player p ON s.player_id = p.id
                WHERE s.date >= date(?)
                ORDER BY s.wordle_number DESC\"\"\", (start_of_week_str,))"""
                    
                    new_query = """cursor.execute(\"\"\"SELECT s.*, p.name 
                FROM score s
                JOIN player p ON s.player_id = p.id
                WHERE s.date >= ?
                ORDER BY s.wordle_number DESC\"\"\", (start_of_week_str,))"""
                    
                    content = content.replace(old_query, new_query)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            logging.info("Fixed export_leaderboard.py to use marker file for weekly reset")
            return True
        else:
            logging.error("Could not find get_player_stats function in export_leaderboard.py")
            return False
    except Exception as e:
        logging.error(f"Error fixing export_leaderboard.py: {e}")
        return False

def add_cache_control():
    """Add strong cache control to website files"""
    try:
        # Generate unique cache buster ID
        cache_buster_id = generate_random_id()
        logging.info(f"Using cache buster ID: {cache_buster_id}")
        
        # Create timestamp file for cache busting
        timestamp_file = os.path.join(EXPORT_DIR, f"timestamp_{cache_buster_id}.txt")
        with open(timestamp_file, 'w') as f:
            f.write(f"Cache buster timestamp: {datetime.now().isoformat()}")
        
        # Create version JS file
        version_file = os.path.join(EXPORT_DIR, f"version_{cache_buster_id}.js")
        with open(version_file, 'w') as f:
            f.write(f"// Cache buster version: {datetime.now().isoformat()}\n")
            f.write(f"window.CACHE_VERSION = '{cache_buster_id}';\n")
        
        # Create .htaccess file for cache control
        htaccess_file = os.path.join(EXPORT_DIR, ".htaccess")
        with open(htaccess_file, 'w') as f:
            f.write("""
# Cache Control
<IfModule mod_headers.c>
    Header set Cache-Control "no-cache, no-store, must-revalidate"
    Header set Pragma "no-cache"
    Header set Expires "0"
</IfModule>
""")
        
        # Create .nojekyll file for GitHub Pages
        nojekyll_file = os.path.join(EXPORT_DIR, ".nojekyll")
        with open(nojekyll_file, 'w') as f:
            f.write("")
        
        # Create cache buster redirect page
        redirect_file = os.path.join(EXPORT_DIR, "cachebuster.html")
        with open(redirect_file, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Redirecting...</title>
    <script>
        window.location.href = "index.html?cb={cache_buster_id}";
    </script>
</head>
<body>
    <p>Redirecting to <a href="index.html?cb={cache_buster_id}">leaderboard</a>...</p>
</body>
</html>""")
        
        # Add cache busting banner to index.html
        index_file = os.path.join(EXPORT_DIR, "index.html")
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add cache control meta tags
            if "<head>" in content:
                cache_meta_tags = """<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <script src="version_{0}.js"></script>""".format(cache_buster_id)
                
                content = content.replace("<head>", cache_meta_tags)
            
            # Add weekly reset banner at the top of the body
            if "<body>" in content:
                today = datetime.now()
                today_weekday = today.weekday()  # 0 is Monday
                days_since_monday = today_weekday
                days_till_next_monday = 7 - today_weekday if today_weekday > 0 else 0
                next_reset = today + timedelta(days=days_till_next_monday)
                next_reset = next_reset.replace(hour=3, minute=0, second=0, microsecond=0)
                
                reset_banner = """<body>
    <div style="background-color: #f8f9fa; padding: 10px; margin-bottom: 20px; border-radius: 5px; text-align: center;">
        <p><strong>Weekly scores reset every Monday at 3:00 AM.</strong> Next reset: {0}</p>
        <p><small>This page was updated on: {1}. <a href="cachebuster.html">Click here</a> if you're seeing outdated data.</small></p>
    </div>""".format(next_reset.strftime("%A, %B %d at %I:%M %p"), datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
                content = content.replace("<body>", reset_banner)
            
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logging.info("Added cache control and banners to index.html")
            return cache_buster_id
        else:
            logging.warning("index.html not found, skipping cache control banners")
            return cache_buster_id
    except Exception as e:
        logging.error(f"Error adding cache control: {e}")
        return None

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            logging.error(f"Output: {result.stdout}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Make sure we're in the export directory
        export_dir = os.path.join(os.getcwd(), "website_export")
        if not os.path.isdir(export_dir):
            logging.error(f"Export directory not found: {export_dir}")
            return False
        
        # Add files to git
        logging.info("Adding files to Git...")
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        logging.info("Committing changes...")
        message = f"Fix weekly reset and cache issues: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", message], cwd=export_dir)
        
        # Force push to GitHub
        logging.info("Force pushing to GitHub...")
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"],
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode == 0:
            logging.info("Successfully pushed to GitHub")
            return True
        else:
            logging.error(f"GitHub push failed: {push_result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    """Main function to fix weekly reset and cache issues"""
    logging.info("Starting fix for weekly reset and cache issues...")
    
    # Step 1: Update weekly reset marker
    logging.info("\nStep 1: Updating weekly reset marker")
    reset_marker_updated = verify_weekly_reset_marker()
    if reset_marker_updated:
        logging.info("Weekly reset marker updated")
    else:
        logging.info("Weekly reset marker was already up-to-date")
    
    # Step 2: Fix export_leaderboard.py
    logging.info("\nStep 2: Fixing export_leaderboard.py")
    if fix_export_leaderboard_script():
        logging.info("Successfully fixed export_leaderboard.py")
    else:
        logging.error("Failed to fix export_leaderboard.py")
    
    # Step 3: Run export_leaderboard.py
    logging.info("\nStep 3: Running export_leaderboard.py")
    if run_export_leaderboard():
        logging.info("Successfully exported website files")
    else:
        logging.error("Failed to export website files")
        return
    
    # Step 4: Add cache control
    logging.info("\nStep 4: Adding cache control")
    cache_buster_id = add_cache_control()
    if cache_buster_id:
        logging.info(f"Added cache control with ID: {cache_buster_id}")
    else:
        logging.error("Failed to add cache control")
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub")
    if push_to_github():
        logging.info("Successfully pushed to GitHub")
    else:
        logging.error("Failed to push to GitHub")
        return
    
    # Final direct access URL
    direct_url = f"https://brentcurtis182.github.io/wordle-league/cachebuster.html"
    logging.info("\n===========================================================")
    logging.info("FIX COMPLETE")
    logging.info("===========================================================")
    logging.info(f"\nAccess the updated website at: {direct_url}")
    logging.info("This special URL will force a cache refresh")
    logging.info("\nAlternatively, use this URL for direct access:")
    logging.info(f"https://brentcurtis182.github.io/wordle-league/index.html?cb={cache_buster_id}")
    
if __name__ == "__main__":
    main()
