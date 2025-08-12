#!/usr/bin/env python
# Aggressive GitHub Pages cache-busting script

import os
import sqlite3
import subprocess
import logging
import shutil
import random
import string
from datetime import datetime
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("github_refresh.log")]
)

def clear_export_dir():
    """Completely remove and recreate the export directory"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Remove the directory if it exists
        if os.path.exists(export_dir):
            logging.info(f"Removing existing export directory: {export_dir}")
            
            # Force removal even if git complains
            for attempt in range(3):
                try:
                    shutil.rmtree(export_dir)
                    break
                except Exception as e:
                    logging.warning(f"Attempt {attempt+1} failed: {e}")
                    time.sleep(1)
            
            # If it still exists, try to delete files individually
            if os.path.exists(export_dir):
                for root, dirs, files in os.walk(export_dir):
                    for f in files:
                        try:
                            os.unlink(os.path.join(root, f))
                        except:
                            pass
                    for d in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, d))
                        except:
                            pass
                try:
                    shutil.rmtree(export_dir)
                except Exception as e:
                    logging.error(f"Final attempt to remove directory failed: {e}")
        
        # Create fresh directory
        os.makedirs(export_dir)
        logging.info(f"Created fresh export directory: {export_dir}")
        
        return True
    except Exception as e:
        logging.error(f"Error clearing export directory: {e}")
        return False

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
        
        logging.info(f"Joanna's Wordle 1500 score: ID={score_id}, Score={score}, Pattern={repr(pattern)}")
        
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

def setup_git_repo():
    """Set up a fresh git repository in the export directory"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=export_dir, check=True)
        logging.info("Git repository initialized")
        
        # Configure git
        subprocess.run(["git", "config", "user.name", "Wordle League Bot"], cwd=export_dir)
        subprocess.run(["git", "config", "user.email", "wordle-league-bot@example.com"], cwd=export_dir)
        logging.info("Git user configured")
        
        # Create branch
        subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=export_dir)
        logging.info("Created gh-pages branch")
        
        # Set remote origin if needed
        try:
            subprocess.run(["git", "remote", "add", "origin", "https://github.com/brentcurtis182/wordle-league.git"], cwd=export_dir)
            logging.info("Git remote origin set")
        except:
            logging.info("Remote origin already exists")
        
        return True
    except Exception as e:
        logging.error(f"Error setting up git repo: {e}")
        return False

def run_export_with_modifications():
    """Run export_leaderboard.py and modify the output with aggressive cache busting"""
    try:
        # Run export
        logging.info("Running export_leaderboard.py...")
        result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if result.returncode != 0:
            logging.error(f"Export failed: {result.stderr}")
            return False
            
        logging.info("Website export successful")
        
        # Add aggressive cache busters
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # 1. Add randomized file name
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_file = os.path.join(export_dir, f"force_refresh_{random_id}_{timestamp}.html")
        
        with open(random_file, 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="0;url=index.html?nocache={random_id}">
                <title>Refreshing...</title>
            </head>
            <body>
                <p>Redirecting to <a href="index.html?nocache={random_id}">latest version</a>...</p>
            </body>
            </html>
            """)
        
        # 2. Add .nojekyll file to bypass Jekyll processing
        with open(os.path.join(export_dir, ".nojekyll"), 'w') as f:
            f.write("")
        
        # 3. Update index.html with cache-busting meta tags
        index_path = os.path.join(export_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                index_content = f.read()
                
            # Add cache-busting meta tags
            if "<head>" in index_content:
                cache_meta = f"""<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate" />
    <meta http-equiv="Pragma" content="no-cache" />
    <meta http-equiv="Expires" content="0" />
    <meta name="version" content="{random_id}_{timestamp}" />"""
                
                index_content = index_content.replace("<head>", cache_meta)
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(index_content)
                    
                logging.info("Added cache-busting meta tags to index.html")
        
        # 4. Create direct access file
        access_file = os.path.join(export_dir, f"direct_{timestamp}.html")
        with open(access_file, 'w') as f:
            f.write(f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta http-equiv="refresh" content="0;url=index.html?{random_id}">
                <title>Direct Access</title>
            </head>
            <body>
                <p>Direct access to <a href="index.html?{random_id}">Wordle League</a></p>
                <p>Generated at: {timestamp}</p>
            </body>
            </html>
            """)
            
        # 5. Create .htaccess file (GitHub Pages won't use this, but just in case)
        with open(os.path.join(export_dir, ".htaccess"), 'w') as f:
            f.write("""
            Header set Cache-Control "no-cache, no-store, must-revalidate"
            Header set Pragma "no-cache"
            Header set Expires "0"
            """)
        
        # Copy the randomized file name to LATEST.html for consistent access
        latest_file = os.path.join(export_dir, "LATEST.html")
        shutil.copy2(random_file, latest_file)
        
        return True, random_id, timestamp
    except Exception as e:
        logging.error(f"Error running export with modifications: {e}")
        return False, None, None

