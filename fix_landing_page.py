#!/usr/bin/env python3
"""
Script to fix the landing page issue by copying landing.html to index.html
"""

import os
import shutil
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_landing.log"),
        logging.StreamHandler()
    ]
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def copy_landing_to_index():
    """Copy the landing.html file to index.html in the website_export directory"""
    try:
        export_dir = "website_export"
        
        # Define paths
        LANDING_PAGE = os.path.join(SCRIPT_DIR, "website_export", "landing.html")
        # Change the destination to a landing directory instead of overwriting index.html
        LANDING_DIR = os.path.join(SCRIPT_DIR, "website_export", "landing")
        LANDING_INDEX = os.path.join(LANDING_DIR, "index.html")
        # Keep this for reference but we won't use it
        # INDEX_PAGE = os.path.join(SCRIPT_DIR, "website_export", "index.html")
        
        # Check if landing.html exists
        if not os.path.exists(LANDING_PAGE):
            logging.error(f"landing.html not found in {export_dir}")
            return False
        
        # Create the landing directory if it doesn't exist
        if not os.path.exists(LANDING_DIR):
            os.makedirs(LANDING_DIR)
        
        # Copy landing.html to index.html in the landing directory
        shutil.copyfile(LANDING_PAGE, LANDING_INDEX)
        logging.info(f"Successfully copied landing.html to {LANDING_INDEX}")
        # Copy landing.html to index.html
        shutil.copyfile(landing_file, index_file)
        logging.info(f"Successfully copied landing.html to index.html")
        return True
    
    except Exception as e:
        logging.error(f"Error copying landing file: {e}")
        return False

def push_to_github():
    """Push the fixed index.html to GitHub Pages"""
    try:
        # Change to the website directory
        os.chdir("website_export")
        
        # Make sure we're on gh-pages branch
        subprocess.run(["git", "checkout", "gh-pages"], check=True)
        
        # Add the index.html file
        subprocess.run(["git", "add", "index.html"], check=True)
        
        # Commit the change
        commit_message = f"Fix landing page display - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        
        logging.info("Successfully pushed updated index.html to GitHub Pages")
        return True
        
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    logging.info("Starting landing page fix process...")
    
    # Copy landing.html to index.html
    if not copy_landing_to_index():
        logging.error("Failed to fix landing page")
        return False
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Landing page fix completed successfully")
        print("Landing page fix completed successfully!")
        print("All leagues should now be visible at https://brentcurtis182.github.io/wordle-league/")
        return True
    else:
        logging.error("Failed to push landing page fix to GitHub")
        print("Failed to push landing page fix. Check fix_landing.log for details.")
        return False

if __name__ == "__main__":
    main()
