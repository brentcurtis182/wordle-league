import os
from bs4 import BeautifulSoup
from datetime import datetime

def fix_warriorz_page():
    """Fix the Wordle Warriorz page completely"""
    warriorz_path = "website_export/index.html"
    gang_path = "website_export/gang/index.html"
    
    # First, read the Gang HTML to get reference structures
    with open(gang_path, 'r', encoding='utf-8') as f:
        gang_html = f.read()
    
    gang_soup = BeautifulSoup(gang_html, 'html.parser')
    
    # Get the Season container from Gang
    gang_season_container = gang_soup.find('div', {'class': 'season-container'})
    if not gang_season_container:
        print("Could not find Season container in Gang page")
        return False
        
    # Get the All-Time container from Gang
    gang_all_time_container = gang_soup.find('div', {'class': 'all-time-container'})
    if not gang_all_time_container:
        print("Could not find All-Time container in Gang page")
        return False
    
    # Get the Stats tab header from Gang
    gang_stats_tab = gang_soup.select_one('ul.nav.nav-tabs li a[href="#stats"]')
    if not gang_stats_tab:
        print("Could not find stats tab in Gang page")
        return False
    
    # Now read the Warriorz HTML
    with open(warriorz_path, 'r', encoding='utf-8') as f:
        warriorz_html = f.read()
    
    warriorz_soup = BeautifulSoup(warriorz_html, 'html.parser')
    
    # Find the stats tab and update its text
    stats_tab = warriorz_soup.select_one('ul.nav.nav-tabs li a[href="#stats"]')
    if stats_tab:
        stats_tab.string = "Season / All-Time Stats"
        print("Updated stats tab text to: Season / All-Time Stats")
    else:
        print("WARNING: Could not find stats tab to update")
    
    # Find the stats div
    stats_div = warriorz_soup.find('div', {'id': 'stats'})
    if not stats_div:
        print("Could not find stats div")
        return False
    
    # Clear out the stats div completely
    stats_div.clear()
    
    # Clone the season container from Gang
    new_season_container = BeautifulSoup(str(gang_season_container), 'html.parser')
    stats_div.append(new_season_container)
    
    # Get the all-time stats HTML from gang page
    all_time_html = str(gang_all_time_container)
    
    # Read the warriors all-time stats table content
    all_time_table = warriorz_soup.find('table')
    if all_time_table:
        print("Found original all-time stats table")
    else:
        # Try to get it from before we made changes
        backup_path = "website_export/backups/index.html_20250810_233451"
        if os.path.exists(backup_path):
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_html = f.read()
            backup_soup = BeautifulSoup(backup_html, 'html.parser')
            all_time_table = backup_soup.find('table')
            if all_time_table:
                print("Found all-time stats table in backup")
            else:
                print("WARNING: Could not find all-time stats table in backup")
        else:
            print("WARNING: No backup file found")
    
    # Create the all-time container based on Gang's structure
    all_time_container = BeautifulSoup(all_time_html, 'html.parser')
    
    # Replace the table in the all-time container with the original table if found
    if all_time_table:
        container_table = all_time_container.find('table')
        if container_table:
            container_table.replace_with(all_time_table)
    
    # Add the all-time container to stats div
    stats_div.append(all_time_container)
    
    # Write the fixed HTML
    with open(warriorz_path, 'w', encoding='utf-8') as f:
        f.write(str(warriorz_soup))
    
    print("Successfully fixed the Wordle Warriorz page completely!")
    return True

if __name__ == "__main__":
    fix_warriorz_page()
