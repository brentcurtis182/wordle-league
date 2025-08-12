#!/usr/bin/env python
# fix_cache_and_weekly.py - Fix browser caching and weekly score reset issues

import os
import logging
import sqlite3
import subprocess
import re
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"fix_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

# Constants
EXPORT_DIR = "website_export"
DATABASE_PATH = "wordle_league.db"
RESET_MARKER_FILE = "last_weekly_reset.txt"

def add_cache_control_headers():
    """Add cache control headers to prevent browser caching"""
    index_path = os.path.join(EXPORT_DIR, "index.html")
    
    try:
        if not os.path.exists(index_path):
            logging.error(f"Index file not found: {index_path}")
            return False
        
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Add cache control meta tags if they don't exist
        if "<meta http-equiv=\"Cache-Control\"" not in content:
            cache_control_meta = """
    <!-- Cache control headers -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
"""
            # Insert after the <head> tag
            content = content.replace("<head>", "<head>" + cache_control_meta)
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logging.info("Added cache control headers to index.html")
        else:
            logging.info("Cache control headers already exist in index.html")
            
        # Add query parameter to all CSS and JS links to bust cache
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Replace CSS links
        content = re.sub(
            r'href="([^"]+\.css)(\?[^"]*)?(")', 
            f'href="\\1?v={timestamp}\\3', 
            content
        )
        
        # Replace JS links
        content = re.sub(
            r'src="([^"]+\.js)(\?[^"]*)?(")', 
            f'src="\\1?v={timestamp}\\3', 
            content
        )
        
        # Add version to img tags
        content = re.sub(
            r'src="([^"]+\.(png|jpg|gif|svg))(\?[^"]*)?(")', 
            f'src="\\1?v={timestamp}\\4', 
            content
        )
        
        # Write changes back to index.html
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info(f"Added cache-busting query parameters with timestamp {timestamp}")
        
        return True
    except Exception as e:
        logging.error(f"Error adding cache control headers: {e}")
        return False

