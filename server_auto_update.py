#!/usr/bin/env python3
# Wordle League Automated Update Script
# This script checks for new Wordle scores and updates the website automatically

import os
import sys
import time
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
        logging.FileHandler("wordle_auto_update.log"),
        logging.StreamHandler()
    ]
)

# Constants
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOCK_FILE = os.path.join(SCRIPT_DIR, "wordle_update.lock")
EXTRACTION_SCRIPT = os.path.join(SCRIPT_DIR, "integrated_auto_update.py")
EXPORT_SCRIPT = os.path.join(SCRIPT_DIR, "export_leaderboard.py")
PUBLISH_SCRIPT = os.path.join(SCRIPT_DIR, "server_publish_to_github.py")

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

def extract_wordle_scores():
    """Run the score extraction script"""
    logging.info("Starting Wordle score extraction...")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run the extraction script
    command = f"python {EXTRACTION_SCRIPT}"
    success, output = run_command(command)
    
    if success:
        logging.info("Wordle score extraction completed successfully")
        return True
    else:
        logging.error("Wordle score extraction failed")
        return False


def # Removed sync_database_tables call:
    """Run the database synchronization script to ensure scores appear on website"""
    logging.info("Synchronizing database tables...")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run the sync script
    command = f"python {SYNC_SCRIPT}"
    success, output = run_command(command)
    
    if success:
        logging.info("Database synchronization completed successfully")
        return True
    else:
        logging.error("Database synchronization failed")
        return False


def export_website():
    """Run the website export script directly"""
    logging.info("Exporting website files...")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # Run the export script
    command = f"python {EXPORT_SCRIPT}"
    success, output = run_command(command)
    
    if success:
        logging.info("Website export completed successfully")
        return True
    else:
        logging.error("Website export failed")
        return False

def publish_to_github():
    """Run the GitHub publishing script with cache busting"""
    logging.info("Publishing to GitHub...")
    
    # Change to script directory
    os.chdir(SCRIPT_DIR)
    
    # First, try the built-in publish script
    command = f"python {PUBLISH_SCRIPT}"
    success, output = run_command(command)
    
    if success:
        logging.info("GitHub publishing completed successfully")
        return True
    else:
        # If normal publishing fails, try direct git commands with cache busting
        logging.warning("Standard publishing failed, attempting manual git push with cache busting...")
        
        try:
            # Navigate to the website export directory
            os.chdir(os.path.join(SCRIPT_DIR, "website_export"))
            
            # Get current timestamp for cache busting
            timestamp = datetime.now().timestamp()
            
            # Add all files
            add_cmd = "git add ."
            run_command(add_cmd)
            
            # Commit with timestamp for cache busting
            commit_cmd = f"git commit -m \"Update with latest scores (timestamp: {timestamp})\""
            run_command(commit_cmd)
            
            # Force push to override any conflicts
            push_cmd = "git push -f origin gh-pages"
            success, output = run_command(push_cmd)
            
            # Return to script directory
            os.chdir(SCRIPT_DIR)
            
            if success:
                logging.info("Manual git push completed successfully")
                return True
            else:
                logging.error("Manual git push failed")
                return False
                
        except Exception as e:
            logging.error(f"Exception during manual git push: {e}")
            # Return to script directory in case of error
            os.chdir(SCRIPT_DIR)
            return False

def main():
    """Main function to run the automated update process"""
    parser = argparse.ArgumentParser(description="Wordle League Automated Update Script")
    parser.add_argument("--force", action="store_true", help="Force extraction even if no new messages")
    parser.add_argument("--extract-only", action="store_true", help="Only extract scores, don't publish")
    parser.add_argument("--sync-only", action="store_true", help="Only sync database tables, don't extract")
    parser.add_argument("--export-only", action="store_true", help="Only export website, don't extract")
    parser.add_argument("--publish-only", action="store_true", help="Only publish to GitHub, don't extract")
    args = parser.parse_args()
    
    # Check if another instance is already running
    if is_process_running():
        logging.warning("Another instance is already running. Exiting.")
        sys.exit(0)
    
    # Create lock file
    create_lock_file()
    
    try:
        start_time = time.time()
        logging.info("Starting Wordle League automated update")
        
        if args.publish_only:
            # Only publish to GitHub
            export_website()
            publish_to_github()
        elif args.export_only:
            # Only export website
            export_website()
        elif args.sync_only:
            # Only sync database tables
            # Removed sync_database_tables call
        elif args.extract_only:
            # Only extract scores
            extract_wordle_scores()
        else:
            # Run full process: extract, sync, export, and publish
            extraction_success = extract_wordle_scores()
            
            if extraction_success:
                # Always sync database tables after extraction
                sync_success = # Removed sync_database_tables call
                
                if sync_success:
                    # Export website files with latest scores
                    export_success = export_website()
                    
                    if export_success:
                        # Publish to GitHub with cache busting
                        publish_to_github()
        
        end_time = time.time()
        duration = end_time - start_time
        logging.info(f"Automated update completed in {duration:.2f} seconds")
    
    except Exception as e:
        logging.error(f"Error in automated update: {e}")
    
    finally:
        # Always remove lock file when done
        remove_lock_file()

if __name__ == "__main__":
    main()
