import os
import sqlite3
import logging
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DB_PATH = "wordle_league.db"
WEBSITE_DIR = "website_export"
SEASON_TEXT = "If players are tied at the end of the week, then both players get a weekly win. First Player to get 4 weekly wins, is the Season Champ!"

def connect_to_database():
    """Connect to the SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None

def add_season_table(html_path, league_id):
    """Add the Season table to a league's HTML file"""
    try:
        # Parse HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # 1. Update tab button text
        for button in soup.select('.tab-button'):
            if button.get('data-tab') == 'stats':
                button.string = 'Season / All-Time Stats'
                logger.info("Updated tab button text")
                break
                
        # 2. Update the stats heading
        stats_div = soup.select_one('#stats')
        if stats_div:
            heading = stats_div.select_one('h2')
            if heading:
                heading.string = 'Season / All-Time Stats'
                logger.info("Updated stats heading")
            
            # 3. Find and remove any existing season containers to prevent duplicates
            existing_season = stats_div.select_one('.season-container')
            if existing_season:
                logger.info("Removing existing season container")
                existing_season.decompose()
            
            # 4. Get all-time stats container
            all_time_container = stats_div.select_one('.all-time-container')
            if all_time_container:
                # Move the "Average includes..." text under the All-Time Stats heading
                all_time_heading = all_time_container.select_one('h3')
                if all_time_heading and all_time_heading.string == 'All-Time Stats':
                    # Check if the description is already in the right place
                    next_p = all_time_heading.find_next('p')
                    if not next_p or not next_p.string or "Average includes all games" not in next_p.string:
                        # Create and insert description
                        desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
                        desc.string = "Average includes all games. Failed attempts (X/6) count as 7 in the average calculation"
                        all_time_heading.insert_after(desc)
                        logger.info("Added All-Time Stats description")
                
                # Create season container
                season_container = soup.new_tag('div', attrs={'class': 'season-container', 'style': 'margin-bottom: 30px;'})
                
                # Add Season 1 heading
                season_heading = soup.new_tag('h3', attrs={'style': 'margin-bottom: 10px; color: #6aaa64;'})
                season_heading.string = 'Season 1'
                season_container.append(season_heading)
                
                # Add description
                season_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
                season_desc.string = SEASON_TEXT
                season_container.append(season_desc)
                
                # Create season table
                season_table = soup.new_tag('table', attrs={'class': 'season-table'})
                
                # Create table header
                thead = soup.new_tag('thead')
                tr = soup.new_tag('tr')
                
                # Column headers
                headers = ['Player', 'Weekly Wins', 'Wordle Week (Score)']
                for header in headers:
                    th = soup.new_tag('th')
                    th.string = header
                    tr.append(th)
                    
                thead.append(tr)
                season_table.append(thead)
                
                # Create table body
                tbody = soup.new_tag('tbody')
                
                # Add empty row indicating no winners yet
                tr = soup.new_tag('tr')
                td = soup.new_tag('td', attrs={'colspan': '3', 'style': 'text-align: center;'})
                td.string = "No weekly winners yet"
                tr.append(td)
                tbody.append(tr)
                
                season_table.append(tbody)
                season_container.append(season_table)
                
                # Insert the season container before all-time stats
                all_time_container.insert_before(season_container)
                logger.info("Added Season table")
                
        # Save the updated HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        logger.info(f"Successfully updated {html_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating {html_path}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function to add Season tables to all leagues"""
    # Define league IDs and their corresponding HTML paths
    leagues = [
        {"id": 1, "path": os.path.join(WEBSITE_DIR, "index.html")},
        {"id": 2, "path": os.path.join(WEBSITE_DIR, "gang", "index.html")},
        {"id": 3, "path": os.path.join(WEBSITE_DIR, "pal", "index.html")},
        {"id": 4, "path": os.path.join(WEBSITE_DIR, "party", "index.html")},
        {"id": 5, "path": os.path.join(WEBSITE_DIR, "vball", "index.html")}
    ]
    
    success_count = 0
    for league in leagues:
        if os.path.exists(league["path"]):
            if add_season_table(league["path"], league["id"]):
                success_count += 1
        else:
            logger.warning(f"League file not found: {league['path']}")
    
    logger.info(f"Updated {success_count} out of {len(leagues)} league files")

if __name__ == "__main__":
    main()
