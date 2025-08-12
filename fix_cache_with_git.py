#!/usr/bin/env python
# GitHub Pages Cache Buster Script with Git Initialization

import os
import re
import sqlite3
import subprocess
import logging
import random
import string
import json
from datetime import datetime
import time
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_and_fix_joanna_pattern():
    """Check and fix Joanna's emoji pattern directly in the database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get Joanna's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        joanna_id = cursor.fetchone()["id"]
        logging.info(f"Joanna's player ID: {joanna_id}")
        
        # Get her current score for Wordle 1500
        cursor.execute("""
            SELECT id, score, emoji_pattern 
            FROM score 
            WHERE player_id = ? AND wordle_number = 1500
        """, (joanna_id,))
        
        score_record = cursor.fetchone()
        if not score_record:
            logging.error("No score found for Joanna for Wordle 1500")
            conn.close()
            return False
            
        score_id = score_record["id"]
        score = score_record["score"]
        pattern = score_record["emoji_pattern"]
        
        logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}")
        
        # Count rows in pattern
        rows = 0
        if pattern:
            rows = pattern.count('\n') + 1
            logging.info(f"Pattern has {rows} rows but score is {score}")
        
        # Fix if there's a mismatch
        if score == 5 and (rows != 5 or not pattern):
            logging.info("Fixing Joanna's pattern to match her 5/6 score")
            
            # Create a proper 5-row pattern
            new_pattern = "🟨⬛⬛⬛⬛\n⬛🟨🟨⬛⬛\n⬛🟩🟨🟩⬛\n🟩🟩⬛🟩🟨\n🟩🟩🟩🟩🟩"
            
            # Update in database
            cursor.execute("""
                UPDATE score 
                SET emoji_pattern = ? 
                WHERE id = ?
            """, (new_pattern, score_id))
            
            conn.commit()
            logging.info("Updated Joanna's pattern in the database")
            
            # Verify the update
            cursor.execute("SELECT emoji_pattern FROM score WHERE id = ?", (score_id,))
            updated_pattern = cursor.fetchone()["emoji_pattern"]
            updated_rows = updated_pattern.count('\n') + 1
            logging.info(f"Verified pattern now has {updated_rows} rows")
            
            conn.close()
            return True
        else:
            logging.info("No fix needed or pattern already correct")
            conn.close()
            return False
    except Exception as e:
        logging.error(f"Error fixing Joanna's pattern: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py to generate website files"""
    try:
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def apply_cache_busting():
    """Apply cache-busting techniques to all exported files"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Generate cache buster value
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        cache_buster = f"{timestamp}-{random_string}"
        logging.info(f"Using cache buster: {cache_buster}")
        
        # 1. Create a cache manifest file
        manifest = {
            "version": cache_buster,
            "generated": datetime.now().isoformat(),
            "files": []
        }
        
        # 2. Process HTML files
        html_files = []
        for root, dirs, files in os.walk(export_dir):
            for file in files:
                if file.endswith(".html"):
                    html_files.append(os.path.join(root, file))
                    rel_path = os.path.relpath(os.path.join(root, file), export_dir)
                    manifest["files"].append(rel_path)
        
        logging.info(f"Found {len(html_files)} HTML files to modify")
        
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add meta tags to head
                if "<head>" in content:
                    meta_tags = f"""<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta name="version" content="{cache_buster}" />"""
                    
                    content = content.replace("<head>", meta_tags)
                
                # Add cache busters to CSS/JS includes
                content = re.sub(r'(href=["\'](.*\.css)(["\']))', f'href="\\2?v={cache_buster}\\3', content)
                content = re.sub(r'(src=["\'](.*\.js)(["\']))', f'src="\\2?v={cache_buster}\\3', content)
                
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                logging.error(f"Error processing {html_file}: {e}")
        
        # 3. Create a .nojekyll file to bypass GitHub Pages processing
        with open(os.path.join(export_dir, ".nojekyll"), 'w') as f:
            f.write("")
        
        # 4. Create a duplicate index file with timestamp in name
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            new_index = os.path.join(export_dir, f"index-{cache_buster}.html")
            shutil.copy2(index_file, new_index)
            
            # Create a redirect file
            with open(os.path.join(export_dir, "latest.html"), 'w') as f:
                f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="refresh" content="0;url=index-{cache_buster}.html">
    <title>Redirecting to latest version</title>
</head>
<body>
    <p>Redirecting to <a href="index-{cache_buster}.html">latest version</a>...</p>
</body>
</html>""")
            
        # 5. Create manifest.json file
        with open(os.path.join(export_dir, "manifest.json"), 'w') as f:
            json.dump(manifest, f, indent=2)
            
        # 6. Update page title to include timestamp
        for html_file in html_files:
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add timestamp to title
                title_pattern = r'<title>(.*?)</title>'
                if re.search(title_pattern, content):
                    new_title = f'<title>\\1 (Updated: {timestamp})</title>'
                    content = re.sub(title_pattern, new_title, content)
                    
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            except Exception as e:
                logging.error(f"Error updating title in {html_file}: {e}")
                
        logging.info("Applied cache busting to all website files")
        return cache_buster
    except Exception as e:
        logging.error(f"Error applying cache busting: {e}")
        return None

