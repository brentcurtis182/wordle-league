#!/usr/bin/env python3
"""
Refresh Website Script

This script:
1. Exports empty websites for all leagues (Wordle Warriorz, PAL, and Wordle Gang)
2. Maintains player lists but shows empty scores
3. Uses the new unified database schema
"""

import os
import sqlite3
import logging
import shutil
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("refresh_websites.log"),
        logging.StreamHandler()
    ]
)

# Database path
DB_PATH = 'wordle_league.db'

# League IDs
LEAGUES = {
    1: "Wordle Warriorz",
    2: "Wordle Gang",
    3: "PAL"
}

def export_empty_website_for_league(league_id):
    """Export empty website for a specific league"""
    try:
        # Get the league name
        league_name = LEAGUES.get(league_id, f"Unknown League {league_id}")
        
        # Determine export path based on league
        if league_id == 1:  # Wordle Warriorz (main league)
            export_path = "website_export"
        elif league_id == 2:  # Wordle Gang
            export_path = "website_export/gang"
        elif league_id == 3:  # PAL
            export_path = "website_export/pal"
        else:
            export_path = f"website_export/league_{league_id}"
        
        # Create export directory if it doesn't exist
        os.makedirs(export_path, exist_ok=True)
        os.makedirs(f"{export_path}/daily", exist_ok=True)
        
        # Create index.html with empty scores
        with open(f"{export_path}/index.html", "w") as f:
            f.write(f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{league_name} Leaderboard</title>
    <link rel="stylesheet" href="../css/styles.css">
</head>
<body>
    <div class="container">
        <h1>{league_name} Leaderboard</h1>
        <div class="section">
            <h2>Latest Scores</h2>
            <p class="refresh-note">Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} (Fresh Start)</p>
            <table class="scores-table">
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Today's Score</th>
                    </tr>
                </thead>
                <tbody>
""")
            
            # Get players for this league
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name
                FROM players
                WHERE league_id = ?
                ORDER BY name
            """, (league_id,))
            
            players = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Add empty row for each player
            for player in players:
                f.write(f"""
                    <tr>
                        <td>{player}</td>
                        <td class="no-score">No Score</td>
                    </tr>""")
            
            # Close the latest scores table and add weekly and all-time sections with empty data
            f.write("""
                </tbody>
            </table>
        </div>
        
        <div class="section">
            <h2>Weekly Stats</h2>
            <p class="refresh-note">Week of Monday, August 1, 2025</p>
            <table class="scores-table">
                <thead>
                    <tr>
                        <th>Player</th>
                        <th>Weekly Score</th>
                        <th>Used Scores</th>
                    </tr>
                </thead>
                <tbody>
""")
            
            # Add empty weekly stats for each player
            for player in players:
                f.write(f"""
                    <tr>
                        <td>{player}</td>
                        <td>-</td>
                        <td>0</td>
                    </tr>""")
            
            f.write("""
                </tbody>
            </table>
            <p class="note">* Failed attempts (X/6) do not count toward "Used Scores" total</p>
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
                <tbody>
""")
            
            # Add empty all-time stats for each player
            for player in players:
                f.write(f"""
                    <tr>
                        <td>{player}</td>
                        <td>-</td>
                        <td>-</td>
                        <td></td>
                    </tr>""")
            
            f.write("""
                </tbody>
            </table>
            <p class="note">* Failed attempts (X/6) count as 7 in the average calculation</p>
        </div>
        
        <footer>
            <p>© 2025 {league_name}. All rights reserved.</p>
        </footer>
    </div>
</body>
</html>
""")
            
        logging.info(f"Exported empty website for league {league_id} ({league_name}) to {export_path}")
        return True
    except Exception as e:
        logging.error(f"Error exporting empty website for league {league_id}: {e}")
        return False

def main():
    """Main function to refresh all websites"""
    logging.info("Starting website refresh")
    
    # Export empty websites for all leagues
    for league_id in LEAGUES:
        success = export_empty_website_for_league(league_id)
        if not success:
            logging.warning(f"Failed to export website for league {league_id}")
    
    logging.info("Website refresh complete!")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nSUCCESS: Websites refreshed with empty scores!")
        print("\nNext steps:")
        print("1. Update extraction code to use the new unified scores table")
        print("2. Run extraction to get fresh scores")
    else:
        print("\nERROR: Failed to refresh websites.")
        print("Check the log file for details.")
