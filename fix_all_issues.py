#!/usr/bin/env python
# fix_all_issues.py - Fix all issues with Wordle League

import os
import sqlite3
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"wordle_fix_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

# Constants
DATABASE_PATH = "wordle_league.db"
WORDLE_NUMBER = 1500
PLAYER_NAME = "Joanna"
CORRECT_GITHUB_PATH = "wordle-league"  # The correct path with hyphen

def connect_to_db():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def remove_joanna_score():
    """Remove Joanna's score for Wordle #1500"""
    conn = connect_to_db()
    if not conn:
        logging.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check for Joanna's ID
        cursor.execute("SELECT id FROM player WHERE name = ?", (PLAYER_NAME,))
        player_row = cursor.fetchone()
        
        if not player_row:
            logging.error(f"Player '{PLAYER_NAME}' not found in database")
            return False
        
        player_id = player_row['id']
        logging.info(f"Found player: {PLAYER_NAME}, ID: {player_id}")
        
        # Check if Joanna has a score for this Wordle
        cursor.execute(
            "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
            (player_id, WORDLE_NUMBER)
        )
        
        score_row = cursor.fetchone()
        if not score_row:
            logging.info(f"No score found for {PLAYER_NAME}, Wordle #{WORDLE_NUMBER}")
            return True  # Nothing to delete
        
        score_id = score_row['id']
        logging.info(f"Found score ID: {score_id}")
        
        # Delete the score
        cursor.execute("DELETE FROM score WHERE id = ?", (score_id,))
        conn.commit()
        
        logging.info(f"Removed score ID {score_id} for {PLAYER_NAME}, Wordle #{WORDLE_NUMBER}")
        
        # Verify the deletion
        cursor.execute(
            "SELECT id FROM score WHERE player_id = ? AND wordle_number = ?", 
            (player_id, WORDLE_NUMBER)
        )
        
        if cursor.fetchone():
            logging.error(f"Failed to delete score for {PLAYER_NAME}, Wordle #{WORDLE_NUMBER}")
            return False
        
        logging.info(f"Successfully removed score for {PLAYER_NAME}, Wordle #{WORDLE_NUMBER}")
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verify_database():
    """Verify database state after changes"""
    conn = connect_to_db()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check all scores for Wordle #1500
        logging.info(f"Current scores for Wordle #{WORDLE_NUMBER}:")
        cursor.execute("""
            SELECT p.name, s.score, s.emoji_pattern 
            FROM score s
            JOIN player p ON s.player_id = p.id
            WHERE s.wordle_number = ?
            ORDER BY p.name
        """, (WORDLE_NUMBER,))
        
        scores = cursor.fetchall()
        has_joanna_score = False
        
        for score in scores:
            score_display = "X/6" if score['score'] == 7 else f"{score['score']}/6"
            logging.info(f"  {score['name']}: {score_display}")
            
            if score['name'] == PLAYER_NAME:
                has_joanna_score = True
        
        if has_joanna_score:
            logging.error(f"ERROR: {PLAYER_NAME} still has a score for Wordle #{WORDLE_NUMBER}!")
            return False
        
        logging.info(f"Verified: {PLAYER_NAME}'s score has been removed successfully")
        return True
        
    finally:
        conn.close()

def update_website_files():
    """Run export_leaderboard.py to update the website files"""
    try:
        logging.info("Updating website files...")
        result = subprocess.run(
            ["python", "export_leaderboard.py"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            logging.error(f"Error updating website files: {result.stderr}")
            return False
        
        logging.info("Successfully updated website files")
        return True
    except Exception as e:
        logging.error(f"Exception updating website files: {e}")
        return False

def check_export_config():
    """Check the export configuration to ensure correct paths"""
    with open("export_leaderboard.py", "r") as f:
        content = f.read()
    
    # Check LEADERBOARD_PATH value
    if "LEADERBOARD_PATH = os.getenv('LEADERBOARD_PATH', 'wordle-league')" in content:
        logging.info("Export configuration LEADERBOARD_PATH is set correctly to 'wordle-league'")
        return True
    elif "LEADERBOARD_PATH = os.getenv('LEADERBOARD_PATH', 'wordleleague')" in content:
        logging.warning("Found incorrect LEADERBOARD_PATH: 'wordleleague', should be 'wordle-league'")
        
        # Fix the path
        fixed_content = content.replace(
            "LEADERBOARD_PATH = os.getenv('LEADERBOARD_PATH', 'wordleleague')",
            "LEADERBOARD_PATH = os.getenv('LEADERBOARD_PATH', 'wordle-league')"
        )
        
        with open("export_leaderboard.py", "w") as f:
            f.write(fixed_content)
            
        logging.info("Fixed LEADERBOARD_PATH in export_leaderboard.py")
        return True
    else:
        logging.warning("Could not locate LEADERBOARD_PATH setting in export_leaderboard.py")
        return False

def check_github_repository():
    """Check the GitHub repository configuration in the website_export directory"""
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Check if it's a Git repository
        try:
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=export_dir, 
                check=True, 
                capture_output=True, 
                text=True
            )
        except subprocess.CalledProcessError:
            logging.error("Not a Git repository")
            return False
        
        # Check remote
        remote_result = subprocess.run(
            ["git", "remote", "-v"], 
            cwd=export_dir, 
            capture_output=True, 
            text=True
        )
        
        logging.info(f"Remote repositories:\n{remote_result.stdout}")
        
        # Check current branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"], 
            cwd=export_dir, 
            capture_output=True, 
            text=True
        )
        
        current_branch = branch_result.stdout.strip()
        logging.info(f"Current branch: {current_branch}")
        
        return True
    except Exception as e:
        logging.error(f"Error checking Git repository: {e}")
        return False

