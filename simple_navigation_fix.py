import os
import re
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(message)s',
                   handlers=[
                       logging.StreamHandler(),
                       logging.FileHandler('navigation_fix.log', 'w')
                   ])

# Configuration
WORDLE_DATABASE = "wordle_league.db"
CONFIG_FILE = "league_config.json"
EXPORT_DIR = "website_export"
WEEKS_DIR = os.path.join(EXPORT_DIR, "weeks")
DAYS_DIR = os.path.join(EXPORT_DIR, "days")

# Current Wordle data
CURRENT_WORDLE_NUM = 1507  # August 4, 2025
WORDLE_START_DATE = datetime(2021, 6, 19)  # Wordle #1

def get_date_for_wordle_num(wordle_num):
    """Calculate the date for a given Wordle number"""
    return WORDLE_START_DATE + timedelta(days=wordle_num-1)

def get_league_config():
    """Load league configuration from the config file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading league configuration: {e}")
        return None

def get_league_slug(league_name):
    """Convert league name to a slug for use in filenames"""
    return re.sub(r'\W+', '-', league_name.lower())

def fix_week_pages():
    """Fix all league-specific week pages by adding game listings and links"""
    league_config = get_league_config()
    if not league_config:
        logging.error("Failed to load league configuration.")
        return
    
    # Define the week range (August 4-10, 2025)
    # Wordle numbers 1507-1513
    start_wordle = 1507
    end_wordle = 1513
    wordle_numbers = list(range(start_wordle, end_wordle + 1))
    
    # Get dates for the week
    start_date = get_date_for_wordle_num(start_wordle)
    week_name = f"aug-4th-(14)"  # Week 14, starting August 4th
    
    # Loop through leagues in the config
    for league_data in league_config['leagues']:
        league_id = league_data['league_id']
        league_name = league_data['name']
        league_slug = get_league_slug(league_name)
        
        # Week page filename
        week_filename = f"{week_name}-{league_slug}.html"
        week_filepath = os.path.join(WEEKS_DIR, week_filename)
        
        # Check if week page exists
        if not os.path.exists(week_filepath):
            logging.warning(f"Week page {week_filename} does not exist, skipping.")
            continue
        
        try:
            # Load existing page
            with open(week_filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Find the games table body
            tbody = soup.select_one('.week-details table tbody')
            if not tbody:
                logging.warning(f"Could not find table body in {week_filename}")
                continue
            
            # Clear existing content
            tbody.clear()
            
            # Add game listings
            for wordle_num in wordle_numbers:
                date = get_date_for_wordle_num(wordle_num)
                day_page = f"wordle-{wordle_num}-{league_slug}.html"
                
                tr = soup.new_tag('tr')
                
                # Wordle number column with link to day page
                td_num = soup.new_tag('td')
                a_tag = soup.new_tag('a', href=f"../days/{day_page}")
                a_tag.string = f"Wordle #{wordle_num}"
                td_num.append(a_tag)
                tr.append(td_num)
                
                # Date column
                td_date = soup.new_tag('td')
                td_date.string = date.strftime("%B %d, %Y")
                tr.append(td_date)
                
                tbody.append(tr)
            
            # Update week title
            h1 = soup.select_one('h1')
            if h1:
                h1.string = f"Wordle Week: August 4-10, 2025"
            
            # Save updated file
            with open(week_filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            logging.info(f"Updated week page: {week_filename}")
            
        except Exception as e:
            logging.error(f"Error updating week page {week_filename}: {e}")

def fix_main_index_page():
    """Fix the main index page to show league tabs"""
    league_config = get_league_config()
    if not league_config:
        logging.error("Failed to load league configuration.")
        return
        
    # Ensure the leagues key exists in config
    if 'leagues' not in league_config:
        logging.error("Invalid league configuration: 'leagues' key not found.")
        return
        
    # Main index page path
    main_index_path = os.path.join(EXPORT_DIR, 'index.html')
    
    try:
        # Load the existing index page
        with open(main_index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Get today's Wordle data for each league
        today_wordle = CURRENT_WORDLE_NUM
        today_date = get_date_for_wordle_num(today_wordle)
        today_date_str = today_date.strftime("%B %d, %Y")
        
        # Create tabs for each league
        tabs_div = soup.select_one('.tab-buttons.tabs')
        if not tabs_div:
            logging.error("Could not find tab buttons div in index.html")
            return
            
        # Clear the existing tab buttons
        tabs_div.clear()
        
        # Create the main tabs section (Latest, Weekly, Stats)
        main_tabs_div = soup.new_tag('div', style="width: 100%; display: flex; justify-content: center;")
        
        latest_button = soup.new_tag('button', attrs={'class': 'tab-button active', 'data-tab': 'latest', 'data-league': 'all'})
        latest_button.string = 'Latest Scores'
        main_tabs_div.append(latest_button)
        
        weekly_button = soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'weekly', 'data-league': 'all'})
        weekly_button.string = 'Weekly Totals'
        main_tabs_div.append(weekly_button)
        
        stats_button = soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'stats', 'data-league': 'all'})
        stats_button.string = 'Season / All-Time Stats'
        main_tabs_div.append(stats_button)
        
        tabs_div.append(main_tabs_div)
        
        # Create league tabs section
        league_tabs_div = soup.new_tag('div', style="width: 100%; display: flex; justify-content: center; margin-top: 10px;")
        
        # Add a league button for each league in the config
        for league in league_config['leagues']:
            league_name = league['name']
            league_slug = get_league_slug(league_name)
            
            # Create league tab button
            league_button = soup.new_tag('button', attrs={
                'class': 'tab-button league-tab',
                'data-league': league_slug
            })
            league_button.string = league_name
            
            # Add league button to the tabs
            league_tabs_div.append(league_button)
        
        # Add the league tabs section to the main tabs div
        tabs_div.append(league_tabs_div)
        
        # Default league is the first one
        default_league = league_config['leagues'][0]
        default_league_name = default_league['name']
        default_league_id = default_league['league_id']
        default_league_slug = get_league_slug(default_league_name)
        
        # Update page title to match default league
        title_tag = soup.select_one('title')
        if title_tag:
            title_tag.string = f"{default_league_name} - Wordle League"
        
        header_title = soup.select_one('header .title')
        if header_title:
            header_title.string = default_league_name
        
        # Update tab content for Latest Scores (latest tab)
        latest_tab = soup.select_one('#latest')
        if latest_tab:
            latest_tab.clear()
            
            # Add title
            title_h2 = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px; font-size: 16px; color: #6aaa64; text-align: center;")
            title_h2.string = f"Wordle #{today_wordle} - {today_date_str}"
            latest_tab.append(title_h2)
            
            # Add a placeholder message
            no_scores_p = soup.new_tag('p', style="text-align: center; padding: 20px;")
            no_scores_p.string = "Visit the current week page to see all scores."
            latest_tab.append(no_scores_p)
            
            # Add link to week page
            link_p = soup.new_tag('p', style="text-align: center; margin-top: 20px;")
            week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html", attrs={'class': 'button'})
            week_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            week_link.string = "View This Week"
            link_p.append(week_link)
            latest_tab.append(link_p)
        
        # Update Weekly Totals tab
        weekly_tab = soup.select_one('#weekly')
        if weekly_tab:
            weekly_tab.clear()
            
            # Add title
            title_h2 = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px;")
            title_h2.string = "Weekly Totals"
            weekly_tab.append(title_h2)
            
            # Add a placeholder message
            no_stats_p = soup.new_tag('p', style="text-align: center; padding: 20px;")
            no_stats_p.string = "Visit the current week page to see all weekly statistics."
            weekly_tab.append(no_stats_p)
            
            # Add link to week page
            link_p = soup.new_tag('p', style="text-align: center;")
            week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html", attrs={'class': 'button'})
            week_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            week_link.string = "View This Week"
            link_p.append(week_link)
            weekly_tab.append(link_p)
        
        # Update Stats tab
        stats_tab = soup.select_one('#stats')
        if stats_tab:
            stats_tab.clear()
            
            # Add title
            title_h2 = soup.new_tag('h2', style="margin-top: 5px; margin-bottom: 10px;")
            title_h2.string = "Season 1"
            stats_tab.append(title_h2)
            
            # Add subtitle
            subtitle_p = soup.new_tag('p', style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;")
            subtitle_p.string = "Weekly wins are tracked here. First player to reach 4 wins is the Season Winner!"
            stats_tab.append(subtitle_p)
            
            # Add link to week page
            link_div = soup.new_tag('div', style="text-align: center; padding: 20px;")
            week_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_slug}.html", attrs={'class': 'button'})
            week_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            week_link.string = "View Current Week"
            link_div.append(week_link)
            stats_tab.append(link_div)
        
        # Add JavaScript for league switching
        script_tag = soup.find('script', src='script.js')
        if script_tag:
            # Add custom script after the main script
            league_script = soup.new_tag('script')
            league_script.string = """
            document.addEventListener('DOMContentLoaded', function() {
                // Handle league tab clicks
                const leagueTabs = document.querySelectorAll('.league-tab');
                const defaultLeague = leagueTabs.length > 0 ? leagueTabs[0].getAttribute('data-league') : null;
                
                // Set default active league
                document.querySelectorAll('.league-tab').forEach(tab => {
                    if (tab.getAttribute('data-league') === defaultLeague) {
                        tab.classList.add('active');
                    }
                });
                
                // League tab click handler
                leagueTabs.forEach(tab => {
                    tab.addEventListener('click', function() {
                        const league = this.getAttribute('data-league');
                        
                        // Update active tab
                        document.querySelectorAll('.league-tab').forEach(t => {
                            t.classList.remove('active');
                        });
                        this.classList.add('active');
                        
                        // Update week links
                        document.querySelectorAll('a[href*="weeks/aug-4th-(14)-"]').forEach(link => {
                            link.setAttribute('href', 'weeks/aug-4th-(14)-' + league + '.html');
                        });
                        
                        // Update header title
                        const leagueName = this.textContent;
                        document.querySelector('header .title').textContent = leagueName;
                        
                        // Store selected league in local storage
                        localStorage.setItem('selectedLeague', league);
                        localStorage.setItem('selectedLeagueName', leagueName);
                    });
                });
                
                // Check if there's a stored league preference
                const storedLeague = localStorage.getItem('selectedLeague');
                const storedLeagueName = localStorage.getItem('selectedLeagueName');
                
                if (storedLeague && storedLeagueName) {
                    // Find the corresponding tab and simulate click
                    const tab = Array.from(leagueTabs).find(t => t.getAttribute('data-league') === storedLeague);
                    if (tab) {
                        // Update header and links without page reload
                        document.querySelector('header .title').textContent = storedLeagueName;
                        document.querySelectorAll('a[href*="weeks/aug-4th-(14)-"]').forEach(link => {
                            link.setAttribute('href', 'weeks/aug-4th-(14)-' + storedLeague + '.html');
                        });
                    }
                }
            });
            """
            soup.body.append(league_script)
        
        # Save the updated index page
        with open(main_index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info("Successfully updated main index page with league navigation")
        
    except Exception as e:
        logging.error(f"Error updating main index page: {e}")

def main():
    """Main execution function"""
    logging.info("Starting navigation fix process...")
    
    # Step 1: Fix league-specific week pages
    logging.info("Step 1: Fixing league-specific week pages...")
    fix_week_pages()
    
    # Step 2: Fix main index page
    logging.info("Step 2: Fixing main index page...")
    fix_main_index_page()
    
    logging.info("Navigation fix complete!")
    logging.info("All fixes have been applied. Please check the website to verify.")
    logging.info("You can run an HTTP server to test locally with: python -m http.server 8080 -d website_export")

if __name__ == "__main__":
    main()
