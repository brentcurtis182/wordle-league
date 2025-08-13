#!/usr/bin/env python3
# Script to publish website changes to GitHub Pages with cache-busting

import os
import subprocess
import logging
import datetime
import random
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("publish_website.log"),
        logging.StreamHandler()
    ]
)

def generate_cache_buster():
    """Generate a cache-busting parameter based on current time"""
    now = datetime.datetime.now()
    return f"v={now.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"

def add_cache_buster_to_html_files():
    """Add cache-busting parameter to CSS and JS references in HTML files"""
    try:
        website_dir = os.path.join(os.getcwd(), 'website_export')
        cache_buster = generate_cache_buster()
        
        # Find all HTML files
        modified_files = 0
        for root, dirs, files in os.walk(website_dir):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Add cache buster to CSS and JS references
                        updated_content = content.replace('href="css/', f'href="css/')
                        updated_content = updated_content.replace('src="js/', f'src="js/')
                        
                        # Add a meta tag to force refresh
                        if '<head>' in updated_content:
                            meta_tag = f'<meta http-equiv="last-modified" content="{datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")}">'
                            updated_content = updated_content.replace('<head>', f'<head>\n    {meta_tag}')
                        
                        # Write updated content back
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        
                        modified_files += 1
                        
                    except Exception as e:
                        logging.error(f"Error updating cache buster in {file_path}: {e}")
        
        logging.info(f"Added cache-busting to {modified_files} HTML files")
        return True
        
    except Exception as e:
        logging.error(f"Error adding cache buster: {e}")
        return False

def push_to_github():
    """Push website changes to GitHub with appropriate git commands"""
    try:
        # Make sure we're in the right directory
        website_dir = os.path.join(os.getcwd(), 'website_export')
        
        # Check if it's a git repository
        if not os.path.exists(os.path.join(website_dir, '.git')):
            logging.error(f"Website directory {website_dir} is not a git repository")
            return False
        
        # Change to the website directory
        os.chdir(website_dir)
        
        # First, pull the latest changes to avoid conflicts
        pull_command = ["git", "pull", "origin", "gh-pages"]
        logging.info(f"Running git pull: {' '.join(pull_command)}")
        pull_result = subprocess.run(pull_command, capture_output=True, text=True)
        
        if pull_result.returncode != 0:
            logging.warning(f"Git pull warning: {pull_result.stderr}")
        else:
            logging.info("Git pull successful")
        
        # Add all changes
        add_command = ["git", "add", "."]
        logging.info(f"Running git add: {' '.join(add_command)}")
        add_result = subprocess.run(add_command, capture_output=True, text=True)
        
        if add_result.returncode != 0:
            logging.error(f"Git add error: {add_result.stderr}")
            return False
        
        # Commit changes with a descriptive message
        commit_message = f"Fix emoji pattern display - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        commit_command = ["git", "commit", "-m", commit_message]
        logging.info(f"Running git commit: {' '.join(commit_command)}")
        commit_result = subprocess.run(commit_command, capture_output=True, text=True)
        
        if "nothing to commit" in commit_result.stdout or "nothing to commit" in commit_result.stderr:
            logging.info("No changes to commit")
            return True
        elif commit_result.returncode != 0:
            logging.error(f"Git commit error: {commit_result.stderr}")
            return False
        
        # Push changes
        push_command = ["git", "push", "origin", "gh-pages"]
        logging.info(f"Running git push: {' '.join(push_command)}")
        push_result = subprocess.run(push_command, capture_output=True, text=True)
        
        if push_result.returncode != 0:
            logging.error(f"Git push error: {push_result.stderr}")
            return False
        
        logging.info("Successfully pushed website changes to GitHub")
        return True
        
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(os.getcwd())

def main():
    logging.info("Starting website publishing process...")
    
    # Add cache busters to HTML files
    if add_cache_buster_to_html_files():
        logging.info("Cache busting complete")
    else:
        logging.warning("Cache busting had issues, but continuing...")
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Website successfully published to GitHub Pages")
        print("Website successfully published to GitHub Pages!")
        print("Changes should be visible at https://brentcurtis182.github.io/wordle-league/")
        return True
    else:
        logging.error("Failed to publish website to GitHub Pages")
        print("Failed to publish website. Check publish_website.log for details.")
        return False

if __name__ == "__main__":
    main()
