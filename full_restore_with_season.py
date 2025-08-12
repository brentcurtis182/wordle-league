import os
import shutil
from bs4 import BeautifulSoup, NavigableString
from datetime import datetime

# Constants
BACKUP_DIR = "website_export_backup_20250810_221305"  # Your 10:13 PM backup
CURRENT_DIR = "website_export"  # Current website export directory
LEAGUES = {
    "main": {"source": os.path.join(BACKUP_DIR, "index.html"), 
             "target": os.path.join(CURRENT_DIR, "index.html")},
    "gang": {"source": os.path.join(BACKUP_DIR, "gang", "index.html"), 
             "target": os.path.join(CURRENT_DIR, "gang", "index.html")},
    "pal": {"source": os.path.join(BACKUP_DIR, "pal", "index.html"), 
            "target": os.path.join(CURRENT_DIR, "pal", "index.html")},
    "party": {"source": os.path.join(BACKUP_DIR, "party", "index.html"), 
              "target": os.path.join(CURRENT_DIR, "party", "index.html")},
    "vball": {"source": os.path.join(BACKUP_DIR, "vball", "index.html"), 
              "target": os.path.join(CURRENT_DIR, "vball", "index.html")}
}

def backup_current_files():
    """Backup current website files before restoration"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"website_export_backup_{timestamp}"
    
    if os.path.exists(CURRENT_DIR):
        shutil.copytree(CURRENT_DIR, backup_dir)
        print(f"Backed up current website files to {backup_dir}")
    else:
        print(f"Warning: Current directory {CURRENT_DIR} not found. No backup created.")
    
    return True

def get_season_container_html():
    """Create the Season table HTML container"""
    html = """
    <div class="season-container" style="margin-bottom: 30px;">
        <h3 style="margin-bottom: 10px; color: #6aaa64;">Season 1</h3>
        <p style="margin-bottom: 15px; font-size: 14px; font-style: italic;">If players are tied at the end of the week, then both players get a weekly win. First Player to get <b>4 weekly wins</b>, is the Season Champ!</p>
        <table class="season-table">
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Weekly Wins</th>
                    <th>Wordle Week (Score)</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan="3" style="text-align: center;">No weekly winners yet</td>
                </tr>
            </tbody>
        </table>
    </div>
    """
    return BeautifulSoup(html, 'html.parser')

def restore_league(league_name):
    """Restore a league's HTML file with Season table and formatting"""
    source_path = LEAGUES[league_name]["source"]
    target_path = LEAGUES[league_name]["target"]
    
    if not os.path.exists(source_path):
        print(f"Error: Source file {source_path} not found for league {league_name}")
        return False
        
    # Create target directory if it doesn't exist
    target_dir = os.path.dirname(target_path)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    # Read the source HTML (with the correct data)
    with open(source_path, 'r', encoding='utf-8') as f:
        source_html = f.read()
    
    soup = BeautifulSoup(source_html, 'html.parser')
    
    # 1. Update the tab name
    stats_tab = soup.select_one('ul.nav.nav-tabs li a[href="#stats"]')
    if stats_tab:
        stats_tab.string = "Season / All-Time Stats"
    
    # 2. Find the stats div
    stats_div = soup.find('div', {'id': 'stats'})
    if not stats_div:
        print(f"Error: Could not find stats div in {source_path}")
        return False
    
    # 3. Add Season container at the beginning
    season_container = get_season_container_html()
    if stats_div.contents:
        stats_div.insert(0, season_container)
    else:
        stats_div.append(season_container)
    
    # 4. Make the All-Time Stats section properly formatted
    all_time_content = stats_div.find_all(['h2', 'p', 'table'])
    
    # Create All-Time container
    all_time_container = soup.new_tag('div')
    all_time_container['class'] = 'all-time-container'
    
    # Add the h2 header
    all_time_header = None
    all_time_desc = None
    all_time_table = None
    
    for content in all_time_content:
        if content.name == 'h2' and 'All-Time Stats' in content.text:
            all_time_header = content
        elif content.name == 'p' and 'All time stats' in content.text:
            all_time_desc = content
            # Make it italic
            content['style'] = content.get('style', '') + '; font-style: italic;'
        elif content.name == 'table' and not content.parent.get('class') == 'season-container':
            all_time_table = content
    
    # If we found existing all-time stats content, use it
    if all_time_header:
        all_time_container.append(all_time_header)
    else:
        h2 = soup.new_tag('h2')
        h2.string = "All-Time Stats"
        all_time_container.append(h2)
        
    if all_time_desc:
        all_time_container.append(all_time_desc)
    else:
        p = soup.new_tag('p')
        p.string = "All time stats includes every game played since this league began!"
        p['style'] = 'font-style: italic;'
        all_time_container.append(p)
        
    if all_time_table:
        all_time_container.append(all_time_table)
    
    # Remove any existing All-Time related content
    for content in all_time_content:
        if content.parent == stats_div:  # Only remove if directly under stats_div
            content.extract()
    
    # Add the All-Time container
    stats_div.append(all_time_container)
    
    # 5. Make the weekly description italic too
    weekly_div = soup.find('div', {'id': 'weekly'})
    if weekly_div:
        weekly_desc = None
        h2 = weekly_div.find('h2')
        if h2:
            weekly_desc = h2.find_next('p')
        
        if weekly_desc:
            weekly_desc['style'] = weekly_desc.get('style', '') + '; font-style: italic;'
    
    # Write the updated HTML
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"Successfully restored {league_name} league with Season table and proper formatting!")
    return True

