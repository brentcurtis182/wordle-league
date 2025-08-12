import os
import re
import json
import logging
import shutil
import sqlite3
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO,
                   format='%(message)s')

# Configuration
WORDLE_DATABASE = "wordle_league.db"
CONFIG_FILE = "league_config.json"
EXPORT_DIR = "website_export"
WEEKS_DIR = os.path.join(EXPORT_DIR, "weeks")
DAYS_DIR = os.path.join(EXPORT_DIR, "days")
BACKUP_DIR = "website_export_backup"

def backup_website():
    """Create a backup of the current website"""
    if os.path.exists(BACKUP_DIR):
        logging.info(f"Backup already exists at {BACKUP_DIR}")
        return True
        
    try:
        if os.path.exists(EXPORT_DIR):
            shutil.copytree(EXPORT_DIR, BACKUP_DIR)
            logging.info(f"Created backup: {EXPORT_DIR} → {BACKUP_DIR}")
            return True
        else:
            logging.error(f"Export directory {EXPORT_DIR} does not exist. Cannot create backup.")
            return False
    except Exception as e:
        logging.error(f"Error creating backup: {e}")
        return False

def restore_original_site():
    """Generate clean versions of the HTML files"""
    try:
        # Clean up the main index page to remove added tabs
        index_path = os.path.join(EXPORT_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Keep only the original tabs
            tab_buttons = soup.select_one('.tab-buttons')
            if tab_buttons:
                # Remove all tabs
                tab_buttons.clear()
                
                # Add back the original tabs
                latest_button = soup.new_tag('button', attrs={'class': 'tab-button active', 'data-tab': 'latest'})
                latest_button.string = 'Latest Scores'
                tab_buttons.append(latest_button)
                
                weekly_button = soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'weekly'})
                weekly_button.string = 'Weekly Totals'
                tab_buttons.append(weekly_button)
                
                stats_button = soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'stats'})
                stats_button.string = 'Season / All-Time Stats'
                tab_buttons.append(stats_button)
                
                # Write the updated file
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                
                logging.info("Restored main index page to original tab structure")
                
        return True
    except Exception as e:
        logging.error(f"Error restoring original site: {e}")
        return False

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
    
    # Loop through leagues in the config
    for league_data in league_config['leagues']:
        league_name = league_data['name']
        league_slug = get_league_slug(league_name)
        
        # Week page filename
        week_filename = f"aug-4th-(14)-{league_slug}.html"
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
                # Calculate the date based on Wordle number
                # August 4th is Wordle 1507, so we add days accordingly
                day_num = 4 + (wordle_num - 1507)
                date_str = f"August {day_num}, 2025"
                
                # Create day page filename
                day_page = f"wordle-{wordle_num}-{league_slug}.html"
                
                # Create table row
                tr = soup.new_tag('tr')
                
                # Wordle number column with link to day page
                td_num = soup.new_tag('td')
                a_tag = soup.new_tag('a', href=f"../days/{day_page}")
                a_tag.string = f"Wordle #{wordle_num}"
                td_num.append(a_tag)
                tr.append(td_num)
                
                # Date column
                td_date = soup.new_tag('td')
                td_date.string = date_str
                tr.append(td_date)
                
                # Add row to table
                tbody.append(tr)
            
            # Save updated file
            with open(week_filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            logging.info(f"Updated week page: {week_filename}")
            
        except Exception as e:
            logging.error(f"Error updating week page {week_filename}: {e}")

def fix_main_index_links():
    """Fix links in the main index page to point to the correct week page"""
    league_config = get_league_config()
    if not league_config:
        logging.error("Failed to load league configuration.")
        return
    
    # Get default league (first in config)
    default_league = league_config['leagues'][0]
    default_league_name = default_league['name']
    default_league_slug = get_league_slug(default_league_name)
    
    # Main index page path
    main_index_path = os.path.join(EXPORT_DIR, 'index.html')
    
    try:
        # Load existing page
        with open(main_index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        
        # Find all links to week pages
        week_links = soup.find_all('a', href=lambda href: href and 'weeks/' in href)
        
        # Update links to point to default league week page
        for link in week_links:
            link['href'] = f"weeks/aug-4th-(14)-{default_league_slug}.html"
        
        # Set correct header title
        header_title = soup.select_one('header .title')
        if header_title:
            header_title.string = default_league_name
        
        # Save updated page
        with open(main_index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Updated main index page links to point to {default_league_name} week page")
        
    except Exception as e:
        logging.error(f"Error updating main index page links: {e}")

def main():
    """Main execution function"""
    logging.info("Starting complete website restoration...")
    
    # Step 1: Create a backup if one doesn't exist
    logging.info("Step 1: Creating backup of current website...")
    backup_success = backup_website()
    if not backup_success:
        logging.warning("Could not create backup. Proceeding with caution.")
    
    # Step 2: Restore original site structure
    logging.info("Step 2: Restoring original site structure...")
    restore_success = restore_original_site()
    if not restore_success:
        logging.error("Failed to restore original site structure. Aborting.")
        return
    
    # Step 3: Fix week pages to link to daily pages
    logging.info("Step 3: Fixing week pages to link to daily pages...")
    fix_week_pages()
    
    # Step 4: Fix links in main index page
    logging.info("Step 4: Fixing main index page links...")
    fix_main_index_links()
    
    logging.info("Website restoration complete!")
    logging.info("You can run an HTTP server to test locally with: python -m http.server 8080 -d website_export")

if __name__ == "__main__":
    main()
