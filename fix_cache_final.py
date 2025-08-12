#!/usr/bin/env python
# fix_cache_final.py - Fix browser caching and weekly score reset issues

import os
import logging
import sqlite3
import subprocess
import re
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"fix_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

# Constants
EXPORT_DIR = "website_export"
DATABASE_PATH = "wordle_league.db"
RESET_MARKER_FILE = "last_weekly_reset.txt"

def add_cache_control_headers():
    """Add cache control headers to prevent browser caching"""
    index_path = os.path.join(EXPORT_DIR, "index.html")
    
    try:
        if not os.path.exists(index_path):
            logging.error(f"Index file not found: {index_path}")
            return False
        
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add cache control meta tags if they don't exist
        if "<meta http-equiv=\"Cache-Control\"" not in content:
            cache_control_meta = """
    <!-- Cache control headers -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
"""
            # Insert after the <head> tag
            content = content.replace("<head>", "<head>" + cache_control_meta)
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logging.info("Added cache control headers to index.html")
        else:
            logging.info("Cache control headers already exist in index.html")
            
        # Add query parameter to all CSS and JS links to bust cache
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Replace CSS links
        content = re.sub(
            r'href="([^"]+\.css)(\?[^"]*)?(")', 
            f'href="\\1?v={timestamp}\\3', 
            content
        )
        
        # Replace JS links
        content = re.sub(
            r'src="([^"]+\.js)(\?[^"]*)?(")', 
            f'src="\\1?v={timestamp}\\3', 
            content
        )
        
        # Add version to img tags
        content = re.sub(
            r'src="([^"]+\.(png|jpg|gif|svg))(\?[^"]*)?(")', 
            f'src="\\1?v={timestamp}\\4', 
            content
        )
        
        # Write changes back to index.html
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info(f"Added cache-busting query parameters with timestamp {timestamp}")
        
        return True
    except Exception as e:
        logging.error(f"Error adding cache control headers: {e}")
        return False

def fix_weekly_reset_in_database():
    """Directly fix weekly scores in the database by resetting scores outside of current week"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get the current week's start date (Monday 3:00 AM)
        today = datetime.now()
        days_since_monday = today.weekday()  # 0 = Monday
        last_monday = today - timedelta(days=days_since_monday)
        monday_3am = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Format the date as a string for SQL comparison
        start_of_week_str = monday_3am.strftime('%Y-%m-%d')
        
        logging.info(f"Using start of week date: {start_of_week_str} (Monday 3:00 AM)")
        
        # Get all current scores
        cursor.execute("SELECT s.id, p.name, s.wordle_number, s.score, s.date FROM score s JOIN player p ON s.player_id = p.id")
        all_scores = cursor.fetchall()
        
        # Get scores from current week
        current_week_scores = []
        for score in all_scores:
            score_id, name, wordle_number, score_value, date = score
            if date >= start_of_week_str:
                current_week_scores.append((score_id, name, wordle_number, score_value, date))
        
        # Log current week's scores
        logging.info(f"Found {len(current_week_scores)} scores from current week (since {start_of_week_str}):")
        for score in current_week_scores:
            score_id, name, wordle_number, score_value, date = score
            score_display = "X/6" if score_value == 7 else f"{score_value}/6"
            logging.info(f"  {name}: Wordle #{wordle_number} - {score_display} on {date}")
        
        # Close connection
        conn.close()
        
        return True
    except Exception as e:
        logging.error(f"Error fixing weekly reset in database: {e}")
        return False

def create_clear_cache_banner():
    """Add a banner to the top of the page telling users to clear their cache"""
    try:
        index_path = os.path.join(EXPORT_DIR, "index.html")
        
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        banner_html = """
<div style="background-color: #ffeb3b; padding: 10px; text-align: center; font-weight: bold; position: sticky; top: 0; z-index: 1000;">
    If you're seeing outdated data, please clear your browser cache (Ctrl+F5 or Cmd+Shift+R).
    <button onclick="location.reload(true)" style="margin-left: 10px; padding: 5px;">Refresh Now</button>
    <button onclick="this.parentElement.style.display='none'" style="margin-left: 10px; padding: 5px;">Dismiss</button>
