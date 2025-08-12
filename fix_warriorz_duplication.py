import os
from bs4 import BeautifulSoup
from datetime import datetime

def fix_warriorz_duplication():
    """Fix the duplication of All-Time Stats in the Wordle Warriorz page"""
    warriorz_path = "website_export/index.html"
    
    # Read the HTML file
    with open(warriorz_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the stats div
    stats_div = soup.find('div', {'id': 'stats'})
    if not stats_div:
        print("Could not find stats div")
        return False
    
    # Check for duplication - there should be only one season container and one all-time container
    season_containers = stats_div.find_all('div', {'class': 'season-container'})
    all_time_containers = stats_div.find_all('div', {'class': 'all-time-container'})
    
    print(f"Found {len(season_containers)} season containers and {len(all_time_containers)} all-time containers")
    
    # Keep the first season container, remove others
    if len(season_containers) > 1:
        for container in season_containers[1:]:
            container.decompose()
    
    # There might be tables directly under stats_div that should be removed
    for element in stats_div.find_all(['h2', 'p', 'div', 'table']):
        # Skip if it's inside a container
        parent_is_container = False
        for parent in element.parents:
            if parent.get('class') and ('season-container' in parent.get('class') or 'all-time-container' in parent.get('class')):
                parent_is_container = True
                break
        
        if not parent_is_container and (element.name == 'h2' and 'All-Time Stats' in element.text or 
                                         element.name == 'p' and 'All time stats includes' in element.text or
                                         element.name == 'table' and not element.get('class')):
            print(f"Removing duplicate element: {element.name}")
            element.decompose()
    
    # Make sure we have only one all-time container with the correct content
    if len(all_time_containers) > 0:
        # Keep only the first all-time container
        for container in all_time_containers[1:]:
            container.decompose()
            
        all_time_container = all_time_containers[0]
        
        # Make sure it has the h2 header
        if not all_time_container.find('h2'):
            h2 = soup.new_tag('h2')
            h2.string = "All-Time Stats"
            all_time_container.insert(0, h2)
        
        # Make sure it has the description
        if not all_time_container.find('p'):
            p = soup.new_tag('p')
            p.string = "All time stats includes every game played since this league began!"
            p['style'] = 'font-style: italic;'
            all_time_container.insert(1, p)
        
        # Make sure it has a table
        if not all_time_container.find('table'):
            table = soup.new_tag('table')
            table['id'] = 'all-time-stats'
            table['class'] = 'table table-striped'
            all_time_container.append(table)
    else:
        # Create a new all-time container
        all_time_container = soup.new_tag('div')
        all_time_container['class'] = 'all-time-container'
        
        # Create header
        h2 = soup.new_tag('h2')
        h2.string = "All-Time Stats"
        all_time_container.append(h2)
        
        # Create description
        p = soup.new_tag('p')
        p.string = "All time stats includes every game played since this league began!"
        p['style'] = 'font-style: italic;'
        all_time_container.append(p)
        
        # Create table
        table = soup.new_tag('table')
        table['id'] = 'all-time-stats'
        table['class'] = 'table table-striped'
        all_time_container.append(table)
        
        # Add to stats div
        stats_div.append(all_time_container)
    
    # Write the fixed HTML
    with open(warriorz_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print("Fixed the All-Time Stats duplication in the Wordle Warriorz page")
    return True

if __name__ == "__main__":
    fix_warriorz_duplication()
