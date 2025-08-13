import os
from bs4 import BeautifulSoup

def fix_all_time_stats(html_path):
    """Fix the All-Time Stats header and description"""
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
        
        # Find the all-time stats description
        all_time_desc = stats_div.find('p', text=lambda t: t and "Average includes all games" in t)
        if all_time_desc:
            # Remove it for now, we'll add it back in the right place
            all_time_desc.extract()
        else:
            print(f"Could not find all-time stats description in {html_path}")
        
        # Find the table container
        table_container = stats_div.find('div', {'class': 'table-container'})
        if not table_container:
            print(f"Could not find table container in {html_path}")
            return False
        
        # Create a container for All-Time Stats
        all_time_container = soup.new_tag('div', attrs={'class': 'all-time-container'})
        
        # Create the All-Time Stats header
        all_time_heading = soup.new_tag('h3', attrs={'style': 'margin-top: 20px; margin-bottom: 10px; color: #6aaa64;'})
        all_time_heading.string = 'All-Time Stats'
        all_time_container.append(all_time_heading)
        
        # Create the All-Time Stats description
        desc_text = "Average includes all games. Failed attempts (X/6) count as 7 in the average calculation."
        new_desc = soup.new_tag('p', attrs={'style': 'margin-bottom: 15px; font-size: 14px;'})
        new_desc.string = desc_text
        all_time_container.append(new_desc)
        
        # Move the table into the all-time container
        table = table_container.find('table')
        if table:
            new_table_container = soup.new_tag('div', attrs={'class': 'table-container'})
            new_table_container.append(table)
            all_time_container.append(new_table_container)
            table_container.replace_with(all_time_container)
        else:
            print(f"Could not find table in {html_path}")
            return False
        
        # Save the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully fixed All-Time Stats in {html_path}")
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
            if fix_all_time_stats(path):
                success_count += 1
        else:
            print(f"File not found: {path}")
    
    print(f"Fixed All-Time Stats in {success_count} out of {len(league_paths)} files")

if __name__ == "__main__":
    main()