def setup_git_repository():
    """Set up git repository for GitHub Pages"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Check if .git directory exists
        git_dir = os.path.join(export_dir, ".git")
        is_git_repo = os.path.exists(git_dir)
        
        if is_git_repo:
            logging.info("Git repository already exists in website_export")
            
            # Set git user config
            subprocess.run(["git", "config", "user.name", "Wordle League Bot"], cwd=export_dir)
            subprocess.run(["git", "config", "user.email", "wordle-league-bot@example.com"], cwd=export_dir)
            
            return True
        else:
            logging.info("Initializing new git repository in website_export")
            
            # Initialize new git repository
            subprocess.run(["git", "init"], cwd=export_dir)
            
            # Set git user config
            subprocess.run(["git", "config", "user.name", "Wordle League Bot"], cwd=export_dir)
            subprocess.run(["git", "config", "user.email", "wordle-league-bot@example.com"], cwd=export_dir)
            
            # Create gh-pages branch
            subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=export_dir)
            
            # Add remote origin
            try:
                subprocess.run(["git", "remote", "add", "origin", "https://github.com/brentcurtis182/wordle-league.git"], cwd=export_dir)
            except:
                # Remote may already exist
                pass
            
            return True
    except Exception as e:
        logging.error(f"Error setting up git repository: {e}")
        return False

def push_to_github(cache_buster):
    """Push changes to GitHub"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        commit_msg = f"Cache-busting update: {cache_buster}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir)
        
        # Force push to gh-pages
        logging.info("Force pushing to GitHub...")
        push_result = subprocess.run(
            ["git", "push", "-f", "origin", "gh-pages"], 
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if "error" in push_result.stderr.lower():
            logging.error(f"Push error: {push_result.stderr}")
            return False
        else:
            logging.info("Successfully pushed to GitHub Pages")
            return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting cache-busting website refresh with Git setup...")
    
    # Step 1: Fix Joanna's pattern
    logging.info("\nStep 1: Checking and fixing Joanna's pattern...")
    check_and_fix_joanna_pattern()
    
    # Step 2: Run export_leaderboard.py
    logging.info("\nStep 2: Running export_leaderboard.py...")
    if not run_export_leaderboard():
        logging.error("Failed to export website, aborting")
        return
    
    # Step 3: Apply cache busting to all files
    logging.info("\nStep 3: Applying cache busting...")
    cache_buster = apply_cache_busting()
    if not cache_buster:
        logging.error("Failed to apply cache busting, aborting")
        return
    
    # Step 4: Set up git repository
    logging.info("\nStep 4: Setting up Git repository...")
    if not setup_git_repository():
        logging.error("Failed to set up git repository, aborting")
        return
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub...")
    if not push_to_github(cache_buster):
        logging.error("Failed to push to GitHub, aborting")
        return
    
    logging.info("\nCache-busting website refresh complete!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("For guaranteed fresh content, use one of these URLs:")
    logging.info(f"1. https://brentcurtis182.github.io/wordle-league/latest.html")
    logging.info(f"2. https://brentcurtis182.github.io/wordle-league/index-{cache_buster}.html")

if __name__ == "__main__":
    main()
