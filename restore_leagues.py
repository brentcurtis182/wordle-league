import os
import shutil
import sqlite3
import datetime
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_leagues.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def ensure_directory(directory):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    return directory

def copy_file(src, dest):
    """Copy a file from source to destination"""
    try:
        shutil.copy2(src, dest)
        logger.info(f"Copied {src} to {dest}")
    except Exception as e:
        logger.error(f"Error copying {src} to {dest}: {e}")

def create_league_index(league_name, output_dir, template_path):
    """Create index.html for a league"""
    try:
        # Read the template
        with open(template_path, 'r') as file:
            template = file.read()
        
        # Replace placeholder with actual league name
        content = template.replace("Wordle Warriorz", f"Wordle {league_name}")
        content = content.replace("{league_name}", league_name)
        
        # Make sure the directory exists
        ensure_directory(output_dir)
        
        # Write the output file
        output_path = os.path.join(output_dir, "index.html")
        with open(output_path, 'w') as file:
            file.write(content)
        
        logger.info(f"Created index for {league_name} at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating index for {league_name}: {e}")
        return False

def create_daily_page(league_name, output_dir, template_path):
    """Create an empty daily score page"""
    try:
        # Read the template
        with open(template_path, 'r') as file:
            template = file.read()
        
        # Replace placeholder with actual league name
        content = template.replace("Wordle Warriorz", f"Wordle {league_name}")
        content = content.replace("{league_name}", league_name)
        
        # Create the daily directory
        daily_dir = os.path.join(output_dir, "daily")
        ensure_directory(daily_dir)
        
        # Current date for filename
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Write the output file
        output_path = os.path.join(daily_dir, f"{today}.html")
        with open(output_path, 'w') as file:
            file.write(content)
        
        logger.info(f"Created daily page for {league_name} at {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error creating daily page for {league_name}: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Change to the website_export directory
        os.chdir("website_export")
        
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_message = f"Restore all leagues with proper styling - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Pull any remote changes with rebase
        subprocess.run(["git", "pull", "--rebase", "origin", "gh-pages"], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push", "origin", "gh-pages"], check=True)
        
        logger.info("Successfully pushed changes to GitHub")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Error pushing to GitHub: {e}")
        return False
    finally:
        # Change back to the root directory
        os.chdir("..")

def get_players_for_league(league_id):
    """Get players for a specific league"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Query players for this league
        cursor.execute(
            "SELECT name FROM players WHERE league_id = ?", 
            (league_id,)
        )
        players = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return players
    except Exception as e:
        logger.error(f"Error getting players for league {league_id}: {e}")
        return []

def main():
    # Base export directory
    export_dir = "website_export"
    
    # League configurations
    leagues = [
        {"id": 1, "name": "Warriorz", "path": ""},  # Root league
        {"id": 2, "name": "Gang", "path": "gang"},
        {"id": 3, "name": "PAL", "path": "pal"}
    ]
    
    # Source templates
    warriorz_index = os.path.join(export_dir, "index.html")
    
    # Check that we have a working template
    if not os.path.exists(warriorz_index):
        logger.error(f"Warriorz index template not found at {warriorz_index}")
        return
    
    # Process each league
    for league in leagues:
        logger.info(f"Processing league: {league['name']}")
        
        # Skip the main Warriorz league at root (already exists)
        if league["id"] != 1:
            # Create league directory
            league_dir = os.path.join(export_dir, league["path"])
            ensure_directory(league_dir)
            
            # Create index.html
            create_league_index(
                league["name"], 
                league_dir,
                warriorz_index
            )
            
            # Create daily directory and sample page
            create_daily_page(
                league["name"],
                league_dir,
                warriorz_index
            )
            
            # Ensure CSS is copied/available
            copy_file(
                os.path.join(export_dir, "styles.css"),
                os.path.join(league_dir, "styles.css")
            )
    
    # Push changes to GitHub
    logger.info("Pushing changes to GitHub...")
    success = push_to_github()
    
    if success:
        logger.info("✅ All leagues have been restored with proper styling!")
    else:
        logger.error("❌ There was an issue pushing changes to GitHub")

if __name__ == "__main__":
    main()
