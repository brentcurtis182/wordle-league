import os
import time
import logging
import subprocess
from datetime import datetime

def update_website():
    """Update the website with new scores"""
    logging.info("Updating website")
    if not os.path.exists("export_leaderboard.py"):
        logging.error("export_leaderboard.py script not found")
        return False
    
    # Check export directory before export
    export_dir = os.path.join(os.getcwd(), "website_export")
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
        logging.info(f"Created export directory: {export_dir}")
    
    # Get list of files before export
    files_before = set()
    if os.path.exists(export_dir):
        for root, _, files in os.walk(export_dir):
            for file in files:
                if file.endswith(".html") or file.endswith(".json"):
                    rel_path = os.path.relpath(os.path.join(root, file), export_dir)
                    files_before.add(rel_path)
    
    # Run the export script
    logging.info("Running export_leaderboard.py script")
    result = subprocess.run(["python", "export_leaderboard.py"], capture_output=True, text=True)
    
    if result.returncode == 0:
        logging.info("Website export script completed successfully")
        
        # Get list of files after export
        files_after = set()
        modified_files = []
        for root, _, files in os.walk(export_dir):
            for file in files:
                if file.endswith(".html") or file.endswith(".json"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, export_dir)
                    files_after.add(rel_path)
                    
                    # Check if file is new or modified
                    if rel_path not in files_before:
                        modified_files.append(f"New: {rel_path}")
                    else:
                        # Check if content has changed
                        if os.path.exists(full_path):
                            mtime = os.path.getmtime(full_path)
                            # If modified in the last minute
                            if time.time() - mtime < 60:
                                modified_files.append(f"Modified: {rel_path}")
        
        # Check for deleted files
        for file in files_before - files_after:
            modified_files.append(f"Deleted: {file}")
        
        if modified_files:
            logging.info(f"Website files changed: {len(modified_files)} files")
            for file in modified_files[:10]:  # Log first 10 changes
                logging.info(f"  {file}")
            if len(modified_files) > 10:
                logging.info(f"  ... and {len(modified_files) - 10} more files")
        else:
            logging.warning("No website files appear to have changed after export")
        
        # Check specifically for today's Wordle file
        from integrated_auto_update import get_todays_wordle_number
        today_wordle = get_todays_wordle_number()
        today_file = f"daily/wordle-{today_wordle}.html"
        today_path = os.path.join(export_dir, today_file)
        if os.path.exists(today_path):
            logging.info(f"Today's Wordle file exists: {today_file}")
            # Check if it was modified recently
            mtime = os.path.getmtime(today_path)
            if time.time() - mtime < 300:  # Modified in the last 5 minutes
                logging.info(f"Today's Wordle file was recently updated")
            else:
                logging.warning(f"Today's Wordle file exists but wasn't recently modified")
        else:
            logging.warning(f"Today's Wordle file doesn't exist: {today_file}")
        
        return True
    else:
        logging.error(f"Website update failed: {result.stderr}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    logging.info("Pushing changes to GitHub")
    
    try:
        # Define the export directory path
        export_dir = os.path.join(os.getcwd(), "website_export")
        logging.info(f"Using export directory: {export_dir}")
        
        if not os.path.exists(export_dir):
            logging.error(f"Export directory not found: {export_dir}")
            return False
        
        # Check if git repo exists, if not initialize it
        if not os.path.exists(os.path.join(export_dir, ".git")):
            logging.info("Initializing git repository in website_export directory")
            subprocess.run(["git", "-C", export_dir, "init"], check=False)
        
        # Always configure git user for this repository (not global)
        git_username = os.environ.get("GITHUB_USERNAME", "Wordle League Bot")
        logging.info(f"Setting git username to: {git_username}")
        subprocess.run(["git", "-C", export_dir, "config", "user.name", git_username], check=False)
        
        git_email = os.environ.get("GITHUB_EMAIL", "wordle.league.bot@example.com")
        logging.info(f"Setting git email to: {git_email}")
        subprocess.run(["git", "-C", export_dir, "config", "user.email", git_email], check=False)
        
        # Add remote if environment variable is set
        git_repo = os.environ.get("GITHUB_REPO")
        if git_repo:
            # Check if remote already exists
            remote_check = subprocess.run(["git", "-C", export_dir, "remote"], capture_output=True, text=True, check=False)
            if "origin" not in remote_check.stdout:
                logging.info(f"Adding remote: {git_repo}")
                subprocess.run(["git", "-C", export_dir, "remote", "add", "origin", git_repo], check=False)
            else:
                logging.info("Remote 'origin' already exists")
                # Update the URL just to be sure
                subprocess.run(["git", "-C", export_dir, "remote", "set-url", "origin", git_repo], check=False)
        
        # Make sure we're on gh-pages branch
        branch_check = subprocess.run(["git", "-C", export_dir, "branch"], capture_output=True, text=True, check=False)
        logging.info(f"Current branches: {branch_check.stdout}")
        
        # Check if gh-pages branch exists
        if "gh-pages" not in branch_check.stdout:
            logging.info("Creating gh-pages branch")
            subprocess.run(["git", "-C", export_dir, "checkout", "-b", "gh-pages"], capture_output=True, text=True, check=False)
        else:
            logging.info("Switching to gh-pages branch")
            subprocess.run(["git", "-C", export_dir, "checkout", "gh-pages"], capture_output=True, text=True, check=False)
        
        # Add all changes
        logging.info("Adding all changes to git")
        result = subprocess.run(["git", "-C", export_dir, "add", "-A"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logging.error(f"Git add failed with code {result.returncode}: {result.stderr}")
            return False
            
        # Check if there are changes to commit
        status_result = subprocess.run(["git", "-C", export_dir, "status", "--porcelain"], capture_output=True, text=True, check=False)
        if not status_result.stdout.strip():
            logging.info("No changes to commit")
            
            # Even though there are no changes, let's check if our local branch is behind remote
            # This could happen if someone else pushed changes
            logging.info("Checking if local branch is behind remote")
            git_token = os.environ.get("GITHUB_TOKEN")
            git_username = os.environ.get("GITHUB_USERNAME")
            
            if git_token and git_username and git_repo:
                # Create authenticated repo URL
                if git_repo.startswith("https://"):
                    auth_repo = f"https://{git_username}:{git_token}@{git_repo[8:]}"
                else:
                    auth_repo = git_repo
                
                # Fetch to see if we're behind
                fetch_result = subprocess.run(["git", "-C", export_dir, "fetch", "origin", "gh-pages"], 
                                            capture_output=True, text=True, check=False)
                
                # Check if we're behind
                behind_check = subprocess.run(["git", "-C", export_dir, "rev-list", "--count", "HEAD..origin/gh-pages"], 
                                            capture_output=True, text=True, check=False)
                
                if behind_check.stdout.strip() and int(behind_check.stdout.strip()) > 0:
                    logging.info(f"Local branch is behind remote by {behind_check.stdout.strip()} commits")
                    logging.info("Pulling latest changes")
                    pull_result = subprocess.run(["git", "-C", export_dir, "pull", "--no-edit", auth_repo, "gh-pages"], 
                                              capture_output=True, text=True, check=False)
                    if pull_result.returncode != 0:
                        logging.warning(f"Git pull had issues: {pull_result.stderr}")
                else:
                    logging.info("Local branch is up to date with remote")
            
            return True  # Not a failure, just no changes
            
        # Commit changes
        commit_message = f"Auto update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info(f"Committing changes with message: {commit_message}")
        result = subprocess.run(["git", "-C", export_dir, "commit", "-m", commit_message], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logging.error(f"Git commit failed with code {result.returncode}: {result.stderr}")
            return False
            
        # Push changes
        # Set up credentials if available
        git_token = os.environ.get("GITHUB_TOKEN")
        git_username = os.environ.get("GITHUB_USERNAME")
        git_repo = os.environ.get("GITHUB_REPO")
        
        if git_token and git_username and git_repo:
            # Extract repo name without https:// prefix
            if git_repo.startswith("https://"):
                auth_repo = f"https://{git_username}:{git_token}@{git_repo[8:]}"
            else:
                auth_repo = git_repo
                
            # Pull latest changes from remote to avoid merge conflicts
            logging.info("Pulling latest changes from remote repository")
            try:
                pull_result = subprocess.run(["git", "-C", export_dir, "pull", "--no-edit", auth_repo, "gh-pages"], 
                                          capture_output=True, text=True, check=False)
                if pull_result.returncode != 0:
                    logging.warning(f"Git pull had issues: {pull_result.stderr}")
                    # Try to resolve conflicts automatically by favoring ours
                    logging.info("Attempting to resolve conflicts automatically")
                    subprocess.run(["git", "-C", export_dir, "checkout", "--ours", "."], 
                                  capture_output=True, text=True, check=False)
                    subprocess.run(["git", "-C", export_dir, "add", "."], 
                                  capture_output=True, text=True, check=False)
                    subprocess.run(["git", "-C", export_dir, "commit", "-m", "Auto-resolving conflicts"], 
                                  capture_output=True, text=True, check=False)
            except Exception as e:
                logging.warning(f"Error during git pull: {e}")
                
            # Push with authentication if available
            logging.info(f"Pushing to GitHub with authentication (user: {git_username})")
            result = subprocess.run(["git", "-C", export_dir, "push", "--set-upstream", auth_repo, "gh-pages"], capture_output=True, text=True, check=False)
        else:
            # Push without authentication
            logging.info("Pushing to GitHub without authentication")
            result = subprocess.run(["git", "-C", export_dir, "push", "--set-upstream", "origin", "gh-pages"], capture_output=True, text=True, check=False)
            
        if result.returncode != 0:
            logging.error(f"Git push failed with code {result.returncode}: {result.stderr}")
            logging.error(f"Git push error: {result.stderr}")
            return False
            
        logging.info("Successfully pushed changes to GitHub")
        return True
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False
