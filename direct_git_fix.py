#!/usr/bin/env python
# Direct fix for Joanna's pattern and GitHub Pages

import os
import sqlite3
import subprocess
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_and_fix_joanna_pattern():
    """Check and fix Joanna's emoji pattern directly in the database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get Joanna's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        joanna_id = cursor.fetchone()["id"]
        logging.info(f"Joanna's player ID: {joanna_id}")
        
        # Get her current score for Wordle 1500
        cursor.execute("""
            SELECT id, score, emoji_pattern 
            FROM score 
            WHERE player_id = ? AND wordle_number = 1500
        """, (joanna_id,))
        
        score_record = cursor.fetchone()
        if not score_record:
            logging.error("No score found for Joanna for Wordle 1500")
            conn.close()
            return False
            
        score_id = score_record["id"]
        score = score_record["score"]
        pattern = score_record["emoji_pattern"]
        
        logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}")
        
        # Count rows in pattern
        rows = 0
        if pattern:
            rows = pattern.count('\n') + 1
            logging.info(f"Pattern has {rows} rows but score is {score}")
        
        # Fix if there's a mismatch
        if score == 5 and (rows != 5 or not pattern):
            logging.info("Fixing Joanna's pattern to match her 5/6 score")
            
            # Create a proper 5-row pattern
            new_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
            
            # Update in database
            cursor.execute("""
                UPDATE score 
                SET emoji_pattern = ? 
                WHERE id = ?
            """, (new_pattern, score_id))
            
            conn.commit()
            logging.info("Updated Joanna's pattern in the database")
            
            # Verify the update
            cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
            updated_pattern = cursor.fetchone()["emoji_pattern"]
            updated_rows = updated_pattern.count('\n') + 1
            logging.info(f"Verified pattern now has {updated_rows} rows")
            
            conn.close()
            return True
        else:
            logging.info("No fix needed or pattern already correct")
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Error fixing Joanna's pattern: {e}")
        return False

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
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def setup_git_repo():
    """Set up a fresh git repository in the export directory"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Check if .git directory exists
        git_dir = os.path.join(export_dir, ".git")
        if os.path.exists(git_dir):
            logging.info("Removing existing .git directory")
            shutil.rmtree(git_dir)
        
        # Initialize new repository
        os.chdir(export_dir)
        
        # Initialize git
        subprocess.run(["git", "init"], check=True)
        logging.info("Git repository initialized")
        
        # Configure git
        subprocess.run(["git", "config", "user.name", "brentcurtis182"], check=True)
        subprocess.run(["git", "config", "user.email", "wordle.league.bot@example.com"], check=True)
        logging.info("Git user configured")
        
        # Add remote origin
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/brentcurtis182/wordle-league.git"], check=True)
        logging.info("Git remote added")
        
        # Create gh-pages branch
        subprocess.run(["git", "checkout", "-b", "gh-pages"], check=True)
        logging.info("Created gh-pages branch")
        
        # Change back to main directory
        os.chdir(os.path.dirname(export_dir))
        
        return True
    except Exception as e:
        logging.error(f"Error setting up git repository: {e}")
        os.chdir(os.path.dirname(export_dir))  # Ensure we change back to main directory
        return False

def add_cache_busting():
    """Add cache busting to website files"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Create timestamp file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        with open(os.path.join(export_dir, f"timestamp_{timestamp}.txt"), "w") as f:
            f.write(f"Cache busting timestamp: {datetime.now().isoformat()}")
        
        # Create .nojekyll file
        with open(os.path.join(export_dir, ".nojekyll"), "w") as f:
            f.write("")
        
        # Add a direct latest version file
        with open(os.path.join(export_dir, "latest.html"), "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta http-equiv="refresh" content="0;url=index.html?t={timestamp}">
    <title>Latest Wordle League</title>
</head>
<body>
    <p>Redirecting to <a href="index.html?t={timestamp}">latest version</a>...</p>
    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>""")
        
        return True
    except Exception as e:
        logging.error(f"Error adding cache busting: {e}")
        return False

def push_to_github():
    """Push changes to GitHub with authentication"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        os.chdir(export_dir)
        
        # Check if GitHub token is available
        github_token = os.environ.get("GITHUB_TOKEN")
        github_username = os.environ.get("GITHUB_USERNAME")
        
        if github_token and github_username:
            # Set up authenticated URL
            auth_url = f"https://{github_username}:{github_token}@github.com/brentcurtis182/wordle-league.git"
            
            # Add all files
            subprocess.run(["git", "add", "."], check=True)
            logging.info("Added all files to git")
            
            # Commit changes
            commit_msg = f"Fix Joanna's pattern and update website: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            logging.info(f"Committed changes: {commit_msg}")
            
            # Push to GitHub
            subprocess.run(["git", "push", "-f", auth_url, "gh-pages"], check=True)
            logging.info("Successfully pushed to GitHub Pages")
            
            # Change back to main directory
            os.chdir(os.path.dirname(export_dir))
            
            return True
        else:
            logging.error("GitHub token or username not found in environment variables")
            os.chdir(os.path.dirname(export_dir))
            return False
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        os.chdir(os.path.dirname(export_dir))
        return False

def main():
    logging.info("Starting direct git fix for Joanna's pattern...")
    
    # Step 1: Fix Joanna's pattern
    logging.info("\nStep 1: Checking and fixing Joanna's pattern...")
    check_and_fix_joanna_pattern()
    
    # Step 2: Run export_leaderboard.py
    logging.info("\nStep 2: Running export_leaderboard.py...")
    run_export_leaderboard()
    
    # Step 3: Set up git repository
    logging.info("\nStep 3: Setting up git repository...")
    if not setup_git_repo():
        logging.error("Failed to set up git repository, aborting")
        return
    
    # Step 4: Add cache busting
    logging.info("\nStep 4: Adding cache busting...")
    add_cache_busting()
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub...")
    if not push_to_github():
        logging.error("Failed to push to GitHub, aborting")
        return
    
    logging.info("\nDirect git fix completed successfully!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info(f"For guaranteed fresh content, use: https://brentcurtis182.github.io/wordle-league/latest.html")
    logging.info("\nNote: GitHub Pages may take a few minutes to update the content.")

if __name__ == "__main__":
    main()
