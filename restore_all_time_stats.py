import os
from bs4 import BeautifulSoup

def restore_all_time_stats(league_html_path, backup_html_path):
    """Restore the All-Time Stats table from the backup while keeping the Season table"""
    print(f"Processing {league_html_path}...")
    
    try:
        # Read the current HTML file
        with open(league_html_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        
        # Read the backup HTML file
        with open(backup_html_path, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        
        # Parse with BeautifulSoup
        current_soup = BeautifulSoup(current_content, 'html.parser')
        backup_soup = BeautifulSoup(backup_content, 'html.parser')
        
        # Find the current stats div
        current_stats_div = current_soup.find('div', {'id': 'stats'})
        if not current_stats_div:
            print(f"Could not find stats div in {league_html_path}")
            return False
            
        # Find the backup stats div and extract the All-Time Stats table
        backup_stats_div = backup_soup.find('div', {'id': 'stats'})
        if not backup_stats_div:
            print(f"Could not find stats div in backup")
            return False
            
        # Get the backup table
        backup_table = backup_stats_div.find('table')
        if not backup_table:
            print(f"Could not find table in backup")
            return False
        
        # Find the All-Time Stats section
        all_time_container = current_stats_div.find('div', {'class': 'all-time-container'})
        if not all_time_container:
            print(f"Could not find all-time container in {league_html_path}")
            return False
            
        # Find the table container in the All-Time Stats section
        table_container = all_time_container.find('div', {'class': 'table-container'})
        if not table_container:
            print(f"Could not find table container in all-time section")
            return False
            
        # Replace the table with the backup table
        current_table = table_container.find('table')
        if current_table:
            current_table.replace_with(backup_table)
        else:
            table_container.append(backup_table)
        
        # Save the file
        with open(league_html_path, 'w', encoding='utf-8') as f:
            f.write(str(current_soup))
        
        print(f"Successfully restored All-Time Stats in {league_html_path}")
        return True
        
    except Exception as e:
        print(f"Error processing {league_html_path}: {e}")
        import traceback
        print(traceback.format_exc())
        return False

def main():
    # Define paths
    backup_dir = "website_export_backup_20250810_221305"
    current_dir = "website_export"
    
    # Define league files
    leagues = [
        {"current": os.path.join(current_dir, "gang", "index.html"), 
         "backup": os.path.join(backup_dir, "gang", "index.html")},
        {"current": os.path.join(current_dir, "pal", "index.html"), 
         "backup": os.path.join(backup_dir, "pal", "index.html")},
        {"current": os.path.join(current_dir, "party", "index.html"), 
         "backup": os.path.join(backup_dir, "party", "index.html")},
        {"current": os.path.join(current_dir, "vball", "index.html"), 
         "backup": os.path.join(backup_dir, "vball", "index.html")}
    ]
    
    success_count = 0
    
    for league in leagues:
        current_path = league["current"]
        backup_path = league["backup"]
        
        if os.path.exists(current_path) and os.path.exists(backup_path):
            if restore_all_time_stats(current_path, backup_path):
                success_count += 1
        else:
            print(f"Files not found: {current_path} or {backup_path}")
    
    print(f"Restored All-Time Stats in {success_count} out of {len(leagues)} files")

if __name__ == "__main__":
    main()
