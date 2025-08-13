import os
import sqlite3
import datetime
import subprocess
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("customize_leagues.log"),
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
        
        # Special case handling for league PAL
        if league_id == 3 and "Pants" not in players:
            players.append("Pants")  # Always include Pants in PAL league
        
        logger.info(f"Found {len(players)} players for league {league_id}: {', '.join(players)}")
        return players
    except Exception as e:
        logger.error(f"Error getting players for league {league_id}: {e}")
        return []

def customize_league_page(html_path, league_name, players):
    """Customize HTML page for specific league"""
    try:
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Update the title
        title = soup.title
        if title:
            title.string = f"Wordle {league_name} Leaderboard"
        
        # Update the H1 heading
        h1 = soup.find('h1')
        if h1:
            h1.string = f"Wordle {league_name} Leaderboard"
        
        # Update any instances of {league_name}
        html_content = str(soup).replace("{league_name}", league_name)
        
        # Re-parse with updated content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the latest scores table body
        latest_tbody = soup.select_one('.section:nth-of-type(1) tbody')
        if latest_tbody:
            # Clear existing rows
            latest_tbody.clear()
            
            # Add rows for each player with "No Score"
            for player in players:
                tr = soup.new_tag('tr')
                
                td_name = soup.new_tag('td')
                td_name.string = player
                tr.append(td_name)
                
                td_score = soup.new_tag('td')
                td_score['class'] = 'no-score'
                td_score.string = "No Score"
                tr.append(td_score)
                
                latest_tbody.append(tr)
        
        # Find the weekly stats table body
        weekly_tbody = soup.select_one('.section:nth-of-type(2) tbody')
        if weekly_tbody:
            # Clear existing rows
            weekly_tbody.clear()
            
            # Add rows for each player with no weekly scores
            for player in players:
                tr = soup.new_tag('tr')
                
                td_name = soup.new_tag('td')
                td_name.string = player
                tr.append(td_name)
                
                td_weekly = soup.new_tag('td')
                td_weekly.string = "-"
                tr.append(td_weekly)
                
                td_used = soup.new_tag('td')
                td_used.string = "0"
                tr.append(td_used)
                
                weekly_tbody.append(tr)
        
        # Find the all-time stats table body
        alltime_tbody = soup.select_one('.section:nth-of-type(3) tbody')
        if alltime_tbody:
            # Clear existing rows
            alltime_tbody.clear()
            
            # Add rows for each player with no all-time stats
            for player in players:
                tr = soup.new_tag('tr')
                
                td_name = soup.new_tag('td')
                td_name.string = player
                tr.append(td_name)
                
                td_games = soup.new_tag('td')
                td_games.string = "-"
                tr.append(td_games)
                
                td_avg = soup.new_tag('td')
                td_avg.string = "-"
                tr.append(td_avg)
                
                td_failed = soup.new_tag('td')
                td_failed.string = ""
                tr.append(td_failed)
                
                alltime_tbody.append(tr)
        
        # Update the date
        p_refresh = soup.select_one('.refresh-note')
        if p_refresh:
            p_refresh.string = f"Updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Fresh Start)"
        
        # Write the updated HTML back to the file
        with open(html_path, 'w', encoding='utf-8') as file:
            file.write(str(soup))
        
        logger.info(f"Customized {html_path} for {league_name} with {len(players)} players")
        return True
    except Exception as e:
        logger.error(f"Error customizing {html_path} for {league_name}: {e}")
        return False

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Change to the website_export directory
        os.chdir("website_export")
        
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_message = f"Customize leagues with proper player lists - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
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

def main():
    # Install BeautifulSoup if not already installed
    try:
        import bs4
    except ImportError:
        subprocess.run(["pip", "install", "beautifulsoup4"], check=True)
        logger.info("Installed BeautifulSoup4")
    
    # Base export directory
    export_dir = "website_export"
    
    # League configurations
    leagues = [
        {"id": 1, "name": "Warriorz", "path": ""},  # Root league
        {"id": 2, "name": "Gang", "path": "gang"},
        {"id": 3, "name": "PAL", "path": "pal"}
    ]
    
    # Process each league
    for league in leagues:
        league_id = league["id"]
        league_name = league["name"]
        league_path = league["path"]
        
        logger.info(f"Processing league: {league_name} (ID: {league_id})")
        
        # Get players for this league
        players = get_players_for_league(league_id)
        
        if not players:
            logger.warning(f"No players found for league {league_name}, using default players")
            if league_id == 1:
                players = ["Brent", "Evan", "Joanna", "Malia", "Nanna"]
            elif league_id == 2:
                players = ["Brent", "Ana", "Kaylie", "Joanna", "Keith", "Rochelle", "Will", "Mylene"]
            elif league_id == 3:
                players = ["Vox", "Fuzwuz", "Pants", "Starslider"]
        
        # Determine the path to the index.html file
        if league_path:
            index_path = os.path.join(export_dir, league_path, "index.html")
        else:
            index_path = os.path.join(export_dir, "index.html")
        
        # Customize the index page
        if os.path.exists(index_path):
            customize_league_page(index_path, league_name, players)
        else:
            logger.error(f"Index file not found at {index_path}")
    
    # Push changes to GitHub
    logger.info("Pushing changes to GitHub...")
    success = push_to_github()
    
    if success:
        logger.info("✅ All leagues have been customized with proper player lists!")
    else:
        logger.error("❌ There was an issue pushing changes to GitHub")

if __name__ == "__main__":
    main()
