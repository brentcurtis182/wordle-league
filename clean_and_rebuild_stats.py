import os
from bs4 import BeautifulSoup

def completely_rebuild_stats(html_path):
    """Clean up and rebuild stats section to remove duplicates"""
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
        
        # Save just the h2 title "Season / All-Time Stats"
        h2_title = stats_div.find('h2')
        if not h2_title:
            print(f"Could not find h2 title in {html_path}")
            return False
        
        # Extract the raw stats table data
        all_time_table = None
        table = stats_div.find('table')
        if table:
            # Make a deep copy of the table rows
            rows = []
            for tr in table.find_all('tr'):
                rows.append(str(tr))
        else:
            print(f"Could not find stats table in {html_path}")
            return False
        
        # Clear everything in the stats div except the h2 title
        stats_div.clear()
        stats_div.append(h2_title)
        
        # 1. Create Season Container
        season_container = soup.new_tag('div', attrs={'class': 'season-container', 'style': 'margin-bottom: 30px;'})
        
        # Add Season 1 heading
        season_heading = soup.new_tag('h3', attrs={'style': 'margin-bottom: 10px; color: #6aaa64;'})
        season_heading.string = 'Season 1'
        season_container.append(season_heading)
        
        # Add Season description
        desc_text = "If players are tied at the end of the week, then both players get a weekly win. First Player to get 4 weekly wins, is the Season Champ!"
        season_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
        season_desc.string = desc_text
        season_container.append(season_desc)
        
        # Create Season table
        season_table = soup.new_tag('table', attrs={'class': 'season-table'})
        
        # Create table header
        thead = soup.new_tag('thead')
        tr = soup.new_tag('tr')
        
        for header in ['Player', 'Weekly Wins', 'Wordle Week (Score)']:
            th = soup.new_tag('th')
            th.string = header
            tr.append(th)
        
        thead.append(tr)
        season_table.append(thead)
        
        # Create table body
        tbody = soup.new_tag('tbody')
        tr = soup.new_tag('tr')
        
        td = soup.new_tag('td', attrs={'colspan': '3', 'style': 'text-align: center;'})
        td.string = "No weekly winners yet"
        tr.append(td)
        tbody.append(tr)
        
        season_table.append(tbody)
        season_container.append(season_table)
        
        # Add Season container to stats div
        stats_div.append(season_container)
        
        # 2. Create All-Time Stats Container
        all_time_container = soup.new_tag('div', attrs={'class': 'all-time-container'})
        
        # Add All-Time Stats heading
        all_time_heading = soup.new_tag('h3', attrs={'style': 'margin-top: 20px; margin-bottom: 10px; color: #6aaa64;'})
        all_time_heading.string = 'All-Time Stats'
        all_time_container.append(all_time_heading)
        
        # Add All-Time Stats description
        all_time_desc_text = "Average includes all games. Failed attempts (X/6) count as 7 in the average calculation."
        all_time_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
        all_time_desc.string = all_time_desc_text
        all_time_container.append(all_time_desc)
        
        # Create table container
        table_container = soup.new_tag('div', attrs={'class': 'table-container'})
        
        # Rebuild the table with the saved rows
        new_table = soup.new_tag('table')
        
        # Append the original table rows
        for row_html in rows:
            row = BeautifulSoup(row_html, 'html.parser')
            new_table.append(row)
        
        table_container.append(new_table)
        all_time_container.append(table_container)
        
        # Add All-Time container to stats div
        stats_div.append(all_time_container)
        
        # Save the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully cleaned and rebuilt stats in {html_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {html_path}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    # Define the main directories
    website_dir = "website_export"
    
    # League paths - focus on the ones with issues
    league_paths = [
        os.path.join(website_dir, "gang", "index.html"),    # Wordle Gang
        os.path.join(website_dir, "pal", "index.html"),     # Wordle PAL
        os.path.join(website_dir, "party", "index.html"),   # Wordle Party
        os.path.join(website_dir, "vball", "index.html")    # Wordle Vball
    ]
    
    success_count = 0
    
    for path in league_paths:
        if os.path.exists(path):
            if completely_rebuild_stats(path):
                success_count += 1
        else:
            print(f"File not found: {path}")
    
    print(f"Fixed {success_count} out of {len(league_paths)} files")

if __name__ == "__main__":
    main()
