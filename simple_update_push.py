import os
import time
import logging
import subprocess
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_update_push.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

def get_todays_wordle_number():
    """Get today's Wordle number"""
    # Hardcoded for July 26, 2025
    return 1498

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
                logging.warning(f"Today's Wordle file exists but was not recently updated")
        else:
            logging.warning(f"Today's Wordle file does not exist: {today_file}")
        
        return True
    else:
        logging.error(f"Website update failed with code {result.returncode}")
        logging.error(f"STDOUT: {result.stdout}")
        logging.error(f"STDERR: {result.stderr}")
        return False

def push_to_github():
    """Push website changes to GitHub"""
    logging.info("Pushing changes to GitHub")
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Check if git is initialized
        git_dir = os.path.join(export_dir, ".git")
        if not os.path.exists(git_dir):
            logging.info("Initializing git repository")
            subprocess.run(["git", "init"], cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Configure git user
        github_username = os.environ.get("GITHUB_USERNAME")
        github_email = os.environ.get("GITHUB_EMAIL")
        
        if github_username:
            subprocess.run(["git", "config", "user.name", github_username], cwd=export_dir, check=True, capture_output=True, text=True)
            logging.info(f"Set git user.name to {github_username}")
        else:
            logging.warning("GITHUB_USERNAME not set, using default")
        
        if github_email:
            subprocess.run(["git", "config", "user.email", github_email], cwd=export_dir, check=True, capture_output=True, text=True)
            logging.info(f"Set git user.email to {github_email}")
        else:
            logging.warning("GITHUB_EMAIL not set, using default")
        
        # Set up remote
        github_repo = os.environ.get("GITHUB_REPO")
        github_token = os.environ.get("GITHUB_TOKEN")
        
        if github_username and github_token and github_repo:
            auth_repo = f"https://{github_username}:{github_token}@github.com/{github_username}/{github_repo}.git"
            
            # Check if remote exists
            remote_result = subprocess.run(["git", "remote", "-v"], cwd=export_dir, capture_output=True, text=True)
            if "origin" not in remote_result.stdout:
                logging.info("Adding git remote")
                subprocess.run(["git", "remote", "add", "origin", auth_repo], cwd=export_dir, check=True, capture_output=True, text=True)
            else:
                logging.info("Updating git remote")
                subprocess.run(["git", "remote", "set-url", "origin", auth_repo], cwd=export_dir, check=True, capture_output=True, text=True)
        else:
            logging.warning("GitHub credentials not set, using default remote if available")
        
        # Switch to gh-pages branch
        branch_result = subprocess.run(["git", "branch", "--show-current"], cwd=export_dir, capture_output=True, text=True)
        current_branch = branch_result.stdout.strip()
        
        if current_branch != "gh-pages":
            logging.info(f"Current branch is {current_branch}, switching to gh-pages")
            
            # Check if gh-pages branch exists
            branch_list = subprocess.run(["git", "branch"], cwd=export_dir, capture_output=True, text=True)
            
            if "gh-pages" in branch_list.stdout:
                # Branch exists, switch to it
                subprocess.run(["git", "checkout", "gh-pages"], cwd=export_dir, check=True, capture_output=True, text=True)
            else:
                # Create and switch to gh-pages branch
                subprocess.run(["git", "checkout", "-b", "gh-pages"], cwd=export_dir, check=True, capture_output=True, text=True)
            
            logging.info("Switched to gh-pages branch")
        else:
            logging.info("Already on gh-pages branch")
        
        # Add all changes
        logging.info("Adding all changes")
        add_result = subprocess.run(["git", "add", "-A"], cwd=export_dir, capture_output=True, text=True)
        logging.info(f"Git add output: {add_result.stdout}")
        if add_result.stderr:
            logging.warning(f"Git add stderr: {add_result.stderr}")
        
        # Check if there are changes to commit
        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=export_dir, capture_output=True, text=True)
        
        if status_result.stdout.strip():
            logging.info(f"Changes detected: {status_result.stdout}")
            
            # Commit changes
            commit_message = f"Update website: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logging.info(f"Committing changes with message: {commit_message}")
            commit_result = subprocess.run(["git", "commit", "-m", commit_message], cwd=export_dir, capture_output=True, text=True)
            logging.info(f"Git commit output: {commit_result.stdout}")
            if commit_result.stderr:
                logging.warning(f"Git commit stderr: {commit_result.stderr}")
            
            # Pull latest changes from remote to avoid merge conflicts
            if github_username and github_token and github_repo:
                logging.info("Pulling latest changes from remote")
                pull_result = subprocess.run(["git", "pull", "--no-edit", auth_repo, "gh-pages"], cwd=export_dir, capture_output=True, text=True)
                logging.info(f"Git pull output: {pull_result.stdout}")
                
                if pull_result.returncode != 0:
                    logging.warning(f"Git pull stderr: {pull_result.stderr}")
                    logging.info("Attempting to resolve conflicts automatically by favoring our changes")
                    
                    # Try to resolve conflicts automatically by favoring ours
                    subprocess.run(["git", "checkout", "--ours", "."], cwd=export_dir, capture_output=True, text=True)
                    subprocess.run(["git", "add", "."], cwd=export_dir, capture_output=True, text=True)
                    subprocess.run(["git", "commit", "-m", "Auto-resolving conflicts"], cwd=export_dir, capture_output=True, text=True)
            
            # Push changes
            logging.info("Pushing changes to remote")
            if github_username and github_token and github_repo:
                push_result = subprocess.run(["git", "push", "--set-upstream", auth_repo, "gh-pages"], cwd=export_dir, capture_output=True, text=True)
            else:
                push_result = subprocess.run(["git", "push", "--set-upstream", "origin", "gh-pages"], cwd=export_dir, capture_output=True, text=True)
            
            logging.info(f"Git push output: {push_result.stdout}")
            if push_result.stderr:
                logging.warning(f"Git push stderr: {push_result.stderr}")
            
            if push_result.returncode == 0:
                logging.info("Successfully pushed changes to GitHub")
                return True
            else:
                logging.error("Failed to push changes to GitHub")
                return False
        else:
            logging.info("No changes to commit")
            
            # Check if we're behind the remote
            if github_username and github_token and github_repo:
                logging.info("Checking if we're behind the remote")
                fetch_result = subprocess.run(["git", "fetch", auth_repo], cwd=export_dir, capture_output=True, text=True)
                status_result = subprocess.run(["git", "status", "-uno"], cwd=export_dir, capture_output=True, text=True)
                
                if "Your branch is behind" in status_result.stdout:
                    logging.info("Local branch is behind remote, pulling latest changes")
                    pull_result = subprocess.run(["git", "pull", "--no-edit", auth_repo, "gh-pages"], cwd=export_dir, capture_output=True, text=True)
                    logging.info(f"Git pull output: {pull_result.stdout}")
                    if pull_result.stderr:
                        logging.warning(f"Git pull stderr: {pull_result.stderr}")
            
            return True
    
    except subprocess.CalledProcessError as e:
        logging.error(f"Git error: {e}")
        if hasattr(e, 'output'):
            logging.error(f"Output: {e.output}")
        if hasattr(e, 'stderr'):
            logging.error(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Error pushing to GitHub: {e}")
        return False

def main():
    logging.info("Starting website update and push")
    
    # Step 1: Update website
    website_success = update_website()
    
    if website_success:
        logging.info("Website updated successfully, now pushing to GitHub")
        
        # Step 2: Push to GitHub
        push_success = push_to_github()
        
        if push_success:
            logging.info("GitHub push completed successfully")
        else:
            logging.error("GitHub push failed")
    else:
        logging.error("Website update failed")

if __name__ == "__main__":
    main()
