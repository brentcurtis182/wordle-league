#!/usr/bin/env python3
"""
Safe version of fix_tabs.py that preserves Season table and tab names.
This script ensures tab functionality works without overwriting our changes.
"""

import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_tabs.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def fix_tabs_safely():
    """Fix tabs while preserving Season table and tab name changes"""
    website_dir = "website_export"
    
    # League paths
    league_paths = [
        os.path.join(website_dir, "index.html"),            # Wordle Warriorz
        os.path.join(website_dir, "gang", "index.html"),    # Wordle Gang
        os.path.join(website_dir, "pal", "index.html"),     # Wordle PAL
        os.path.join(website_dir, "party", "index.html"),   # Wordle Party
        os.path.join(website_dir, "vball", "index.html")    # Wordle Vball
    ]
    
    for path in league_paths:
        if os.path.exists(path):
            logger.info(f"Processing {path}...")
            
            # Create a backup before making changes
            backup_path = f"{path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            try:
                with open(path, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()
                
                with open(backup_path, 'w', encoding='utf-8') as f_out:
                    f_out.write(content)
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.error(f"Failed to create backup for {path}: {e}")
                continue
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Check if any changes are needed to CSS paths
            css_link = soup.find('link', {'rel': 'stylesheet'})
            if css_link:
                if not css_link['href'].startswith('http') and not css_link['href'].startswith('/'):
                    # Already relative, no change needed
                    logger.info(f"CSS path is already relative: {css_link['href']}")
                else:
                    logger.info(f"Updating CSS path from {css_link['href']} to styles.css")
                    css_link['href'] = 'styles.css'
            
            # Make sure tab button with data-tab="stats" has "Season / All-Time Stats" as text
            stats_button = soup.select_one('button.tab-button[data-tab="stats"]')
            if stats_button:
                if "Season" not in stats_button.text:
                    stats_button.string = "Season / All-Time Stats"
                    logger.info("Fixed stats button text to 'Season / All-Time Stats'")
            
            # Add any missing JavaScript for tab functionality
            script_text = """
<script>
document.addEventListener('DOMContentLoaded', function() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });
});
</script>
"""
            
            # Check if script already exists
            existing_script = soup.find('script', text=lambda t: t and 'tabButtons' in t)
            if not existing_script:
                logger.info("Adding tab functionality script")
                new_script = BeautifulSoup(script_text, 'html.parser')
                soup.body.append(new_script)
            
            # Write the updated HTML
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.info(f"Successfully updated {path}")
            except Exception as e:
                logger.error(f"Failed to update {path}: {e}")
                # Restore from backup
                try:
                    with open(backup_path, 'r', encoding='utf-8') as f_in:
                        backup_content = f_in.read()
                    
                    with open(path, 'w', encoding='utf-8') as f_out:
                        f_out.write(backup_content)
                    logger.info(f"Restored {path} from backup after error")
                except Exception as restore_err:
                    logger.error(f"Failed to restore from backup: {restore_err}")
        else:
            logger.warning(f"File not found: {path}")
    
    logger.info("Tab fixing process completed")

if __name__ == "__main__":
    fix_tabs_safely()
