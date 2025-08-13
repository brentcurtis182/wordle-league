import os
import shutil
import re
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

def restore_original_structure():
    """
    Restores the original league structure with each league having its own page,
    preserving the Latest Scores, Weekly Totals with days of the week, and Season/All-Time Stats tabs.
    """
    print("Starting restoration process...")
    
    # Create backup of current site
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_site_backup = f"website_export_backup_{timestamp}"
    print(f"Creating backup of current site to {current_site_backup}")
    if os.path.exists("website_export"):
        shutil.copytree("website_export", current_site_backup)
    
    # Base template - using the known good August 6th backup for structure
    # We'll incorporate season changes templates and features
    aug6_template_path = "website_export_backup/backups/index_20250806_131435.html"
    season_template_path = "backups/season_changes/index.html.bak"
    
    if not os.path.exists(aug6_template_path):
        print(f"August 6th template not found: {aug6_template_path}")
        return
    
    if not os.path.exists(season_template_path):
        print(f"Season changes template not found: {season_template_path}")
        return
    
    # Get today's date and Wordle number
    today = datetime.now()
    today_formatted = today.strftime("%B %d, %Y")
    
    # Wordle #1513 is August 10, 2025
    wordle_num = 1513
    
    print(f"Updating template with Wordle #{wordle_num} - {today_formatted}")
    
    # Load the base HTML template
    with open(aug6_template_path, 'r', encoding='utf-8') as f:
        base_html_content = f.read()
    
    # Load the season template to extract the enhanced table structures
    with open(season_template_path, 'r', encoding='utf-8') as f:
        season_html_content = f.read()
    
    # Parse both templates
    base_soup = BeautifulSoup(base_html_content, 'html.parser')
    season_soup = BeautifulSoup(season_html_content, 'html.parser')
    
    # Update the title and Wordle number
    wordle_date_element = base_soup.select_one('h2[style*="color: #6aaa64"]')
    if wordle_date_element:
        wordle_date_element.string = f"Wordle #{wordle_num} - {today_formatted}"
    
    # Update "Weekly Totals" tab to include days of the week
    # Extract the weekly table structure from season template
    weekly_table_headers = season_soup.select_one('#weekly table thead')
    if weekly_table_headers:
        # Replace the headers in the base template
        base_weekly_headers = base_soup.select_one('#weekly table thead')
        if base_weekly_headers:
            base_weekly_headers.replace_with(weekly_table_headers)
    
    # Update "All-Time Stats" to "Season / All-Time Stats"
    stats_button = base_soup.select_one('button.tab-button[data-tab="stats"]')
    if stats_button:
        stats_button.string = "Season / All-Time Stats"
    
    # Create the season stats table structure
    stats_div = base_soup.select_one('#stats')
    if stats_div:
        # Update the title
        stats_title = stats_div.select_one('h2')
        if stats_title:
            stats_title.string = "Season / All-Time Stats"
        
        # Add season winners table above the all-time stats
        season_table_html = """
        <h3 style="margin-top: 15px; margin-bottom: 10px;">Season 1 Weekly Winners</h3>
        <p style="margin-top: 0; margin-bottom: 10px; font-size: 0.9em; font-style: italic;">
            First player to reach 4 weekly wins is the Season Champion!
        </p>
        <div class="table-container season-winners">
            <table>
                <thead>
                    <tr>
                        <th>Week</th>
                        <th>Winner</th>
                        <th>Score</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><a href="weeks/july-28th-(13).html">July 28, 2025</a></td>
                        <td>Joanna</td>
                        <td>14</td>
                    </tr>
                    <tr>
                        <td><a href="weeks/aug-4th-(14).html">August 4, 2025</a></td>
                        <td>Brent</td>
                        <td>13</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <h3 style="margin-top: 25px; margin-bottom: 10px;">All-Time Stats</h3>
        """
        
        # Insert the season table before the all-time stats table
        all_time_table = stats_div.select_one('.table-container')
        if all_time_table:
            all_time_table.insert_before(BeautifulSoup(season_table_html, 'html.parser'))
    
    # For each league, create a separate index file
    leagues = ["wordle-warriorz", "wordle-gang", "wordle-pal", "wordle-party", "wordle-vball"]
    league_display_names = {
        "wordle-warriorz": "Wordle Warriorz",
        "wordle-gang": "Wordle Gang",
        "wordle-pal": "Wordle PAL",
        "wordle-party": "Wordle Party",
        "wordle-vball": "Wordle Vball"
    }
    
    # Process leagues
    for league in leagues:
        league_name = league_display_names.get(league, league.replace("-", " ").title())
        print(f"Processing {league_name}...")
        
        # Make a copy of the base soup for this league
        league_soup = BeautifulSoup(str(base_soup), 'html.parser')
        
        # Update league name in the header
        if league_soup.select('header .title'):
            league_soup.select('header .title')[0].string = league_name
        
        # Set the page title
        if league_soup.title:
            league_soup.title.string = f"{league_name} - Wordle League"
        
        # Create league directory if it doesn't exist
        league_dir = os.path.join("website_export", league if league != "wordle-warriorz" else "")
        os.makedirs(league_dir, exist_ok=True)
        
        # Create weeks directory if needed
        weeks_dir = os.path.join(league_dir, "weeks")
        os.makedirs(weeks_dir, exist_ok=True)
        
        # Create days directory if needed
        days_dir = os.path.join(league_dir, "days")
        os.makedirs(days_dir, exist_ok=True)
        
        # Save the updated content to the league's index.html
        output_path = os.path.join(league_dir, "index.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(str(league_soup))
            
        print(f"Created {output_path}")
        
        # Update the week links in the season table
        update_week_links(output_path, league)
    
    # Ensure landing page exists and links to each league
    create_landing_page(leagues, league_display_names)
    
    print("\nRestoration complete! Next steps:")
    print("1. Run your update_data_keep_format.py script to populate tables with current scores")
    print("2. Check that all leagues have the correct structure and tabs")
    print("3. Verify the season stats table shows weekly winners correctly")

def update_week_links(html_path, league):
    """Update the week links in the season table to point to the correct league files."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find all week links in the season table
    week_links = soup.select('.season-winners a')
    for link in week_links:
        href = link.get('href', '')
        if 'weeks/' in href:
            # Update link to include league name
            base_name = href.split('/')[-1].split('.')[0]
            new_href = f"weeks/{base_name}-{league}.html"
            link['href'] = new_href
    
    # Save the updated content
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

def create_landing_page(leagues, league_display_names):
    """Creates a simple landing page that links to each league."""
    print("Creating landing page...")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wordle Leagues</title>
    <link rel="stylesheet" href="styles.css">
    <style>
        .league-links {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 30px;
            gap: 15px;
        }
        .league-link {
            display: inline-block;
            padding: 10px 20px;
            background-color: #6aaa64;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 18px;
            transition: background-color 0.3s;
            min-width: 200px;
            text-align: center;
        }
        .league-link:hover {
            background-color: #538d4e;
        }
    </style>
</head>
<body>
    <header style="padding: 10px 0; margin-bottom: 10px;">
        <div class="container" style="padding: 10px; text-align: center;">
            <h1 class="title" style="font-size: 24px; margin-bottom: 0; text-align: center;">Wordle Leagues</h1>
        </div>
    </header>
    
    <div class="container">
        <div class="league-links">
"""
    
    # Add links for each league
    for league in leagues:
        league_path = "" if league == "wordle-warriorz" else f"{league}/"
        league_name = league_display_names.get(league, league.replace("-", " ").title())
        html_content += f'            <a class="league-link" href="{league_path}">{league_name}</a>\n'
    
    html_content += """        </div>
    </div>
</body>
</html>
"""
    
    # Save the landing page
    with open("website_export/index.html", 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("Landing page created at website_export/index.html")

if __name__ == "__main__":
    restore_original_structure()