def force_github_push():
    """Force update to GitHub with corrected paths"""
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Configure git if needed
        subprocess.run(
            ["git", "config", "user.name", "brentcurtis182"], 
            cwd=export_dir, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        # Make sure we're on the gh-pages branch
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"], 
            cwd=export_dir, 
            capture_output=True, 
            text=True
        )
        
        current_branch = branch_result.stdout.strip()
        
        if current_branch != "gh-pages":
            logging.info(f"Current branch is {current_branch}, switching to gh-pages")
            try:
                # Try to checkout existing branch
                subprocess.run(
                    ["git", "checkout", "gh-pages"], 
                    cwd=export_dir, 
                    check=True, 
                    capture_output=True, 
                    text=True
                )
            except subprocess.CalledProcessError:
                # Create new branch if it doesn't exist
                subprocess.run(
                    ["git", "checkout", "-b", "gh-pages"], 
                    cwd=export_dir, 
                    check=True, 
                    capture_output=True, 
                    text=True
                )
        
        # Pull latest changes first
        try:
            logging.info("Pulling latest changes from GitHub...")
            subprocess.run(
                ["git", "pull", "origin", "gh-pages"], 
                cwd=export_dir, 
                check=True, 
                capture_output=True, 
                text=True
            )
        except subprocess.CalledProcessError:
            logging.warning("Failed to pull changes, continuing anyway...")
        
        # Create timestamp file to force a change
        timestamp_file = os.path.join(export_dir, "last_update.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Also update index.html with comment
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add timestamp comment
            timestamp_comment = f"<!-- Force update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->"
            
            if "<!-- Force update:" in content:
                # Replace existing comment
                import re
                content = re.sub(r"<!-- Force update:.*?-->", timestamp_comment, content)
            else:
                # Add new comment at end
                content += "\n" + timestamp_comment
            
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)
        
        # Add all changes
        logging.info("Adding all changes to Git")
        subprocess.run(
            ["git", "add", "-A"], 
            cwd=export_dir, 
            check=True, 
            capture_output=True, 
            text=True
        )
        
        # Commit changes
        commit_message = f"Force update with corrected paths: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info(f"Committing with message: {commit_message}")
        
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
        logging.info("Force pushing changes to GitHub")
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"], 
            cwd=export_dir, 
            capture_output=True, 
            text=True
        )
        
        if push_result.returncode == 0:
            logging.info("Successfully pushed changes to GitHub")
            return True
        else:
            logging.error(f"Failed to push to GitHub: {push_result.stderr}")
            return False
    
    except Exception as e:
        logging.error(f"Error during GitHub push: {e}")
        return False

def main():
    """Main function to fix all issues"""
    logging.info("Starting comprehensive fix process")
    
    # Step 1: Remove Joanna's score
    logging.info("\nSTEP 1: Removing Joanna's score")
    if not remove_joanna_score():
        logging.error("Failed to remove Joanna's score")
    
    # Step 2: Verify database changes
    logging.info("\nSTEP 2: Verifying database changes")
    if not verify_database():
        logging.error("Database verification failed")
    
    # Step 3: Check export configuration
    logging.info("\nSTEP 3: Checking export configuration")
    check_export_config()
    
    # Step 4: Update website files
    logging.info("\nSTEP 4: Updating website files")
    if not update_website_files():
        logging.error("Failed to update website files")
    
    # Step 5: Check GitHub repository
    logging.info("\nSTEP 5: Checking GitHub repository")
    if not check_github_repository():
        logging.error("Failed to check GitHub repository")
    
    # Step 6: Force push to GitHub
    logging.info("\nSTEP 6: Pushing to GitHub with correct path")
    if not force_github_push():
        logging.error("Failed to push to GitHub")
    
    logging.info("\nAll fixes completed!")

if __name__ == "__main__":
    main()
