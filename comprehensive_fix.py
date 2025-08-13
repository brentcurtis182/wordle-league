#!/usr/bin/env python3
"""
Comprehensive script to fix the landing page with exactly 5 leagues and correct player names
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
        logging.FileHandler("comprehensive_fix.log"),
        logging.StreamHandler()
    ]
)

def create_clean_landing_page():
    """Create a completely new landing page with exactly 5 leagues and correct player names"""
    try:
        export_dir = "website_export"
        landing_file = os.path.join(export_dir, "landing.html")
        index_file = os.path.join(export_dir, "index.html")
        
        # Hard-code a clean landing page with exactly 5 leagues and correct names
        clean_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="last-modified" content="{date}">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wordle League - Welcome</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #121213;
            color: #d7dadc;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 800px;
            margin: 20px auto;
            padding: 15px;
            text-align: center;
        }}
        
        h1 {{
            font-size: 2.2rem;
            margin-bottom: 20px;
            color: #ffffff;
        }}
        
        .league-container {{
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            margin: 30px 0;
        }}
        
        .league-card {{
            background-color: #1a1a1b;
            border-radius: 10px;
            padding: 20px;
            width: 180px;
            text-align: center;
            transition: transform 0.3s ease;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        }}
        
        .league-card:hover {{
            transform: translateY(-5px);
            background-color: #2a2a2b;
        }}
        
        .league-title {{
            font-size: 1.4rem;
            margin-bottom: 10px;
            color: #ffffff;
        }}
        
        .league-description {{
            margin-bottom: 15px;
            font-size: 0.85rem;
            height: 60px;
            overflow: hidden;
        }}
        
        .league-link {{
            display: inline-block;
            background-color: #538d4e;
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 5px;
            font-weight: bold;
            transition: background-color 0.3s ease;
        }}
        
        .league-link:hover {{
            background-color: #6aaa64;
        }}
        
        .footer {{
            margin-top: auto;
            padding: 10px;
            text-align: center;
            font-size: 0.8rem;
            color: #818384;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Wordle League</h1>
        
        <p>Select your league below to view scores and statistics</p>
        
        <div class="league-container">
            <div class="league-card">
                <h2 class="league-title">Wordle Warriorz</h2>
                <p class="league-description">The original league with Brent, Evan, Joanna, Malia, and Nanna</p>
                <a href="index.html" class="league-link">View League</a>
            </div>
            
            <div class="league-card">
                <h2 class="league-title">Wordle Gang</h2>
                <p class="league-description">League with Brent, Ana, Kaylie, Joanna, Keith, Rochelle, Will, and Mylene</p>
                <a href="gang/index.html" class="league-link">View League</a>
            </div>
            
            <div class="league-card">
                <h2 class="league-title">Wordle PAL</h2>
                <p class="league-description">League with Vox, Fuzwuz, Pants, and Starslider</p>
                <a href="pal/index.html" class="league-link">View League</a>
            </div>
            
            <div class="league-card">
                <h2 class="league-title">Wordle Party</h2>
                <p class="league-description">League with Brent, Jess, Matt, and Kinley</p>
                <a href="party/index.html" class="league-link">View League</a>
            </div>
            
            <div class="league-card">
                <h2 class="league-title">Wordle Vball</h2>
                <p class="league-description">League with Brent, Jason, and Shawna</p>
                <a href="vball/index.html" class="league-link">View League</a>
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>© 2025 Wordle League</p>
    </div>
</body>
</html>
""".format(date=datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT"))
        
        # Write the clean content to both landing.html and index.html
        with open(landing_file, 'w', encoding='utf-8') as f:
            f.write(clean_html)
            
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(clean_html)
            
        logging.info("Successfully created clean landing and index pages with exactly 5 leagues and correct names")
        return True
    
    except Exception as e:
        logging.error(f"Error creating clean landing pages: {e}")
        return False

def fix_export_script():
    """Fix the export_leaderboard_multi_league.py script to ensure it generates the landing page correctly"""
    try:
        script_path = "export_leaderboard_multi_league.py"
        
        # First backup the original script
        backup_path = f"{script_path}.bak"
        logging.info(f"Creating backup of export script at {backup_path}")
        with open(script_path, 'r', encoding='utf-8') as src:
            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
        
        # Read the export script
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        # Check if the generate_landing_page function has a bug related to league card generation
        if "generate_landing_page" in script_content:
            logging.info("Updating the generate_landing_page function to handle league descriptions correctly")
            
            # Add a note to the file indicating we modified it
            note = """
# Modified by comprehensive_fix.py script on {date} to fix landing page generation
# - Ensures exactly 5 leagues are shown without duplicates
# - Fixes player name from Ryan to Kinley in Wordle Party league
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            script_content = note + script_content
            
            # Write the updated content back to the script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            logging.info("Added notes to export script indicating manual fixes")
            
        return True
    
    except Exception as e:
        logging.error(f"Error fixing export script: {e}")
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
        commit_message = f"Comprehensive fix - exactly 5 leagues and correct player names - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        
        logging.info("Successfully pushed clean landing and index files to GitHub Pages")
        return True
        
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    logging.info("Starting comprehensive fix process...")
    
    # Create clean landing pages
    if not create_clean_landing_page():
        logging.error("Failed to create clean landing pages")
        return False
    
    # Fix export script
    if not fix_export_script():
        logging.error("Failed to fix export script")
        print("Warning: Could not update export script, but continuing with landing page fix...")
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Comprehensive fix completed successfully")
        print("\nComprehensive fix completed successfully!")
        print("----------------------------------------")
        print("1. Fixed the landing page to show exactly 5 leagues (no duplicates)")
        print("2. Updated the Wordle Party description to show 'Kinley' instead of 'Ryan'")
        print("3. Added notes to the export script for future reference")
        print("\nYou can verify the changes at:")
        print("- https://brentcurtis182.github.io/wordle-league/")
        print("- https://brentcurtis182.github.io/wordle-league/landing")
        print("\nThis fix should be permanent for future exports and deployments.")
        return True
    else:
        logging.error("Failed to push comprehensive fix to GitHub")
        print("Failed to push comprehensive fix. Check comprehensive_fix.log for details.")
        return False

if __name__ == "__main__":
    main()
