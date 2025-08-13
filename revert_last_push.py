#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Revert the last push to GitHub Pages for Wordle League
"""

import os
import subprocess
import logging
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GITHUB_PAGES_DIR = os.path.join(SCRIPT_DIR, "github_pages_temp")

def clone_or_update_repo():
    """Clone or update the GitHub Pages repository"""
    try:
        # Check if repo directory exists, remove if it does
        if os.path.exists(GITHUB_PAGES_DIR):
            shutil.rmtree(GITHUB_PAGES_DIR)
        
        # Clone the repository
        logging.info("Cloning GitHub repository")
        subprocess.run(['git', 'clone', 'https://github.com/brentcurtis182/wordle-league.git', GITHUB_PAGES_DIR], check=True)
        
        return True
    except Exception as e:
        logging.error(f"Error cloning repository: {e}")
        return False

def revert_last_commit():
    """Revert the last commit and push the revert"""
    try:
        # Change to GitHub repository directory
        os.chdir(GITHUB_PAGES_DIR)
        
        # Configure Git
        subprocess.run(['git', 'config', 'user.email', 'wordle.league@example.com'], check=True)
        subprocess.run(['git', 'config', 'user.name', 'Wordle League Bot'], check=True)
        
        # Get last commit hash for reference
        last_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('utf-8').strip()
        logging.info(f"Last commit: {last_commit}")
        
        # Revert the last commit
        subprocess.run(['git', 'revert', '--no-edit', 'HEAD'], check=True)
        
        # Push the revert
        subprocess.run(['git', 'push'], check=True)
        
        logging.info(f"Successfully reverted last commit ({last_commit[:7]})")
        logging.info("Website should be restored to previous state within a few minutes")
        return True
    except Exception as e:
        logging.error(f"Error during revert operation: {e}")
        return False

def main():
    """Main function to revert the last push"""
    logging.info("Starting revert of last GitHub Pages push")
    
    # First, clone the repository
    if not clone_or_update_repo():
        logging.error("Failed to clone repository. Aborting revert.")
        return False
    
    # Revert the last commit
    if not revert_last_commit():
        logging.error("Failed to revert last commit. Revert incomplete.")
        return False
    
    logging.info("Revert complete!")
    return True

if __name__ == "__main__":
    main()
