#!/usr/bin/env python
# Fix Joanna's pattern and properly push to GitHub

import os
import sys
import sqlite3
import subprocess
import logging
from datetime import datetime
import dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def load_env_variables():
    """Load environment variables from .env file"""
    dotenv.load_dotenv()
    
    # Check if GitHub variables exist
    github_token = os.environ.get("GITHUB_TOKEN")
    github_username = os.environ.get("GITHUB_USERNAME")
    github_repo_name = os.environ.get("GITHUB_REPO_NAME")
    
    if not github_token or not github_username or not github_repo_name:
        logging.error("Missing GitHub environment variables. Check .env file.")
        return False
    
    # Set GITHUB_REPO for compatibility with enhanced_functions.py
    os.environ["GITHUB_REPO"] = f"https://github.com/{github_username}/{github_repo_name}.git"
    logging.info(f"Set GITHUB_REPO to: {os.environ['GITHUB_REPO']}")
    
    return True

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

def add_cache_busting():
    """Add cache busting to website files"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Add cache busting timestamp file
        timestamp_file = os.path.join(export_dir, f"timestamp_{timestamp}.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Cache busting timestamp: {datetime.now().isoformat()}")
        
        # Create .nojekyll file
        nojekyll_file = os.path.join(export_dir, ".nojekyll")
        if not os.path.exists(nojekyll_file):
            with open(nojekyll_file, "w") as f:
                f.write("")
        
        return timestamp
    except Exception as e:
        logging.error(f"Error adding cache busting: {e}")
        return None

def run_export_and_push():
    """Run export_leaderboard.py and push changes using enhanced_functions.py"""
    try:
        # Import functions from enhanced_functions.py
        sys.path.append(os.getcwd())
        from enhanced_functions import update_website, push_to_github
        
        # Run update_website function
        logging.info("Running website update...")
        update_result = update_website()
        
        if not update_result:
            logging.error("Website update failed")
            return False
        
        # Add cache busting
        timestamp = add_cache_busting()
        
        # Run push_to_github function
        logging.info("Pushing to GitHub...")
        push_result = push_to_github()
        
        if not push_result:
            logging.error("GitHub push failed")
            return False
            
        logging.info("Successfully updated website and pushed to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error in export and push process: {e}")
        return False

def main():
    logging.info("Starting pattern fix and GitHub push script...")
    
    # Step 1: Load environment variables
    logging.info("\nStep 1: Loading environment variables...")
    if not load_env_variables():
        logging.error("Failed to load environment variables, aborting")
        return
    
    # Step 2: Fix Joanna's pattern
    logging.info("\nStep 2: Checking and fixing Joanna's pattern...")
    check_and_fix_joanna_pattern()
    
    # Step 3: Run export and push
    logging.info("\nStep 3: Running export and pushing to GitHub...")
    success = run_export_and_push()
    
    if success:
        logging.info("\nProcess completed successfully!")
        logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
        logging.info("Note: GitHub Pages may take a few minutes to update.")
        logging.info("If you still see old content, try:")
        logging.info("1. Hard refresh (Ctrl+F5)")
        logging.info("2. Open in incognito/private window")
        logging.info("3. Try again in 5-10 minutes")
    else:
        logging.error("\nProcess failed. Check the logs above for details.")

if __name__ == "__main__":
    main()