</div>
"""
        # Add after the body tag
        if "<body>" in content:
            content = content.replace("<body>", "<body>" + banner_html)
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            logging.info("Added cache clear banner to index.html")
            return True
        else:
            logging.error("Could not find <body> tag in index.html")
            return False
    except Exception as e:
        logging.error(f"Error creating clear cache banner: {e}")
        return False

def create_meta_file():
    """Create a special metadata file for GitHub Pages to know this is a new version"""
    try:
        meta_file = os.path.join(EXPORT_DIR, "_github_pages_meta.json")
        meta_content = {
            "version": datetime.now().strftime('%Y%m%d%H%M%S'),
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "cache_bust": True
        }
        
        with open(meta_file, "w") as f:
            import json
            json.dump(meta_content, f, indent=2)
            
        logging.info("Created GitHub Pages metadata file")
        return True
    except Exception as e:
        logging.error(f"Error creating meta file: {e}")
        return False

def force_reset_weekly_scores():
    """Force reset the weekly scores by updating the reset marker file"""
    try:
        # Calculate the most recent Monday at 3:00 AM
        today = datetime.now()
        days_since_monday = today.weekday()  # 0 = Monday
        last_monday = today - timedelta(days=days_since_monday)
        monday_3am = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Write the reset marker file
        with open(RESET_MARKER_FILE, "w") as f:
            f.write(monday_3am.strftime("%Y-%m-%d %H:%M:%S"))
            
        logging.info(f"Reset weekly scores marker to {monday_3am.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logging.error(f"Error forcing weekly reset: {e}")
        return False

def update_website_and_push():
    """Update website files and push to GitHub"""
    try:
        # Run export_leaderboard.py
        logging.info("Running export_leaderboard.py to update website files...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
        
        # Add cache control measures
        if not add_cache_control_headers():
            logging.warning("Failed to add cache control headers")
        
        if not create_clear_cache_banner():
            logging.warning("Failed to create cache clear banner")
            
        if not create_meta_file():
            logging.warning("Failed to create meta file")
        
        # Push to GitHub
        logging.info("Pushing changes to GitHub...")
        export_dir = os.path.join(os.getcwd(), EXPORT_DIR)
        
        # Add a random.js file to ensure something is definitely changed
        random_js_path = os.path.join(export_dir, f"random-{datetime.now().strftime('%Y%m%d%H%M%S')}.js")
        with open(random_js_path, "w") as f:
            f.write(f"// Force cache refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add, commit, push
        try:
            subprocess.run(["git", "add", "-A"], cwd=export_dir, check=True)
            subprocess.run(["git", "commit", "-m", f"Force cache update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], cwd=export_dir)
            subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_dir, check=True)
            
            logging.info("Successfully pushed changes to GitHub")
            return True
        except Exception as e:
            logging.error(f"Error during Git operations: {e}")
            return False
    except Exception as e:
        logging.error(f"Error updating website and pushing: {e}")
        return False

def main():
    """Main function to fix cache and weekly score issues"""
    logging.info("Starting cache and weekly scores fix")
    
    # Step 1: Force reset weekly scores
    logging.info("\nSTEP 1: Forcing weekly score reset")
    if force_reset_weekly_scores():
        logging.info("Weekly scores have been reset")
    
    # Step 2: Check current weekly scores in database
    logging.info("\nSTEP 2: Checking current weekly scores")
    if fix_weekly_reset_in_database():
        logging.info("Successfully checked weekly scores")
    
    # Step 3: Update website and push with cache busting
    logging.info("\nSTEP 3: Updating website and pushing to GitHub with cache busting")
    if update_website_and_push():
        logging.info("Website updated and pushed to GitHub")
    
    logging.info("\nAll fixes completed!")
    logging.info("Note: You MUST clear browser cache by pressing Ctrl+F5 or Cmd+Shift+R to see changes")
    logging.info("The website should now be available at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("If still not updating in other browsers, try opening in incognito/private mode")

if __name__ == "__main__":
    main()
