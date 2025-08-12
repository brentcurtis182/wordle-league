import os
import datetime
import subprocess
import logging
import sqlite3
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("restore_styling.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# League configurations
LEAGUES = [
    {"id": 1, "name": "Warriorz", "path": "", "title": "Wordle Warriorz Leaderboard"},
    {"id": 2, "name": "Gang", "path": "gang", "title": "Wordle Gang Leaderboard"},
    {"id": 3, "name": "PAL", "path": "pal", "title": "Wordle PAL Leaderboard"}
]

def ensure_directory(directory):
    """Ensure directory exists, create if it doesn't"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")
    return directory

def get_players_for_league(league_id):
    """Get players for a specific league from database"""
    try:
        conn = sqlite3.connect("wordle_league.db")
        cursor = conn.cursor()
        
        # Query players for this league
        cursor.execute(
            "SELECT name FROM players WHERE league_id = ? ORDER BY name", 
            (league_id,)
        )
        players = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Special case handling for league PAL
        if league_id == 3 and "Pants" not in players:
            players.append("Pants")
            logger.info("Added 'Pants' to PAL league players")
        
        logger.info(f"Found {len(players)} players for league {league_id}: {', '.join(players)}")
        return players
    except Exception as e:
        logger.error(f"Error getting players for league {league_id}: {e}")
        # Fall back to hardcoded values if database fails
        if league_id == 1:  # Warriorz
            players = ["Brent", "Evan", "Joanna", "Malia", "Nanna"]
        elif league_id == 2:  # Gang
            players = ["Ana", "Brent", "Joanna", "Kaylie", "Keith", "Mylene", "Rochelle", "Will"]
        elif league_id == 3:  # PAL
            players = ["Fuzwuz", "Pants", "Starslider", "Vox"]
        logger.info(f"Using fallback player list for league {league_id}: {', '.join(players)}")
        return players

def get_original_template():
    """Get original working template from the repository"""
    try:
        # Use the known good commit to get the template
        result = subprocess.run(
            ["git", "show", "1a4c91f:index.html"], 
            cwd="website_export",
            capture_output=True, 
            text=True, 
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get original template: {e}")
        # Fallback to reading from file if it exists
        if os.path.exists("website_export/original_working.html"):
            with open("website_export/original_working.html", "r", encoding="utf-8") as f:
                return f.read()
        else:
            logger.error("Cannot find original template")
            return None

def customize_template_for_league(template_html, league_config, players):
    """Customize the template for a specific league while preserving structure"""
    if not template_html:
        logger.error("No template provided")
        return None
    
    league_id = league_config["id"]
    league_name = league_config["name"]
    league_title = league_config["title"]
    
    # Parse the template
    soup = BeautifulSoup(template_html, "html.parser")
    
    # Update the title
    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = league_title
    
    # Update the h1 title
    h1_title = soup.find("h1", class_="title")
    if h1_title:
        h1_title.string = league_title
    
    # Current date for refresh note
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Find the refresh note and update it
    refresh_note = soup.find("p", class_="refresh-note")
    if refresh_note:
        refresh_note.string = f"Last updated: {today}"
    
    # Handle latest scores section
    latest_scores = soup.find("div", {"id": "latest"})
    if latest_scores:
        # Find the scores table
        latest_table = latest_scores.find("table", class_="scores-table")
        if latest_table and latest_table.find("tbody"):
            # Clear existing rows
            tbody = latest_table.find("tbody")
            tbody.clear()
            
            # Add rows for each player with "No Score"
            for player in players:
                tr = soup.new_tag("tr")
                
                # Player name cell
                td_name = soup.new_tag("td")
                td_name.string = player
                tr.append(td_name)
                
                # Score cell with "No Score" message
                td_score = soup.new_tag("td")
                td_score["class"] = "no-score"
                td_score.string = "No Score"
                tr.append(td_score)
                
                tbody.append(tr)
    
    # Handle weekly stats section
    weekly_stats = soup.find("div", {"id": "weekly"})
    if weekly_stats:
        # Find the weekly stats table
        weekly_table = weekly_stats.find("table", class_="scores-table")
        if weekly_table and weekly_table.find("tbody"):
            # Clear existing rows
            tbody = weekly_table.find("tbody")
            tbody.clear()
            
            # Add rows for each player with empty stats
            for player in players:
                tr = soup.new_tag("tr")
                
                # Player name cell
                td_name = soup.new_tag("td")
                td_name.string = player
                tr.append(td_name)
                
                # Weekly score cell (empty)
                td_weekly = soup.new_tag("td")
                td_weekly.string = "-"
                tr.append(td_weekly)
                
                # Used scores cell
                td_used = soup.new_tag("td")
                td_used.string = "0"
                tr.append(td_used)
                
                tbody.append(tr)
    
    # Handle all-time stats section
    stats = soup.find("div", {"id": "stats"})
    if stats:
        # Find the stats table
        stats_table = stats.find("table", class_="scores-table")
        if stats_table and stats_table.find("tbody"):
            # Clear existing rows
            tbody = stats_table.find("tbody")
            tbody.clear()
            
            # Add rows for each player with empty stats
            for player in players:
                tr = soup.new_tag("tr")
                
                # Player name cell
                td_name = soup.new_tag("td")
                td_name.string = player
                tr.append(td_name)
                
                # Games played cell
                td_games = soup.new_tag("td")
                td_games.string = "-"
                tr.append(td_games)
                
                # Average cell
                td_avg = soup.new_tag("td")
                td_avg.string = "-"
                tr.append(td_avg)
                
                # Failed attempts cell (empty)
                td_failed = soup.new_tag("td")
                td_failed["class"] = "failed-attempts"
                td_failed.string = ""
                tr.append(td_failed)
                
                tbody.append(tr)
    
    # Update footer if it exists
    footer_text = soup.find("div", {"class": "container"}, recursive=True)
    if footer_text and footer_text.find("p"):
        year = datetime.datetime.now().year
        footer_text.find("p").string = f"© {year} Wordle {league_name}. All rights reserved."
    
    return str(soup)

def process_league(league_config, template_html, base_path):
    """Process a single league"""
    league_id = league_config["id"]
    league_name = league_config["name"]
    league_path = league_config["path"]
    
    # Create full directory path
    league_dir = os.path.join(base_path, league_path)
    ensure_directory(league_dir)
    
    # Get players for this league
    players = get_players_for_league(league_id)
    
    # Create the customized HTML
    html_content = customize_template_for_league(template_html, league_config, players)
    
    if html_content:
        # Write the index.html file
        index_path = os.path.join(league_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"Created {index_path} for {league_name} with {len(players)} players")
        
        # Copy styles.css to the directory if it's not the root
        if league_path:
            src_css = os.path.join(base_path, "styles.css")
            dst_css = os.path.join(league_dir, "styles.css")
            
            # Make sure source CSS exists
            if os.path.exists(src_css):
                with open(src_css, "r", encoding="utf-8") as src:
                    css_content = src.read()
                
                with open(dst_css, "w", encoding="utf-8") as dst:
                    dst.write(css_content)
                    
                logger.info(f"Copied styles.css to {league_dir}")
            else:
                logger.warning(f"Source CSS file not found: {src_css}")
        
        # Create daily directory
        daily_dir = os.path.join(league_dir, "daily")
        ensure_directory(daily_dir)
        
        return True
    else:
        logger.error(f"Failed to create HTML content for {league_name}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Change to the website_export directory
        os.chdir("website_export")
        
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_message = f"Restore styling while keeping correct player lists - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Pull with rebase to avoid conflicts
        subprocess.run(["git", "pull", "--rebase", "origin", "gh-pages"], check=True)
        
        # Force push to GitHub to ensure we overwrite any cached content
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], check=True)
        
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

def main():
    # Get the original template
    template_html = get_original_template()
    
    if not template_html:
        logger.error("Failed to get original template. Aborting.")
        return
    
    # Base path for website files
    base_path = "website_export"
    
    # Process each league
    success = True
    for league in LEAGUES:
        logger.info(f"Processing league: {league['name']} (ID: {league['id']})")
        if not process_league(league, template_html, base_path):
            success = False
            logger.error(f"Failed to process league: {league['name']}")
    
    if success:
        # Push changes to GitHub
        push_to_github()
        logger.info("✅ All leagues have been successfully restored with proper styling and player lists!")
    else:
        logger.error("❌ Failed to restore one or more leagues")

if __name__ == "__main__":
    main()
