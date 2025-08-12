#!/usr/bin/env python3
"""
Script to restore the website and database to the snapshot from July 31, 2025
"""
import os
import subprocess
import shutil
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_snapshot.log"),
        logging.StreamHandler()
    ]
)

def run_command(cmd, cwd=None):
    """Run a command and log output"""
    logging.info(f"Running command: {cmd}")
    process = subprocess.run(
        cmd, 
        shell=True, 
        cwd=cwd,
        text=True, 
        capture_output=True
    )
    logging.info(f"Command completed with exit code: {process.returncode}")
    if process.stdout:
        logging.info(f"Output: {process.stdout}")
    if process.stderr:
        logging.warning(f"Errors: {process.stderr}")
    return process.returncode

def restore_website():
    """Restore website from backup"""
    logging.info("Restoring website from backup...")
    try:
        # Use robocopy to restore website files (mirror backup to website_export)
        run_command("robocopy c:\\Wordle-League\\website_backup c:\\Wordle-League\\website_export /E /MIR")
        logging.info("Website restored successfully")
        return True
    except Exception as e:
        logging.error(f"Error restoring website: {e}")
        return False

def restore_database():
    """Restore database from backup"""
    logging.info("Restoring database from backup...")
    try:
        # First make sure the current database is closed
        # by forcing any connections to close through Python's GC
        import gc
        gc.collect()
        
        # Small delay to ensure files are released
        time.sleep(1)
        
        # Copy backup database over current database
        shutil.copy2("c:\\Wordle-League\\wordle_league_backup.db", "c:\\Wordle-League\\wordle_league.db")
        logging.info("Database restored successfully")
        return True
    except Exception as e:
        logging.error(f"Error restoring database: {e}")
        return False

def push_to_github():
    """Push restored website to GitHub"""
    logging.info("Pushing restored website to GitHub...")
    try:
        # Change to website_export directory
        cwd = "c:\\Wordle-League\\website_export"
        
        # Set git config
        run_command("git config user.name \"brentcurtis182\"", cwd=cwd)
        run_command("git config user.email \"wordle.league.bot@example.com\"", cwd=cwd)
        
        # Add and commit changes
        run_command("git add .", cwd=cwd)
        run_command("git commit -m \"Restored to snapshot from July 31, 2025\"", cwd=cwd)
        
        # Force push to overwrite any changes on GitHub
        run_command("git push -f origin gh-pages", cwd=cwd)
        
        logging.info("Successfully pushed restored website to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    """Main function to restore snapshot"""
    logging.info("Starting restoration of July 31 snapshot...")
    
    website_restored = restore_website()
    db_restored = restore_database()
    
    if website_restored and db_restored:
        logging.info("Local files restored successfully")
        
        # Optionally push to GitHub (comment out if not needed)
        push_to_github()
    else:
        logging.error("Restoration failed")

if __name__ == "__main__":
    main()
