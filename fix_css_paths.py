#!/usr/bin/env python3
"""
Fix CSS Paths and Push to GitHub

This script:
1. Ensures all HTML files reference the CSS correctly 
2. Pushes the fixes to GitHub Pages
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
        logging.FileHandler("css_fix.log"),
        logging.StreamHandler()
    ]
)

# Directory to fix and push
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

def fix_css_references():
    """Fix CSS references in HTML files"""
    base_dir = WEBSITE_DIR
    
    # Fix main index.html
    main_index = os.path.join(base_dir, "index.html")
    if os.path.exists(main_index):
        run_command([
            "powershell", "-Command",
            "(Get-Content -Path index.html -Encoding UTF8) -replace '../css/styles.css', 'styles.css' | Set-Content -Path index.html -Encoding UTF8"
        ], cwd=base_dir)
        logging.info(f"Fixed CSS path in {main_index}")
    
    # Fix league index files
    for league in ["pal", "gang"]:
        league_index = os.path.join(base_dir, league, "index.html")
        if os.path.exists(league_index):
            run_command([
                "powershell", "-Command",
                "(Get-Content -Path index.html -Encoding UTF8) -replace '../css/styles.css', '../styles.css' | Set-Content -Path index.html -Encoding UTF8"
            ], cwd=os.path.join(base_dir, league))
            logging.info(f"Fixed CSS path in {league_index}")
    
    # Fix daily files
    for league in ["", "pal/", "gang/"]:
        daily_dir = os.path.join(base_dir, f"{league}daily")
        if os.path.exists(daily_dir):
            for file in os.listdir(daily_dir):
                if file.endswith(".html"):
                    daily_file = os.path.join(daily_dir, file)
                    run_command([
                        "powershell", "-Command", 
                        f"(Get-Content -Path \"{file}\" -Encoding UTF8) -replace 'styles.css', '../../styles.css' | Set-Content -Path \"{file}\" -Encoding UTF8"
                    ], cwd=daily_dir)
                    logging.info(f"Fixed CSS path in {daily_file}")

def push_to_github():
    """Push CSS fixes to GitHub Pages"""
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
            f"Fix: Restore CSS styling by fixing stylesheet paths ({timestamp})"
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
    """Main function to fix CSS and push to GitHub Pages"""
    logging.info("Starting CSS path fix")
    
    # First fix all CSS references
    fix_css_references()
    
    # Then push to GitHub
    success = push_to_github()
    
    if success:
        logging.info("Successfully pushed CSS fixes to GitHub Pages")
    else:
        logging.error("Failed to push CSS fixes to GitHub Pages")
    
    return success

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: CSS fixes pushed to GitHub Pages!")
        print("\nThe fixed websites with proper styling should be visible shortly at:")
        print("- Main League: https://brentcurtis182.github.io/wordle-league/")
        print("- Wordle Gang: https://brentcurtis182.github.io/wordle-league/gang/")
        print("- PAL League: https://brentcurtis182.github.io/wordle-league/pal/")
    else:
        print("\nERROR: Failed to push CSS fixes to GitHub Pages.")
        print("Check the log file for details.")
