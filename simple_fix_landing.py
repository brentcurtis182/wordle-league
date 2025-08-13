#!/usr/bin/env python3
"""
Simple script to fix both landing.html and index.html to show all 5 leagues
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
        logging.FileHandler("simple_fix_landing.log"),
        logging.StreamHandler()
    ]
)

def fix_landing_pages():
    """Add the missing leagues to both landing.html and index.html"""
    try:
        export_dir = "website_export"
        landing_file = os.path.join(export_dir, "landing.html")
        index_file = os.path.join(export_dir, "index.html")
        
        # Read the current landing.html content
        with open(landing_file, 'r', encoding='utf-8') as f:
            landing_content = f.read()
        
        # Create the HTML for the new leagues to add
        new_leagues_html = """
            <div class="league-card">
                <h2 class="league-title">Wordle Party</h2>
                <p class="league-description">League with Brent, Jess, Matt, and Ryan</p>
                <a href="party/index.html" class="league-link">View League</a>
            </div>
            
            <div class="league-card">
                <h2 class="league-title">Wordle Vball</h2>
                <p class="league-description">League with Brent, Jason, and Shawna</p>
                <a href="vball/index.html" class="league-link">View League</a>
            </div>
"""
        
        # Find the position to insert the new leagues (after the PAL league)
        pal_div_close_pos = landing_content.find('</div>', landing_content.find('Wordle PAL'))
        if pal_div_close_pos == -1:
            logging.error("Could not find the PAL league closing div")
            return False
            
        # Insert the new leagues after the PAL league card
        container_close_pos = pal_div_close_pos + 6  # Length of '</div>'
        updated_landing_content = landing_content[:container_close_pos] + new_leagues_html + landing_content[container_close_pos:]
        
        # Write the updated content to landing.html
        with open(landing_file, 'w', encoding='utf-8') as f:
            f.write(updated_landing_content)
        
        # Copy the updated landing.html to index.html
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(updated_landing_content)
            
        logging.info("Successfully updated landing.html and index.html with all 5 leagues")
        return True
        
    except Exception as e:
        logging.error(f"Error fixing landing pages: {e}")
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
        commit_message = f"Fix landing page to show all 5 leagues - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        
        logging.info("Successfully pushed updated landing and index files to GitHub Pages")
        return True
        
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    logging.info("Starting simple landing pages fix process...")
    
    # Fix landing.html and index.html
    if not fix_landing_pages():
        logging.error("Failed to fix landing pages")
        return False
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Landing pages fix completed successfully")
        print("Landing pages fix completed successfully!")
        print("All 5 leagues should now be visible at:")
        print("- https://brentcurtis182.github.io/wordle-league/")
        print("- https://brentcurtis182.github.io/wordle-league/landing")
        return True
    else:
        logging.error("Failed to push landing pages fix to GitHub")
        print("Failed to push landing pages fix. Check simple_fix_landing.log for details.")
        return False

if __name__ == "__main__":
    main()
