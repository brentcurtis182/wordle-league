#!/usr/bin/env python3
import re
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def emergency_fix():
    """Direct search and replace in the HTML file"""
    file_path = 'website_export/pal/daily/wordle-1503.html'
    
    try:
        # Create backup
        backup_path = file_path + ".emergency.bak"
        shutil.copy2(file_path, backup_path)
        logging.info(f"Backup created at {backup_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Use a more generous pattern match
        old_pattern = r'<div class="emoji-row">🟩🟩🟩🟩🟩", Thursday, July 31 2025, 9:58 AM.</div>'
        new_pattern = r'<div class="emoji-row">🟩🟩🟩🟩🟩</div>'
        
        # Replace the problematic pattern
        new_content = content.replace(old_pattern, new_pattern)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logging.info("Successfully fixed the emoji pattern!")
            return True
        else:
            logging.warning("Pattern not found. Let's try with regex")
            
            # Try a more flexible regex approach
            pattern = re.compile(r'<div class="emoji-row">(🟩🟩🟩🟩🟩).*?</div>')
            new_content = pattern.sub(r'<div class="emoji-row">\1</div>', content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logging.info("Successfully fixed the emoji pattern with regex!")
                return True
            else:
                logging.error("Could not find the pattern even with regex")
                return False
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    logging.info("Starting emergency fix")
    result = emergency_fix()
    logging.info(f"Emergency fix completed: {result}")
