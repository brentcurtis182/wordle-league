#!/usr/bin/env python3
# Wordle Multi-League Automated Update Script
# This script checks for new Wordle scores across all leagues and updates the websites automatically

import os
import sys
import time
import json
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("wordle_multi_league_update.log"),
        logging.StreamHandler()
    ]
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(SCRIPT_DIR, "wordle_multi_update.lock")

# Multi-league scripts
EXTRACTION_SCRIPT = os.path.join(SCRIPT_DIR, "integrated_auto_update_multi_league.py")
# Use our new wrapper script instead of the template-based exporter
UPDATE_SCRIPT = os.path.join(SCRIPT_DIR, "update_all_correct_structure.py")
# Keep for reference but don't use
# EXPORT_SCRIPT = os.path.join(SCRIPT_DIR, "export_leaderboard_multi_league.py")

def is_process_running():
    """Check if another instance of this script is already running"""
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process with this PID exists
            try:
                os.kill(pid, 0)
                logging.warning(f"Another instance is already running with PID {pid}")
                return True
            except OSError:
                # Process not running, remove stale lock file
                logging.warning(f"Removing stale lock file for PID {pid}")
                os.remove(LOCK_FILE)
                return False
        except Exception as e:
            logging.error(f"Error checking lock file: {e}")
            # Remove potentially corrupted lock file
            os.remove(LOCK_FILE)
            return False
    return False

def create_lock_file():
    """Create a lock file with current PID"""
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        logging.info(f"Created lock file with PID {os.getpid()}")
    except Exception as e:
        logging.error(f"Error creating lock file: {e}")
        sys.exit(1)

def remove_lock_file():
    """Remove the lock file"""
    if os.path.exists(LOCK_FILE):
        try:
            os.remove(LOCK_FILE)
            logging.info("Removed lock file")
        except Exception as e:
            logging.error(f"Error removing lock file: {e}")

def run_command(command):
    """Run a shell command and return the output"""
    try:
        logging.info(f"Running command: {command}")
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(f"Command output: {result.stdout.strip()}")
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return False, e.stderr
    except Exception as e:
        logging.error(f"Exception running command: {e}")
        return False, str(e)

def get_league_config():
    """Load league configuration from JSON file"""
    config_file = os.path.join(SCRIPT_DIR, "league_config.json")
    
    if not os.path.exists(config_file):
        logging.error("league_config.json not found")
        return None
        
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logging.info(f"Loaded {len(config['leagues'])} leagues from configuration")
        return config
    except Exception as e:
        logging.error(f"Error loading league config: {e}")
        return None

def extract_wordle_scores():
    """Run the multi-league score extraction script"""
    logging.info("Starting multi-league Wordle score extraction...")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run the extraction script
    command = f"python {EXTRACTION_SCRIPT}"
    success, output = run_command(command)
    
    if success:
        logging.info("Multi-league Wordle score extraction completed successfully")
        return True
    else:
        logging.error("Multi-league Wordle score extraction failed")
        return False

# Removed sync_database_tables function as it's not being used

def export_websites():
    """Run the multi-league website update script that maintains proper tab structure"""
    logging.info("Updating multi-league websites with proper structure...")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run our new update script that preserves tab structure and day columns
    command = f"python {UPDATE_SCRIPT}"
    success, output = run_command(command)
    
    if success:
        logging.info("Multi-league websites updated successfully with correct structure")
        return True
    else:
        logging.error("Multi-league website update failed")
        return False

def publish_to_github():
    """Publish the website to GitHub with cache busting"""
    logging.info("Publishing websites to GitHub...")
    
    try:
        # Import the push_to_github function from enhanced_functions
        sys.path.append(SCRIPT_DIR)
        from enhanced_functions import push_to_github
        
        # Call the function directly
        result = push_to_github()
        
        if result:
            logging.info("GitHub publish completed successfully")
            return True
        else:
            logging.warning("Standard publishing failed, attempting manual git push with cache busting...")
            return manual_github_push()
            
    except ImportError:
        logging.error("Could not import push_to_github from enhanced_functions")
        return manual_github_push()
    except Exception as e:
        logging.error(f"Exception during publishing: {e}")
        return manual_github_push()

def manual_github_push():
    """Fallback method to manually push to GitHub with cache busting"""
    try:
        # Navigate to the website export directory
        os.chdir(os.path.join(SCRIPT_DIR, "website_export"))
        
        # Get current timestamp for cache busting
        timestamp = datetime.now().timestamp()
        
        # Make sure we're on the gh-pages branch
        run_command("git checkout gh-pages")
        
        # Pull first to avoid conflicts
        run_command("git pull origin gh-pages")
        
        # Add all files
        run_command("git add .")
        
        # Commit with timestamp for cache busting
        commit_cmd = f"git commit -m \"Update with latest scores from all leagues (timestamp: {timestamp})\""
        run_command(commit_cmd)
        
        # Push to GitHub
        push_cmd = "git push origin gh-pages"
        success, output = run_command(push_cmd)
        
        # Return to script directory
        os.chdir(SCRIPT_DIR)
        
        if success:
            logging.info("Manual git push completed successfully")
            return True
        else:
            # If regular push failed, try force push as last resort
            os.chdir(os.path.join(SCRIPT_DIR, "website_export"))
            force_push_cmd = "git push -f origin gh-pages"
            success, output = run_command(force_push_cmd)
            os.chdir(SCRIPT_DIR)
            
            if success:
                logging.info("Force git push completed successfully")
                return True
            else:
                logging.error("All git push attempts failed")
                return False
    except Exception as e:
        logging.error(f"Exception during manual git push: {e}")
        # Return to script directory in case of error
        os.chdir(SCRIPT_DIR)
        return False

def main():
    """Main function to run the automated update process"""
    parser = argparse.ArgumentParser(description="Wordle Multi-League Automated Update Script")
    parser.add_argument("--force", action="store_true", help="Force extraction even if no new messages")
    parser.add_argument("--extract-only", action="store_true", help="Only extract scores, don't publish")
    parser.add_argument("--export-only", action="store_true", help="Only export websites, don't extract")
    parser.add_argument("--publish-only", action="store_true", help="Only publish to GitHub, don't extract")
    parser.add_argument("--league", type=int, help="Process only a specific league ID")
    args = parser.parse_args()
    
    # Check if another instance is already running
    if is_process_running():
        logging.warning("Another instance is already running. Exiting.")
        sys.exit(0)
    
    # Create lock file
    create_lock_file()
    
    try:
        start_time = time.time()
        logging.info("Starting Wordle Multi-League automated update")
        
        # Load league configuration
        config = get_league_config()
        if not config:
            logging.error("Failed to load league configuration. Exiting.")
            sys.exit(1)
            
        # Process based on command arguments
        if args.publish_only:
            # Only publish to GitHub
            export_websites()
            publish_to_github()
        elif args.export_only:
            # Only export websites
            export_websites()
        elif args.extract_only:
            # Only extract scores
            extract_wordle_scores()
        else:
            # Run full process: extract, export, and publish
            extraction_success = extract_wordle_scores()
            
            # Skip database sync - no longer needed with unified scores table
            logging.info("Database sync step skipped - using unified scores table")
            sync_success = True  # Skip sync, mark as successful
            
            # Export all league websites
            export_success = export_websites()
            
            # Publish to GitHub with cache busting
            if export_success:
                publish_to_github()
        
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Multi-league automated update completed in {duration:.2f} seconds")
    
    except Exception as e:
        logging.error(f"Error in multi-league automated update: {e}")
    
    finally:
        # Always remove lock file when done
        remove_lock_file()

if __name__ == "__main__":
    main()
