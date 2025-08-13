#!/usr/bin/env python
# ultimate_fix.py - Definitive fix for Joanna's score and weekly reset issues

import os
import sqlite3
import subprocess
import logging
import shutil
from datetime import datetime, timedelta
import time
import json
import random
import string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("ultimate_fix.log")]
)

# Constants
DATABASE_PATH = "wordle_league.db"
BACKUP_DB_PATH = f"wordle_league_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
EXPORT_DIR = "website_export"
RESET_MARKER_FILE = "last_weekly_reset.txt"
CACHE_BUSTER = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def backup_database():
    """Create a backup of the database before making changes"""
    try:
        shutil.copy2(DATABASE_PATH, BACKUP_DB_PATH)
        logging.info(f"Database backup created: {BACKUP_DB_PATH}")
        return True
    except Exception as e:
        logging.error(f"Error backing up database: {e}")
        return False

def remove_joanna_score():
    """Remove Joanna's incorrect score for Wordle #1500 with validation"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # First find Joanna's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.info("Joanna not found in players table")
            conn.close()
            return False
            
        joanna_id = result[0]
        logging.info(f"Found Joanna's player ID: {joanna_id}")
        
        # Check if Joanna's score exists for Wordle #1500
        cursor.execute(
            "SELECT * FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (joanna_id,)
        )
        score = cursor.fetchone()
        
        if score:
            logging.info(f"Found Joanna's score for Wordle #1500: {dict(score)}")
            
            # Delete Joanna's score for Wordle #1500
            cursor.execute(
                "DELETE FROM score WHERE player_id = ? AND wordle_number = 1500", 
                (joanna_id,)
            )
            
            conn.commit()
            logging.info(f"Removed {cursor.rowcount} score(s) for Joanna, Wordle #1500")
            
            # Validate deletion
            cursor.execute(
                "SELECT * FROM score WHERE player_id = ? AND wordle_number = 1500", 
                (joanna_id,)
            )
            if cursor.fetchone():
                logging.error("VALIDATION FAILED: Score still exists after deletion!")
                conn.close()
                return False
            else:
                logging.info("VALIDATION PASSED: Score was successfully deleted")
        else:
            logging.info("No score found for Joanna, Wordle #1500")
        
        # Add an extra check for any scores with Wordle #1500
        cursor.execute("SELECT p.name, s.* FROM score s JOIN player p ON s.player_id = p.id WHERE s.wordle_number = 1500")
        all_scores = cursor.fetchall()
        logging.info(f"All scores for Wordle #1500: {[dict(s) for s in all_scores]}")
        
        # Close the connection
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error removing Joanna's score: {e}")
        return False

def modify_export_leaderboard():
    """Modify export_leaderboard.py to ensure weekly scores are calculated correctly"""
    try:
        file_path = "export_leaderboard.py"
        
        # Read the current content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Replace all weekly score calculation logic with a fixed version
        weekly_pattern = "# Get the current week's start date (Monday)"
        weekly_code_end = "start_of_week_str = start_of_week.strftime('%Y-%m-%d')"
        
        # New code block that enforces using today as start date if today is Monday
        new_weekly_code = """# Get the current week's start date (Monday at 3:00 AM)
    today = datetime.now()
    today_weekday = today.weekday()
    
    # If today is Monday, use today at 3:00 AM as the start of week
    if today_weekday == 0:  # Monday is 0
        start_of_week = today.replace(hour=3, minute=0, second=0, microsecond=0)
        logging.info("TODAY IS MONDAY: Using today at 3:00 AM as start of week")
    else:
        # Otherwise use the previous Monday
        start_of_week = today - timedelta(days=today_weekday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        
    # Format the date as a string for SQL comparison"""
        
        # Find the start of the weekly code block
        weekly_start = content.find(weekly_pattern)
        
        if weekly_start != -1:
            # Find the end of the block
            weekly_end = content.find(weekly_code_end, weekly_start) + len(weekly_code_end)
            
            # Replace the weekly code block
            content = content[:weekly_start] + new_weekly_code + content[weekly_end:]
            logging.info("Modified weekly calculation code in export_leaderboard.py")
        else:
            logging.error("Could not find weekly calculation code in export_leaderboard.py")
            return False
        
        # Add logging import if not already present
        if "import logging" not in content:
            if "import os" in content:
                content = content.replace("import os", "import os\nimport logging")
                logging.info("Added logging import to export_leaderboard.py")
        
        # Add logging configuration if not already present
        if "logging.basicConfig" not in content:
            log_config = """
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
"""
            # Find a good place to insert it (after imports)
            if "import " in content:
                last_import = content.rfind("import ")
                last_import = content.find("\n", last_import) + 1
                content = content[:last_import] + log_config + content[last_import:]
                logging.info("Added logging configuration to export_leaderboard.py")
        
        # Write the modified content back
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info("Successfully modified export_leaderboard.py")
        return True
    except Exception as e:
        logging.error(f"Error modifying export_leaderboard.py: {e}")
        return False

def force_weekly_reset():
    """Force a weekly reset by updating the reset marker file to today at 3:00 AM"""
    try:
        # Get today at 3:00 AM (since today is Monday)
        today = datetime.now()
        today_3am = today.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Write to reset marker file
        with open(RESET_MARKER_FILE, "w") as f:
            f.write(today_3am.strftime("%Y-%m-%d %H:%M:%S"))
            
        logging.info(f"Weekly reset marker updated to: {today_3am.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logging.error(f"Error forcing weekly reset: {e}")
        return False

def list_weekly_scores():
    """List all scores for the current week (since Monday 3:00 AM)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Calculate the start of week (Monday 3:00 AM)
        today = datetime.now()
        if today.weekday() == 0:  # Today is Monday
            start_of_week = today.replace(hour=3, minute=0, second=0, microsecond=0)
        else:
            # This shouldn't happen today, but include for completeness
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday)
            start_of_week = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Format for SQL comparison
        start_of_week_str = start_of_week.strftime("%Y-%m-%d")
        
        # Query scores from this week
        cursor.execute("""
            SELECT p.name, s.wordle_number, s.score, s.date
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.date >= ?
            ORDER BY s.date DESC, p.name ASC
        """, (start_of_week_str,))
        
        scores = cursor.fetchall()
        
        logging.info(f"Scores for current week (since {start_of_week_str}):")
        if not scores:
            logging.info("  No scores found for this week")
            weekly_data = []
        else:
            weekly_data = []
            for score in scores:
                score_dict = dict(score)
                score_display = "X/6" if score_dict["score"] == 7 else f"{score_dict['score']}/6"
                logging.info(f"  {score_dict['name']}: Wordle #{score_dict['wordle_number']} - {score_display} on {score_dict['date']}")
                weekly_data.append(score_dict)
        
        # Save the weekly scores to a JSON file for reference
        with open("weekly_scores.json", "w") as f:
            json.dump(weekly_data, f, indent=4)
        
        logging.info(f"Weekly scores saved to weekly_scores.json")
        
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error listing weekly scores: {e}")
        return False

def rebuild_export_directory():
    """Completely rebuild the export directory from scratch to avoid git issues"""
    try:
        export_path = os.path.join(os.getcwd(), EXPORT_DIR)
        
        # Check if export directory exists
        if os.path.exists(export_path):
            logging.info(f"Backing up existing export directory")
            backup_dir = f"{EXPORT_DIR}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Use robocopy to copy files (handles permission issues better on Windows)
            subprocess.run([
                "robocopy", 
                export_path, 
                backup_dir, 
                "/E", "/NP", "/R:2", "/W:2"
            ], shell=True)
            
            # Try to remove the old directory with permissions fixes
            logging.info(f"Removing existing export directory")
            
            # First make sure all files are writeable
            for root, dirs, files in os.walk(export_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    try:
                        os.chmod(full_path, 0o777)
                    except:
                        pass
            
            # Wait a moment for any file handles to be released
            time.sleep(2)
            
            # Remove the directory
            try:
                shutil.rmtree(export_path)
            except Exception as e:
                logging.error(f"Error removing directory: {e}")
                
                # Try using robocopy to empty the directory as a fallback
                empty_dir = os.path.join(os.getcwd(), "empty_dir")
                os.makedirs(empty_dir, exist_ok=True)
                
                subprocess.run([
                    "robocopy", 
                    empty_dir, 
                    export_path, 
                    "/MIR", "/NP"
                ], shell=True)
                
                if os.path.exists(empty_dir):
                    shutil.rmtree(empty_dir)
        
        # Create fresh export directory
        os.makedirs(export_path, exist_ok=True)
        logging.info(f"Created fresh export directory: {export_path}")
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=export_path, check=True)
        subprocess.run(["git", "config", "user.name", "brentcurtis182"], cwd=export_path, check=True)
        subprocess.run(["git", "config", "user.email", "brentcurtis182@github.com"], cwd=export_path, check=True)
        
        # Create and switch to gh-pages branch
        subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=export_path, check=True)
        
        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/brentcurtis182/wordle-league.git"], 
            cwd=export_path, 
            check=True
        )
        
        logging.info("Git repository initialized with gh-pages branch")
        return True
    except Exception as e:
        logging.error(f"Error rebuilding export directory: {e}")
        return False

def add_cache_control():
    """Add comprehensive cache control to export"""
    try:
        export_path = os.path.join(os.getcwd(), EXPORT_DIR)
        
        # Create a timestamp file with cache buster
        with open(os.path.join(export_path, f"timestamp_{CACHE_BUSTER}.txt"), "w") as f:
            f.write(f"Last update: {datetime.now()}")
        
        # Create version file with cache buster
        with open(os.path.join(export_path, f"version_{CACHE_BUSTER}.js"), "w") as f:
            f.write(f"// Version: {datetime.now().strftime('%Y%m%d%H%M%S')}")
        
        # Create .nojekyll file for GitHub Pages
        with open(os.path.join(export_path, ".nojekyll"), "w") as f:
            pass
            
        # Create cache control meta file
        with open(os.path.join(export_path, ".htaccess"), "w") as f:
            f.write("""
<IfModule mod_expires.c>
  ExpiresActive On
  ExpiresDefault "access plus 0 seconds"
  ExpiresByType text/html "access plus 0 seconds"
  ExpiresByType text/css "access plus 0 seconds"
  ExpiresByType text/javascript "access plus 0 seconds"
  ExpiresByType application/javascript "access plus 0 seconds"
</IfModule>

<IfModule mod_headers.c>
  Header set Cache-Control "no-store, no-cache, must-revalidate, max-age=0"
  Header set Pragma "no-cache"
  Header set Expires "0"
</IfModule>
""")
        
        # Create a cache-busting index page that redirects
        with open(os.path.join(export_path, "cachebuster.html"), "w") as f:
            f.write(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Cache Busting</title>
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <script>
    // Force cache refresh by redirecting with unique query parameter
    window.location.href = "index.html?cb={CACHE_BUSTER}";
  </script>
</head>
<body>
  <p>Redirecting to the latest version...</p>
  <p><a href="index.html?cb={CACHE_BUSTER}">Click here if not redirected</a></p>
</body>
</html>
""")
        
        logging.info("Added comprehensive cache control")
        return True
    except Exception as e:
        logging.error(f"Error adding cache control: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            # Print output for debugging
            for line in result.stdout.splitlines():
                logging.info(f"Export: {line}")
            
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def modify_index_html():
    """Modify index.html to add cache busting and weekly reset indicator"""
    try:
        index_path = os.path.join(EXPORT_DIR, "index.html")
        
        if not os.path.exists(index_path):
            logging.error(f"index.html not found at {index_path}")
            return False
        
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add cache busting meta tags
        if "<head>" in content:
            cache_meta = """  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">"""
            content = content.replace("<head>", f"<head>\n{cache_meta}")
            logging.info("Added cache control meta tags to index.html")
        
        # Add weekly reset indicator
        if "<h2>Weekly Totals" in content:
            today = datetime.now()
            reset_indicator = f"""<div style="background-color: #ffd700; padding: 10px; margin: 10px 0; border-radius: 5px;">
<strong>Weekly Reset:</strong> Scores reset Monday, {today.strftime('%B %d')} at 3:00 AM. Version: {CACHE_BUSTER}
</div>"""
            content = content.replace("<h2>Weekly Totals", f"{reset_indicator}\n<h2>Weekly Totals")
            logging.info("Added weekly reset indicator to index.html")
        
        # Add banner at top
        if "<body>" in content:
            banner = f"""<div style="background-color: #ff5722; color: white; padding: 15px; text-align: center; font-weight: bold; margin-bottom: 20px;">
UPDATED {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Weekly scores reset for this week!
<br><small>If the page looks outdated, please <a href="cachebuster.html" style="color: white; text-decoration: underline;">click here</a> or clear your browser cache.</small>
</div>"""
            content = content.replace("<body>", f"<body>\n{banner}")
            logging.info("Added banner to index.html")
        
        # Write the modified content back
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info("Successfully modified index.html")
        return True
    except Exception as e:
        logging.error(f"Error modifying index.html: {e}")
        return False

def push_to_github():
    """Push changes to GitHub with force option"""
    try:
        export_path = os.path.join(os.getcwd(), EXPORT_DIR)
        
        logging.info("Adding files to Git...")
        subprocess.run(["git", "add", "-A"], cwd=export_path, check=True)
        
        logging.info("Committing changes...")
        message = f"Weekly reset + Joanna fix + Cache busting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=export_path
        )
        
        logging.info("Force pushing to GitHub...")
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_path, check=True)
        
        logging.info("Successfully pushed to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def create_direct_access_url():
    """Create a direct access URL for the user"""
    try:
        url = f"https://brentcurtis182.github.io/wordle-league/index.html?cb={CACHE_BUSTER}"
        
        logging.info(f"Direct access URL created: {url}")
        logging.info(f"This URL should bypass any caching issues")
        
        # Create a local file with the URL for easy access
        with open("direct_url.txt", "w") as f:
            f.write(f"Direct URL (guaranteed to bypass cache):\n{url}")
        
        return url
    except Exception as e:
        logging.error(f"Error creating direct access URL: {e}")
        return None

def main():
    """Main function"""
    logging.info("=" * 80)
    logging.info("STARTING ULTIMATE FIX")
    logging.info("=" * 80)
    
    # Step 1: Backup database
    logging.info("\nStep 1: Backing up database")
    if backup_database():
        logging.info("Database backup complete")
    
    # Step 2: Remove Joanna's score with validation
    logging.info("\nStep 2: Removing Joanna's score with validation")
    if remove_joanna_score():
        logging.info("Joanna's score removal complete")
    
    # Step 3: Modify export_leaderboard.py for weekly reset
    logging.info("\nStep 3: Modifying export_leaderboard.py")
    if modify_export_leaderboard():
        logging.info("Export leaderboard script modified")
    
    # Step 4: Force weekly reset
    logging.info("\nStep 4: Forcing weekly reset")
    if force_weekly_reset():
        logging.info("Weekly reset forced")
    
    # Step 5: List weekly scores
    logging.info("\nStep 5: Listing weekly scores")
    if list_weekly_scores():
        logging.info("Weekly scores listed")
    
    # Step 6: Rebuild export directory
    logging.info("\nStep 6: Rebuilding export directory")
    if rebuild_export_directory():
        logging.info("Export directory rebuilt")
    
    # Step 7: Run export_leaderboard.py
    logging.info("\nStep 7: Running export_leaderboard.py")
    if run_export_leaderboard():
        logging.info("Leaderboard export complete")
    
    # Step 8: Add cache control
    logging.info("\nStep 8: Adding cache control")
    if add_cache_control():
        logging.info("Cache control added")
    
    # Step 9: Modify index.html
    logging.info("\nStep 9: Modifying index.html")
    if modify_index_html():
        logging.info("Index.html modified")
    
    # Step 10: Push to GitHub
    logging.info("\nStep 10: Pushing to GitHub")
    if push_to_github():
        logging.info("GitHub push complete")
    
    # Step 11: Create direct access URL
    logging.info("\nStep 11: Creating direct access URL")
    url = create_direct_access_url()
    if url:
        logging.info("Direct access URL created")
    
    logging.info("\n" + "=" * 80)
    logging.info("ULTIMATE FIX COMPLETE")
    logging.info("=" * 80)
    logging.info(f"\nAccess the updated website at: {url}")
    logging.info("This URL includes a cache buster that guarantees you see the latest version")
    logging.info("If you still see outdated information, try opening in incognito/private mode")

if __name__ == "__main__":
    main()
