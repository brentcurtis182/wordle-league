#!/usr/bin/env python3
import os
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_mobile_view():
    """
    Fix the mobile view issue by ensuring proper viewport meta tag and enhanced mobile CSS.
    """
    website_export_dir = os.path.join(os.getcwd(), "website_export")
    
    # Check if website_export directory exists
    if not os.path.exists(website_export_dir):
        logger.error(f"Directory {website_export_dir} does not exist")
        return False
    
    # Process all HTML files
    for root, dirs, files in os.walk(website_export_dir):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                
                # Backup the file first
                backup_path = file_path + ".bak"
                shutil.copy2(file_path, backup_path)
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ensure proper viewport meta tag exists
                if '<meta name="viewport"' not in content:
                    content = content.replace('<meta charset="UTF-8">', 
                                            '<meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
                
                # Write updated content back to the file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Updated {file_path}")
    
    # Update CSS file with enhanced mobile styles
    css_file = os.path.join(website_export_dir, "styles.css")
    if os.path.exists(css_file):
        # Backup the CSS file
        shutil.copy2(css_file, css_file + ".bak")
        
        # Read the CSS content
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # Check if mobile media query already exists
        if "@media (max-width: 768px)" not in css_content:
            # Add mobile styles
            mobile_css = """
@media (max-width: 768px) {
    .container {
        padding: 5px;
    }
    .tab-button {
        padding: 8px 15px;
        font-size: 1em;
    }
    .score-card {
        padding: 8px;
    }
    .player-name {
        font-size: 1em;
    }
    .emoji-pattern {
        font-size: 0.5rem;
    }
    table {
        font-size: 0.9em;
    }
    th, td {
        padding: 6px 8px;
    }
}
"""
            css_content += mobile_css
        
        # Write updated CSS content back
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(css_content)
        
        logger.info(f"Updated CSS file with enhanced mobile styles")
    
    logger.info("Mobile view fixes applied successfully!")
    return True

if __name__ == "__main__":
    logger.info("Starting mobile view fix process...")
    fix_mobile_view()
