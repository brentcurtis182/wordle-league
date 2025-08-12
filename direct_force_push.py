#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct Force Push Script for Wordle League Website
This script will directly force push the fixed website files to GitHub Pages.
"""

import os
import subprocess
import logging
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(SCRIPT_DIR, "website_export")
REPO_URL = "https://github.com/brentcurtis182/wordle-league.git"
TEMP_DIR = os.path.join(SCRIPT_DIR, "temp_gh_pages")

def run_command(cmd, cwd=None):
    """Run a command and return the output"""
    try:
        logging.info(f"Running: {cmd}")
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        if result.stdout:
            logging.info(f"Output: {result.stdout.strip()}")
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        if e.stderr:
            logging.error(f"Error output: {e.stderr}")
        return False, str(e.stderr) if e.stderr else str(e)
    except Exception as e:
        logging.error(f"Exception: {e}")
        return False, str(e)

def clean_temp_dir():
    """Clean up the temporary directory"""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            logging.info(f"Removed existing directory: {TEMP_DIR}")
        except Exception as e:
            logging.error(f"Failed to remove temp directory: {e}")
            # Try a more aggressive approach with system commands
            if os.name == 'nt':  # Windows
                run_command(f"rmdir /s /q {TEMP_DIR}")
            else:  # Unix/Linux
                run_command(f"rm -rf {TEMP_DIR}")

def clone_repo_gh_pages():
    """Clone only the gh-pages branch to a temp directory"""
    clean_temp_dir()
    os.makedirs(TEMP_DIR, exist_ok=True)
    success, output = run_command(f"git clone --single-branch --branch gh-pages {REPO_URL} {TEMP_DIR}")
    return success

def copy_export_files():
    """Copy all website files to the temp directory"""
    try:
        # Copy all website files (excluding .git directory)
        for item in os.listdir(EXPORT_DIR):
            src = os.path.join(EXPORT_DIR, item)
            dst = os.path.join(TEMP_DIR, item)
            
            if os.path.isdir(src):
                if item == '.git':
                    continue  # Skip .git directory
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
                
        logging.info("Successfully copied website files to temp directory")
        return True
    except Exception as e:
        logging.error(f"Failed to copy website files: {e}")
        return False

def commit_and_force_push():
    """Commit changes and force push to GitHub"""
    # Add all files
    success, _ = run_command("git add .", cwd=TEMP_DIR)
    if not success:
        return False
    
    # Commit with a clear message about the fix
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Fix emoji patterns display (removed 'No emoji pattern available' text) - {timestamp}"
    success, _ = run_command(f'git commit -m "{commit_message}"', cwd=TEMP_DIR)
    if not success:
        # Not a failure, might just be nothing to commit
        logging.info("No changes to commit or commit failed")
    
    # Force push to origin
    success, output = run_command("git push --force origin gh-pages", cwd=TEMP_DIR)
    return success

def main():
    logging.info("Starting direct force push deployment")
    
    # Step 1: Clone the repo (gh-pages branch only)
    if not clone_repo_gh_pages():
        logging.error("Failed to clone repository. Aborting.")
        return False
    
    # Step 2: Copy all website files
    if not copy_export_files():
        logging.error("Failed to copy website files. Aborting.")
        return False
    
    # Step 3: Commit and force push
    if not commit_and_force_push():
        logging.error("Failed to push to GitHub. Deployment failed.")
        return False
    
    logging.info("Deployment successful!")
    logging.info("Website should be updated at https://brentcurtis182.github.io/wordle-league/ within a few minutes")
    return True

if __name__ == "__main__":
    main()
