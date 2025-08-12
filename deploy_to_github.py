#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deploy Wordle League website files to GitHub Pages with cache-busting
"""

import os
import subprocess
import logging
import time
import re
import random
import string
import shutil
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Configuration
WEBSITE_EXPORT_PATH = os.path.join(SCRIPT_DIR, "website_export")
GITHUB_PAGES_DIR = os.path.join(SCRIPT_DIR, "github_pages_temp")

# Ensure the GitHub Pages temp directory exists
if not os.path.exists(GITHUB_PAGES_DIR):
    os.makedirs(GITHUB_PAGES_DIR, exist_ok=True)

def generate_cache_buster():
    """Generate a random cache-busting string"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_chars = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{timestamp}_{random_chars}"

def add_cache_buster_to_files():
    """Add cache-busting parameters to CSS and JS references in HTML files"""
    cache_buster = generate_cache_buster()
    logging.info(f"Using cache buster: {cache_buster}")
    
    for root, _, files in os.walk(WEBSITE_EXPORT_PATH):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add cache-busting to CSS files
                    content = re.sub(
                        r'href="([^"]+\.css)(?:\?[^"]*)?(")',
                        f'href="\\1?v={cache_buster}\\2',
                        content
                    )
                    
                    # Add cache-busting to JS files
                    content = re.sub(
                        r'src="([^"]+\.js)(?:\?[^"]*)?(")',
                        f'src="\\1?v={cache_buster}\\2',
                        content
                    )
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                        
                    logging.info(f"Added cache-busting to {file_path}")
                except Exception as e:
                    logging.error(f"Error adding cache-busting to {file_path}: {e}")

def copy_website_files():
    """Copy website files to GitHub repository folder"""
    # First, add cache-busting parameters
    add_cache_buster_to_files()
    
    # Clear the GitHub pages directory
    try:
        if os.path.exists(GITHUB_PAGES_DIR):
            for item in os.listdir(GITHUB_PAGES_DIR):
                if item == '.git':
                    continue  # Keep the .git directory
                    
                item_path = os.path.join(GITHUB_PAGES_DIR, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        else:
            os.makedirs(GITHUB_PAGES_DIR, exist_ok=True)
        
        # Copy all website export files to GitHub directory
        for item in os.listdir(WEBSITE_EXPORT_PATH):
            source = os.path.join(WEBSITE_EXPORT_PATH, item)
            destination = os.path.join(GITHUB_PAGES_DIR, item)
            
            if os.path.isdir(source):
                shutil.copytree(source, destination, dirs_exist_ok=True)
            else:
                shutil.copy2(source, destination)
        
        logging.info(f"Copied website files from {WEBSITE_EXPORT_PATH} to {GITHUB_PAGES_DIR}")
        return True
    except Exception as e:
        logging.error(f"Error copying files: {e}")
        return False

def clone_or_update_repo():
    """Clone or update the GitHub Pages repository"""
    try:
        # Check if .git directory exists in the GitHub pages directory
        git_dir = os.path.join(GITHUB_PAGES_DIR, '.git')
        if not os.path.exists(git_dir):
            # Clone the repository
            logging.info("Cloning GitHub repository")
            subprocess.run(['git', 'clone', 'https://github.com/brentcurtis182/wordle-league.git', GITHUB_PAGES_DIR], check=True)
        else:
            # Update the repository
            logging.info("Updating existing GitHub repository")
            os.chdir(GITHUB_PAGES_DIR)
            subprocess.run(['git', 'pull'], check=True)
        
        return True
    except Exception as e:
        logging.error(f"Error cloning/updating repository: {e}")
        return False

def commit_and_push():
    """Commit and push changes to GitHub"""
    try:
        # Change to GitHub repository directory
        os.chdir(GITHUB_PAGES_DIR)
        
        # Configure Git if needed (in case this is a fresh clone)
        try:
            subprocess.run(['git', 'config', 'user.email', 'wordle.league@example.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Wordle League Bot'], check=True)
        except Exception as e:
            logging.warning(f"Could not configure Git user: {e}")
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit changes
        commit_message = f"Update website with fixed scores consistency - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        except subprocess.CalledProcessError:
            logging.info("No changes to commit, repository is up to date")
            return True
        
        # Push to GitHub
        subprocess.run(['git', 'push'], check=True)
        
        logging.info("Successfully pushed to GitHub Pages")
        logging.info("Website should be available at https://brentcurtis182.github.io/wordle-league/")
        return True
    except Exception as e:
        logging.error(f"Error during Git operations: {e}")
        return False

def main():
    """Main deployment function"""
    logging.info("Starting deployment to GitHub Pages")
    
    # First, clone or update the GitHub Pages repository
    if not clone_or_update_repo():
        logging.error("Failed to clone/update repository. Aborting deployment.")
        return False
    
    # Copy website files to the repository directory
    if not copy_website_files():
        logging.error("Failed to copy website files. Aborting deployment.")
        return False
    
    # Commit and push the changes
    if not commit_and_push():
        logging.error("Failed to commit and push. Deployment incomplete.")
        return False
    
    logging.info("Deployment complete!")
    logging.info("Website should be available at https://brentcurtis182.github.io/wordle-league/ within a few minutes")
    return True

if __name__ == "__main__":
    main()
