#!/usr/bin/env python3
"""
Push Website to GitHub Pages

This script:
1. Adds all changes in the website_export directory
2. Pulls the latest changes from the remote repo first
3. Commits with a clear message about the fresh start
4. Pushes to GitHub Pages
"""

import os
import subprocess
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_push.log"),
        logging.StreamHandler()
    ]
)

# Directory to push
WEBSITE_DIR = "website_export"

def run_command(command, cwd=None):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            text=True,
            capture_output=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}")
        logging.error(f"Error: {e.stderr.strip()}")
        return None

def push_to_github():
    """Push website files to GitHub Pages"""
    if not os.path.isdir(WEBSITE_DIR):
        logging.error(f"Website directory {WEBSITE_DIR} not found")
        return False
        
    try:
        # Step 1: Navigate to website directory
        os.chdir(WEBSITE_DIR)
        logging.info(f"Changed to directory: {os.getcwd()}")
        
        # Step 2: Check git status
        status = run_command(["git", "status"])
        logging.info(f"Git status: {status}")
        
        # Step 3: Add all changes
        add_result = run_command(["git", "add", "."])
        logging.info("Added all changes to staging")
        
        # Step 4: Pull latest changes first (avoid rejection)
        pull_result = run_command(["git", "pull", "origin", "gh-pages"])
        logging.info(f"Pulled latest changes: {pull_result}")
        
        # Step 5: Commit changes
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_result = run_command([
            "git", "commit", "-m", 
            f"Fresh start: Clear all scores for database overhaul ({timestamp})"
        ])
        
        if commit_result is None:
            logging.warning("Nothing to commit, working tree clean")
            return True
            
        logging.info(f"Committed changes: {commit_result}")
        
        # Step 6: Push to GitHub
        push_result = run_command(["git", "push", "origin", "gh-pages"])
        logging.info(f"Pushed to GitHub: {push_result}")
        
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    """Main function to push to GitHub Pages"""
    logging.info("Starting GitHub Pages push")
    
    success = push_to_github()
    
    if success:
        logging.info("Successfully pushed to GitHub Pages")
    else:
        logging.error("Failed to push to GitHub Pages")
    
    return success

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Website changes pushed to GitHub Pages!")
        print("\nThe cleared websites should be visible shortly at:")
        print("- Main League: https://brentcurtis182.github.io/wordle-league/")
        print("- Wordle Gang: https://brentcurtis182.github.io/wordle-league/gang/")
        print("- PAL League: https://brentcurtis182.github.io/wordle-league/pal/")
    else:
        print("\nERROR: Failed to push to GitHub Pages.")
        print("Check the log file for details.")
