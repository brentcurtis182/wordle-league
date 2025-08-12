#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Safe deployment script for Wordle League website to GitHub Pages
Preserves emoji patterns and ensures proper UTF-8 encoding
"""

import os
import subprocess
import logging
import shutil
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WEBSITE_EXPORT_PATH = os.path.join(SCRIPT_DIR, "website_export")
GITHUB_PAGES_DIR = os.path.join(SCRIPT_DIR, "github_pages_temp")

def clean_temp_dir():
    """Clean up the temporary GitHub pages directory"""
    if os.path.exists(GITHUB_PAGES_DIR):
        try:
            shutil.rmtree(GITHUB_PAGES_DIR)
        except Exception as e:
            logging.warning(f"Could not remove temp directory: {e}")
            # If we can't remove it, try to clean it
            for root, dirs, files in os.walk(GITHUB_PAGES_DIR):
                for file in files:
                    try:
                        os.remove(os.path.join(root, file))
                    except:
                        pass

    # Create fresh directory
    os.makedirs(GITHUB_PAGES_DIR, exist_ok=True)
    return True

def clone_repository():
    """Clone the GitHub Pages repository"""
    try:
        logging.info("Cloning GitHub repository")
        subprocess.run(['git', 'clone', 'https://github.com/brentcurtis182/wordle-league.git', GITHUB_PAGES_DIR], check=True)
        return True
    except Exception as e:
        logging.error(f"Error cloning repository: {e}")
        return False

def add_cache_busting_param(html_content, timestamp):
    """Safely add cache-busting parameter to CSS and JS references"""
    # Only target href and src attributes with .css or .js extensions
    css_pattern = re.compile(r'href="([^"]+\.css)(?:\?[^"]*)?(")')
    js_pattern = re.compile(r'src="([^"]+\.js)(?:\?[^"]*)?(")')
    
    # Replace with cache busting parameter
    html_content = css_pattern.sub(f'href="\\1?v={timestamp}\\2', html_content)
    html_content = js_pattern.sub(f'src="\\1?v={timestamp}\\2', html_content)
    
    return html_content

def copy_website_files():
    """Safely copy website files to GitHub Pages directory with cache-busting"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    logging.info(f"Using cache buster timestamp: {timestamp}")
    
    try:
        # Copy all website export files to GitHub directory
        for root, dirs, files in os.walk(WEBSITE_EXPORT_PATH):
            # Get relative path from WEBSITE_EXPORT_PATH
            rel_path = os.path.relpath(root, WEBSITE_EXPORT_PATH)
            # Create corresponding directory in GITHUB_PAGES_DIR
            if rel_path != '.':
                os.makedirs(os.path.join(GITHUB_PAGES_DIR, rel_path), exist_ok=True)
            
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(GITHUB_PAGES_DIR, rel_path, file) if rel_path != '.' else os.path.join(GITHUB_PAGES_DIR, file)
                
                if file.endswith('.html'):
                    # For HTML files, read content, add cache busting, then write
                    try:
                        with open(src_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Only modify the CSS and JS references
                        content = add_cache_busting_param(content, timestamp)
                        
                        with open(dst_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        logging.info(f"Processed HTML file with cache-busting: {os.path.relpath(src_file, WEBSITE_EXPORT_PATH)}")
                    except Exception as e:
                        logging.error(f"Error processing HTML file {src_file}: {e}")
                        # Fall back to direct copy if HTML processing fails
                        shutil.copy2(src_file, dst_file)
                else:
                    # For non-HTML files, just copy directly
                    shutil.copy2(src_file, dst_file)
        
        return True
    except Exception as e:
        logging.error(f"Error copying website files: {e}")
        return False

def commit_and_push():
    """Commit and push changes to GitHub"""
    try:
        # Change to GitHub repository directory
        os.chdir(GITHUB_PAGES_DIR)
        
        # Configure Git
        try:
            subprocess.run(['git', 'config', 'user.email', 'wordle.league@example.com'], check=True)
            subprocess.run(['git', 'config', 'user.name', 'Wordle League Bot'], check=True)
        except Exception as e:
            logging.warning(f"Could not configure Git user: {e}")
        
        # Add all files
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit changes
        commit_message = f"Update Wordle League website with fixed emoji patterns - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        try:
            result = subprocess.run(['git', 'commit', '-m', commit_message], check=True, capture_output=True, text=True)
            logging.info(f"Commit result: {result.stdout}")
        except subprocess.CalledProcessError as e:
            if "nothing to commit" in str(e.stdout) or "nothing to commit" in str(e.stderr):
                logging.info("No changes to commit, repository is up to date")
                return True
            raise
        
        # Pull first to integrate remote changes
        try:
            subprocess.run(['git', 'pull', '--rebase'], check=True)
            logging.info("Successfully pulled latest changes from GitHub")
        except Exception as e:
            logging.warning(f"Could not pull latest changes: {e}")
            # If pull fails, try a force push
            logging.info("Attempting force push...")
            try:
                subprocess.run(['git', 'push', '--force'], check=True)
                logging.info("Successfully force pushed to GitHub Pages")
                logging.info("Website should be available at https://brentcurtis182.github.io/wordle-league/ within a few minutes")
                return True
            except Exception as e2:
                logging.error(f"Force push failed: {e2}")
                return False
        
        # Push to GitHub
        subprocess.run(['git', 'push'], check=True)
        
        logging.info("Successfully pushed to GitHub Pages")
        logging.info("Website should be available at https://brentcurtis182.github.io/wordle-league/ within a few minutes")
        return True
    except Exception as e:
        logging.error(f"Error during Git operations: {e}")
        return False

def main():
    """Main deployment function"""
    logging.info("Starting safe deployment to GitHub Pages")
    
    # Clean up temp directory
    clean_temp_dir()
    
    # Clone the repository
    if not clone_repository():
        logging.error("Failed to clone repository. Aborting deployment.")
        return False
    
    # Copy website files
    if not copy_website_files():
        logging.error("Failed to copy website files. Aborting deployment.")
        return False
    
    # Commit and push
    if not commit_and_push():
        logging.error("Failed to commit and push. Deployment incomplete.")
        return False
    
    logging.info("Deployment complete!")
    return True

if __name__ == "__main__":
    main()
