import os
import logging
from datetime import datetime
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run_command(cmd):
    """Run a shell command and return the output"""
    try:
        logging.info(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, check=True, 
                               capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed: {e}")
        logging.error(f"Error output: {e.stderr}")
        return None

def main():
    """Update the website directly without extraction"""
    try:
        # Change to the correct directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Skip extraction and just update the website
        logging.info("Exporting leaderboard...")
        run_command("python export_leaderboard.py")
        
        # Publish to GitHub
        logging.info("Publishing to GitHub...")
        result = run_command("python server_publish_to_github.py")
        
        # Force push from the website_export directory if needed
        if "Updates were rejected" in str(result):
            logging.info("Push rejected, attempting force push...")
            os.chdir("website_export")
            run_command("git add .")
            run_command(f'git commit -m "Update website with latest scores - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')
            run_command("git push -f origin gh-pages")
        
        logging.info("Website update complete!")
        
    except Exception as e:
        logging.error(f"Error: {e}")

if __name__ == "__main__":
    main()
