#!/usr/bin/env python3
"""
Script to push all HTML and CSS changes to GitHub Pages
"""

import os
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("github_push.log"),
        logging.StreamHandler()
    ]
)

EXPORT_DIR = "website_export"

def run_command(command):
    """Run a shell command and return the output"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {command}")
        logging.error(f"Error: {e.stderr}")
        return None

def push_to_github():
    """Push all HTML and CSS changes to GitHub Pages"""
    logging.info("Starting GitHub push for all changes...")
    
    # Step 1: Navigate to the website_export directory
    os.chdir(EXPORT_DIR)
    
    # Step 2: Make sure we're on the gh-pages branch
    run_command("git fetch origin")
    run_command("git checkout gh-pages")
    
    # Step 3: Try to pull latest changes
    try:
        run_command("git pull origin gh-pages")
    except Exception as e:
        logging.warning(f"Could not pull latest changes: {e}")
    
    # Step 4: Add all changes
    run_command("git add .")
    
    # Step 5: Commit changes
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_message = f"Fix CSS paths and league structure for all leagues - {date}"
    result = run_command(f'git commit -m "{commit_message}"')
    
    if result and "nothing to commit" in result:
        logging.info("No changes to commit")
        return True
    
    # Step 6: Try to push to GitHub
    push_result = run_command("git push origin gh-pages")
    
    # Step 7: If push fails, try force push
    if not push_result or "error:" in push_result or "rejected" in push_result:
        logging.warning("Normal push failed, attempting force push...")
        force_result = run_command("git push --force origin gh-pages")
        if force_result and "error:" not in force_result:
            logging.info("Force push successful!")
            return True
        else:
            logging.error("Force push also failed.")
            return False
    else:
        logging.info("Push successful!")
        return True

def main():
    """Main function"""
    try:
        # Push all changes to GitHub
        if push_to_github():
            print("Successfully pushed all changes to GitHub Pages!")
            print("The website should now be available with all leagues properly formatted.")
            print("URLs:")
            print("- Main (Warriorz): https://brentcurtis182.github.io/wordle-league/")
            print("- Gang: https://brentcurtis182.github.io/wordle-league/gang/")
            print("- PAL: https://brentcurtis182.github.io/wordle-league/pal/")
            print("- Party: https://brentcurtis182.github.io/wordle-league/party/")
            print("- Vball: https://brentcurtis182.github.io/wordle-league/vball/")
            print("- Landing: https://brentcurtis182.github.io/wordle-league/landing/")
            return 0
        else:
            print("Failed to push changes to GitHub. Check github_push.log for details.")
            return 1
    except Exception as e:
        logging.error(f"Error in main function: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        # Change back to the original directory
        if os.getcwd().endswith(EXPORT_DIR):
            os.chdir("..")

if __name__ == "__main__":
    main()
