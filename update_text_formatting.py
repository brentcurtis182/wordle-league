import os
from bs4 import BeautifulSoup, NavigableString

def update_text_formatting(html_path):
    """Update text formatting in the HTML file"""
    print(f"Processing {html_path}...")
    
    try:
        # Read the HTML file
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find the Season container
        season_container = soup.find('div', {'class': 'season-container'})
        if not season_container:
            print(f"Could not find season container in {html_path}")
            return False
            
        # Find the Season description paragraph
        season_desc = season_container.find('p')
        if season_desc:
            # Make the paragraph text italic
            season_desc['style'] = season_desc.get('style', '') + '; font-style: italic;'
            
            # Make "4 weekly wins" bold
            desc_text = season_desc.string
            if "4 weekly wins" in desc_text:
                # Clear existing text
                season_desc.string = ''
                
                # Split text around "4 weekly wins"
                parts = desc_text.split("4 weekly wins")
                
                # Add parts with bold for "4 weekly wins"
                season_desc.append(NavigableString(parts[0]))
                bold = soup.new_tag('b')
                bold.string = "4 weekly wins"
                season_desc.append(bold)
                season_desc.append(NavigableString(parts[1]))
            else:
                print(f"Could not find '4 weekly wins' text in {html_path}")
        else:
            print(f"Could not find season description in {html_path}")
        
        # Find the All-Time Stats container
        all_time_container = soup.find('div', {'class': 'all-time-container'})
        if all_time_container:
            # Find the All-Time Stats description paragraph
            all_time_desc = all_time_container.find('p')
            if all_time_desc:
                # Make the paragraph text italic
                all_time_desc['style'] = all_time_desc.get('style', '') + '; font-style: italic;'
            else:
                print(f"Could not find all-time description in {html_path}")
        else:
            print(f"Could not find all-time container in {html_path}")
        
        # Save the file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully updated text formatting in {html_path}")
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
            if update_text_formatting(path):
                success_count += 1
        else:
            print(f"File not found: {path}")
    
    print(f"Updated text formatting in {success_count} out of {len(league_paths)} files")

if __name__ == "__main__":
    main()
