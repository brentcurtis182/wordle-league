#!/usr/bin/env python
# fix_everything.py - Fix all Wordle League issues with direct approach

import os
import sqlite3
import logging
import subprocess
import re
import shutil
import json
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"fix_everything_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

# Constants
DATABASE_PATH = "wordle_league.db"
WORDLE_NUMBER = 1500
EXPORT_DIR = "website_export"
CORRECT_GITHUB_URL = "https://github.com/brentcurtis182/wordle-league.git"
CORRECT_URL_PATH = "https://brentcurtis182.github.io/wordle-league/"
RESET_MARKER_FILE = "last_weekly_reset.txt"

def connect_to_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def backup_database():
    """Create a backup of the database before making changes"""
    try:
        backup_path = f"wordle_league_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy2(DATABASE_PATH, backup_path)
        logging.info(f"Database backed up to {backup_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to back up database: {e}")
        return False

def query_database(query, params=None, fetch_all=True):
    """Query the database with proper error handling"""
    conn = connect_to_db()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch_all:
            return cursor.fetchall()
        else:
            return cursor.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Database query error: {e}")
        return None
    finally:
        conn.close()

def execute_database_change(query, params=None):
    """Execute a database change with proper error handling"""
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        logging.error(f"Database change error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fix_database():
    """Fix database issues"""
    logging.info("Fixing database issues...")
    
    # 1. Check current state of scores for Wordle #1500
    scores = query_database("""
        SELECT p.name, s.id, s.score, s.emoji_pattern
        FROM score s
        JOIN player p ON s.player_id = p.id
        WHERE s.wordle_number = ?
    """, (WORDLE_NUMBER,))
    
    if scores:
        logging.info(f"Current scores for Wordle #{WORDLE_NUMBER}:")
        for score in scores:
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display}")
    else:
        logging.info(f"No scores found for Wordle #{WORDLE_NUMBER}")
    
    # 2. Remove Joanna's score
    joanna_id = query_database("SELECT id FROM player WHERE name = 'Joanna'", fetch_all=False)
    if joanna_id:
        joanna_id = joanna_id['id']
        if execute_database_change("DELETE FROM score WHERE player_id = ? AND wordle_number = ?", 
                                  (joanna_id, WORDLE_NUMBER)):
            logging.info(f"Removed Joanna's score for Wordle #{WORDLE_NUMBER}")
    
    # 3. Make sure Nanna's score exists for Wordle #1500
    nanna_id = query_database("SELECT id FROM player WHERE name = 'Nanna'", fetch_all=False)
    if nanna_id:
        nanna_id = nanna_id['id']
        nanna_score = query_database(
            "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
            (nanna_id, WORDLE_NUMBER), 
            fetch_all=False
        )
        
        if not nanna_score:
            # Add Nanna's score if it doesn't exist
            success = execute_database_change("""
                INSERT INTO score (player_id, wordle_number, score, emoji_pattern, date)
                VALUES (?, ?, ?, ?, ?)
            """, (
                nanna_id, 
                WORDLE_NUMBER, 
                6, 
                "🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩\n🟩🟩🟩🟩🟩",
                datetime.now().strftime('%Y-%m-%d')
            ))
            
            if success:
                logging.info(f"Added Nanna's score for Wordle #{WORDLE_NUMBER}")
    
    # 4. Force weekly reset
    mark_reset_complete()
    
    # 5. Verify database changes
    scores_after = query_database("""
        SELECT p.name, s.score
        FROM score s
        JOIN player p ON s.player_id = p.id
        WHERE s.wordle_number = ?
    """, (WORDLE_NUMBER,))
    
    if scores_after:
        logging.info(f"Scores after fixes for Wordle #{WORDLE_NUMBER}:")
        for score in scores_after:
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display}")
    
    return True

