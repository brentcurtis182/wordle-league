import os
import datetime
import subprocess
import logging
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("rebuild_league_sites.log"),
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
        
        logger.info(f"Found {len(players)} players for league {league_id}: {', '.join(players)}")
        return players
    except Exception as e:
        logger.error(f"Error getting players for league {league_id}: {e}")
        # Fall back to hardcoded values if database fails
        if league_id == 1:
            return ["Brent", "Evan", "Joanna", "Malia", "Nanna"]
        elif league_id == 2:
            return ["Ana", "Brent", "Joanna", "Kaylie", "Keith", "Mylene", "Rochelle", "Will"]
        elif league_id == 3:
            return ["Fuzwuz", "Pants", "Starslider", "Vox"]
        return []

def create_league_site(league_config, base_path):
    """Create complete league site structure"""
    league_id = league_config["id"]
    league_name = league_config["name"]
    league_path = league_config["path"]
    league_dir = os.path.join(base_path, league_path)
    
    # Ensure the directory exists
    ensure_directory(league_dir)
    
    # Get players for this league
    players = get_players_for_league(league_id)
    if not players:
        logger.warning(f"No players found for league {league_id}, using backup list")
        if league_id == 3:  # PAL
            players = ["Fuzwuz", "Pants", "Starslider", "Vox"]
    
    # Create index.html with all sections
    index_path = os.path.join(league_dir, "index.html")
    create_index_page(index_path, league_name, players)
    
    # Ensure a CSS file exists
    css_path = os.path.join(league_dir, "styles.css")
    copy_css_file(os.path.join(base_path, "styles.css"), css_path)
    
    # Create daily directory and placeholder
    daily_dir = os.path.join(league_dir, "daily")
    ensure_directory(daily_dir)
    
    return league_dir

def create_index_page(output_path, league_name, players):
    """Generate a complete index.html file for a league"""
    today = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    title = f"Wordle {league_name} Leaderboard"
    
    # Build the latest scores section
    latest_rows = ""
    for player in players:
        latest_rows += f'''
        <tr>
            <td>{player}</td>
            <td class="no-score">No Score</td>
        </tr>'''
    
    # Build the weekly stats section
    weekly_rows = ""
    for player in players:
        weekly_rows += f'''
        <tr>
            <td>{player}</td>
            <td>-</td>
            <td>0</td>
        </tr>'''
    
    # Build the all-time stats section
    alltime_rows = ""
    for player in players:
        alltime_rows += f'''
        <tr>
            <td>{player}</td>
            <td>-</td>
            <td>-</td>
            <td></td>
        </tr>'''
    
    # Create the full HTML content
    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <link rel="stylesheet" href="styles.css">
    <style>
        /* Emoji pattern styles */
        .score-display {{
            display: flex;
            align-items: center;
        }}
        
        .emoji-pattern {{
            margin-left: 15px;
            font-size: 12px;
        }}
        
        .emoji-row {{
            margin-bottom: 2px;
        }}
        
        /* Weekly stats highlight */
        .highlight {{
            background-color: rgba(106, 170, 100, 0.2);
        }}
        
        /* Failed attempts styling */
        .failed-attempts {{
            background-color: rgba(220, 53, 69, 0.2);
            color: #dc3545;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
        }}
        
        /* When failed attempts is 0, make it less prominent */
        td.failed-attempts:empty {{
            background-color: transparent;
            color: #d7dadc;
            font-weight: normal;
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1 class="title">{title}</h1>
        </div>
    </header>
    <div class="container">
        <div class="section">
            <h2>Latest Scores</h2>
            <p class="refresh-note">Updated: {today} (Fresh Start)</p>
            <table class="scores-table">
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Today's Score</th>
                    </tr>
                </thead>
                <tbody>{latest_rows}
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Weekly Stats</h2>
            <p>Week of Monday, August 1, 2025</p>
            <table class="scores-table">
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Weekly Score</th>
                        <th>Used Scores</th>
                    </tr>
                </thead>
                <tbody>{weekly_rows}
                </tbody>
            </table>
            <p><em>* Failed attempts (X/6) do not count towards your "Used Scores"</em></p>
        </div>
        
        <div class="section">
            <h2>All-Time Stats</h2>
            <table class="scores-table">
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Games Played</th>
                        <th>Average</th>
                        <th>Failed Attempts</th>
                    </tr>
                </thead>
                <tbody>{alltime_rows}
                </tbody>
            </table>
            <p><em>* Failed attempts (X/6) count as 7 in the average calculation</em></p>
        </div>
    </div>
    <footer>
        <div class="container">
            <p>&copy; 2025 {league_name}. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>'''
    
    # Write the file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"Created {output_path} for {league_name} with {len(players)} players")

def copy_css_file(src_path, dst_path):
    """Copy the CSS file to the target location"""
    # Common dark theme CSS for Wordle
    css_content = '''
/* General styles */
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #121213;
    color: #d7dadc;
}
.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 10px;
}
header {
    background-color: #1a1a1b;
    padding: 10px 0;
    margin-bottom: 10px;
}
.title {
    margin: 0 auto;
    color: #6aaa64;
    font-size: 24px;
    text-align: center;
}
.subtitle {
    margin: 5px 0 0;
    color: #d7dadc;
    font-size: 0.9em;
}

