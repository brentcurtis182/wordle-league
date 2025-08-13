import os
import time
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("force_update.log"),
        logging.StreamHandler()
    ]
)

def force_update():
    """Force an update to the website files and push to GitHub"""
    logging.info("Starting force update")
    export_dir = os.path.join(os.getcwd(), "website_export")
    
    if not os.path.exists(export_dir):
        logging.error(f"Export directory does not exist: {export_dir}")
        return False
    
    try:
        # Create or update the timestamp file
        timestamp_file = os.path.join(export_dir, "last_update.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        logging.info("Created timestamp file to force Git to detect changes")
        
        # Also update index.html with a comment to force a change
        index_file = os.path.join(export_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Add or update a timestamp comment at the end of the file
            timestamp_comment = f"<!-- Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -->"
            
            if "<!-- Last updated:" in content:
                # Replace existing timestamp comment
                import re
                content = re.sub(r"<!-- Last updated:.*?-->", timestamp_comment, content)
            else:
                # Add new timestamp comment
                content += "\n" + timestamp_comment
            
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(content)
            
            logging.info("Updated index.html with timestamp comment")
        
        # Configure git
        subprocess.run(["git", "config", "user.name", "brentcurtis182"], cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Make sure we're on the gh-pages branch
        branch_result = subprocess.run(["git", "branch", "--show-current"], cwd=export_dir, capture_output=True, text=True)
        current_branch = branch_result.stdout.strip()
        
        if current_branch != "gh-pages":
            logging.info(f"Current branch is {current_branch}, switching to gh-pages")
            subprocess.run(["git", "checkout", "gh-pages"], cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Pull latest changes first
        logging.info("Pulling latest changes from remote")
        pull_result = subprocess.run(["git", "pull", "origin", "gh-pages"], cwd=export_dir, capture_output=True, text=True)
        logging.info(f"Git pull output: {pull_result.stdout}")
        
        # Add all changes
        logging.info("Adding all changes")
        subprocess.run(["git", "add", "-A"], cwd=export_dir, check=True, capture_output=True, text=True)
        
        # Commit changes
        commit_message = f"Force update website: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info(f"Committing changes with message: {commit_message}")
        commit_result = subprocess.run(["git", "commit", "-m", commit_message], cwd=export_dir, capture_output=True, text=True)
        logging.info(f"Git commit output: {commit_result.stdout}")
        
        # Push changes
        logging.info("Pushing changes to remote")
        push_result = subprocess.run(["git", "push", "origin", "gh-pages"], cwd=export_dir, capture_output=True, text=True)
        logging.info(f"Git push output: {push_result.stdout}")
        
        if push_result.returncode == 0:
            logging.info("Successfully pushed changes to GitHub")
            return True
        else:
            logging.error("Failed to push changes to GitHub")
            logging.warning("Attempting force push as last resort")
            force_push_result = subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=export_dir, capture_output=True, text=True)
            
            if force_push_result.returncode == 0:
                logging.info("Successfully force pushed changes to GitHub")
                return True
            else:
                logging.error("Failed to force push changes to GitHub")
                return False
    
    except Exception as e:
        logging.error(f"Error during force update: {e}")
        return False

if __name__ == "__main__":
    force_update()
