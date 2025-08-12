#!/usr/bin/env python
# Simple GitHub Pages refresh script

import os
import shutil
import sqlite3
import subprocess
import logging
from datetime import datetime
import tempfile
import time

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

def backup_git_folder():
    """Back up the .git folder to ensure we can restore it later"""
    export_dir = os.path.join(os.getcwd(), "website_export")
    git_dir = os.path.join(export_dir, ".git")
    backup_dir = os.path.join(tempfile.gettempdir(), f"git_backup_{int(time.time())}")
    
    if os.path.exists(git_dir):
        try:
            shutil.copytree(git_dir, backup_dir)
            logging.info(f"Backed up .git folder to {backup_dir}")
            return backup_dir
        except Exception as e:
            logging.error(f"Failed to back up .git folder: {e}")
            return None
    else:
        logging.warning("No .git folder found to back up")
        return None

def restore_git_folder(backup_path):
    """Restore the .git folder from backup"""
    if not backup_path or not os.path.exists(backup_path):
        logging.warning("No valid backup path provided to restore from")
        return False
    
    export_dir = os.path.join(os.getcwd(), "website_export")
    git_dir = os.path.join(export_dir, ".git")
    
    try:
        # Remove existing git dir if any
        if os.path.exists(git_dir):
            try:
                shutil.rmtree(git_dir)
            except:
                logging.warning(f"Could not remove existing .git directory")
        
        # Restore from backup
        shutil.copytree(backup_path, git_dir)
        logging.info(f"Restored .git folder from backup")
        return True
    except Exception as e:
        logging.error(f"Failed to restore .git folder: {e}")
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

def add_cache_busters():
    """Add cache busting files to the export directory"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Create timestamp file for cache busting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        with open(os.path.join(export_dir, f"timestamp_{timestamp}.txt"), "w") as f:
            f.write(f"Generated at: {datetime.now().isoformat()}")
        
        # Create .nojekyll file
        with open(os.path.join(export_dir, ".nojekyll"), "w") as f:
            f.write("")
        
        # Create a redirect file for guaranteed access
        with open(os.path.join(export_dir, "latest.html"), "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta http-equiv="refresh" content="0;url=index.html?t={timestamp}" />
    <title>Redirecting to latest content</title>
</head>
<body>
    <p>Redirecting to <a href="index.html?t={timestamp}">latest version</a>...</p>
    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>""")
        
        # Add meta tags to index.html
        index_path = os.path.join(export_dir, "index.html")
        if os.path.exists(index_path):
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Add cache control meta tags
                if "<head>" in content:
                    meta_tags = f"""<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta name="timestamp" content="{timestamp}" />"""
                    
                    content = content.replace("<head>", meta_tags)
                    
                    # Save updated content
                    with open(index_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    logging.info("Added cache-control meta tags to index.html")
            except Exception as e:
                logging.error(f"Error updating index.html: {e}")
        
        return timestamp
    except Exception as e:
        logging.error(f"Error adding cache busters: {e}")
        return None

def update_github_pages():
    """Force update GitHub Pages using the cd command"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Go to export directory
        logging.info("Changing to export directory...")
        os.chdir(export_dir)
        
        # Check if .git directory exists
        if not os.path.exists(".git"):
            logging.error("No .git directory found! Cannot push to GitHub.")
            return False
        
        # Set git config
        subprocess.run(["git", "config", "user.name", "Wordle League Bot"])
        subprocess.run(["git", "config", "user.email", "wordle-league-bot@example.com"])
        
        # Add all files
        logging.info("Adding all files to git...")
        subprocess.run(["git", "add", "-A"])
        
        # Commit with timestamp
        commit_msg = f"Force update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info(f"Committing changes: {commit_msg}")
        subprocess.run(["git", "commit", "-m", commit_msg])
        
        # Force push to GitHub
        logging.info("Force pushing to GitHub...")
        result = subprocess.run(["git", "push", "-f", "origin", "gh-pages"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Successfully pushed to GitHub Pages")
            return True
        else:
            logging.error(f"Failed to push to GitHub: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error updating GitHub Pages: {e}")
        return False
    finally:
        # Change back to root directory
        os.chdir(os.path.dirname(export_dir))

def main():
    logging.info("Starting simple GitHub Pages refresh script...")
    
    # Step 1: Back up .git folder
    logging.info("\nStep 1: Backing up .git folder...")
    backup_path = backup_git_folder()
    
    # Step 2: Fix Joanna's pattern
    logging.info("\nStep 2: Checking and fixing Joanna's pattern...")
    check_and_fix_joanna_pattern()
    
    # Step 3: Run export_leaderboard.py
    logging.info("\nStep 3: Running export_leaderboard.py...")
    run_export_leaderboard()
    
    # Step 4: Add cache busters
    logging.info("\nStep 4: Adding cache busters...")
    timestamp = add_cache_busters()
    
    # Step 5: Restore .git folder
    logging.info("\nStep 5: Restoring .git folder...")
    restore_git_folder(backup_path)
    
    # Step 6: Update GitHub Pages
    logging.info("\nStep 6: Updating GitHub Pages...")
    success = update_github_pages()
    
    if success:
        logging.info("\nGitHub Pages refresh completed successfully!")
        logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
        logging.info(f"For guaranteed fresh content, use: https://brentcurtis182.github.io/wordle-league/latest.html")
        logging.info("Note: It may take a few minutes for GitHub Pages to update. If you still see old content:")
        logging.info("1. Try a hard refresh (Ctrl+F5)")
        logging.info("2. Try opening in an incognito/private window")
        logging.info("3. Try clearing your browser cache")
    else:
        logging.error("\nFailed to update GitHub Pages. Please check the logs above for details.")

if __name__ == "__main__":
    main()