/* Score card styles */
.score-card {
    background-color: #1a1a1b;
    border-radius: 5px;
    padding: 10px;
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.player-info {
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.player-name {
    font-weight: bold;
    font-size: 1.1em;
    margin-bottom: 4px;
}
.player-score {
    font-size: 1.1em;
    font-weight: bold;
    display: inline-block;
}
.player-score span {
    padding: 2px 8px;
    border-radius: 3px;
    display: inline-block;
}
.score-display {
    font-size: 1.2em;
    font-weight: bold;
    padding: 5px 10px;
    border-radius: 3px;
    display: flex;
    align-items: center;
}
.score-1 {
    background-color: #6aaa64;
    color: #121213;
}
.score-2 {
    background-color: #6aaa64;
    color: #121213;
}
.score-3 {
    background-color: #6aaa64;
    color: #121213;
}
.score-4 {
    background-color: #c9b458;
    color: #121213;
}
.score-5 {
    background-color: #c9b458;
    color: #121213;
}
.score-6 {
    background-color: #c9b458;
    color: #121213;
}
.score-X {
    background-color: #86888a;
    color: #121213;
}
.score-none {
    background-color: #3a3a3c;
    color: #d7dadc;
}

/* Section styles */
.section {
    background-color: #1a1a1b;
    border-radius: 5px;
    padding: 15px;
    margin-bottom: 20px;
}
.section h2 {
    margin-top: 0;
    color: #6aaa64;
    font-size: 1.2em;
    margin-bottom: 10px;
}
.refresh-note {
    font-size: 0.8em;
    color: #86888a;
    margin-bottom: 15px;
    text-align: center;
}

/* Table styles */
.scores-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 10px;
}
.scores-table th {
    text-align: left;
    padding: 8px;
    border-bottom: 1px solid #3a3a3c;
    color: #86888a;
    font-weight: normal;
}
.scores-table td {
    padding: 8px;
    border-bottom: 1px solid #3a3a3c;
}
.no-score {
    color: #86888a;
    font-style: italic;
}

/* Footer styles */
footer {
    margin-top: 30px;
    padding: 10px 0;
    border-top: 1px solid #3a3a3c;
    font-size: 0.8em;
    color: #86888a;
    text-align: center;
}
'''
    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(css_content)
    logger.info(f"Created CSS file: {dst_path}")

def push_to_github():
    """Push changes to GitHub"""
    try:
        # Change to the website_export directory
        os.chdir("website_export")
        
        # Add all changes
        subprocess.run(["git", "add", "."], check=True)
        
        # Commit changes
        commit_message = f"Complete league site rebuild - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
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
    base_path = "website_export"
    
    # League configurations
    leagues = [
        {"id": 1, "name": "Warriorz", "path": ""},
        {"id": 2, "name": "Gang", "path": "gang"},
        {"id": 3, "name": "PAL", "path": "pal"}
    ]
    
    # Process each league
    for league in leagues:
        logger.info(f"Rebuilding site for league: {league['name']} (ID: {league['id']})")
        create_league_site(league, base_path)
    
    # Push changes to GitHub
    logger.info("Pushing changes to GitHub...")
    push_to_github()
    
    logger.info("Website rebuild complete!")

if __name__ == "__main__":
    main()
