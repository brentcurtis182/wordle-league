import os
import re
from bs4 import BeautifulSoup

def insert_season_table(html_path):
    """Insert the Season table directly into the HTML file"""
    print(f"Processing {html_path}...")
    
    try:
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the stats div
        stats_div = soup.find('div', {'id': 'stats'})
        if not stats_div:
            print(f"Could not find stats div in {html_path}")
            return False
            
        # Check if season table already exists
        existing_season = stats_div.find('div', {'class': 'season-container'})
        if existing_season:
            print(f"Season table already exists in {html_path}, removing it first")
            existing_season.decompose()
            
        # Find where to insert the Season table - right after the h2 and paragraph
        all_time_table = stats_div.find('div', {'class': 'table-container'})
        if not all_time_table:
            print(f"Could not find table container in {html_path}")
            return False
            
        # Create season container
        season_container = soup.new_tag('div', attrs={'class': 'season-container', 'style': 'margin-bottom: 30px;'})
        
        # Create Season heading
        season_heading = soup.new_tag('h3', attrs={'style': 'margin-bottom: 10px; color: #6aaa64;'})
        season_heading.string = 'Season 1'
        season_container.append(season_heading)
        
        # Create description
        desc_text = "If players are tied at the end of the week, then both players get a weekly win. First Player to get 4 weekly wins, is the Season Champ!"
        season_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
        season_desc.string = desc_text
        season_container.append(season_desc)
        
        # Create Season table
        table = soup.new_tag('table', attrs={'class': 'season-table'})
        
        # Create table header
        thead = soup.new_tag('thead')
        tr = soup.new_tag('tr')
        
        for header in ['Player', 'Weekly Wins', 'Wordle Week (Score)']:
            th = soup.new_tag('th')
            th.string = header
            tr.append(th)
        
        thead.append(tr)
        table.append(thead)
        
        # Create table body
        tbody = soup.new_tag('tbody')
        tr = soup.new_tag('tr')
        
        td = soup.new_tag('td', attrs={'colspan': '3', 'style': 'text-align: center;'})
        td.string = "No weekly winners yet"
        tr.append(td)
        tbody.append(tr)
        
        table.append(tbody)
        season_container.append(table)
        
        # Insert season container before the all-time stats table
        all_time_table.insert_before(season_container)
        
        # Save the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully added Season table to {html_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {html_path}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    # Define the main directories
    website_dir = "website_export"
    
    # League paths
    league_paths = [
        os.path.join(website_dir, "index.html"),            # Wordle Warriorz
        os.path.join(website_dir, "gang", "index.html"),    # Wordle Gang
        os.path.join(website_dir, "pal", "index.html"),     # Wordle PAL
        os.path.join(website_dir, "party", "index.html"),   # Wordle Party
        os.path.join(website_dir, "vball", "index.html")    # Wordle Vball
    ]
    
    success_count = 0
    
    for path in league_paths:
        if os.path.exists(path):
            if insert_season_table(path):
                success_count += 1
        else:
            print(f"File not found: {path}")
    
    print(f"Added Season table to {success_count} out of {len(league_paths)} files")

if __name__ == "__main__":
    main()
