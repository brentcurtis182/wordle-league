import os
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime
import shutil

def backup_current_file(file_path):
    """Create a backup of a file before modifying it"""
    if os.path.exists(file_path):
        backup_dir = os.path.dirname(file_path) + "/backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/{os.path.basename(file_path)}_{timestamp}"
        
        shutil.copy2(file_path, backup_file)
        print(f"Backed up {file_path} to {backup_file}")

def get_gang_season_container():
    """Get the Season container HTML from Wordle Gang page to use as a template"""
    gang_path = "website_export/gang/index.html"
    
    with open(gang_path, 'r', encoding='utf-8') as f:
        gang_html = f.read()
    
    gang_soup = BeautifulSoup(gang_html, 'html.parser')
    season_container = gang_soup.find('div', {'class': 'season-container'})
    
    if not season_container:
        raise Exception("Could not find Season container in Gang page")
    
    return season_container

def restore_season_table_to_warriorz():
    """Restore the Season table to the Wordle Warriorz main page"""
    warriorz_path = "website_export/index.html"
    
    # First, backup the current file
    backup_current_file(warriorz_path)
    
    # Read the current Wordle Warriorz HTML
    with open(warriorz_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check if the page has the updated tab title
    tab_li = soup.select_one('ul.nav.nav-tabs li a[href="#stats"]')
    if tab_li:
        tab_li.string = "Season / All-Time Stats"
    else:
        print("Warning: Could not find stats tab to update")
    
    # Find or create the stats div
    stats_div = soup.find('div', {'id': 'stats'})
    if not stats_div:
        print("Warning: Could not find stats div. Creating one.")
        stats_div = soup.new_tag('div')
        stats_div['id'] = 'stats'
        stats_div['class'] = 'tab-pane fade'
        # Find the tabs content
        tabs_content = soup.find('div', {'class': 'tab-content'})
        if tabs_content:
            tabs_content.append(stats_div)
        else:
            print("Error: Could not find tab content to add stats div")
            return False
    
    # Get the Season container from Wordle Gang page as a template
    try:
        gang_season_container = get_gang_season_container()
    except Exception as e:
        print(f"Error getting Gang season container: {e}")
        return False
    
    # Remove any existing season container
    existing_season = stats_div.find('div', {'class': 'season-container'})
    if existing_season:
        existing_season.decompose()
    
    # Add the Season container at the start of stats_div
    if stats_div.contents:
        stats_div.insert(0, gang_season_container)
    else:
        stats_div.append(gang_season_container)
    
    # Make sure we have an All-Time Stats container with proper header and description
    all_time_container = stats_div.find('div', {'class': 'all-time-container'})
    if not all_time_container:
        # Create All-Time container
        all_time_container = soup.new_tag('div')
        all_time_container['class'] = 'all-time-container'
        
        # Create All-Time header
        h2 = soup.new_tag('h2')
        h2.string = "All-Time Stats"
        all_time_container.append(h2)
        
        # Create description
        p = soup.new_tag('p')
        p.string = "All time stats includes every game played since this league began!"
        p['style'] = 'font-style: italic;'
        all_time_container.append(p)
        
        # Find existing table or create placeholder
        all_time_table = stats_div.find('table', {'id': 'all-time-stats'})
        if all_time_table:
            # If we found an existing all-time stats table, move it inside our container
            all_time_container.append(all_time_table)
        else:
            # Create placeholder table
            table = soup.new_tag('table')
            table['id'] = 'all-time-stats'
            table['class'] = 'table table-striped'
            all_time_container.append(table)
        
        # Add the All-Time container after the Season container
        stats_div.append(all_time_container)
    else:
        # Make sure the description is italic
        desc = all_time_container.find('p')
        if desc:
            desc['style'] = desc.get('style', '') + '; font-style: italic;'
    
    # Apply Italian formatting to the season description
    season_container = stats_div.find('div', {'class': 'season-container'})
    if season_container:
        season_desc = season_container.find('p')
        if season_desc:
            season_desc['style'] = season_desc.get('style', '') + '; font-style: italic;'
            
            # Apply bold to "4 weekly wins" if it exists
            desc_text = season_desc.string
            if desc_text and "4 weekly wins" in desc_text:
                season_desc.clear()
                parts = desc_text.split("4 weekly wins")
                season_desc.append(NavigableString(parts[0]))
                bold = soup.new_tag('b')
                bold.string = "4 weekly wins"
                season_desc.append(bold)
                season_desc.append(NavigableString(parts[1]))
    
    # Apply italic formatting to weekly description too
    weekly_div = soup.find('div', {'id': 'weekly'})
    if weekly_div:
        weekly_desc = None
        h2 = weekly_div.find('h2')
        if h2:
            weekly_desc = h2.find_next('p')
        
        if weekly_desc:
            weekly_desc['style'] = weekly_desc.get('style', '') + '; font-style: italic;'
    
    # Update the Wordle number and date to latest
    wordle_heading = soup.select_one('h2[style*="color: #6aaa64"]')
    if wordle_heading:
        current_date = datetime.now().strftime("%B %d, %Y")
        new_text = f"Wordle #1513 - August 10, 2025"
        wordle_heading.string = new_text
    
    # Write the updated HTML back to file
    with open(warriorz_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("Successfully restored the Wordle Warriorz page with Season table and proper formatting!")
    return True

def disable_problematic_scripts():
    """Disable problematic scripts that keep reverting to Aug 6th backup"""
    problematic_scripts = [
        "restore_original_structure.py",
        "fix_tabs.py"
    ]
    
    for script in problematic_scripts:
        if os.path.exists(script):
            disabled_name = f"DISABLED_{script}"
            try:
                os.rename(script, disabled_name)
                print(f"Disabled {script} by renaming to {disabled_name}")
            except Exception as e:
                print(f"Could not disable {script}: {e}")

def main():
    """Main function"""
    print("Starting restoration of Wordle Warriorz page...")
    
    # Disable problematic scripts
    disable_problematic_scripts()
    
    # Restore the Warriorz page
    restore_season_table_to_warriorz()
    
    print("Restoration complete!")

if __name__ == "__main__":
    main()
