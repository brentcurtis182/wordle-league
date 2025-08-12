#!/usr/bin/env python3
"""
Fix the CSS paths in the league subdirectory HTML files to point to the root directory
"""

import os
import logging
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_css_paths.log"),
        logging.StreamHandler()
    ]
)

# League subdirectories
LEAGUE_DIRS = [
    "wordle-gang",
    "wordle-pal",
    "wordle-party",
    "wordle-vball"
]

def fix_css_paths():
    """Fix CSS paths in league HTML files"""
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'website_export')
    
    # Also copy CSS files to league directories to be safe
    css_file = os.path.join(base_dir, 'styles.css')
    script_file = os.path.join(base_dir, 'script.js')
    
    if not os.path.exists(css_file):
        logging.error(f"CSS file not found: {css_file}")
        return False
        
    for league_dir in LEAGUE_DIRS:
        league_path = os.path.join(base_dir, league_dir)
        
        if not os.path.exists(league_path):
            logging.warning(f"League directory not found: {league_path}")
            continue
            
        index_file = os.path.join(league_path, 'index.html')
        
        if not os.path.exists(index_file):
            logging.warning(f"Index file not found: {index_file}")
            continue
            
        logging.info(f"Processing {index_file}...")
        
        try:
            # Read the HTML file
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse the HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find CSS link and update path
            css_links = soup.find_all('link', rel='stylesheet')
            fixed = False
            
            for link in css_links:
                if 'href' in link.attrs and link['href'] == 'styles.css':
                    link['href'] = '../styles.css'
                    fixed = True
                    logging.info(f"Fixed CSS path in {index_file}")
            
            # Find any script tags and update paths
            scripts = soup.find_all('script')
            for script in scripts:
                if 'src' in script.attrs and script['src'] == 'script.js':
                    script['src'] = '../script.js'
                    fixed = True
                    logging.info(f"Fixed script path in {index_file}")
                    
            # Add script for tabs if missing
            has_tab_script = False
            for script in scripts:
                if script.string and 'openTab' in script.string:
                    has_tab_script = True
                    break
                    
            if not has_tab_script:
                script_tag = soup.new_tag('script')
                script_tag.string = """
                function openTab(evt, tabName) {
                    var i, tabcontent, tabbuttons;
                    
                    tabcontent = document.getElementsByClassName("tab-content");
                    for (i = 0; i < tabcontent.length; i++) {
                        tabcontent[i].style.display = "none";
                    }
                    
                    tabbuttons = document.getElementsByClassName("tab-button");
                    for (i = 0; i < tabbuttons.length; i++) {
                        tabbuttons[i].className = tabbuttons[i].className.replace(" active", "");
                    }
                    
                    document.getElementById(tabName).style.display = "block";
                    evt.currentTarget.className += " active";
                }
                
                // Set default tab to open
                document.addEventListener('DOMContentLoaded', function() {
                    document.querySelector('.tab-button').click();
                });
                """
                soup.body.append(script_tag)
                fixed = True
                logging.info(f"Added tab script to {index_file}")
            
            # Update tab buttons to ensure they have onclick handlers
            tab_buttons = soup.select('.tab-button')
            for button in tab_buttons:
                if 'data-tab' in button.attrs and ('onclick' not in button.attrs or 'openTab' not in button['onclick']):
                    button['onclick'] = f"openTab(event, '{button['data-tab']}')"
                    fixed = True
                    logging.info(f"Fixed tab button in {index_file}")
            
            if fixed:
                # Write the updated HTML back to the file
                with open(index_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                    
                logging.info(f"Updated {index_file}")
            else:
                logging.info(f"No changes needed for {index_file}")
                
            # Copy CSS file to league directory for redundancy
            league_css = os.path.join(league_path, 'styles.css')
            if not os.path.exists(league_css):
                with open(css_file, 'r', encoding='utf-8') as src, open(league_css, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
                logging.info(f"Copied CSS file to {league_css}")
                
            # Copy JS file to league directory for redundancy
            if os.path.exists(script_file):
                league_js = os.path.join(league_path, 'script.js')
                if not os.path.exists(league_js):
                    with open(script_file, 'r', encoding='utf-8') as src, open(league_js, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                    logging.info(f"Copied JS file to {league_js}")
                    
        except Exception as e:
            logging.error(f"Error processing {index_file}: {e}")
    
    return True

def main():
    logging.info("Starting CSS path fixes...")
    
    if fix_css_paths():
        logging.info("CSS paths fixed successfully!")
        print("CSS paths fixed successfully!")
    else:
        logging.error("Failed to fix CSS paths")
        print("Failed to fix CSS paths")

if __name__ == "__main__":
    main()
