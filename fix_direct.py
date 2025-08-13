#!/usr/bin/env python
# fix_direct.py - Direct fix for all issues with minimal complexity

import os
import sqlite3
import subprocess
import logging
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

# Constants
DATABASE_PATH = "wordle_league.db"
EXPORT_DIR = "website_export"

def remove_joanna_score():
    """Remove Joanna's incorrect score for Wordle #1500"""
    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # First find Joanna's player ID
        cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
        result = cursor.fetchone()
        if not result:
            logging.info("Joanna not found in players table")
            conn.close()
            return False
            
        joanna_id = result[0]
        logging.info(f"Found Joanna's player ID: {joanna_id}")
        
        # Delete Joanna's score for Wordle #1500
        cursor.execute(
            "DELETE FROM score WHERE player_id = ? AND wordle_number = 1500", 
            (joanna_id,)
        )
        
        if cursor.rowcount > 0:
            logging.info(f"Removed {cursor.rowcount} score(s) for Joanna, Wordle #1500")
        else:
            logging.info("No scores found for Joanna, Wordle #1500")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error removing Joanna's score: {e}")
        return False

def rebuild_export_directory():
    """Clean and rebuild the export directory from scratch"""
    try:
        export_path = os.path.join(os.getcwd(), EXPORT_DIR)
        
        # Check if export directory exists
        if os.path.exists(export_path):
            logging.info(f"Backing up existing export directory")
            backup_dir = f"{EXPORT_DIR}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copytree(export_path, backup_dir, dirs_exist_ok=True)
            
            logging.info(f"Removing existing export directory")
            shutil.rmtree(export_path)
        
        # Create fresh export directory
        os.makedirs(export_path, exist_ok=True)
        logging.info(f"Created fresh export directory: {export_path}")
        
        # Initialize git repository
        subprocess.run(["git", "init"], cwd=export_path, check=True)
        subprocess.run(["git", "config", "user.name", "brentcurtis182"], cwd=export_path, check=True)
        subprocess.run(["git", "config", "user.email", "brentcurtis182@github.com"], cwd=export_path, check=True)
        
        # Create and switch to gh-pages branch
        subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=export_path, check=True)
        
        # Add remote
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/brentcurtis182/wordle-league.git"], 
            cwd=export_path, 
            check=True
        )
        
        logging.info("Git repository initialized with gh-pages branch")
        return True
    except Exception as e:
        logging.error(f"Error rebuilding export directory: {e}")
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

def add_cache_busting():
    """Add cache busting to the exported files"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Create a timestamp file
        with open(os.path.join(EXPORT_DIR, "timestamp.txt"), "w") as f:
            f.write(f"Last update: {datetime.now()}")
        
        # Create version file
        with open(os.path.join(EXPORT_DIR, "version.js"), "w") as f:
            f.write(f"// Version: {timestamp}")
        
        # Create .nojekyll file for GitHub Pages
        with open(os.path.join(EXPORT_DIR, ".nojekyll"), "w") as f:
            pass
            
        logging.info("Added cache busting files")
        return True
    except Exception as e:
        logging.error(f"Error adding cache busting: {e}")
        return False

def push_to_github():
    """Push changes to GitHub with force option"""
    try:
        export_path = os.path.join(os.getcwd(), EXPORT_DIR)
        
        logging.info("Adding files to Git...")
        subprocess.run(["git", "add", "."], cwd=export_path, check=True)
        
        logging.info("Committing changes...")
        subprocess.run(
            ["git", "commit", "-m", f"Force update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
            cwd=export_path
        )
        
        logging.info("Force pushing to GitHub...")
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_path, check=True)
        
        logging.info("Successfully pushed to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    """Main function"""
    logging.info("Starting direct fix...")
    
    # Step 1: Remove Joanna's incorrect score
    logging.info("\nStep 1: Removing Joanna's incorrect score")
    if remove_joanna_score():
        logging.info("Successfully removed Joanna's score")
    
    # Step 2: Rebuild the export directory from scratch
    logging.info("\nStep 2: Rebuilding export directory")
    if rebuild_export_directory():
        logging.info("Successfully rebuilt export directory")
    
    # Step 3: Run export_leaderboard.py
    logging.info("\nStep 3: Running export_leaderboard.py")
    if run_export_leaderboard():
        logging.info("Successfully generated website files")
    
    # Step 4: Add cache busting
    logging.info("\nStep 4: Adding cache busting")
    if add_cache_busting():
        logging.info("Successfully added cache busting")
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub")
    if push_to_github():
        logging.info("Successfully pushed to GitHub")
    
    logging.info("\nAll fixes completed!")
    logging.info("The website should now be available at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("Note: GitHub Pages may take a few minutes to update. Try opening in a private/incognito window.")

if __name__ == "__main__":
    main()