def modify_export_leaderboard():
    """Modify the export_leaderboard.py file to fix weekly scores calculation"""
    try:
        with open("export_leaderboard.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Fix the start_of_week to be Monday 3:00 AM instead of Monday 12:00 AM
        if "start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)" in content:
            content = content.replace(
                "start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)",
                "start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)"
            )
            logging.info("Updated start_of_week to use 3:00 AM instead of midnight")
        
        # Add a debug print to show what start_of_week is being used
        if "# Format the date as a string for SQL comparison" in content:
            debug_line = '    print(f"Using start of week: {start_of_week_str}")  # Debug print\n'
            content = content.replace(
                "# Format the date as a string for SQL comparison",
                "# Format the date as a string for SQL comparison\n" + debug_line
            )
            logging.info("Added debug print for start_of_week")
        
        # Write the modified content back to the file
        with open("export_leaderboard.py", "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info("Successfully modified export_leaderboard.py")
        return True
    except Exception as e:
        logging.error(f"Error modifying export_leaderboard.py: {e}")
        return False

def create_404_page():
    """Create a 404.html page that redirects to the main page"""
    try:
        redirect_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="0;URL='https://brentcurtis182.github.io/wordle-league/'" />
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <title>Redirecting to Wordle League</title>
</head>
<body>
    <h1>Redirecting to Wordle League...</h1>
    <p>If you are not redirected automatically, click <a href="https://brentcurtis182.github.io/wordle-league/">here</a>.</p>
    <script>
        window.location.href = "https://brentcurtis182.github.io/wordle-league/";
    </script>
</body>
</html>"""
        
        # Write the 404 page
        with open(os.path.join(EXPORT_DIR, "404.html"), "w", encoding="utf-8") as f:
            f.write(redirect_html)
        
        logging.info("Created 404.html redirect page")
        return True
    except Exception as e:
        logging.error(f"Error creating 404 page: {e}")
        return False

def create_htaccess():
    """Create a .htaccess file with cache control directives"""
    try:
        htaccess_content = """# Cache Control
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresDefault "access plus 0 seconds"
    ExpiresByType text/html "access plus 0 seconds"
    ExpiresByType text/css "access plus 0 seconds"
    ExpiresByType application/javascript "access plus 0 seconds"
    ExpiresByType image/jpeg "access plus 0 seconds"
    ExpiresByType image/png "access plus 0 seconds"
</IfModule>

<IfModule mod_headers.c>
    Header set Cache-Control "no-cache, no-store, must-revalidate"
    Header set Pragma "no-cache"
    Header set Expires "0"
</IfModule>

# Redirect for alternate URL paths
RedirectMatch 301 ^/wordleleague$ /wordle-league/
RedirectMatch 301 ^/wordleleague/$ /wordle-league/

# Default index
DirectoryIndex index.html
"""
        
        with open(os.path.join(EXPORT_DIR, ".htaccess"), "w") as f:
            f.write(htaccess_content)
            
        logging.info("Created .htaccess file with cache control directives")
        return True
    except Exception as e:
        logging.error(f"Error creating .htaccess file: {e}")
        return False

def create_custom_js():
    """Create a custom JS file to force cache refresh on client side"""
    try:
        js_content = f"""// cache-buster.js - Created {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
document.addEventListener("DOMContentLoaded", function() {{
    // Force page reload if it's been cached
    if (performance.navigation.type === 1) {{
        // This is a page reload, clear cache and reload
        console.log("Page reloaded, clearing cache...");
        
        // Clear local cache for this page
        if (window.caches) {{
            caches.keys().then(function(names) {{
                for (let name of names) {{
                    caches.delete(name);
                }}
            }});
        }}
    }}
    
    // Add timestamp to report cache status
    const timestampDiv = document.createElement('div');
    timestampDiv.style.fontSize = '10px';
    timestampDiv.style.color = '#999';
    timestampDiv.style.textAlign = 'center';
    timestampDiv.style.padding = '5px';
    timestampDiv.innerHTML = 'Page last generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (v{datetime.now().strftime('%Y%m%d%H%M%S')})';
    document.body.appendChild(timestampDiv);
}});
"""
        
        # Create the js file
        js_path = os.path.join(EXPORT_DIR, "cache-buster.js")
        with open(js_path, "w") as f:
            f.write(js_content)
            
        # Now modify index.html to include this script
        index_path = os.path.join(EXPORT_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Add the script before the closing </body> tag
        script_tag = f'<script src="cache-buster.js?v={datetime.now().strftime("%Y%m%d%H%M%S")}"></script>'
        
        if "</body>" in content:
            content = content.replace("</body>", script_tag + "\n</body>")
            
            with open(index_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            logging.info("Created cache-buster.js and added it to index.html")
            return True
        else:
            logging.error("Could not find </body> tag in index.html")
            return False
    except Exception as e:
        logging.error(f"Error creating custom JS: {e}")
        return False

def force_reset_weekly_scores():
    """Force reset the weekly scores by updating the reset marker file"""
    try:
        # Calculate the most recent Monday at 3:00 AM
        today = datetime.now()
        days_since_monday = today.weekday()  # 0 = Monday
        last_monday = today - timedelta(days=days_since_monday)
        monday_3am = last_monday.replace(hour=3, minute=0, second=0, microsecond=0)
        
        # Write the reset marker file
        with open(RESET_MARKER_FILE, "w") as f:
            f.write(monday_3am.strftime("%Y-%m-%d %H:%M:%S"))
            
        logging.info(f"Reset weekly scores marker to {monday_3am.strftime('%Y-%m-%d %H:%M:%S')}")
        return True
    except Exception as e:
        logging.error(f"Error forcing weekly reset: {e}")
        return False

def update_website_and_push():
    """Update website files and push to GitHub"""
    try:
        # Run export_leaderboard.py
        logging.info("Running export_leaderboard.py to update website files...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
        
        # Add the cache control measures to the exported files
        if not add_cache_control_headers():
            logging.warning("Failed to add cache control headers")
        
        if not create_404_page():
            logging.warning("Failed to create 404 page")
            
        if not create_htaccess():
            logging.warning("Failed to create .htaccess")
            
        if not create_custom_js():
            logging.warning("Failed to create custom JS")
            
        # Push to GitHub
        logging.info("Pushing changes to GitHub...")
        export_dir = os.path.join(os.getcwd(), EXPORT_DIR)
        
        # Create timestamp file to force a change
        timestamp_file = os.path.join(export_dir, "timestamp.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add, commit, push
        try:
            subprocess.run(["git", "add", "-A"], cwd=export_dir, check=True)
            subprocess.run(["git", "commit", "-m", f"Force update with cache busting: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"], cwd=export_dir)
            subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_dir, check=True)
            
            logging.info("Successfully pushed changes to GitHub")
            return True
        except Exception as e:
            logging.error(f"Error during Git operations: {e}")
            return False
    except Exception as e:
        logging.error(f"Error updating website and pushing: {e}")
        return False

def main():
    """Main function to fix cache and weekly score issues"""
    logging.info("Starting cache and weekly scores fix")
    
    # Step 1: Force reset weekly scores
    logging.info("\nSTEP 1: Forcing weekly score reset")
    if force_reset_weekly_scores():
        logging.info("Weekly scores have been reset")
    
    # Step 2: Modify export_leaderboard.py
    logging.info("\nSTEP 2: Modifying export_leaderboard.py")
    if modify_export_leaderboard():
        logging.info("Successfully modified export_leaderboard.py")
    
    # Step 3: Update website and push
    logging.info("\nSTEP 3: Updating website and pushing to GitHub")
    if update_website_and_push():
        logging.info("Website updated and pushed to GitHub")
    
    logging.info("\nAll fixes completed!")
    logging.info("Note: You may need to hard-refresh browsers (Ctrl+F5 or Cmd+Shift+R) to see changes")
    logging.info("The website should now be available at: https://brentcurtis182.github.io/wordle-league/")

if __name__ == "__main__":
    main()
