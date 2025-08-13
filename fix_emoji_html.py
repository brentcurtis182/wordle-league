#!/usr/bin/env python3
import os
import re
import logging
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fix_emoji_patterns_in_files():
    """Clean up emoji patterns in HTML files by removing appended text"""
    try:
        # Directories to process
        directories = [
            'website_export/daily',         # Main league
            'website_export/pal/daily',     # PAL league
            'website_export/gang/daily'     # Gang league
        ]
        
        # Compile regex pattern once
        # This pattern matches emoji square pattern followed by anything else on the line
        emoji_pattern = re.compile(r'(<div class="emoji-row">)([⬜⬛🟨🟩🟥🟦🟪🟧🟫⬜]{5})(.*?)(</div>)')
        
        files_processed = 0
        files_modified = 0
        
        for directory in directories:
            if not os.path.exists(directory):
                logging.info(f"Directory not found: {directory}")
                continue
                
            logging.info(f"Processing directory: {directory}")
            
            # Process all HTML files
            for filename in os.listdir(directory):
                if filename.endswith('.html'):
                    filepath = os.path.join(directory, filename)
                    files_processed += 1
                    
                    # Create backup if not already exists
                    backup_file = f"{filepath}.bak"
                    if not os.path.exists(backup_file):
                        shutil.copy2(filepath, backup_file)
                        logging.info(f"Created backup: {backup_file}")
                    
                    # Read file content
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Fix emoji patterns
                    modified_content = emoji_pattern.sub(r'\1\2\4', content)
                    
                    # Only write if changes were made
                    if modified_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(modified_content)
                        files_modified += 1
                        logging.info(f"Fixed emoji patterns in {filepath}")
        
        logging.info(f"Processed {files_processed} files, modified {files_modified} files")
        return files_modified
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return 0

def fix_template():
    """Update the wordle.html template to ensure it doesn't generate files with appended text"""
    template_path = 'website_export/templates/wordle.html'
    
    try:
        if not os.path.exists(template_path):
            logging.error(f"Template file not found: {template_path}")
            return False
            
        # Create backup if not already exists
        backup_file = f"{template_path}.bak"
        if not os.path.exists(backup_file):
            shutil.copy2(template_path, backup_file)
            logging.info(f"Created backup of template: {backup_file}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for the emoji pattern rendering section
        pattern_section = re.search(r'({% if score\.emoji_pattern %}.*?{% for line in score\.emoji_pattern\.split\(\'\\\n\'\) %}.*?<div class="emoji-row">)(.*?)(</div>.*?{% endfor %}.*?{% endif %})', content, re.DOTALL)
        
        if pattern_section:
            # Get the current line cleaning logic
            current_line_logic = pattern_section.group(2)
            
            # Check if we need to update it
            if '|' not in current_line_logic and 'split' not in current_line_logic:
                # Replace with improved line cleaning
                new_line_logic = "{{ line.split(',')[0].split('.')[0].strip('\"') }}"
                new_content = content.replace(pattern_section.group(0), 
                                            f"{pattern_section.group(1)}{new_line_logic}{pattern_section.group(3)}")
                
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                logging.info(f"Updated template with improved emoji line cleaning")
                return True
            else:
                logging.info(f"Template already has line cleaning logic")
                return False
        else:
            logging.warning(f"Could not find emoji pattern section in template")
            return False
            
    except Exception as e:
        logging.error(f"Error updating template: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting emoji pattern fix")
    
    # Fix existing HTML files
    files_fixed = fix_emoji_patterns_in_files()
    
    # Update template to prevent future issues
    template_updated = fix_template()
    
    # Run export again if we fixed files
    if files_fixed > 0 or template_updated:
        logging.info("Running export again to ensure all files are updated")
        os.system("python integrated_auto_update_multi_league.py --export-only")
        logging.info("Export completed")
    
    logging.info("Emoji pattern fix completed")
