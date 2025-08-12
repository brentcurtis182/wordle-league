#!/usr/bin/env python3
"""
Script to fix the player name in the Wordle Party league description on the landing page
"""

import os
import logging
import re
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_player_name.log"),
        logging.StreamHandler()
    ]
)

def fix_player_name():
    """Fix the player name in the Wordle Party league description from Ryan to Kinley"""
    try:
        export_dir = "website_export"
        landing_file = os.path.join(export_dir, "landing.html")
        index_file = os.path.join(export_dir, "index.html")
        
        # Fix landing.html
        with open(landing_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace Ryan with Kinley in the Wordle Party description
        fixed_content = re.sub(
            r'(Wordle Party</h2>\s*<p class="league-description">League with Brent, Jess, Matt, and )Ryan',
            r'\1Kinley',
            content
        )
        
        with open(landing_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
            
        # Fix index.html
        with open(index_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Replace Ryan with Kinley in the Wordle Party description
        fixed_content = re.sub(
            r'(Wordle Party</h2>\s*<p class="league-description">League with Brent, Jess, Matt, and )Ryan',
            r'\1Kinley',
            content
        )
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
            
        logging.info("Successfully updated player name from Ryan to Kinley in league descriptions")
        return True
    
    except Exception as e:
        logging.error(f"Error fixing player name: {e}")
        return False

def push_to_github():
    """Push the fixed landing.html and index.html to GitHub Pages"""
    try:
        # Change to the website directory
        os.chdir("website_export")
        
        # Make sure we're on gh-pages branch
        subprocess.run(["git", "checkout", "gh-pages"], check=True)
        
        # Add the modified files
        subprocess.run(["git", "add", "landing.html", "index.html"], check=True)
        
        # Commit the changes
        commit_message = f"Fix player name in Wordle Party description - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        
        logging.info("Successfully pushed player name fix to GitHub Pages")
        return True
        
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    logging.info("Starting player name fix process...")
    
    # Fix player name in league descriptions
    if not fix_player_name():
        logging.error("Failed to fix player name")
        return False
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Player name fix completed successfully")
        print("Player name fix completed successfully!")
        print("The Wordle Party league description now shows 'Kinley' instead of 'Ryan'")
        return True
    else:
        logging.error("Failed to push player name fix to GitHub")
        print("Failed to push player name fix. Check fix_player_name.log for details.")
        return False

if __name__ == "__main__":
    main()
