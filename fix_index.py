import os
import json
from bs4 import BeautifulSoup

# Configuration
EXPORT_DIR = "website_export"
CONFIG_FILE = "league_config.json"

def get_league_config():
    """Load league configuration"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading league configuration: {e}")
        return None

def fix_index_page():
    """Recreate the index page tabs and structure"""
    league_config = get_league_config()
    if not league_config:
        print("Failed to load league configuration")
        return False
    
    # Get default league
    default_league = league_config['leagues'][0]
    default_league_name = default_league['name']
    
    # Create a completely new index page structure
    index_path = os.path.join(EXPORT_DIR, "index.html")
    
    try:
        # Load the current page to preserve as much as possible
        with open(index_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            
        # Update the header title
        header_title = soup.select_one('header .title')
        if header_title:
            header_title.string = default_league_name
        
        # Reset page title
        title_tag = soup.select_one('title')
        if title_tag:
            title_tag.string = f"{default_league_name} - Wordle League"
        
        # Clear and fix the tab buttons
        tab_buttons = soup.select_one('.tab-buttons.tabs')
        if tab_buttons:
            tab_buttons.clear()
            
            latest_button = soup.new_tag('button', attrs={'class': 'tab-button active', 'data-tab': 'latest'})
            latest_button.string = 'Latest Scores'
            tab_buttons.append(latest_button)
            
            weekly_button = soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'weekly'})
            weekly_button.string = 'Weekly Totals'
            tab_buttons.append(weekly_button)
            
            stats_button = soup.new_tag('button', attrs={'class': 'tab-button', 'data-tab': 'stats'})
            stats_button.string = 'Season / All-Time Stats'
            tab_buttons.append(stats_button)
        
        # Fix the latest tab content - add View This Week button
        latest_tab = soup.select_one('#latest')
        if latest_tab:
            # Clear tab content
            latest_tab.clear()
            
            # Add content with View This Week button
            title_h2 = soup.new_tag('h2', style="text-align: center; margin: 20px 0;")
            title_h2.string = "Latest Scores"
            latest_tab.append(title_h2)
            
            button_div = soup.new_tag('div', style="text-align: center; margin: 30px 0;")
            button_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_name.lower().replace(' ', '-')}.html", attrs={'class': 'button'})
            button_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            button_link.string = "View This Week"
            button_div.append(button_link)
            latest_tab.append(button_div)
        
        # Fix weekly tab content
        weekly_tab = soup.select_one('#weekly')
        if weekly_tab:
            weekly_tab.clear()
            
            title_h2 = soup.new_tag('h2', style="text-align: center; margin: 20px 0;")
            title_h2.string = "Weekly Totals"
            weekly_tab.append(title_h2)
            
            msg_p = soup.new_tag('p', style="text-align: center;")
            msg_p.string = "Weekly statistics are available on the weekly pages."
            weekly_tab.append(msg_p)
            
            button_div = soup.new_tag('div', style="text-align: center; margin: 30px 0;")
            button_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_name.lower().replace(' ', '-')}.html", attrs={'class': 'button'})
            button_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            button_link.string = "View This Week"
            button_div.append(button_link)
            weekly_tab.append(button_div)
            
        # Fix stats tab content
        stats_tab = soup.select_one('#stats')
        if stats_tab:
            stats_tab.clear()
            
            title_h2 = soup.new_tag('h2', style="text-align: center; margin: 20px 0;")
            title_h2.string = "Season 1"
            stats_tab.append(title_h2)
            
            msg_p = soup.new_tag('p', style="text-align: center; font-style: italic;")
            msg_p.string = "Weekly wins are tracked here. First player to reach 4 wins is the Season Winner!"
            stats_tab.append(msg_p)
            
            button_div = soup.new_tag('div', style="text-align: center; margin: 30px 0;")
            button_link = soup.new_tag('a', href=f"weeks/aug-4th-(14)-{default_league_name.lower().replace(' ', '-')}.html", attrs={'class': 'button'})
            button_link['style'] = "display: inline-block; padding: 10px 20px; text-decoration: none; color: white; background-color: #6aaa64; border-radius: 4px;"
            button_link.string = "View Current Week"
            button_div.append(button_link)
            stats_tab.append(button_div)
        
        # Save the updated index page
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        print(f"Successfully fixed index page with proper tabs and button")
        return True
    except Exception as e:
        print(f"Error fixing index page: {e}")
        return False

if __name__ == "__main__":
    print("Fixing main index page structure...")
    if fix_index_page():
        print("Main index page fixed successfully!")
        print("You can run an HTTP server to test locally with: python -m http.server 8080 -d website_export")
    else:
        print("Failed to fix main index page.")