def highlight_top_player(league_name):
    """Highlight the top player in the All-Time Stats table"""
    target_path = LEAGUES[league_name]["target"]
    
    # Read the HTML file
    with open(target_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the All-Time Stats table
    all_time_container = soup.find('div', {'class': 'all-time-container'})
    if not all_time_container:
        print(f"Could not find All-Time container in {target_path}")
        return False
        
    all_time_table = all_time_container.find('table')
    if not all_time_table:
        print(f"Could not find All-Time table in {target_path}")
        return False
    
    # Find all rows with player data
    rows = all_time_table.find_all('tr')
    if len(rows) <= 1:  # Header row only
        print(f"No player data rows found in All-Time table for {league_name}")
        return False
    
    # Find the player with the lowest average (top player)
    best_avg = float('inf')
    best_row = None
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all('td')
        if len(cells) >= 3:
            avg_text = cells[2].text.strip()
            try:
                avg = float(avg_text)
                if avg < best_avg:
                    best_avg = avg
                    best_row = row
            except ValueError:
                # Not a number, might be "-" for no games
                continue
    
    # Highlight the top player's row
    if best_row:
        best_row['style'] = 'background-color: rgba(106, 170, 100, 0.3);'
        
        # Write the updated HTML
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Highlighted top player in All-Time Stats table for {league_name}")
    else:
        print(f"Could not determine top player for {league_name}")
    
    return True

def main():
    """Main function to restore all leagues with Season table and formatting"""
    print("Starting full website restoration with Season table...")
    
    # Backup current website files first
    backup_current_files()
    
    # Restore each league
    for league in LEAGUES:
        print(f"\nProcessing {league} league...")
        if restore_league(league):
            # Add highlighting for top player
            highlight_top_player(league)
        else:
            print(f"Failed to restore {league} league")
    
    print("\nRestoration complete!")
    print("The website should now have:")
    print("1. All correct league data from the 10:13 PM backup")
    print("2. Season tables added to all leagues")
    print("3. Proper tab naming ('Season / All-Time Stats')")
    print("4. Italic descriptions and bold '4 weekly wins' text")
    print("5. Highlighted top players in All-Time Stats tables")
    print("\nPlease check the pages to verify everything is correct.")

if __name__ == "__main__":
    main()
