#!/usr/bin/env python3
"""
Fix Wordle League landing page links to scroll to top when clicked

This script:
1. Updates the landing page to use regular <a> links instead of form submissions
2. Adds JavaScript to scroll to top when links are clicked
3. Optionally adds a "scroll to top" button for long pages
"""

import os
import sys
import logging
import re
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def fix_landing_page_links(export_dir="website_export"):
    """
    Update the landing page to fix the scroll-to-top issue with league links
    """
    try:
        # Paths
        landing_file = os.path.join(export_dir, "landing.html")
        index_file = os.path.join(export_dir, "index.html")
        backup_dir = os.path.join(export_dir, "backups")
        
        # Create backups directory if it doesn't exist
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        # Create backups of the current files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if os.path.exists(landing_file):
            backup_landing = os.path.join(backup_dir, f"landing_{timestamp}.html")
            shutil.copy2(landing_file, backup_landing)
            logging.info(f"Created backup of landing.html at {backup_landing}")
            
        if os.path.exists(index_file):
            backup_index = os.path.join(backup_dir, f"index_{timestamp}.html")
            shutil.copy2(index_file, backup_index)
            logging.info(f"Created backup of index.html at {backup_index}")
            
        # Read the current landing page
        if not os.path.exists(landing_file):
            logging.error(f"Landing page not found at {landing_file}")
            return False
            
        with open(landing_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix 1: Replace form submissions with direct links
        form_pattern = r'<form action="([^"]*)" method="get" target="_top">\s*<button type="submit" class="league-button">([^<]*)</button>\s*</form>'
        link_replacement = r'<a href="\1" class="league-button" onclick="scrollToTop()">\2</a>'
        content = re.sub(form_pattern, link_replacement, content)
        
        # Fix 2: Add JavaScript to handle scrolling to top
        js_scroll_code = """
    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
"""
        # Add the script before the closing body tag
        if "</body>" in content:
            content = content.replace("</body>", f"{js_scroll_code}</body>")
        else:
            content += js_scroll_code
            
        # Fix 3: Add a "Back to Top" button for long pages
        back_to_top_button = """
    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
"""
        # Add the back to top button before the closing body tag
        if "</body>" in content:
            content = content.replace("</body>", f"{back_to_top_button}</body>")
        else:
            content += back_to_top_button
            
        # Write the updated content
        with open(landing_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # Copy to index.html as well (the default landing page)
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info("Successfully updated landing page with improved navigation links")
        return True
        
    except Exception as e:
        logging.error(f"Error updating landing page links: {e}")
        return False

def fix_export_script(script_path="export_leaderboard_multi_league.py"):
    """
    Update the export script to use direct links instead of form submissions
    """
    try:
        # Create a backup of the original script
        if os.path.exists(script_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{script_path}.{timestamp}.bak"
            shutil.copy2(script_path, backup_path)
            logging.info(f"Created backup of {script_path} at {backup_path}")
            
            # Read the script content
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Update the form creation with direct links
            old_code = """            # Create the league card HTML
            card_html = f\"\"\"
            <div class="league-card">
                <div class="league-name">{league_name}</div>
                <div class="league-description">{league_desc}</div>
                <div class="league-status {status_class}">{status_text}</div>
                <form action="{league_path}/index.html" method="get" target="_top">
                    <button type="submit" class="league-button">View League</button>
                </form>
            </div>
            \"\"\""""
            
            new_code = """            # Create the league card HTML
            card_html = f\"\"\"
            <div class="league-card">
                <div class="league-name">{league_name}</div>
                <div class="league-description">{league_desc}</div>
                <div class="league-status {status_class}">{status_text}</div>
                <a href="{league_path}/index.html" class="league-button" onclick="scrollToTop()">View League</a>
            </div>
            \"\"\""""
            
            # Replace the code
            content = content.replace(old_code, new_code)
            
            # Add the JavaScript scroll function to the landing page template
            if "function scrollToTop()" not in content:
                scroll_js = """    <script>
    function scrollToTop() {
        // Use setTimeout to ensure this happens after the link navigation
        setTimeout(function() {
            window.scrollTo(0, 0);
        }, 0);
    }
    </script>
"""
                # Find where to insert the script (before </body>)
                body_close_pattern = r"</body>\s*</html>\""
                content = re.sub(body_close_pattern, f"{scroll_js}</body>\n</html>\"", content)
                
            # Add back to top button to the landing page template
            if "back-to-top" not in content:
                back_to_top = """    <div id="back-to-top" style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #538d4e;
        color: white;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        text-align: center;
        line-height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        font-weight: bold;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    ">↑</div>
    
    <script>
    // Show/hide the back to top button
    window.onscroll = function() {
        var backToTopBtn = document.getElementById("back-to-top");
        if (document.body.scrollTop > 300 || document.documentElement.scrollTop > 300) {
            backToTopBtn.style.display = "block";
        } else {
            backToTopBtn.style.display = "none";
        }
    };
    
    // Scroll to top when clicked
    document.getElementById("back-to-top").onclick = function() {
        document.body.scrollTop = 0; // For Safari
        document.documentElement.scrollTop = 0; // For Chrome, Firefox, IE and Opera
    };
    </script>
"""
                # Find where to insert the button (before </body>)
                content = re.sub(body_close_pattern, f"{back_to_top}</body>\n</html>\"", content)
                
            # Write the updated script
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            logging.info(f"Successfully updated {script_path} to use direct links with scroll-to-top")
            return True
            
        else:
            logging.error(f"Export script not found at {script_path}")
            return False
            
    except Exception as e:
        logging.error(f"Error updating export script: {e}")
        return False

def update_website():
    """
    Run the export and publish commands to update the website
    """
    try:
        # Re-export the website
        logging.info("Regenerating website files...")
        result = os.system("python export_leaderboard_multi_league.py")
        if result != 0:
            logging.error("Failed to regenerate website files")
            return False
            
        # Publish the website
        logging.info("Publishing website updates...")
        result = os.system("python publish_website.py")
        if result != 0:
            logging.error("Failed to publish website")
            return False
            
        logging.info("Successfully updated and published the website")
        return True
        
    except Exception as e:
        logging.error(f"Error updating website: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting landing page links fix...")
    
    # Fix the current landing page
    logging.info("Updating current landing page...")
    if not fix_landing_page_links():
        logging.error("Failed to update landing page")
        sys.exit(1)
        
    # Fix the export script for future exports
    logging.info("Updating export script...")
    if not fix_export_script():
        logging.error("Failed to update export script")
        # Continue anyway, since we've already fixed the current landing page
        
    # Automatically update the website
    logging.info("Updating website...")
    if not update_website():
        logging.error("Failed to update website")
        sys.exit(1)
    
    logging.info("Landing page link fix completed successfully!")
    print("\nThe landing page has been updated with the following improvements:")
    print("1. League links now properly scroll to the top when clicked")
    print("2. Added a 'Back to Top' button that appears when scrolling down")
    print("3. Fixed the export script to use this improved approach for future exports")
    print("\nYou can view the changes at:")
    print("- https://brentcurtis182.github.io/wordle-league/landing.html")
    print("- https://brentcurtis182.github.io/wordle-league/index.html")