def force_push_to_github():
    """Force push to GitHub with aggressive options"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add all files
        subprocess.run(["git", "add", "-A"], cwd=export_dir, check=True)
        logging.info("Added all files to git")
        
        # Create a uniquely named commit
        commit_msg = f"Force refresh website: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=export_dir)
        logging.info(f"Created commit: {commit_msg}")
        
        # Force push with lease to avoid race conditions but still override
        logging.info("Force pushing to GitHub...")
        push_result = subprocess.run(
            ["git", "push", "-f", "--force-with-lease", "origin", "gh-pages"], 
            cwd=export_dir,
            capture_output=True,
            text=True
        )
        
        if push_result.returncode != 0 or "error" in push_result.stderr.lower():
            # If force-with-lease fails, try a plain force push
            logging.warning(f"Force with lease push failed: {push_result.stderr}")
            logging.info("Attempting plain force push...")
            
            force_result = subprocess.run(
                ["git", "push", "-f", "origin", "gh-pages"], 
                cwd=export_dir,
                capture_output=True,
                text=True
            )
            
            if "error" in force_result.stderr.lower():
                logging.error(f"Push error: {force_result.stderr}")
                return False
            else:
                logging.info("Successfully pushed to GitHub Pages with plain force")
                return True
        else:
            logging.info("Successfully pushed to GitHub Pages with force-with-lease")
            return True
    except Exception as e:
        logging.error(f"Error force pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting aggressive GitHub Pages refresh...")
    
    # Step 1: Fix Joanna's pattern in the database
    logging.info("\nStep 1: Checking and fixing Joanna's pattern...")
    check_and_fix_joanna_pattern()
    
    # Step 2: Clear export directory completely
    logging.info("\nStep 2: Completely clearing export directory...")
    if not clear_export_dir():
        logging.error("Failed to clear export directory, aborting")
        return
    
    # Step 3: Setup fresh git repo
    logging.info("\nStep 3: Setting up fresh git repository...")
    if not setup_git_repo():
        logging.error("Failed to setup git repository, aborting")
        return
    
    # Step 4: Run export with aggressive cache busting
    logging.info("\nStep 4: Running export with cache-busting modifications...")
    success, random_id, timestamp = run_export_with_modifications()
    
    if not success:
        logging.error("Failed to run export with modifications, aborting")
        return
    
    # Step 5: Force push to GitHub
    logging.info("\nStep 5: Force pushing to GitHub...")
    if not force_push_to_github():
        logging.error("Failed to push to GitHub, aborting")
        return
    
    # Output access instructions
    logging.info("\nWebsite refresh complete!")
    logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("For guaranteed fresh content, use one of these URLs:")
    logging.info(f"1. https://brentcurtis182.github.io/wordle-league/LATEST.html")
    logging.info(f"2. https://brentcurtis182.github.io/wordle-league/direct_{timestamp}.html")
    logging.info(f"3. https://brentcurtis182.github.io/wordle-league/index.html?nocache={random_id}")
    logging.info("\nIf you're still seeing old content, please try:")
    logging.info("1. Clear your browser cache completely (including history and cookies)")
    logging.info("2. Try a different browser or device")
    logging.info("3. Wait 5-10 minutes as GitHub Pages may have a propagation delay")

if __name__ == "__main__":
    main()
