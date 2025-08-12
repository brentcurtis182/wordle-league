#!/usr/bin/env python3
"""
Direct CSS Fix

This script fixes the CSS styling issues on the Wordle League website by:
1. Ensuring styles.css exists in both root and css subdirectory
2. Updating all HTML files to use relative paths that work consistently
"""

import os
import logging
import re
import shutil
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Base directory
WEBSITE_DIR = "website_export"

def ensure_css_directories():
    """Ensure CSS directories exist and files are copied correctly"""
    # Make sure css directory exists at root level
    css_dir = os.path.join(WEBSITE_DIR, "css")
    if not os.path.exists(css_dir):
        os.makedirs(css_dir)
        logging.info(f"Created CSS directory: {css_dir}")
    
    # Copy styles.css to css directory if it doesn't exist there
    root_css = os.path.join(WEBSITE_DIR, "styles.css")
    css_dir_file = os.path.join(css_dir, "styles.css")
    
    if os.path.exists(root_css):
        shutil.copy2(root_css, css_dir_file)
        logging.info(f"Copied styles.css to {css_dir_file}")
    else:
        logging.error("styles.css not found in website_export root!")
        return False
    
    return True

def fix_css_paths_in_file(file_path):
    """Fix CSS paths in a single HTML file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Get relative path to root from this file
    rel_path_to_root = os.path.relpath(WEBSITE_DIR, os.path.dirname(file_path))
    if rel_path_to_root == '.':
        rel_path_to_root = ''
    else:
        # Convert Windows backslashes to forward slashes for web paths
        rel_path_to_root = rel_path_to_root.replace('\\', '/')
        if not rel_path_to_root.endswith('/'):
            rel_path_to_root += '/'
    
    # Define the new CSS path
    if rel_path_to_root:
        new_css_path = f"{rel_path_to_root}css/styles.css"
    else:
        new_css_path = "css/styles.css"
    
    # Find and replace any link tag referencing CSS
    css_link_pattern = re.compile(r'<link\s+[^>]*?href=["\']([^"\']*(?:css|styles)[^"\']*)["\'][^>]*>')
    
    def replace_css_link(match):
        full_match = match.group(0)
        # Keep everything the same but replace just the href value
        return full_match.replace(match.group(1), new_css_path)
    
    new_content = css_link_pattern.sub(replace_css_link, content)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    logging.info(f"Fixed CSS path in {file_path} to {new_css_path}")
    return True

def find_and_fix_all_html_files():
    """Find and fix CSS paths in all HTML files"""
    fixed_files = 0
    
    for root, _, files in os.walk(WEBSITE_DIR):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                if fix_css_paths_in_file(file_path):
                    fixed_files += 1
    
    return fixed_files

def push_to_github():
    """Push changes to GitHub Pages"""
    try:
        # Change to the website directory
        os.chdir(WEBSITE_DIR)
        logging.info(f"Changed to directory: {os.getcwd()}")
        
        # Check status
        status_output = subprocess.check_output(["git", "status"], text=True)
        logging.info(f"Git status: {status_output}")
        
        # Add all changes
        subprocess.check_call(["git", "add", "."])
        logging.info("Added all changes to staging")
        
        # Pull latest changes to avoid conflicts
        pull_output = subprocess.check_output(["git", "pull"], text=True)
        logging.info(f"Pulled latest changes: {pull_output}")
        
        # Create commit message with timestamp
        commit_message = f"Fix: Direct CSS styling fix by ensuring consistent paths ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        subprocess.check_call(["git", "commit", "-m", commit_message])
        logging.info(f"Committed changes: {commit_message}")
        
        # Push to GitHub
        push_output = subprocess.check_output(["git", "push"], text=True)
        logging.info(f"Pushed to GitHub: {push_output}")
        
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    """Main function"""
    logging.info("Starting direct CSS fix")
    
    # Make sure CSS directories and files are set up
    if not ensure_css_directories():
        logging.error("Failed to set up CSS directories")
        return False
    
    # Fix CSS paths in all HTML files
    fixed_count = find_and_fix_all_html_files()
    logging.info(f"Fixed CSS paths in {fixed_count} HTML files")
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Successfully pushed CSS fixes to GitHub Pages")
        print("\nSUCCESS: CSS fixes pushed to GitHub Pages!")
        print("\nThe fixed websites with proper styling should be visible shortly at:")
        print("- Main League: https://brentcurtis182.github.io/wordle-league/")
        print("- Wordle Gang: https://brentcurtis182.github.io/wordle-league/gang/")
        print("- PAL League: https://brentcurtis182.github.io/wordle-league/pal/")
        return True
    else:
        logging.error("Failed to push CSS fixes to GitHub")
        return False

if __name__ == "__main__":
    main()