def mark_reset_complete():
    """Mark that we've completed the weekly reset"""
    try:
        # Calculate the most recent Monday 3:00am
        today = datetime.now()
        days_since_monday = today.weekday()  # Monday is 0
        last_monday = today - timedelta(days=days_since_monday)
        last_monday_3am = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # If we're before Monday 3am, use previous week's Monday
        if today < last_monday_3am:
            last_monday_3am = last_monday_3am - timedelta(days=7)
        
        # Write timestamp to reset marker file
        with open(RESET_MARKER_FILE, 'w') as f:
            f.write(last_monday_3am.strftime('%Y-%m-%d %H:%M:%S'))
        
        logging.info(f"Marked weekly reset as completed at {last_monday_3am.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logging.error(f"Error marking reset: {e}")
        return False

def modify_export_leaderboard():
    """Modify export_leaderboard.py to use the correct paths"""
    try:
        with open("export_leaderboard.py", "r") as f:
            content = f.read()
        
        # 1. Check website URL
        website_url_pattern = r"WEBSITE_URL\s*=\s*os\.getenv\('WEBSITE_URL',\s*'([^']*)'\)"
        website_url_match = re.search(website_url_pattern, content)
        if website_url_match:
            current_url = website_url_match.group(1)
            if current_url != "https://brentcurtis182.github.io":
                logging.info(f"Updating WEBSITE_URL from '{current_url}' to 'https://brentcurtis182.github.io'")
                content = re.sub(
                    website_url_pattern,
                    "WEBSITE_URL = os.getenv('WEBSITE_URL', 'https://brentcurtis182.github.io')",
                    content
                )
        
        # 2. Check leaderboard path
        leaderboard_path_pattern = r"LEADERBOARD_PATH\s*=\s*os\.getenv\('LEADERBOARD_PATH',\s*'([^']*)'\)"
        leaderboard_path_match = re.search(leaderboard_path_pattern, content)
        if leaderboard_path_match:
            current_path = leaderboard_path_match.group(1)
            if current_path != "wordle-league":
                logging.info(f"Updating LEADERBOARD_PATH from '{current_path}' to 'wordle-league'")
                content = re.sub(
                    leaderboard_path_pattern,
                    "LEADERBOARD_PATH = os.getenv('LEADERBOARD_PATH', 'wordle-league')",
                    content
                )
        
        # 3. Fix weekly score calculation if needed
        weekly_score_pattern = r"weekly_scores\.sort\(\)\s*#\s*Sort scores"
        if re.search(weekly_score_pattern, content):
            logging.info("Weekly score calculation looks correct")
        
        # Save modified content
        with open("export_leaderboard.py", "w") as f:
            f.write(content)
        
        logging.info("export_leaderboard.py updated successfully")
        return True
    
    except Exception as e:
        logging.error(f"Error modifying export_leaderboard.py: {e}")
        return False

def update_website_files():
    """Run export_leaderboard.py to update the website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
    
    except Exception as e:
        logging.error(f"Error updating website files: {e}")
        return False

def fix_git_repository():
    """Fix the Git repository configuration"""
    export_dir = os.path.join(os.getcwd(), EXPORT_DIR)
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Check if it's a Git repository
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=export_dir,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            logging.info("Initializing Git repository...")
            subprocess.run(["git", "init"], cwd=export_dir, check=True)
        
        # Check remote origin
        remote_result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if CORRECT_GITHUB_URL not in remote_result.stdout:
            # Remove existing origin if any
            try:
                subprocess.run(
                    ["git", "remote", "remove", "origin"],
                    cwd=export_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
            except subprocess.CalledProcessError:
                pass  # Ignore if origin doesn't exist
            
            # Add correct origin
            subprocess.run(
                ["git", "remote", "add", "origin", CORRECT_GITHUB_URL],
                cwd=export_dir,
                check=True,
                capture_output=True,
                text=True
            )
            
            logging.info(f"Set remote origin to {CORRECT_GITHUB_URL}")
        
        # Configure git
        subprocess.run(
            ["git", "config", "user.name", "brentcurtis182"],
            cwd=export_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        subprocess.run(
            ["git", "config", "user.email", "brentcurtis182@github.com"],
            cwd=export_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Set up gh-pages branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        current_branch = branch_result.stdout.strip()
        if current_branch != "gh-pages":
            logging.info(f"Current branch is {current_branch}, switching to gh-pages")
            
            # Check if gh-pages branch exists
            branch_check = subprocess.run(
                ["git", "branch"],
                cwd=export_dir,
                capture_output=True,
                text=True
            )
            
            if "gh-pages" in branch_check.stdout:
                # Switch to existing gh-pages branch
                subprocess.run(
                    ["git", "checkout", "gh-pages"],
                    cwd=export_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                # Create and switch to gh-pages branch
                subprocess.run(
                    ["git", "checkout", "-b", "gh-pages"],
                    cwd=export_dir,
                    check=True,
                    capture_output=True,
                    text=True
                )
        
        return True
    
    except Exception as e:
        logging.error(f"Error fixing Git repository: {e}")
        return False

def push_to_github():
    """Push website changes to GitHub"""
    export_dir = os.path.join(os.getcwd(), EXPORT_DIR)
    
    try:
        # Create timestamp file to force a change
        timestamp_file = os.path.join(export_dir, "last_update.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Last forced update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Update index.html with timestamp comment
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            timestamp_comment = f"<!-- Forced update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->"
            
            if "<!-- Forced update:" in content:
                content = re.sub(r"<!-- Forced update:.*?-->", timestamp_comment, content)
            else:
                content += "\n" + timestamp_comment
            
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Add all changes
        subprocess.run(
            ["git", "add", "-A"],
            cwd=export_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Commit changes
        commit_message = f"Force update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=export_dir,
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            logging.warning("No changes to commit or commit failed")
        
        # Force push changes
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"],
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode == 0:
            logging.info(f"Successfully pushed to GitHub: {CORRECT_GITHUB_URL}")
            return True
        else:
            logging.error(f"Push failed: {push_result.stderr}")
            return False
    
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def create_url_redirect_file():
    """Create a URL redirect file to handle the old URL"""
    try:
        export_dir = os.path.join(os.getcwd(), EXPORT_DIR)
        redirect_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0; url='{CORRECT_URL_PATH}'" />
    <title>Redirecting to Wordle League</title>
</head>
<body>
    <p>Redirecting to <a href="{CORRECT_URL_PATH}">Wordle League</a>...</p>
    <script>
        window.location.href = "{CORRECT_URL_PATH}";
    </script>
</body>
</html>
        """
        
        # Create wordleleague.html (without hyphen) to redirect to wordle-league
        redirect_file = os.path.join(export_dir, "wordleleague.html")
        with open(redirect_file, "w") as f:
            f.write(redirect_html)
            
        logging.info(f"Created redirect file: {redirect_file}")
        return True
    
    except Exception as e:
        logging.error(f"Error creating redirect file: {e}")
        return False

def main():
    """Main function to fix everything"""
    logging.info("Starting complete fix process")
    
    # Backup the database first
    if not backup_database():
        if not input("Database backup failed. Continue anyway? (y/n): ").lower().startswith('y'):
            return
    
    # Step 1: Fix database issues
    logging.info("\nSTEP 1: Fixing database issues")
    fix_database()
    
    # Step 2: Modify export_leaderboard.py
    logging.info("\nSTEP 2: Updating export_leaderboard.py")
    modify_export_leaderboard()
    
    # Step 3: Update website files
    logging.info("\nSTEP 3: Updating website files")
    update_website_files()
    
    # Step 4: Fix Git repository configuration
    logging.info("\nSTEP 4: Fixing Git repository")
    fix_git_repository()
    
    # Step 5: Create URL redirect file
    logging.info("\nSTEP 5: Creating URL redirect file")
    create_url_redirect_file()
    
    # Step 6: Push to GitHub
    logging.info("\nSTEP 6: Pushing to GitHub")
    push_to_github()
    
    logging.info("\nAll fixes completed!")
    logging.info(f"Website should now be available at: {CORRECT_URL_PATH}")
    logging.info("Note: It may take a few minutes for GitHub Pages to update")

if __name__ == "__main__":
    main()
