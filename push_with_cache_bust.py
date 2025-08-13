#!/usr/bin/env python
# Push website changes with cache busting

import os
import sys
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def add_cache_busting():
    """Add cache busting files to the website export directory"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create timestamp file for cache busting
        timestamp_file = os.path.join(export_dir, f"timestamp_{timestamp}.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Cache busting timestamp: {datetime.now().isoformat()}")
        logging.info(f"Added cache busting timestamp file: {timestamp_file}")
        
        # Create or update .nojekyll file
        nojekyll_file = os.path.join(export_dir, ".nojekyll")
        with open(nojekyll_file, "w") as f:
            f.write("")
        logging.info("Added .nojekyll file")
        
        # Create a redirect page for guaranteed fresh content
        redirect_file = os.path.join(export_dir, "latest.html")
        with open(redirect_file, "w") as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta http-equiv="refresh" content="0;url=index.html?t={timestamp}">
    <title>Latest Wordle League</title>
</head>
<body>
    <p>Redirecting to <a href="index.html?t={timestamp}">latest version</a>...</p>
    <p>Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>""")
        logging.info(f"Added cache-busting redirect page: latest.html")
        
        # Add meta tags to index.html
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check if cache control meta tags are already present
            if "<meta http-equiv=\"Cache-Control\"" not in content:
                # Add cache control meta tags before </head>
                cache_tags = f"""
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="generated" content="{datetime.now().isoformat()}">
</head>"""
                content = content.replace("</head>", cache_tags)
                
                # Write updated content back
                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(content)
                logging.info("Added cache control meta tags to index.html")
        
        return True
    except Exception as e:
        logging.error(f"Error adding cache busting: {e}")
        return False

def push_with_enhanced_functions():
    """Push changes using enhanced_functions.py"""
    try:
        # Import push_to_github from enhanced_functions
        sys.path.append(os.getcwd())
        from enhanced_functions import push_to_github
        
        # Run push_to_github function
        logging.info("Pushing to GitHub using enhanced_functions.py...")
        result = push_to_github()
        
        if result:
            logging.info("Successfully pushed changes to GitHub")
            return True
        else:
            logging.error("Failed to push changes to GitHub")
            return False
    except Exception as e:
        logging.error(f"Error pushing with enhanced_functions: {e}")
        return False

def main():
    logging.info("Starting website push with cache busting...")
    
    # Step 1: Add cache busting
    logging.info("\nStep 1: Adding cache busting...")
    if not add_cache_busting():
        logging.error("Failed to add cache busting, continuing anyway")
    
    # Step 2: Push changes
    logging.info("\nStep 2: Pushing changes to GitHub...")
    if push_with_enhanced_functions():
        logging.info("\nProcess completed successfully!")
        logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
        logging.info(f"For guaranteed fresh content, use: https://brentcurtis182.github.io/wordle-league/latest.html")
        logging.info("\nNote: GitHub Pages may take a few minutes to update the content.")
    else:
        logging.error("\nFailed to push changes to GitHub.")

if __name__ == "__main__":
    main()
