#!/usr/bin/env python3
# Wordle League GitHub Pages Deployment Script
# This script exports the leaderboard and deploys it to GitHub Pages

import os
import subprocess
import re
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_publish.log"),
        logging.StreamHandler()
    ]
)

# Constants
EXPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "website_export")
REPO_URL = "https://github.com/brentcurtis182/wordle-league.git"
GITHUB_PAGES_URL = "https://brentcurtis182.github.io/wordle-league/"

def run_command(command, cwd=None):
    """Run a shell command and return the output"""
    try:
        logging.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        logging.info(f"Command output: {result.stdout.strip()}")
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return None

def export_leaderboard():
    """Run the export script to generate website files"""
    logging.info("Running multi-league export script...")
    run_command("python export_leaderboard_multi_league.py")
    logging.info("Export complete")

def get_wordle_number():
    """Extract the current Wordle number from the index.html file"""
    try:
        index_path = os.path.join(EXPORT_DIR, "index.html")
        with open(index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'Wordle #(\d+)', content)
            if match:
                return match.group(1)
    except Exception as e:
        logging.error(f"Error extracting Wordle number: {e}")
    
    # Default to current date if Wordle number can't be extracted
    return datetime.now().strftime("%Y%m%d")

def deploy_to_github():
    """Deploy the website to GitHub Pages"""
    logging.info("Starting GitHub Pages deployment...")
    
    # Step 1: Export the leaderboard (Disabled - using update_all_correct_structure.py instead)
    # export_leaderboard()
    
    # Step 2: Navigate to the website_export directory
    os.chdir(EXPORT_DIR)
    
    # Step 3: Make sure we're on the gh-pages branch
    run_command("git fetch origin")
    run_command("git checkout gh-pages")
    
    # Step 4: Try to pull latest changes (may fail if there are conflicts)
    try:
        run_command("git pull origin gh-pages")
    except Exception as e:
        logging.warning(f"Could not pull latest changes: {e}")
    
    # Step 5: Add all changes
    run_command("git add .")
    
    # Step 6: Commit changes
    wordle_number = get_wordle_number()
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Update website with fixed emoji patterns for Wordle #{wordle_number} - {date}"
    run_command(f'git commit -m "{commit_message}"')
    
    # Step 7: Try to push to GitHub
    push_result = run_command("git push origin gh-pages")
    
    # Step 8: If push fails, try force push
    if not push_result or "error:" in push_result or "rejected" in push_result:
        logging.warning("Normal push failed, attempting force push...")
        force_result = run_command("git push --force origin gh-pages")
        if force_result and "error:" not in force_result:
            logging.info("Force push successful!")
        else:
            logging.error("Force push also failed.")
    
    logging.info(f"Deployment complete. Website should be updated at {GITHUB_PAGES_URL}")
    logging.info("Note: It may take a few minutes for GitHub Pages to update.")

if __name__ == "__main__":
    try:
        deploy_to_github()
    except Exception as e:
        logging.error(f"Deployment failed: {e}")
