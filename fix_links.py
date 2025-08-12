#!/usr/bin/env python3
"""
Script to fix clickable links for the two new leagues on landing page
"""

import os
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_links.log"),
        logging.StreamHandler()
    ]
)

def fix_links():
    """Fix the links for the two new leagues to make them clickable on desktop browsers"""
    try:
        export_dir = "website_export"
        landing_file = os.path.join(export_dir, "landing.html")
        index_file = os.path.join(export_dir, "index.html")
        
        # Fix HTML code for both files
        for file_path in [landing_file, index_file]:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Fix 1: Ensure z-index is properly set for league cards
            if "z-index:" not in content:
                content = content.replace(".league-card {", ".league-card {\n            position: relative;\n            z-index: 1;")
                
            # Fix 2: Ensure the link covers the entire card for better clickability
            if ".league-link {" in content:
                content = content.replace(".league-link {", ".league-link {\n            position: relative;\n            z-index: 2;")
                
            # Fix 3: Add explicit pointer cursor for better usability
            if "cursor: pointer;" not in content:
                content = content.replace(".league-link:hover {", ".league-link:hover {\n            cursor: pointer;")
                
            # Fix 4: Ensure the link itself has no pointer-events issues
            if "pointer-events: auto;" not in content:
                content = content.replace(".league-link {", ".league-link {\n            pointer-events: auto;")
                
            # Write the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        logging.info("Successfully fixed links for better desktop browser clickability")
        return True
    
    except Exception as e:
        logging.error(f"Error fixing links: {e}")
        return False

def push_to_github():
    """Push the fixed files to GitHub Pages"""
    try:
        # Change to the website directory
        os.chdir("website_export")
        
        # Make sure we're on gh-pages branch
        subprocess.run(["git", "checkout", "gh-pages"], check=True)
        
        # Add the modified files
        subprocess.run(["git", "add", "landing.html", "index.html"], check=True)
        
        # Commit the changes
        commit_message = f"Fix clickable links for desktop browsers - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        
        logging.info("Successfully pushed link fixes to GitHub Pages")
        return True
        
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    logging.info("Starting link fix process...")
    
    # Fix links for better clickability
    if not fix_links():
        logging.error("Failed to fix links")
        return False
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Link fix completed successfully")
        print("\nLink fix completed successfully!")
        print("The league links should now be properly clickable on desktop browsers.")
        print("Changes made:")
        print("1. Added z-index to league cards for proper layering")
        print("2. Improved link positioning and clickability")
        print("3. Added explicit pointer cursor for better usability")
        print("\nYou can verify the changes at:")
        print("- https://brentcurtis182.github.io/wordle-league/")
        print("- https://brentcurtis182.github.io/wordle-league/landing")
        return True
    else:
        logging.error("Failed to push link fixes to GitHub")
        print("Failed to push link fixes. Check fix_links.log for details.")
        return False

if __name__ == "__main__":
    main()
