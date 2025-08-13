#!/usr/bin/env python
# fix_github_push.py - Script to verify and fix GitHub push issues

import os
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"github_push_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

def check_git_status():
    """Check the status of the Git repository"""
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Check if it's a Git repository
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], 
                          cwd=export_dir, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            logging.error("Not a Git repository. Initializing Git...")
            subprocess.run(["git", "init"], cwd=export_dir, check=True)
        
        # Check remote
        remote_result = subprocess.run(["git", "remote", "-v"], 
                                      cwd=export_dir, capture_output=True, text=True)
        logging.info(f"Remote repositories:\n{remote_result.stdout}")
        
        # Check current branch
        branch_result = subprocess.run(["git", "branch", "--show-current"], 
                                      cwd=export_dir, capture_output=True, text=True)
        current_branch = branch_result.stdout.strip()
        logging.info(f"Current branch: {current_branch}")
        
        # Check status
        status_result = subprocess.run(["git", "status"], 
                                      cwd=export_dir, capture_output=True, text=True)
        logging.info(f"Git status:\n{status_result.stdout}")
        
        return True
    except Exception as e:
        logging.error(f"Error checking Git status: {e}")
        return False

def verify_database_changes():
    """Verify that Joanna's score has been removed from the database"""
    import sqlite3
    
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check scores for Wordle #1500
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.wordle_number = 1500
        """)
        
        scores = cursor.fetchall()
        
        logging.info(f"Current scores for Wordle #1500:")
        has_joanna_score = False
        
        for score in scores:
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display}")
            
            if score['name'] == 'Joanna':
                has_joanna_score = True
        
        if has_joanna_score:
            logging.error("ERROR: Joanna still has a score for Wordle #1500!")
        else:
            logging.info("Verified: Joanna's score for Wordle #1500 has been removed")
            
        return not has_joanna_score
        
    except Exception as e:
        logging.error(f"Database verification error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def force_github_push():
    """Force update to the website files and push to GitHub"""
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Re-export website files first
        logging.info("Re-exporting website files...")
        export_result = subprocess.run(["python", "export_leaderboard.py"], 
                                     capture_output=True, text=True)
        
        if export_result.returncode != 0:
            logging.error(f"Website export failed: {export_result.stderr}")
            return False
        
        logging.info("Website export successful")
        
        # Create or update the timestamp file to force a change
        timestamp_file = os.path.join(export_dir, "last_update.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info("Created timestamp file to force Git to detect changes")
        
        # Configure git
        subprocess.run(["git", "config", "user.name", "brentcurtis182"], 
                      cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Make sure we're on the gh-pages branch
        branch_result = subprocess.run(["git", "branch", "--show-current"], 
                                      cwd=export_dir, capture_output=True, text=True)
        current_branch = branch_result.stdout.strip()
        
        if current_branch != "gh-pages":
            logging.info(f"Current branch is {current_branch}, switching to gh-pages")
            
            # Check if gh-pages branch exists
            branch_check = subprocess.run(["git", "branch"], 
                                         cwd=export_dir, capture_output=True, text=True)
            
            if "gh-pages" in branch_check.stdout:
                # Switch to existing gh-pages branch
                subprocess.run(["git", "checkout", "gh-pages"], 
                              cwd=export_dir, check=True, capture_output=True, text=True)
            else:
                # Create and switch to gh-pages branch
                subprocess.run(["git", "checkout", "-b", "gh-pages"], 
                              cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Add all changes
        logging.info("Adding all changes")
        subprocess.run(["git", "add", "-A"], 
                      cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Commit changes
        commit_message = f"Force update website: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info(f"Committing changes with message: {commit_message}")
        commit_result = subprocess.run(["git", "commit", "-m", commit_message], 
                                      cwd=export_dir, capture_output=True, text=True)
        
        # Force push changes
        logging.info("Force pushing changes to remote")
        push_result = subprocess.run(["git", "push", "-f", "origin", "gh-pages"], 
                                    cwd=export_dir, capture_output=True, text=True)
        
        if push_result.returncode == 0:
            logging.info("Successfully force pushed changes to GitHub")
            logging.info(f"Push output: {push_result.stdout}")
            return True
        else:
            logging.error(f"Failed to push changes to GitHub: {push_result.stderr}")
            
            # Check if the repository has an origin
            remote_check = subprocess.run(["git", "remote", "-v"], 
                                         cwd=export_dir, capture_output=True, text=True)
            
            if "origin" not in remote_check.stdout:
                logging.error("No 'origin' remote found. Please verify the git configuration.")
            
            return False
        
    except Exception as e:
        logging.error(f"Error during GitHub push: {e}")
        return False

def main():
    """Main function to check and fix GitHub push issues"""
    logging.info("Starting GitHub push fix process")
    
    # Step 1: Verify that the database changes have been made
    logging.info("Step 1: Verifying database changes")
    if not verify_database_changes():
        logging.error("Database verification failed! Joanna's score may still be in the database.")
        return
    
    # Step 2: Check the status of the Git repository
    logging.info("Step 2: Checking Git repository status")
    if not check_git_status():
        logging.error("Git status check failed!")
        return
    
    # Step 3: Force push to GitHub
    logging.info("Step 3: Force pushing to GitHub")
    if force_github_push():
        logging.info("GitHub push fix completed successfully!")
    else:
        logging.error("GitHub push failed!")
    
    logging.info("Fix process completed")

if __name__ == "__main__":
    main()
