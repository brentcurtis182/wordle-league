#!/usr/bin/env python3
"""
Inline CSS Fix

This script embeds critical CSS styles directly into each HTML file to ensure proper
display while maintaining the external CSS file references.
"""

import os
import logging
import re
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Base directory
WEBSITE_DIR = "website_export"

# Critical CSS styles to embed - these are the basic styles needed for proper display
CRITICAL_CSS = """
<style>
body {
    font-family: 'Arial', sans-serif;
    background-color: #f5f5f5;
    color: #333;
    margin: 0;
    padding: 0;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

h1 {
    color: #2c3e50;
    text-align: center;
    margin-bottom: 30px;
}

.section {
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

.scores-table {
    width: 100%;
    border-collapse: collapse;
}

.scores-table th, .scores-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.scores-table th {
    background-color: #f2f2f2;
}

.score-1 { color: #1e7e34; }
.score-2 { color: #1e7e34; }
.score-3 { color: #28a745; }
.score-4 { color: #fd7e14; }
.score-5 { color: #ffc107; }
.score-6 { color: #dc3545; }
.score-X { color: #dc3545; }
</style>
"""

def add_inline_css_to_file(file_path):
    """Add inline CSS to a single HTML file"""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if we've already added our inline CSS
    if "/* CRITICAL WORDLE LEAGUE STYLES */" in content:
        logging.info(f"File {file_path} already has inline CSS")
        return False
    
    # Find the head section and insert our inline CSS
    head_end_pattern = re.compile(r'(</head>)', re.IGNORECASE)
    new_content = head_end_pattern.sub(CRITICAL_CSS + r'\1', content)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    
    logging.info(f"Added inline CSS to {file_path}")
    return True

def find_and_fix_all_html_files():
    """Find and add inline CSS to all HTML files"""
    fixed_files = 0
    
    for root, _, files in os.walk(WEBSITE_DIR):
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                if add_inline_css_to_file(file_path):
                    fixed_files += 1
    
    return fixed_files

def push_to_github():
    """Push changes to GitHub Pages"""
    try:
        # Change to the website directory
        os.chdir(WEBSITE_DIR)
        logging.info(f"Changed to directory: {os.getcwd()}")
        
        # Add all changes
        subprocess.check_call(["git", "add", "."])
        logging.info("Added all changes to staging")
        
        # Pull latest changes to avoid conflicts
        pull_output = subprocess.check_output(["git", "pull"], text=True)
        logging.info(f"Pulled latest changes: {pull_output}")
        
        # Create commit message with timestamp
        commit_message = f"Fix: Added inline CSS to ensure proper styling ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
        subprocess.check_call(["git", "commit", "-m", commit_message])
        logging.info(f"Committed changes: {commit_message}")
        
        # Push to GitHub
        push_output = subprocess.check_output(["git", "push"], text=True)
        logging.info(f"Pushed to GitHub: {push_output}")
        
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir("..")

def main():
    """Main function"""
    logging.info("Starting inline CSS fix")
    
    # Fix CSS in all HTML files
    fixed_count = find_and_fix_all_html_files()
    logging.info(f"Added inline CSS to {fixed_count} HTML files")
    
    # Push changes to GitHub
    if push_to_github():
        logging.info("Successfully pushed inline CSS fixes to GitHub Pages")
        print("\nSUCCESS: Inline CSS fixes pushed to GitHub Pages!")
        print("\nThe fixed websites with proper styling should be visible shortly at:")
        print("- Main League: https://brentcurtis182.github.io/wordle-league/")
        print("- Wordle Gang: https://brentcurtis182.github.io/wordle-league/gang/")
        print("- PAL League: https://brentcurtis182.github.io/wordle-league/pal/")
        return True
    else:
        logging.error("Failed to push inline CSS fixes to GitHub")
        return False

if __name__ == "__main__":
    main()
