import os
from bs4 import BeautifulSoup

def fix_button_tabs():
    """Fix button tab names in all league HTML files to show 'Season / All-Time Stats'"""
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
            
            # Find the button for stats
            stats_button = soup.select_one('button.tab-button[data-tab="stats"]')
            
            if stats_button:
                old_text = stats_button.text
                stats_button.string = "Season / All-Time Stats"
                print(f"Updated button tab from '{old_text}' to 'Season / All-Time Stats'")
                
                # Write the updated HTML
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            else:
                print(f"WARNING: Could not find stats button tab in {path}")
        else:
            print(f"WARNING: File not found: {path}")
    
    print("Button tab name update complete!")

if __name__ == "__main__":
    fix_button_tabs()
