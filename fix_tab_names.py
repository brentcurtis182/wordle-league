import os
from bs4 import BeautifulSoup

def fix_tab_names():
    """Fix tab names in all league HTML files to show 'Season / All-Time Stats'"""
    website_dir = "website_export"
    
    # League paths
    league_paths = [
        os.path.join(website_dir, "index.html"),            # Wordle Warriorz
        os.path.join(website_dir, "gang", "index.html"),    # Wordle Gang
        os.path.join(website_dir, "pal", "index.html"),     # Wordle PAL
        os.path.join(website_dir, "party", "index.html"),   # Wordle Party
        os.path.join(website_dir, "vball", "index.html")    # Wordle Vball
    ]
    
    for path in league_paths:
        if os.path.exists(path):
            print(f"Processing {path}...")
            
            # Read the HTML file
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find the tab link for stats
            tab_links = soup.select('ul.nav.nav-tabs li a')
            
            # Print all tab links for debugging
            print(f"Found {len(tab_links)} tab links:")
            for i, link in enumerate(tab_links):
                print(f"  {i+1}: href={link.get('href', 'None')} - text={link.text}")
            
            # Find and update the stats tab specifically - try multiple selectors
            stats_tab = None
            
            # Method 1: Direct href match
            stats_tab = soup.select_one('ul.nav.nav-tabs li a[href="#stats"]')
            if stats_tab:
                print(f"Found stats tab via href: {stats_tab.text}")
            
            # Method 2: Text match (if href method failed)
            if not stats_tab:
                for link in tab_links:
                    if "stats" in link.text.lower():
                        stats_tab = link
                        print(f"Found stats tab via text: {stats_tab.text}")
                        break
            
            if stats_tab:
                old_text = stats_tab.text
                stats_tab.string = "Season / All-Time Stats"
                print(f"Updated tab from '{old_text}' to 'Season / All-Time Stats'")
                
                # Write the updated HTML
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            else:
                print(f"WARNING: Could not find stats tab in {path}")
        else:
            print(f"WARNING: File not found: {path}")
    
    print("Tab name update complete!")

if __name__ == "__main__":
    fix_tab_names()
