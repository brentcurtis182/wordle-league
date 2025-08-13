#!/usr/bin/env python
# Repair the git repository and push changes

import os
import sys
import shutil
import tempfile
import subprocess
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

def main():
    try:
        # Step 1: Create temporary directory
        temp_dir = tempfile.mkdtemp()
        logging.info(f"Created temporary directory: {temp_dir}")
        
        # Step 2: Export current website files
        logging.info("Running export_leaderboard.py to generate website files...")
        result = subprocess.run(["python", "export_leaderboard.py"], 
                              capture_output=True, text=True, check=False)
        if result.returncode != 0:
            logging.error(f"Export failed: {result.stderr}")
            return False
        logging.info("Website files exported successfully")
        
        # Step 3: Back up current website files (except .git)
        export_dir = os.path.join(os.getcwd(), "website_export")
        logging.info(f"Backing up website files from {export_dir} to {temp_dir}")
        for item in os.listdir(export_dir):
            if item != '.git':
                src = os.path.join(export_dir, item)
                dst = os.path.join(temp_dir, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # Step 4: Clone fresh repository
        clone_dir = os.path.join(tempfile.gettempdir(), f"wordle_league_clone_{int(datetime.now().timestamp())}")
        os.makedirs(clone_dir, exist_ok=True)
        logging.info(f"Cloning fresh repository to {clone_dir}")
        
        # Use GitHub token for authentication if available
        github_token = os.environ.get("GITHUB_TOKEN")
        github_username = os.environ.get("GITHUB_USERNAME")
        
        if github_token and github_username:
            auth_url = f"https://{github_username}:{github_token}@github.com/brentcurtis182/wordle-league.git"
        else:
            auth_url = "https://github.com/brentcurtis182/wordle-league.git"
        
        # Clone repository with gh-pages branch
        clone_result = subprocess.run(
            ["git", "clone", "-b", "gh-pages", auth_url, clone_dir],
            capture_output=True, text=True, check=False
        )
        
        if clone_result.returncode != 0:
            logging.error(f"Clone failed: {clone_result.stderr}")
            # Try cloning without specifying branch
            clone_result = subprocess.run(
                ["git", "clone", auth_url, clone_dir],
                capture_output=True, text=True, check=False
            )
            if clone_result.returncode != 0:
                logging.error(f"Second clone attempt failed: {clone_result.stderr}")
                return False
            
            # Create gh-pages branch
            os.chdir(clone_dir)
            subprocess.run(["git", "checkout", "--orphan", "gh-pages"])
            subprocess.run(["git", "rm", "-rf", "."])
            os.chdir(os.path.dirname(export_dir))
        
        # Step 5: Copy backed up website files to clone directory
        logging.info("Copying website files to cloned repository")
        for item in os.listdir(temp_dir):
            src = os.path.join(temp_dir, item)
            dst = os.path.join(clone_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
        
        # Step 6: Add cache busting
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        timestamp_file = os.path.join(clone_dir, f"timestamp_{timestamp}.txt")
        with open(timestamp_file, "w") as f:
            f.write(f"Cache busting timestamp: {datetime.now().isoformat()}")
        
        # Create .nojekyll file
        with open(os.path.join(clone_dir, ".nojekyll"), "w") as f:
            pass
        
        # Add meta tags to index.html
        index_file = os.path.join(clone_dir, "index.html")
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            if "<meta http-equiv=\"Cache-Control\"" not in content:
                cache_tags = f"""
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <meta name="generated" content="{datetime.now().isoformat()}">
</head>"""
                content = content.replace("</head>", cache_tags)
                
                with open(index_file, "w", encoding="utf-8") as f:
                    f.write(content)
        
        # Step 7: Commit and push changes
        os.chdir(clone_dir)
        logging.info("Configuring git")
        subprocess.run(["git", "config", "user.name", "brentcurtis182"])
        subprocess.run(["git", "config", "user.email", "wordle.league.bot@example.com"])
        
        logging.info("Adding all files to git")
        subprocess.run(["git", "add", "-A"])
        
        commit_message = f"Fix Joanna's pattern and update website - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logging.info(f"Committing: {commit_message}")
        subprocess.run(["git", "commit", "-m", commit_message])
        
        logging.info("Pushing to GitHub")
        if github_token and github_username:
            push_result = subprocess.run(
                ["git", "push", "-f", auth_url, "gh-pages"],
                capture_output=True, text=True, check=False
            )
        else:
            push_result = subprocess.run(
                ["git", "push", "-f", "origin", "gh-pages"],
                capture_output=True, text=True, check=False
            )
        
        if push_result.returncode != 0:
            logging.error(f"Push failed: {push_result.stderr}")
            return False
        
        logging.info("Successfully pushed changes to GitHub")
        
        # Step 8: Replace the old export directory with the new repository
        os.chdir(os.path.dirname(export_dir))
        logging.info("Replacing old export directory with new repository")
        
        # Try to remove old export directory
        try:
            shutil.rmtree(export_dir)
        except Exception as e:
            logging.warning(f"Could not remove old export directory: {e}")
            # Try to rename it
            try:
                old_export_backup = f"{export_dir}_backup_{int(datetime.now().timestamp())}"
                shutil.move(export_dir, old_export_backup)
                logging.info(f"Renamed old export directory to {old_export_backup}")
            except Exception as e:
                logging.error(f"Could not rename old export directory: {e}")
                return False
        
        # Copy cloned repository to export directory
        try:
            shutil.copytree(clone_dir, export_dir)
            logging.info("Successfully replaced export directory with new repository")
        except Exception as e:
            logging.error(f"Could not copy new repository to export directory: {e}")
            return False
        
        logging.info("\nProcess completed successfully!")
        logging.info(f"Access the updated website at: https://brentcurtis182.github.io/wordle-league/")
        logging.info("Note: GitHub Pages may take a few minutes to update.")
        
        return True
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return False
    finally:
        # Change back to original directory
        os.chdir(os.path.dirname(export_dir))

if __name__ == "__main__":
    main()
