import os
import re
import json
from bs4 import BeautifulSoup

# Configuration
EXPORT_DIR = "website_export"
WEEKS_DIR = os.path.join(EXPORT_DIR, "weeks")
DAYS_DIR = os.path.join(EXPORT_DIR, "days")
CONFIG_FILE = "league_config.json"

def get_league_config():
    """Load league configuration from the config file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading league configuration: {e}")
        return None

def get_league_slug(league_name):
    """Convert league name to a slug for use in filenames"""
    return re.sub(r'\W+', '-', league_name.lower())

def fix_week_pages():
    """Fix week pages to link to the correct daily pages"""
    league_config = get_league_config()
    if not league_config:
        print("Failed to load league configuration.")
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
            print(f"Week page {week_filename} does not exist, skipping.")
            continue
        
        try:
            # Load existing page
            with open(week_filepath, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Find the games table body
            tbody = soup.select_one('.week-details table tbody')
            if not tbody:
                print(f"Could not find table body in {week_filename}")
                continue
            
            # Clear existing rows to rebuild them
            tbody.clear()
            
            # Add game listings
            for wordle_num in wordle_numbers:
                day_page = f"wordle-{wordle_num}-{league_slug}.html"
                
                tr = soup.new_tag('tr')
                
                # Wordle number column with link to day page
                td_num = soup.new_tag('td')
                a_tag = soup.new_tag('a', href=f"../days/{day_page}")
                a_tag.string = f"Wordle #{wordle_num}"
                td_num.append(a_tag)
                tr.append(td_num)
                
                # Date column (we don't have dates, so we'll use placeholder)
                td_date = soup.new_tag('td')
                td_date.string = f"August {4 + (wordle_num - 1507)}, 2025"
                tr.append(td_date)
                
                tbody.append(tr)
            
            # Save updated file
            with open(week_filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            print(f"Updated week page: {week_filename}")
            
        except Exception as e:
            print(f"Error updating week page {week_filename}: {e}")

def fix_main_index_page():
    """Fix the main index page to link to the correct week page"""
    league_config = get_league_config()
    if not league_config:
        print("Failed to load league configuration.")
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
        
        # Find all "View This Week" or similar links
        week_links = soup.find_all('a', href=lambda href: href and 'weeks/' in href)
        
        # Update links to point to default league week page
        for link in week_links:
            link['href'] = f"weeks/aug-4th-(14)-{default_league_slug}.html"
        
        # Save updated page
        with open(main_index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        print(f"Updated main index page links to point to {default_league_slug} week page")
        
    except Exception as e:
        print(f"Error updating main index page: {e}")

def main():
    """Main execution function"""
    print("Starting minimal navigation fix...")
    
    # Step 1: Fix week pages to link to daily pages
    print("Step 1: Fixing week pages to link to daily pages...")
    fix_week_pages()
    
    # Step 2: Fix main index to link to week pages
    print("Step 2: Fixing main index to link to week pages...")
    fix_main_index_page()
    
    print("Minimal navigation fix complete!")
    print("You can run an HTTP server to test locally with: python -m http.server 8080 -d website_export")

if __name__ == "__main__":
    main()
