#!/usr/bin/env python3
"""
Script to add the Season table to all league pages without disrupting the existing structure.
This script makes targeted changes to the HTML files to:
1. Update the "All-Time Stats" tab to "Season / All-Time Stats"
2. Add a "Season 1" table before the All-Time Stats table
3. Include only players who have won a weekly competition
"""

import os
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# League information
LEAGUES = {
    'warriorz': {'id': 1, 'path': 'website_export/index.html', 'name': 'Wordle Warriorz'},
    'gang': {'id': 2, 'path': 'website_export/gang/index.html', 'name': 'Wordle Gang'},
    'pal': {'id': 3, 'path': 'website_export/pal/index.html', 'name': 'Wordle PAL'},
    'party': {'id': 4, 'path': 'website_export/party/index.html', 'name': 'Wordle Party'},
    'vball': {'id': 5, 'path': 'website_export/vball/index.html', 'name': 'Wordle Vball'}
}

# DB connection
DB_PATH = 'wordle_league.db'

def get_weekly_winners(conn, league_id):
    """
    Get the weekly winners for a league.
    Returns dict mapping weeks to lists of winners and their scores.
    
    Note: For now, we return an empty dict since we want to start with
    an empty Season table until the first weekly winner is determined at midnight.
    """
    # Return empty dict - no winners yet until weekly reset at midnight
    return {}

def get_player_weekly_wins(conn, league_id):
    """
    Count weekly wins for each player in the league.
    Returns dict mapping player names to win counts.
    """
    # For now, we only have data for the current week, so we'll simulate this
    # by checking the current week's winners
    weekly_winners = get_weekly_winners(conn, league_id)
    
    player_wins = {}
    for week, winners in weekly_winners.items():
        for name, _ in winners:
            if name in player_wins:
                player_wins[name] += 1
            else:
                player_wins[name] = 1
    
    return player_wins

def update_html_with_season_table(league_key):
    """Update a league's HTML to add the Season table and update the tab title"""
    league_info = LEAGUES.get(league_key)
    if not league_info:
        logger.error(f"Unknown league: {league_key}")
        return False
    
    league_id = league_info['id']
    html_path = league_info['path']
    league_name = league_info['name']
    
    logger.info(f"Updating {league_name} with Season table...")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        
        # Get weekly winners and player win counts
        weekly_winners = get_weekly_winners(conn, league_id)
        player_wins = get_player_weekly_wins(conn, league_id)
        
        # Parse the HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Update the tab button text
        stats_button = soup.select_one('button.tab-button[data-tab="stats"]')
        if stats_button:
            stats_button.string = "Season / All-Time Stats"
            logger.info("Updated tab button text to 'Season / All-Time Stats'")
        
        # Update the heading in the stats tab
        stats_tab = soup.select_one('#stats')
        if stats_tab:
            stats_heading = stats_tab.select_one('h2')
            if stats_heading:
                # Create a new h2 with the updated text
                new_heading = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px;")
                new_heading.string = "Season / All-Time Stats"
                stats_heading.replace_with(new_heading)
                logger.info("Updated stats heading to 'Season / All-Time Stats'")
                
                # Find the all-time stats table container
                table_container = stats_tab.select_one('.table-container')
                
                if table_container:
                    # Create the Season 1 heading and description
                    season_heading = soup.new_tag('h3', style="margin-top: 15px; margin-bottom: 10px;")
                    season_heading.string = "Season 1"
                    
                    season_desc = soup.new_tag('p', style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;")
                    season_desc.string = "If players are tied at the end of the week, then both players get a weekly win. First Player to get 4 weekly wins, is the Season Champ!"
                    
                    # Create the season table
                    season_table_container = soup.new_tag('div', attrs={'class': 'table-container season-winners'})
                    season_table = soup.new_tag('table')
                    
                    # Create the table header
                    thead = soup.new_tag('thead')
                    tr = soup.new_tag('tr')
                    
                    th_player = soup.new_tag('th')
                    th_player.string = 'Player'
                    tr.append(th_player)
                    
                    th_wins = soup.new_tag('th')
                    th_wins.string = 'Weekly Wins'
                    tr.append(th_wins)
                    
                    th_week = soup.new_tag('th')
                    th_week.string = 'Wordle Week (Score)'
                    tr.append(th_week)
                    
                    thead.append(tr)
                    season_table.append(thead)
                    
                    # Create table body
                    tbody = soup.new_tag('tbody')
                    
                    # Start with empty table - no winners yet until weekly reset at midnight
                    # The table will be populated with the first weekly winner after midnight tonight
                    tr = soup.new_tag('tr')
                    td = soup.new_tag('td', attrs={'colspan': '3', 'style': 'text-align: center;'})
                    td.string = "No weekly winners yet - first winner will be determined after Sunday at midnight"
                    tr.append(td)
                    tbody.append(tr)
                        
                    season_table.append(tbody)
                    season_table_container.append(season_table)
                    
                    # Insert the new content before the all-time stats table
                    all_time_heading = soup.new_tag('h3', style="margin-top: 25px; margin-bottom: 10px;")
                    all_time_heading.string = "All-Time Stats"
                    
                    # Insert all new elements
                    table_container.insert_before(season_heading)
                    season_heading.insert_after(season_desc)
                    season_desc.insert_after(season_table_container)
                    season_table_container.insert_after(all_time_heading)
                    
                    logger.info("Added Season 1 table before All-Time Stats")
                else:
                    logger.error("Could not find table container")
            else:
                logger.error("Could not find stats heading")
        else:
            logger.error("Could not find stats tab")
        
        # Save the updated HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logger.info(f"Successfully updated {html_path} with Season table")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {html_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Update all league pages with the Season table"""
    for league_key in LEAGUES:
        success = update_html_with_season_table(league_key)
        if success:
            logger.info(f"Successfully updated {league_key} with Season table")
        else:
            logger.error(f"Failed to update {league_key}")
    
    logger.info("Season table updates completed for all leagues")

if __name__ == "__main__":
    main()
