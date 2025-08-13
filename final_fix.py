#!/usr/bin/env python
# Final fix for Wordle League website

import os
import sqlite3
import subprocess
import logging
import shutil
import time
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def verify_database():
    """Verify that Joanna's score is removed"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Check Joanna's score
        cursor.execute("""
            SELECT s.* FROM score s 
            JOIN player p ON s.player_id = p.id 
            WHERE p.name = 'Joanna' AND s.wordle_number = 1500
        """)
        score = cursor.fetchone()
        
        if score:
            logging.warning(f"Found Joanna's score, removing it: {score}")
            
            # Get Joanna's ID
            cursor.execute("SELECT id FROM player WHERE name = 'Joanna'")
            joanna_id = cursor.fetchone()[0]
            
            # Delete the score
            cursor.execute("DELETE FROM score WHERE player_id = ? AND wordle_number = 1500", (joanna_id,))
            conn.commit()
            logging.info(f"Removed Joanna's score")
        else:
            logging.info("Joanna's score already removed - good!")
            
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Database verification failed: {e}")
        return False

def clean_export_directory():
    """Clean the export directory and set up git"""
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    # Remove directory if it exists
    if os.path.exists(export_dir):
        try:
            # Handle read-only files
            for root, dirs, files in os.walk(export_dir, topdown=False):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.chmod(file_path, 0o777)  # Make writable
                    except:
                        pass
                        
            shutil.rmtree(export_dir, ignore_errors=True)
            time.sleep(1)  # Give system time to release handles
            logging.info(f"Removed existing export directory: {export_dir}")
        except Exception as e:
            logging.error(f"Error removing export directory: {e}")
            return False
    
    # Create fresh directory
    try:
        os.makedirs(export_dir, exist_ok=True)
        logging.info(f"Created fresh export directory: {export_dir}")
        
        # Initialize git
        subprocess.run(["git", "init"], cwd=export_dir, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=export_dir, check=True, capture_output=True)
        
        # Configure git (just for this repository)
        subprocess.run(["git", "config", "user.email", "automation@example.com"], cwd=export_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Wordle League Automation"], cwd=export_dir, check=True, capture_output=True)
        
        # Set remote origin
        subprocess.run(
            ["git", "remote", "add", "origin", "https://github.com/brentcurtis182/wordle-league.git"], 
            cwd=export_dir, 
            check=True,
            capture_output=True
        )
        
        logging.info("Git repository initialized with gh-pages branch")
        return True
    except Exception as e:
        logging.error(f"Error setting up export directory: {e}")
        return False

def run_export_leaderboard():
    """Run export_leaderboard.py with proper weekly reset date"""
    try:
        # Create weekly reset marker file
        today = datetime.now()
        today_weekday = today.weekday()  # 0 is Monday
        days_since_monday = today_weekday
        start_of_week = today - timedelta(days=days_since_monday)
        start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
        start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
        
        with open("weekly_reset_marker.txt", 'w') as f:
            f.write(start_of_week_str)
        logging.info(f"Created weekly reset marker: {start_of_week_str}")
        
        # Run export script
        logging.info("Running export_leaderboard.py...")
        process = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
        
        if process.returncode == 0:
            logging.info("Website export successful")
            return True
        else:
            logging.error(f"Website export failed: {process.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error running export_leaderboard.py: {e}")
        return False

def add_cache_control():
    """Add cache control to exported files"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add .nojekyll file
        with open(os.path.join(export_dir, ".nojekyll"), 'w') as f:
            f.write("")
        
        # Add index.html cache control meta tags if it exists
        index_path = os.path.join(export_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add cache control meta tags if not already present
            if "<meta http-equiv=\"Cache-Control\"" not in content:
                head_tag = "<head>"
                cache_tags = """<head>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">"""
                
                content = content.replace(head_tag, cache_tags)
                
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logging.info("Added cache control meta tags to index.html")
        else:
            logging.warning("index.html not found, couldn't add cache control tags")
        
        # Create a timestamp file to bust cache
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        with open(os.path.join(export_dir, f"timestamp_{timestamp}.txt"), 'w') as f:
            f.write(f"Generated at: {datetime.now().isoformat()}")
        
        logging.info("Added cache control files")
        return True
    except Exception as e:
        logging.error(f"Error adding cache control: {e}")
        return False

def push_to_github():
    """Force push to GitHub Pages"""
    try:
        export_dir = os.path.join(os.getcwd(), "website_export")
        
        # Add all files
        subprocess.run(["git", "add", "."], cwd=export_dir, check=True)
        
        # Commit changes
        commit_msg = f"Fix Joanna score and weekly reset: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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

def create_log_file():
    """Create log file with details of what was done"""
    try:
        with open("fix_log.txt", 'w') as f:
            f.write(f"Wordle League Fix Log - {datetime.now().isoformat()}\n\n")
            
            # Check database state
            conn = sqlite3.connect("wordle_league.db")
            cursor = conn.cursor()
            
            # Get all players
            cursor.execute("SELECT id, name FROM player")
            players = cursor.fetchall()
            f.write(f"Players in database: {len(players)}\n")
            for player in players:
                f.write(f"  ID: {player[0]}, Name: {player[1]}\n")
            
            # Check for Joanna's score
            cursor.execute("""
                SELECT s.* FROM score s 
                JOIN player p ON s.player_id = p.id 
                WHERE p.name = 'Joanna' AND s.wordle_number = 1500
            """)
            joanna_score = cursor.fetchone()
            f.write(f"\nJoanna Wordle #1500 score: {'Found' if joanna_score else 'Not found (correct)'}\n")
            
            # Get weekly scores
            today = datetime.now()
            today_weekday = today.weekday()
            days_since_monday = today_weekday
            start_of_week = today - timedelta(days=days_since_monday)
            start_of_week = start_of_week.replace(hour=3, minute=0, second=0, microsecond=0)
            start_of_week_str = start_of_week.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute("""
                SELECT s.wordle_number, s.date, p.name 
                FROM score s
                JOIN player p ON s.player_id = p.id
                WHERE s.date >= ?
                ORDER BY s.date DESC
            """, (start_of_week_str,))
            weekly_scores = cursor.fetchall()
            
            f.write(f"\nWeekly scores since {start_of_week_str}: {len(weekly_scores)}\n")
            for score in weekly_scores:
                f.write(f"  Wordle #{score[0]} - {score[2]} - {score[1]}\n")
            
            # Check export directory
            export_dir = os.path.join(os.getcwd(), "website_export")
            f.write(f"\nExport directory exists: {os.path.exists(export_dir)}\n")
            if os.path.exists(export_dir):
                index_path = os.path.join(export_dir, "index.html")
                f.write(f"index.html exists: {os.path.exists(index_path)}\n")
                
                if os.path.exists(os.path.join(export_dir, ".git")):
                    f.write("Git repository initialized\n")
                
            conn.close()
            logging.info("Created detailed log file: fix_log.txt")
            return True
    except Exception as e:
        logging.error(f"Error creating log file: {e}")
        return False

def main():
    logging.info("Starting final fix for Wordle League website...")
    
    # Step 1: Verify database
    logging.info("\nStep 1: Verifying database...")
    if not verify_database():
        logging.error("Database verification failed. Stopping.")
        return
    
    # Step 2: Clean export directory
    logging.info("\nStep 2: Cleaning export directory...")
    if not clean_export_directory():
        logging.error("Failed to clean export directory. Stopping.")
        return
    
    # Step 3: Run export_leaderboard.py
    logging.info("\nStep 3: Running export_leaderboard.py...")
    if not run_export_leaderboard():
        logging.error("Failed to run export_leaderboard.py. Stopping.")
        return
    
    # Step 4: Add cache control
    logging.info("\nStep 4: Adding cache control...")
    if not add_cache_control():
        logging.error("Failed to add cache control. Continuing anyway.")
    
    # Step 5: Push to GitHub
    logging.info("\nStep 5: Pushing to GitHub...")
    if not push_to_github():
        logging.error("Failed to push to GitHub. Stopping.")
        return
    
    # Step 6: Create log file
    logging.info("\nStep 6: Creating log file...")
    create_log_file()
    
    logging.info("\n=====================================")
    logging.info("Final fix complete!")
    logging.info("=====================================")
    logging.info("\nAccess the updated website at: https://brentcurtis182.github.io/wordle-league/")
    logging.info("If you still see old data, please use Ctrl+F5 or open in incognito mode.")
    logging.info("Wait approximately 1-2 minutes for GitHub Pages to update.")
    logging.info("\nWeekly scores should reflect only scores since Monday 3:00 AM.")
    logging.info("Currently, this might be empty if no new scores have been added since then.")

if __name__ == "__main__":
    main()
