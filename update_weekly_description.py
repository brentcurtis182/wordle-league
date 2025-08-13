import os
from bs4 import BeautifulSoup

def update_weekly_description(html_path):
    """Update text formatting for the weekly tab description"""
    print(f"Processing {html_path}...")
    
    try:
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the weekly stats div
        weekly_div = soup.find('div', {'id': 'weekly'})
        if not weekly_div:
            print(f"Could not find weekly div in {html_path}")
            return False
            
        # Find the weekly description paragraph
        # Usually comes after h2 and before the table
        weekly_desc = None
        h2 = weekly_div.find('h2')
        if h2:
            # Look for a paragraph after the h2
            weekly_desc = h2.find_next('p')
            
        if weekly_desc:
            # Make the paragraph text italic
            weekly_desc['style'] = weekly_desc.get('style', '') + '; font-style: italic;'
        else:
            print(f"Could not find weekly description in {html_path}")
            
        # Save the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully updated weekly description in {html_path}")
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
            if update_weekly_description(path):
                success_count += 1
        else:
            print(f"File not found: {path}")
    
    print(f"Updated weekly descriptions in {success_count} out of {len(league_paths)} files")

if __name__ == "__main__":
    main()
